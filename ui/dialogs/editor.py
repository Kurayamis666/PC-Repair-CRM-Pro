# ui/dialogs/editor.py
"""
Универсальный редактор записей для таблиц в PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Убран nested mainloop, добавлены переводы, валидация
✅ УЛУЧШЕНО: Динамическая генерация полей, обработка ошибок, индикатор загрузки
✅ СОВМЕСТИМО: Интеграция с системой тем, переводов и утилит
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable, List, Tuple
from datetime import datetime

from core.logger import app_logger
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.toast import ToastNotification
from utils.validators import validate_required, validate_string_length, validate_number


class RecordEditor(ctk.CTkToplevel):
    """
    Универсальное модальное окно для редактирования записей
    
    ✅ НЕ вызывает mainloop() — работает в цикле событий родителя
    ✅ Полный перевод всех текстов через get_text()
    ✅ Динамическая генерация полей на основе схемы таблицы
    ✅ Валидация данных перед сохранением
    ✅ Индикатор загрузки и обработка ошибок
    """
    
    # ⚙️ Конфигурация по умолчанию
    DEFAULT_FIELD_WIDTH: int = 400
    DEFAULT_FIELD_HEIGHT: int = 40
    MAX_TEXT_LENGTH: int = 500
    
    # 🗂️ Схема полей для известных таблиц (для динамической генерации)
    # В реальном проекте это может загружаться из БД или конфига
    TABLE_SCHEMAS: Dict[str, List[Dict[str, Any]]] = {
        "employees": [
            {"name": "full_name", "label": "full_name", "type": "text", "required": True, "max_length": 100},
            {"name": "position", "label": "position", "type": "text", "required": False, "max_length": 100},
            {"name": "phone", "label": "phone", "type": "phone", "required": False},
            {"name": "email", "label": "email", "type": "email", "required": False},
            {"name": "salary", "label": "salary", "type": "number", "required": False, "min": 0},
        ],
        "contractors": [
            {"name": "name", "label": "contractor_name", "type": "text", "required": True, "max_length": 200},
            {"name": "inn", "label": "inn", "type": "inn", "required": False},
            {"name": "phone", "label": "phone", "type": "phone", "required": False},
            {"name": "email", "label": "email", "type": "email", "required": False},
            {"name": "address", "label": "address", "type": "text", "required": False, "max_length": 300},
        ],
        "parts": [
            {"name": "name", "label": "part_name", "type": "text", "required": True, "max_length": 200},
            {"name": "sku", "label": "sku", "type": "text", "required": False, "max_length": 50},
            {"name": "quantity", "label": "quantity", "type": "number", "required": True, "min": 0},
            {"name": "unit", "label": "unit", "type": "text", "required": False, "max_length": 20},
            {"name": "cost", "label": "cost_price", "type": "number", "required": False, "min": 0},
            {"name": "price", "label": "retail_price", "type": "number", "required": False, "min": 0},
        ],
    }
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,  # ✅ CTkBaseClass вместо строгого CTk
        table_name: str,
        record_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        lang: str = "ru",
        on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
        schema: Optional[List[Dict[str, Any]]] = None,  # ✅ Позволяет передать кастомную схему
    ):
        super().__init__(parent)
        
        self.table_name = table_name
        self.record_id = record_id
        self.data = data or {}
        self.lang = lang
        self.on_save = on_save
        self.schema = schema or self.TABLE_SCHEMAS.get(table_name, [])
        
        # 🔧 UI элементы (для доступа из валидации)
        self._fields: Dict[str, ctk.CTkEntry] = {}
        self._save_btn: Optional[ctk.CTkButton] = None
        self._loading_label: Optional[ctk.CTkLabel] = None
        
        # ✅ Переведённый заголовок
        title_key = "edit_record" if record_id else "create_record"
        title = get_text(title_key, self.lang) or ("✏️ Редактирование" if record_id else "➕ Создание")
        table_label = get_text(f"table_{table_name}", self.lang) or table_name
        self.title(f"{title}: {table_label}")
        
        self.geometry("550x500")
        self.minsize(480, 450)  # ✅ Адаптивный минимальный размер
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        # 🎯 Центрирование относительно родителя
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 550) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 500) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        
        self._build_ui()
        
        # 🎯 Фокус на первое поле если есть
        self.after(100, self._focus_first_field)
    
    def _build_ui(self) -> None:
        """Построение интерфейса с динамической генерацией полей"""
        
        # 🏷️ Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        
        title_key = "edit_record" if self.record_id else "create_record"
        title = get_text(title_key, self.lang) or ("✏️ Редактирование" if self.record_id else "➕ Создание")
        table_label = get_text(f"table_{self.table_name}", self.lang) or self.table_name
        
        ctk.CTkLabel(
            header,
            text=f"{title}: {table_label}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(pady=15)
        
        # 📋 Скроллируемая форма
        form_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ✅ Динамическая генерация полей на основе схемы
        if self.schema:
            self._build_dynamic_form(form_frame)
        else:
            # ✅ Заглушка для неизвестных таблиц
            self._build_stub_form(form_frame)
        
        # ⏳ Индикатор загрузки (скрыт по умолчанию)
        self._loading_label = ctk.CTkLabel(
            self,
            text="",
            text_color=ColorTheme.INFO,
            font=ctk.CTkFont(size=11)
        )
        self._loading_label.pack(pady=5)
        
        # 🔘 Кнопки
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            buttons_frame,
            text=get_text("cancel", self.lang),
            command=self.destroy,
            width=120,
            height=35,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(side="left", padx=10)
        
        self._save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 " + get_text("save", self.lang),
            command=self._save,
            width=120,
            height=35,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
        )
        self._save_btn.pack(side="right", padx=10)
    
    def _build_dynamic_form(self, parent) -> None:
        """Построение формы на основе схемы таблицы"""
        for field_config in self.schema:
            field_name = field_config["name"]
            label_key = field_config.get("label", field_name)
            field_type = field_config.get("type", "text")
            required = field_config.get("required", False)
            max_length = field_config.get("max_length", self.MAX_TEXT_LENGTH)
            
            # ✅ Переведённая метка + индикатор обязательности
            label_text = get_text(label_key, self.lang) or field_name
            if required:
                label_text += " *"
            
            ctk.CTkLabel(
                parent,
                text=label_text,
                text_color=ColorTheme.TEXT_PRIMARY,
                anchor="w"
            ).pack(anchor="w", pady=(10, 5))
            
            # ✅ Создание поля ввода в зависимости от типа
            if field_type == "text":
                entry = ctk.CTkEntry(
                    parent,
                    placeholder_text=get_text(f"{field_name}_placeholder", self.lang),
                    width=self.DEFAULT_FIELD_WIDTH,
                    height=self.DEFAULT_FIELD_HEIGHT,
                    fg_color=ColorTheme.BG_INPUT,
                    text_color=ColorTheme.TEXT_PRIMARY,
                )
            elif field_type == "number":
                entry = ctk.CTkEntry(
                    parent,
                    placeholder_text="0",
                    width=self.DEFAULT_FIELD_WIDTH,
                    height=self.DEFAULT_FIELD_HEIGHT,
                    fg_color=ColorTheme.BG_INPUT,
                    text_color=ColorTheme.TEXT_PRIMARY,
                )
            elif field_type == "email":
                entry = ctk.CTkEntry(
                    parent,
                    placeholder_text="user@example.com",
                    width=self.DEFAULT_FIELD_WIDTH,
                    height=self.DEFAULT_FIELD_HEIGHT,
                    fg_color=ColorTheme.BG_INPUT,
                    text_color=ColorTheme.TEXT_PRIMARY,
                )
            elif field_type == "phone":
                entry = ctk.CTkEntry(
                    parent,
                    placeholder_text="+7 (999) 123-45-67",
                    width=self.DEFAULT_FIELD_WIDTH,
                    height=self.DEFAULT_FIELD_HEIGHT,
                    fg_color=ColorTheme.BG_INPUT,
                    text_color=ColorTheme.TEXT_PRIMARY,
                )
            else:
                entry = ctk.CTkEntry(
                    parent,
                    width=self.DEFAULT_FIELD_WIDTH,
                    height=self.DEFAULT_FIELD_HEIGHT,
                    fg_color=ColorTheme.BG_INPUT,
                    text_color=ColorTheme.TEXT_PRIMARY,
                )
            
            entry.pack(fill="x", pady=5)
            
            # ✅ Сохраняем ссылку на поле и конфигурацию для валидации
            self._fields[field_name] = {
                "widget": entry,
                "config": field_config,
            }
            
            # ✅ Заполняем существующими данными если редактируем
            if self.record_id and field_name in self.data:
                entry.delete(0, "end")
                entry.insert(0, str(self.data[field_name]) if self.data[field_name] is not None else "")
    
    def _build_stub_form(self, parent) -> None:
        """Заглушка для таблиц без схемы"""
        ctk.CTkLabel(
            parent,
            text=f"{get_text('editor_stub', self.lang) or 'Редактор для таблицы'} '{self.table_name}'\n\n{get_text('dynamic_form_coming', self.lang) or '(В разработке — здесь будет динамическая форма)'}",
            font=ctk.CTkFont(size=14),
            text_color=ColorTheme.TEXT_SECONDARY,
            justify="center",
        ).pack(pady=50)
        
        # ✅ Пример поля ID если есть
        if self.record_id:
            ctk.CTkLabel(
                parent,
                text=f"{get_text('record_id', self.lang) or 'ID записи'}: {self.record_id}",
                text_color=ColorTheme.TEXT_PRIMARY,
            ).pack(pady=10)
    
    def _focus_first_field(self) -> None:
        """Установить фокус на первое поле ввода"""
        if self._fields:
            first_field_name = next(iter(self._fields))
            widget = self._fields[first_field_name]["widget"]
            if widget and widget.winfo_exists():
                widget.focus_set()
                widget.select_range(0, "end")
    
    def _set_loading(self, loading: bool) -> None:
        """Показать/скрыть индикатор загрузки"""
        if loading:
            if self._loading_label:
                self._loading_label.configure(text="🔄 " + (get_text("saving", self.lang) or "Сохранение..."))
            if self._save_btn:
                self._save_btn.configure(state="disabled")
            # Блокируем поля
            for field_data in self._fields.values():
                widget = field_data["widget"]
                if widget:
                    widget.configure(state="disabled")
        else:
            if self._loading_label:
                self._loading_label.configure(text="")
            if self._save_btn:
                self._save_btn.configure(state="normal")
            for field_data in self._fields.values():
                widget = field_data["widget"]
                if widget:
                    widget.configure(state="normal")
    
    def _validate_fields(self) -> tuple[bool, str]:
        """Валидация всех полей формы"""
        for field_name, field_data in self._fields.items():
            widget = field_data["widget"]
            config = field_data["config"]
            
            value = widget.get().strip() if hasattr(widget, "get") else ""
            required = config.get("required", False)
            field_type = config.get("type", "text")
            max_length = config.get("max_length", self.MAX_TEXT_LENGTH)
            min_val = config.get("min")
            max_val = config.get("max")
            
            # ✅ Проверка обязательности
            if required and not value:
                label = get_text(config.get("label", field_name), self.lang) or field_name
                return False, get_text("field_required", self.lang).format(label) or f"{label} обязателен"
            
            # ✅ Проверка длины для текстовых полей
            if field_type == "text" and value and len(value) > max_length:
                label = get_text(config.get("label", field_name), self.lang) or field_name
                return False, get_text("field_too_long", self.lang).format(label, max_length) or f"{label} не может превышать {max_length} символов"
            
            # ✅ Проверка числа
            if field_type == "number" and value:
                try:
                    num_val = float(value)
                    if min_val is not None and num_val < min_val:
                        return False, get_text("number_too_small", self.lang).format(min_val) or f"Значение должно быть не менее {min_val}"
                    if max_val is not None and num_val > max_val:
                        return False, get_text("number_too_large", self.lang).format(max_val) or f"Значение не может превышать {max_val}"
                except ValueError:
                    label = get_text(config.get("label", field_name), self.lang) or field_name
                    return False, get_text("invalid_number", self.lang) or f"{label} должен быть числом"
            
            # ✅ Проверка email
            if field_type == "email" and value:
                if "@" not in value or "." not in value.split("@")[-1]:
                    label = get_text(config.get("label", field_name), self.lang) or field_name
                    return False, get_text("invalid_email", self.lang) or f"{label} должен быть в формате user@domain.com"
            
            # ✅ Проверка телефона (базовая)
            if field_type == "phone" and value:
                digits = "".join(c for c in value if c.isdigit())
                if len(digits) < 10:
                    label = get_text(config.get("label", field_name), self.lang) or field_name
                    return False, get_text("invalid_phone", self.lang) or f"{label} должен содержать минимум 10 цифр"
        
        return True, ""
    
    def _collect_data(self) -> Dict[str, Any]:
        """Собрать данные из полей формы"""
        result = {}
        
        for field_name, field_data in self._fields.items():
            widget = field_data["widget"]
            config = field_data["config"]
            field_type = config.get("type", "text")
            
            value = widget.get().strip() if hasattr(widget, "get") else ""
            
            # ✅ Конвертация типов
            if field_type == "number" and value:
                try:
                    result[field_name] = float(value) if "." in value else int(value)
                except ValueError:
                    result[field_name] = None
            elif field_type == "boolean":
                result[field_name] = value.lower() in ("true", "1", "yes", "да")
            elif not value:
                result[field_name] = None  # ✅ Пустые строки → None
            else:
                result[field_name] = value
        
        return result
    
    def _save(self) -> None:
        """Сохранение данных с валидацией и обработкой ошибок"""
        # ✅ Валидация полей
        valid, error_msg = self._validate_fields()
        if not valid:
            ToastNotification(self, error_msg, "warning")
            return
        
        # ✅ Сбор данных
        data = self._collect_data()
        
        # ✅ Показываем индикатор загрузки
        self._set_loading(True)
        
        try:
            # ✅ Логирование БЕЗ module= параметра
            app_logger.info(f"💾 Saving {'update' if self.record_id else 'insert'} to {self.table_name}")
            
            # ✅ Вызов колбэка с обработкой ошибок
            if self.on_save:
                try:
                    self.on_save(data)
                except Exception as e:
                    app_logger.error(f"❌ Error in on_save callback: {e}")
                    ToastNotification(self, f"{get_text('callback_error', self.lang)}: {e}", "error")
                    return
            
            # ✅ Успешное сохранение
            ToastNotification(self, get_text("record_saved", self.lang) or "✅ Запись сохранена", "success")
            
            # ✅ Закрываем диалог
            self.destroy()
            
        except Exception as e:
            app_logger.exception(f"❌ Error saving record: {e}")
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
    
    @classmethod
    def open_editor(
        cls,
        parent: ctk.CTkBaseClass,
        table_name: str,
        tree=None,  # Optional[ttk.Treeview]
        lang: str = "ru",
        on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> "RecordEditor":
        """
        Класс-метод для открытия редактора
        
        ✅ НЕ вызывает mainloop() — диалог работает в цикле родителя
        ✅ Возвращает экземпляр для дальнейшего управления
        
        Args:
            parent: Родительское окно
            table_name: Имя таблицы
            tree: Treeview виджет для извлечения данных (опционально)
            lang: Язык интерфейса
            on_save: Callback после успешного сохранения
            
        Returns:
            RecordEditor: Созданный экземпляр редактора
            
        Example:
            >>> editor = RecordEditor.open_editor(parent, "employees", tree=my_tree)
            >>> editor.transient(parent)
            >>> editor.grab_set()
        """
        # ✅ Извлечение данных из Treeview с безопасным сопоставлением
        record_id = None
        data = None
        
        if tree is not None:
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                values = item.get("values", [])
                columns = tree["columns"]
                
                # ✅ Безопасное сопоставление: проверяем что колонок и значений одинаковое количество
                if values and len(values) == len(columns):
                    record_id = values[0] if values[0] else None
                    data = dict(zip(columns, values))
                elif values:
                    # ✅ Fallback: берём по порядку, но с предупреждением
                    app_logger.warning(f"⚠️ Column/value count mismatch for table {table_name}")
                    record_id = values[0] if values[0] else None
                    data = {f"col_{i}": v for i, v in enumerate(values)}
        
        # ✅ Создаём редактор (БЕЗ mainloop!)
        editor = cls(
            parent=parent,
            table_name=table_name,
            record_id=record_id,
            data=data,
            lang=lang,
            on_save=on_save,
        )
        
        # ✅ Настраиваем модальность (делает родитель)
        # editor.transient(parent)  # Уже сделано в __init__
        # editor.grab_set()  # Уже сделано в __init__
        
        return editor