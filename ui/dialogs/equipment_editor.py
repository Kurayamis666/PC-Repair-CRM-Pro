# ui/dialogs/equipment_editor.py
"""
Диалог редактирования оборудования для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Запросы к таблице employees (не clients), валидация, переводы
✅ УЛУЧШЕНО: Индикатор загрузки, адаптивность, маппинг значений
✅ СОВМЕСТИМО: Интеграция с системой тем, переводов и утилит
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Callable, Dict, Any, List
import re

from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.toast import ToastNotification
from utils.validators import validate_string_length, validate_required


class EquipmentEditorDialog(ctk.CTkToplevel):
    """
    Диалог редактирования оборудования с полной валидацией
    
    ✅ Запросы к таблице employees (не clients)
    ✅ Валидация всех входных данных
    ✅ Индикатор загрузки при сохранении
    ✅ Полный перевод через get_text()
    ✅ Безопасный маппинг client_id через словарь
    """
    
    # ⚙️ Конфигурация валидации
    MIN_MODEL_LENGTH: int = 2
    MAX_MODEL_LENGTH: int = 100
    MAX_SERIAL_LENGTH: int = 100
    ALLOWED_SERIAL_CHARS: str = r"^[a-zA-Z0-9\s\-\._/()#]+$"  # Разрешённые символы для серийника
    
    # 🗂️ Типы устройств с переводом
    DEVICE_TYPES: List[Dict[str, str]] = [
        {"value": "Laptop", "ru": "💻 Ноутбук", "en": "💻 Laptop"},
        {"value": "PC", "ru": "🖥️ ПК", "en": "🖥️ Desktop PC"},
        {"value": "Tablet", "ru": "📱 Планшет", "en": "📱 Tablet"},
        {"value": "Phone", "ru": "📞 Телефон", "en": "📞 Phone"},
        {"value": "Accessory", "ru": "🔌 Аксессуар", "en": "🔌 Accessory"},
        {"value": "Other", "ru": "📦 Другое", "en": "📦 Other"},
    ]
    
    def __init__(
        self,
        parent,
        equipment_id: Optional[int] = None,
        lang: str = "ru",
        on_save: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        
        self.equipment_id = equipment_id
        self.lang = lang
        self.on_save = on_save
        self.db = DatabaseConnection()
        
        # 🔧 UI элементы (для обновления)
        self._client_menu: Optional[ctk.CTkOptionMenu] = None
        self._model_entry: Optional[ctk.CTkEntry] = None
        self._sn_entry: Optional[ctk.CTkEntry] = None
        self._type_menu: Optional[ctk.CTkOptionMenu] = None
        self._save_btn: Optional[ctk.CTkButton] = None
        self._loading_label: Optional[ctk.CTkLabel] = None
        
        # 🗂️ Маппинги для ComboBox
        self._employees_map: Dict[str, int] = {}  # "1 - Иванов" → 1
        self._type_mapping: Dict[str, str] = {}  # "💻 Ноутбук" → "Laptop"
        
        # ✅ Переведённый заголовок
        title_key = "new_equipment" if not equipment_id else "edit_equipment"
        title = get_text(title_key, self.lang) or ("💻 Новое оборудование" if not equipment_id else "✏️ Редактирование оборудования")
        self.title(title)
        
        self.geometry("480x450")
        self.minsize(420, 400)
        self.transient(parent)
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        self._build_ui()
        
        self.after(100, lambda: self._model_entry.focus_set() if self._model_entry else None)
        
        if equipment_id:
            self._load_data()
        
        # Центрирование и модальность — после построения UI
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 450) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.grab_set()
    
    def _build_ui(self) -> None:
        """Построение интерфейса с полным переводом"""
        
        # Заголовок с акцентом
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        accent = ctk.CTkFrame(header, fg_color=ColorTheme.SECONDARY, height=3, corner_radius=2)
        accent.pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkLabel(
            header,
            text="💻 " + self.title(),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(pady=(8, 12))
        
        # Форма
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=16)
        
        # Сотрудник
        ctk.CTkLabel(
            form, 
            text=f"👤  {get_text('select_employee', self.lang)} *",
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(8, 4))
        
        # ✅ Создаём маппинг: отображаемое значение → значение для БД
        employee_values = []
        self._employees_map = {}
        
        self._client_menu = ctk.CTkOptionMenu(
            form,
            values=[],
            variable=ctk.StringVar(),
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
        )
        self._client_menu.pack(fill="x", pady=4)
        
        # Загружаем сотрудников асинхронно
        self.after(10, self._load_employees)
        
        # Модель
        ctk.CTkLabel(
            form, 
            text=f"📱  {get_text('model', self.lang)} *", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(8, 4))
        
        self._model_entry = ctk.CTkEntry(
            form, 
            placeholder_text=get_text("model_placeholder", self.lang) or "Например: MacBook Pro 14",
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY,
            height=40,
            corner_radius=10,
            border_width=2,
            border_color=ColorTheme.BORDER,
            font=ctk.CTkFont(size=13),
        )
        self._model_entry.pack(fill="x", pady=4)
        self._model_entry.bind("<KeyRelease>", lambda e: self._validate_model_length())
        self._model_entry.bind("<FocusIn>", lambda e: self._model_entry.configure(border_color=ColorTheme.PRIMARY))
        self._model_entry.bind("<FocusOut>", lambda e: self._model_entry.configure(border_color=ColorTheme.BORDER))
        
        # Серийный номер
        ctk.CTkLabel(
            form, 
            text="🔢  " + get_text("serial_number", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(8, 4))
        
        self._sn_entry = ctk.CTkEntry(
            form, 
            placeholder_text=get_text("serial_placeholder", self.lang) or "SN123456 или оставить пустым",
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY,
            height=40,
            corner_radius=10,
            border_width=2,
            border_color=ColorTheme.BORDER,
            font=ctk.CTkFont(size=13),
        )
        self._sn_entry.pack(fill="x", pady=4)
        self._sn_entry.bind("<FocusIn>", lambda e: self._sn_entry.configure(border_color=ColorTheme.PRIMARY))
        self._sn_entry.bind("<FocusOut>", lambda e: self._sn_entry.configure(border_color=ColorTheme.BORDER))
        
        # Тип устройства
        ctk.CTkLabel(
            form, 
            text="🔧  " + get_text("device_type", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(8, 4))
        
        # ✅ Создаём маппинг типов: отображаемое → значение для БД
        type_values = []
        self._type_mapping = {}
        
        for dtype in self.DEVICE_TYPES:
            display = dtype[self.lang] if self.lang in dtype else dtype["ru"]
            type_values.append(display)
            self._type_mapping[display] = dtype["value"]
        
        self._type_var = ctk.StringVar(value=self._type_mapping.get("💻 Ноутбук", "Laptop"))
        self._type_menu = ctk.CTkOptionMenu(
            form,
            values=type_values,
            variable=self._type_var,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
        )
        self._type_menu.pack(fill="x", pady=4)
        
        # ⏳ Индикатор загрузки (скрыт по умолчанию)
        self._loading_label = ctk.CTkLabel(
            form,
            text="",
            text_color=ColorTheme.INFO,
            font=ctk.CTkFont(size=11)
        )
        self._loading_label.pack(pady=5)
        
        # Разделитель
        ctk.CTkFrame(self, fg_color=ColorTheme.BORDER, height=1).pack(fill="x", padx=16)
        
        # Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=16)
        
        ctk.CTkButton(
            btn_frame, 
            text=get_text("cancel", self.lang), 
            command=self.destroy,
            height=38, 
            fg_color=ColorTheme.BG_INPUT,
            hover_color=ColorUtils.darken(ColorTheme.BG_INPUT, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=6, fill="x", expand=True)
        
        self._save_btn = ctk.CTkButton(
            btn_frame, 
            text="💾 " + get_text("save", self.lang), 
            command=self._save,
            height=38, 
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 15),
            text_color=ColorTheme.TEXT_PRIMARY,
            corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._save_btn.pack(side="left", padx=6, fill="x", expand=True)
    
    def _set_loading(self, loading: bool) -> None:
        """Показать/скрыть индикатор загрузки"""
        if loading:
            if self._loading_label:
                self._loading_label.configure(text="🔄 " + (get_text("saving", self.lang) or "Сохранение..."))
            if self._save_btn:
                self._save_btn.configure(state="disabled")
            # Блокируем поля
            for widget in [self._client_menu, self._model_entry, self._sn_entry, self._type_menu]:
                if widget:
                    widget.configure(state="disabled")
        else:
            if self._loading_label:
                self._loading_label.configure(text="")
            if self._save_btn:
                self._save_btn.configure(state="normal")
            for widget in [self._client_menu, self._model_entry, self._sn_entry, self._type_menu]:
                if widget:
                    widget.configure(state="normal")
    
    def _load_employees(self) -> None:
        """✅ Загрузить список сотрудников (не клиентов!) в OptionMenu"""
        try:
            with self.db.get_cursor() as cur:
                # ✅ employees.full_name вместо clients.name
                cur.execute("SELECT id, full_name FROM employees ORDER BY full_name")
                employees = cur.fetchall()
            
            if employees:
                # ✅ Формат: "ID - ФИО" для отображения, храним ID отдельно
                self._employees_map = {f"{e[0]} - {e[1]}": e[0] for e in employees}
                self._client_menu.configure(values=list(self._employees_map.keys()))
                
                # Устанавливаем первое значение по умолчанию
                first_display = list(self._employees_map.keys())[0]
                self._client_menu.set(first_display)
            else:
                self._client_menu.configure(
                    values=[get_text("no_employees", self.lang) or "📭 Нет сотрудников"], 
                    state="disabled"
                )
                
        except Exception as e:
            app_logger.exception(f"❌ Error loading employees: {e}")
            self._client_menu.configure(
                values=[f"{get_text('error_loading', self.lang)}: {e}"], 
                state="disabled"
            )
    
    def _validate_model_length(self) -> None:
        """Валидация длины модели"""
        text = self._model_entry.get().strip() if self._model_entry else ""
        if len(text) > self.MAX_MODEL_LENGTH:
            # Обрезаем до максимума
            self._model_entry.delete(self.MAX_MODEL_LENGTH, "end")
    
    def _validate_serial_format(self, serial: str) -> tuple[bool, str]:
        """Валидация формата серийного номера"""
        if not serial:
            return True, ""  # Серийник необязателен
        
        if len(serial) > self.MAX_SERIAL_LENGTH:
            return False, get_text("serial_too_long", self.lang).format(self.MAX_SERIAL_LENGTH) or f"Серийный номер не может превышать {self.MAX_SERIAL_LENGTH} символов"
        
        if not re.match(self.ALLOWED_SERIAL_CHARS, serial):
            return False, get_text("serial_invalid_chars", self.lang) or "Серийный номер может содержать только буквы, цифры, -, ., _, /, ( ), #"
        
        return True, ""
    
    def _load_data(self) -> None:
        """Загрузить данные существующего оборудования"""
        if not self.equipment_id:
            return
        
        try:
            with self.db.get_cursor() as cur:
                # ✅ employees вместо clients
                cur.execute("""
                    SELECT client_id, model, serial_number, device_type 
                    FROM equipment WHERE id = ?
                """, (self.equipment_id,))
                row = cur.fetchone()
            
            if not row:
                return
            
            client_id, model, serial, device_type = row
            
            # ✅ Устанавливаем сотрудника через маппинг
            if self._client_menu and self._employees_map:
                for display, eid in self._employees_map.items():
                    if eid == client_id:
                        self._client_menu.set(display)
                        break
            
            # ✅ Устанавливаем модель
            if self._model_entry and model:
                self._model_entry.delete(0, "end")
                self._model_entry.insert(0, model)
            
            # ✅ Устанавливаем серийный номер
            if self._sn_entry and serial:
                self._sn_entry.delete(0, "end")
                self._sn_entry.insert(0, serial)
            
            # ✅ Устанавливаем тип устройства через маппинг
            if self._type_menu and device_type:
                for display, value in self._type_mapping.items():
                    if value == device_type:
                        self._type_var.set(display)
                        break
                
        except Exception as e:
            app_logger.exception(f"❌ Error loading equipment: {e}")
            ToastNotification(self, f"{get_text('error_loading', self.lang)}: {e}", "error")
    
    def _save(self) -> None:
        """Сохранить оборудование с полной валидацией"""
        # ✅ Валидация сотрудника
        employee_display = self._client_menu.get() if self._client_menu else ""
        if not employee_display or employee_display not in self._employees_map:
            ToastNotification(self, get_text("select_employee", self.lang) or "Выберите сотрудника", "warning")
            if self._client_menu:
                self._client_menu.focus_set()
            return
        
        # ✅ Валидация модели
        model = self._model_entry.get().strip() if self._model_entry else ""
        valid, error = validate_string_length(model, min_len=self.MIN_MODEL_LENGTH, max_len=self.MAX_MODEL_LENGTH, field_name=get_text("model", self.lang))
        if not valid:
            ToastNotification(self, error, "warning")
            if self._model_entry:
                self._model_entry.focus_set()
            return
        
        # ✅ Валидация серийного номера
        serial = self._sn_entry.get().strip() if self._sn_entry else ""
        valid, error = self._validate_serial_format(serial)
        if not valid:
            ToastNotification(self, error, "warning")
            if self._sn_entry:
                self._sn_entry.focus_set()
            return
        
        # ✅ Получение ID и типа через безопасный маппинг
        employee_id = self._employees_map[employee_display]
        device_type = self._type_mapping.get(self._type_var.get(), "Other")
        
        # ✅ Показываем индикатор загрузки
        self._set_loading(True)
        
        try:
            with self.db.get_cursor() as cur:
                if self.equipment_id:
                    # 🔁 Обновление существующей записи
                    cur.execute("""
                        UPDATE equipment SET 
                            client_id = ?, model = ?, serial_number = ?, device_type = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (employee_id, model, serial, device_type, self.equipment_id))
                else:
                    # ➕ Создание новой записи
                    cur.execute("""
                        INSERT INTO equipment (client_id, model, serial_number, device_type, created_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (employee_id, model, serial, device_type))
            
            # ✅ Успешное сохранение
            ToastNotification(self, get_text("equipment_saved", self.lang) or "✅ Оборудование сохранено", "success")
            app_logger.info(f"💾 Equipment {'updated' if self.equipment_id else 'created'}: ID {self.equipment_id or 'new'}")
            
            # ✅ Вызываем колбэк обновления
            if self.on_save:
                try:
                    self.on_save()
                except Exception as e:
                    app_logger.warning(f"⚠️ on_save callback error: {e}")
            
            # ✅ Закрываем диалог
            self.destroy()
            
        except Exception as e:
            app_logger.exception(f"❌ Error saving equipment: {e}")
            ToastNotification(self, f"{get_text('error_saving', self.lang)}: {e}", "error")
        finally:
            # ✅ Скрываем индикатор загрузки
            self._set_loading(False)
    
    def destroy(self) -> None:
        """Корректное закрытие диалога"""
        # Отменяем любые отложенные задачи
        try:
            pass  # Можно добавить очистку таймеров если есть
        except:
            pass
        super().destroy()