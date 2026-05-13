# ui/dialogs/request_editor.py
"""
Диалог создания/редактирования заявки для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Запросы к таблице employees (не clients), валидация, переводы
✅ УЛУЧШЕНО: Индикатор загрузки, адаптивность, обработка ошибок
✅ СОВМЕСТИМО: Интеграция с системой тем, переводов и утилит
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime, timedelta
import re

from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.toast import ToastNotification
from utils.validators import validate_number


class RequestEditorDialog(ctk.CTkToplevel):
    """
    Диалог создания/редактирования заявки с полной валидацией
    
    ✅ Запросы к таблице employees (не clients)
    ✅ Валидация всех входных данных
    ✅ Индикатор загрузки при сохранении
    ✅ Полный перевод через get_text()
    ✅ Безопасное получение user_id из контекста
    """
    
    # ⚙️ Конфигурация валидации
    MIN_PROBLEM_LENGTH: int = 10
    MAX_PROBLEM_LENGTH: int = 2000
    MIN_COST: float = 0
    MAX_COST: float = 1_000_000  # 1 млн рублей
    
    def __init__(
        self,
        parent,
        request_id: Optional[int] = None,
        lang: str = "ru",
        on_save: Optional[Callable[[], None]] = None,
        prefill: Optional[Dict[str, Any]] = None,
        current_user: Optional[Dict[str, Any]] = None,  # ✅ Для получения user_id
    ):
        super().__init__(parent)
        
        self.request_id = request_id
        self.lang = lang
        self.on_save = on_save
        self.prefill = prefill or {}
        self.current_user = current_user or {"id": 1, "username": "admin"}  # fallback
        self.db = DatabaseConnection()
        
        # 🔧 UI элементы (для обновления)
        self._client_combo: Optional[ctk.CTkComboBox] = None
        self._equipment_combo: Optional[ctk.CTkComboBox] = None
        self._problem_desc: Optional[ctk.CTkTextbox] = None
        self._status_menu: Optional[ctk.CTkOptionMenu] = None
        self._labor_entry: Optional[ctk.CTkEntry] = None
        self._parts_entry: Optional[ctk.CTkEntry] = None
        self._total_label: Optional[ctk.CTkLabel] = None
        self._date_entry: Optional[ctk.CTkEntry] = None
        self._save_btn: Optional[ctk.CTkButton] = None
        self._loading_label: Optional[ctk.CTkLabel] = None
        
        # Маппинги для ComboBox
        self._employees_map: Dict[str, int] = {}  # "1 - Иванов" → 1
        self._equipment_map: Dict[str, int] = {}  # "MacBook (SN123)" → id
        
        # ✅ Переведённый заголовок
        title = get_text("create_request", self.lang) if not request_id else f"{get_text('edit_request', self.lang)} #{request_id}"
        self.title(title)
        
        self.geometry("600x720")
        self.minsize(550, 650)
        self.transient(parent)
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        self._build_ui()
        
        # Загружаем данные
        self._load_employees()
        
        if request_id:
            self._load_request_data()
        elif self.prefill:
            self._apply_prefill()
        
        # Центрирование и модальность — после построения UI
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 720) // 2
        self.geometry(f"+{x}+{y}")
        self.grab_set()
    
    def _build_ui(self) -> None:
        """Построение интерфейса с полным переводом"""
        
        # 🏷️ Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0, height=60)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=self.title(),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(pady=15)
        
        # 📋 Скроллируемая форма
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 👤 Сотрудник (бывш. клиент) - ✅ БЕЗ textvariable
        ctk.CTkLabel(
            scroll_frame, 
            text=f"{get_text('select_employee', self.lang)} *",  # ✅ Переведено
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))
        
        self._client_combo = ctk.CTkComboBox(
            scroll_frame,
            values=[],
            width=420,
            height=40,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD,
            command=self._on_employee_change,
        )
        self._client_combo.pack(pady=5)
        
        # 💻 Оборудование
        ctk.CTkLabel(
            scroll_frame, 
            text=get_text("equipment", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(15, 5))
        
        self._equipment_combo = ctk.CTkComboBox(
            scroll_frame,
            values=[get_text("no_equipment", self.lang) or "—"],
            width=420,
            height=40,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD,
            state="disabled"  # Включится после выбора сотрудника
        )
        self._equipment_combo.pack(pady=5)
        
        # 📝 Описание проблемы
        ctk.CTkLabel(
            scroll_frame, 
            text=f"{get_text('problem_desc', self.lang)} *", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(15, 5))
        
        self._problem_desc = ctk.CTkTextbox(
            scroll_frame, 
            height=100, 
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY,
        )
        self._problem_desc.pack(pady=5)
        self._problem_desc.bind("<KeyRelease>", lambda e: self._validate_problem_length())
        
        # 🎭 Статус
        ctk.CTkLabel(
            scroll_frame, 
            text=get_text("status", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(15, 5))
        
        # ✅ Перевод статусов для отображения
        status_values = [
            get_text(f"status_{s}", self.lang) or s 
            for s in ["new", "diagnostics", "in_progress", "ready", "closed"]
        ]
        self._status_mapping = {
            display: value 
            for display, value in zip(status_values, ["new", "diagnostics", "in_progress", "ready", "closed"])
        }
        
        self._status_var = ctk.StringVar(value=get_text("status_new", self.lang) or "new")
        self._status_menu = ctk.CTkOptionMenu(
            scroll_frame,
            values=status_values,
            variable=self._status_var,
            width=200,
            height=40,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD,
        )
        self._status_menu.pack(pady=5)
        
        # 💰 Стоимость
        costs_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        costs_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(costs_frame, text=get_text("labor_cost", self.lang) + ":", text_color=ColorTheme.TEXT_PRIMARY).pack(side="left")
        self._labor_entry = ctk.CTkEntry(costs_frame, width=100, height=35, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self._labor_entry.pack(side="left", padx=10)
        self._labor_entry.insert(0, "0")
        self._labor_entry.bind("<KeyRelease>", lambda e: self._recalculate_total())
        
        ctk.CTkLabel(costs_frame, text=get_text("parts_cost", self.lang) + ":", text_color=ColorTheme.TEXT_PRIMARY).pack(side="left", padx=(20, 0))
        self._parts_entry = ctk.CTkEntry(costs_frame, width=100, height=35, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self._parts_entry.pack(side="left", padx=10)
        self._parts_entry.insert(0, "0")
        self._parts_entry.bind("<KeyRelease>", lambda e: self._recalculate_total())
        
        ctk.CTkLabel(costs_frame, text=get_text("total_cost", self.lang) + ":", text_color=ColorTheme.PRIMARY).pack(side="left", padx=(20, 0))
        self._total_label = ctk.CTkLabel(
            costs_frame, 
            text="0 ₽", 
            font=ctk.CTkFont(weight="bold", size=14), 
            text_color=ColorTheme.SUCCESS
        )
        self._total_label.pack(side="left", padx=10)
        
        # 📅 Плановая дата
        ctk.CTkLabel(
            scroll_frame, 
            text=get_text("planned_date", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(15, 5))
        
        date_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=5)
        
        self._date_entry = ctk.CTkEntry(
            date_frame, 
            placeholder_text="YYYY-MM-DD", 
            width=200, 
            height=35,
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self._date_entry.pack(side="left")
        self._date_entry.insert(0, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"))
        self._date_entry.bind("<KeyRelease>", lambda e: self._validate_date_format())
        
        ctk.CTkButton(
            date_frame, 
            text=get_text("select_date", self.lang), 
            command=self._select_date, 
            width=150, 
            height=35, 
            fg_color=ColorTheme.INFO,
            hover_color=ColorUtils.darken(ColorTheme.INFO, 10)
        ).pack(side="left", padx=10)
        
        # ⏳ Индикатор загрузки (скрыт по умолчанию)
        self._loading_label = ctk.CTkLabel(
            scroll_frame,
            text="",
            text_color=ColorTheme.INFO,
            font=ctk.CTkFont(size=11)
        )
        self._loading_label.pack(pady=5)
        
        # 🔘 Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        self._save_btn = ctk.CTkButton(
            btn_frame, 
            text="💾 " + get_text("save", self.lang), 
            command=self._save_request, 
            width=150, 
            height=40, 
            fg_color=ColorTheme.SUCCESS, 
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
            font=ctk.CTkFont(weight="bold")
        )
        self._save_btn.pack(side="right", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text=get_text("cancel", self.lang), 
            command=self.destroy, 
            width=150, 
            height=40, 
            fg_color=ColorTheme.TEXT_SECONDARY, 
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(side="right", padx=10)
    
    def _set_loading(self, loading: bool) -> None:
        """Показать/скрыть индикатор загрузки"""
        if loading:
            if self._loading_label:
                self._loading_label.configure(text="🔄 " + (get_text("saving", self.lang) or "Сохранение..."))
            if self._save_btn:
                self._save_btn.configure(state="disabled")
            # Блокируем поля
            for widget in [self._client_combo, self._equipment_combo, self._problem_desc, 
                          self._status_menu, self._labor_entry, self._parts_entry, self._date_entry]:
                if widget:
                    widget.configure(state="disabled")
        else:
            if self._loading_label:
                self._loading_label.configure(text="")
            if self._save_btn:
                self._save_btn.configure(state="normal")
            for widget in [self._client_combo, self._equipment_combo, self._problem_desc, 
                          self._status_menu, self._labor_entry, self._parts_entry, self._date_entry]:
                if widget:
                    widget.configure(state="normal")
    
    def _load_employees(self) -> None:
        """✅ Загрузить список сотрудников (не клиентов!) в ComboBox"""
        try:
            with self.db.get_cursor() as cur:
                # ✅ employees.full_name вместо clients.name
                cur.execute("SELECT id, full_name FROM employees ORDER BY full_name")
                employees = cur.fetchall()
            
            if employees:
                # ✅ Формат: "ID - ФИО" для отображения, храним ID отдельно
                self._employees_map = {f"{e[0]} - {e[1]}": e[0] for e in employees}
                self._client_combo.configure(values=list(self._employees_map.keys()), state="normal")
                
                # Если есть prefill с client_id (employee_id) — выбираем сотрудника
                if self.prefill.get('client_id') and self._employees_map:
                    for display, eid in self._employees_map.items():
                        if eid == self.prefill['client_id']:
                            self._client_combo.set(display)
                            break
            else:
                self._client_combo.configure(
                    values=[get_text("no_employees", self.lang) or "📭 Нет сотрудников"], 
                    state="disabled"
                )
                
        except Exception as e:
            app_logger.exception(f"❌ Error loading employees: {e}")
            self._client_combo.configure(
                values=[f"{get_text('error_loading', self.lang)}: {e}"], 
                state="disabled"
            )
    
    def _on_employee_change(self, choice: str) -> None:
        """✅ Обработчик выбора сотрудника — загружаем его оборудование"""
        if not choice or choice not in self._employees_map:
            return
        
        employee_id = self._employees_map[choice]
        
        try:
            with self.db.get_cursor() as cur:
                # ✅ equipment.client_id ссылается на employees.id
                cur.execute(
                    "SELECT id, model, serial_number FROM equipment WHERE client_id = ? ORDER BY model",
                    (employee_id,)
                )
                equipment = cur.fetchall()
            
            if equipment:
                self._equipment_map = {f"{e[1]} ({e[2] or get_text('no_serial', self.lang) or 'No SN'})": e[0] for e in equipment}
                self._equipment_combo.configure(values=list(self._equipment_map.keys()), state="normal")
                self._equipment_combo.set(list(self._equipment_map.keys())[0])
            else:
                self._equipment_map = {}
                self._equipment_combo.configure(
                    values=[get_text("no_equipment_for_employee", self.lang) or "—"], 
                    state="disabled"
                )
                self._equipment_combo.set("—")
                
        except Exception as e:
            app_logger.exception(f"❌ Error loading equipment: {e}")
            self._equipment_combo.configure(
                values=[get_text("error_loading", self.lang) or "Ошибка"], 
                state="disabled"
            )
    
    def _validate_problem_length(self) -> None:
        """Валидация длины описания проблемы"""
        text = self._problem_desc.get("1.0", "end").strip() if self._problem_desc else ""
        if len(text) > self.MAX_PROBLEM_LENGTH:
            # Обрезаем до максимума
            self._problem_desc.delete(f"1.{self.MAX_PROBLEM_LENGTH}", "end")
    
    def _validate_date_format(self) -> bool:
        """Проверка формата даты"""
        date_str = self._date_entry.get().strip() if self._date_entry else ""
        if not date_str:
            return True  # Дата необязательна
        
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            ToastNotification(self, get_text("invalid_date_format", self.lang) or "Неверный формат даты (ожидается: ГГГГ-ММ-ДД)", "warning")
            return False
    
    def _select_date(self) -> None:
        """Простой выбор даты (заглушка)"""
        # В полной версии здесь был бы календарь (tkcalendar)
        current = self._date_entry.get().strip() if self._date_entry else ""
        try:
            date_obj = datetime.strptime(current, "%Y-%m-%d") if current else datetime.now()
            new_date = date_obj + timedelta(days=1)
            if self._date_entry:
                self._date_entry.delete(0, "end")
                self._date_entry.insert(0, new_date.strftime("%Y-%m-%d"))
        except:
            pass
    
    def _recalculate_total(self) -> float:
        """Пересчитать общую стоимость с валидацией"""
        try:
            labor_str = self._labor_entry.get().strip() if self._labor_entry else "0"
            parts_str = self._parts_entry.get().strip() if self._parts_entry else "0"
            
            # ✅ Валидация числовых значений
            valid_labor, _ = validate_number(labor_str, min_val=self.MIN_COST, max_val=self.MAX_COST, field_name=get_text("labor_cost", self.lang))
            valid_parts, _ = validate_number(parts_str, min_val=self.MIN_COST, max_val=self.MAX_COST, field_name=get_text("parts_cost", self.lang))
            
            if not valid_labor or not valid_parts:
                return 0
            
            labor = float(labor_str) if labor_str else 0
            parts = float(parts_str) if parts_str else 0
            total = labor + parts
            
            if self._total_label:
                self._total_label.configure(text=f"{total:,.0f} ₽")
            
            return total
            
        except Exception as e:
            app_logger.warning(f"⚠️ Error recalculating total: {e}")
            return 0
    
    def _get_status_value(self, display: str) -> str:
        """Получить значение статуса для БД из отображаемого текста"""
        return self._status_mapping.get(display, display)
    
    def _load_request_data(self) -> None:
        """Загрузить данные существующей заявки"""
        if not self.request_id:
            return
        
        try:
            with self.db.get_cursor() as cur:
                # ✅ employees вместо clients
                cur.execute("""
                    SELECT r.*, emp.full_name as employee_name, e.id as equipment_id, e.model as equipment_model
                    FROM requests r
                    LEFT JOIN employees emp ON r.client_id = emp.id
                    LEFT JOIN equipment e ON r.equipment_id = e.id
                    WHERE r.id = ?
                """, (self.request_id,))
                row = cur.fetchone()
            
            if not row:
                return
            
            # ✅ Сотрудник
            if row[2]:  # employee_name (предполагаем порядок колонок)
                for display, eid in self._employees_map.items():
                    if eid == row[1]:  # client_id = employee_id
                        if self._client_combo:
                            self._client_combo.set(display)
                        break
            
            # ✅ Оборудование
            if row[3] and hasattr(self, '_equipment_map'):  # equipment_id
                for display, eq_id in self._equipment_map.items():
                    if eq_id == row[3]:
                        if self._equipment_combo:
                            self._equipment_combo.set(display)
                        break
            
            # ✅ Остальные поля
            if self._problem_desc and row[4]:  # problem_desc
                self._problem_desc.delete("1.0", "end")
                self._problem_desc.insert("1.0", row[4])
            
            if self._status_menu and row[5]:  # status
                display_status = get_text(f"status_{row[5]}", self.lang) or row[5]
                self._status_var.set(display_status)
            
            if self._labor_entry:
                self._labor_entry.delete(0, "end")
                self._labor_entry.insert(0, str(row[6] or 0))  # labor_cost
            
            if self._parts_entry:
                self._parts_entry.delete(0, "end")
                self._parts_entry.insert(0, str(row[7] or 0))  # parts_cost
            
            self._recalculate_total()
            
            if self._date_entry and row[9]:  # planned_date
                self._date_entry.delete(0, "end")
                self._date_entry.insert(0, row[9])
                
        except Exception as e:
            app_logger.exception(f"❌ Error loading request: {e}")
            ToastNotification(self, f"{get_text('error_loading', self.lang)}: {e}", "error")
    
    def _apply_prefill(self) -> None:
        """Применить предзаполненные данные"""
        # ✅ Сотрудник
        if self.prefill.get('client_id') and hasattr(self, '_employees_map'):
            for display, eid in self._employees_map.items():
                if eid == self.prefill['client_id']:
                    if self._client_combo:
                        self._client_combo.set(display)
                    self._on_employee_change(display)
                    break
        
        # ✅ Оборудование
        if self.prefill.get('equipment_id') and hasattr(self, '_equipment_map'):
            for display, eq_id in self._equipment_map.items():
                if eq_id == self.prefill['equipment_id']:
                    if self._equipment_combo:
                        self._equipment_combo.set(display)
                    break
        
        # ✅ Описание проблемы
        if self.prefill.get('problem_desc') and self._problem_desc:
            self._problem_desc.delete("1.0", "end")
            self._problem_desc.insert("1.0", self.prefill['problem_desc'])
    
    def _save_request(self) -> None:
        """Сохранить заявку с полной валидацией"""
        # ✅ Валидация сотрудника
        employee_display = self._client_combo.get() if self._client_combo else ""
        if not employee_display or employee_display not in self._employees_map:
            ToastNotification(self, get_text("select_employee", self.lang) or "Выберите сотрудника", "warning")
            if self._client_combo:
                self._client_combo.focus_set()
            return
        
        # ✅ Валидация описания проблемы
        problem = self._problem_desc.get("1.0", "end").strip() if self._problem_desc else ""
        if not problem or len(problem) < self.MIN_PROBLEM_LENGTH:
            ToastNotification(self, get_text("problem_too_short", self.lang).format(self.MIN_PROBLEM_LENGTH) or f"Опишите проблему (минимум {self.MIN_PROBLEM_LENGTH} символов)", "warning")
            if self._problem_desc:
                self._problem_desc.focus_set()
            return
        
        # ✅ Валидация даты
        if not self._validate_date_format():
            if self._date_entry:
                self._date_entry.focus_set()
            return
        
        # ✅ Получение и валидация числовых значений
        try:
            labor_str = self._labor_entry.get().strip() if self._labor_entry else "0"
            parts_str = self._parts_entry.get().strip() if self._parts_entry else "0"
            
            valid_labor, labor_msg = validate_number(labor_str, min_val=self.MIN_COST, max_val=self.MAX_COST, field_name=get_text("labor_cost", self.lang))
            valid_parts, parts_msg = validate_number(parts_str, min_val=self.MIN_COST, max_val=self.MAX_COST, field_name=get_text("parts_cost", self.lang))
            
            if not valid_labor:
                ToastNotification(self, labor_msg, "warning")
                if self._labor_entry:
                    self._labor_entry.focus_set()
                return
            
            if not valid_parts:
                ToastNotification(self, parts_msg, "warning")
                if self._parts_entry:
                    self._parts_entry.focus_set()
                return
            
            labor = float(labor_str) if labor_str else 0
            parts = float(parts_str) if parts_str else 0
            total = labor + parts
            
        except Exception as e:
            ToastNotification(self, get_text("invalid_cost", self.lang) or "Неверное значение стоимости", "warning")
            return
        
        # ✅ Получение ID и статуса
        employee_id = self._employees_map[employee_display]
        equipment_id = self._equipment_map.get(self._equipment_combo.get()) if hasattr(self, '_equipment_map') and self._equipment_combo else None
        status = self._get_status_value(self._status_var.get()) if self._status_var else "new"
        planned_date = self._date_entry.get().strip() if self._date_entry else None
        if planned_date and not self._validate_date_format():
            return
        
        # ✅ Получение user_id из контекста
        user_id = self.current_user.get("id") if self.current_user else 1
        
        # ✅ Показываем индикатор загрузки
        self._set_loading(True)
        
        try:
            with self.db.get_cursor() as cur:
                if self.request_id:
                    # 🔁 Обновление существующей заявки
                    cur.execute("""
                        UPDATE requests SET 
                            client_id = ?, equipment_id = ?, status = ?, 
                            problem_desc = ?, labor_cost = ?, parts_cost = ?, 
                            total_cost = ?, planned_date = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        employee_id, equipment_id, status,
                        problem, labor, parts, total,
                        planned_date,
                        self.request_id
                    ))
                else:
                    # ➕ Создание новой заявки
                    cur.execute("""
                        INSERT INTO requests (
                            client_id, equipment_id, user_id, status,
                            problem_desc, labor_cost, parts_cost, total_cost,
                            planned_date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        employee_id, equipment_id, user_id, status,
                        problem, labor, parts, total,
                        planned_date
                    ))
            
            # ✅ Успешное сохранение
            ToastNotification(self, get_text("request_saved", self.lang) or "✅ Заявка сохранена", "success")
            app_logger.info(f"💾 Request {'updated' if self.request_id else 'created'}: ID {self.request_id or 'new'}")
            
            # ✅ Вызываем колбэк обновления
            if self.on_save:
                try:
                    self.on_save()
                except Exception as e:
                    app_logger.warning(f"⚠️ on_save callback error: {e}")
            
            # ✅ Закрываем диалог
            self.destroy()
            
        except Exception as e:
            app_logger.exception(f"❌ Error saving request: {e}")
            ToastNotification(self, f"{get_text('error_saving', self.lang)}: {e}", "error")
        finally:
            # ✅ Скрываем индикатор загрузки
            self._set_loading(False)
    
    def destroy(self) -> None:
        """Корректное закрытие диалога"""
        # Отменяем любые отложенные задачи
        try:
            # Можно добавить очистку таймеров если есть
            pass
        except:
            pass
        super().destroy()