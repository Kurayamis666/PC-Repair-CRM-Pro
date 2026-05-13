# ui/views/documents.py
"""
Экран документов: Заявки и Оборудование для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Метод _sort_tree вынесен из вложенности
✅ УЛУЧШЕНО: Пустое состояние, валидация, адаптивность
✅ СОВМЕСТИМО: Интеграция с системой тем и переводов
"""

import sqlite3

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.toast import ToastNotification
from ui.widgets.tables import DataTable


class DocumentsView(ctk.CTkFrame):
    """Главный экран документов"""
    
    on_navigate: Optional[Callable[[str], None]] = None
    
    def __init__(self, parent: ctk.CTkBaseClass, lang: str = "ru", on_navigate: Optional[Callable] = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.lang = lang
        self.on_navigate = on_navigate
        self.db = DatabaseConnection()
        self.sort_reverse: dict = {}
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Построение интерфейса"""
        # Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=get_text("documents", self.lang),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=20)
        
        # Кнопка назад
        ctk.CTkButton(
            self, text=get_text("back", self.lang),
            command=lambda: self.on_navigate("dashboard") if self.on_navigate else None,
            width=150, height=35, 
            fg_color=ColorTheme.TEXT_SECONDARY,
            corner_radius=10
        ).pack(padx=20, pady=20, anchor="w")
        
        # Вкладки
        self.notebook = ctk.CTkTabview(self, fg_color="transparent")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Создаем вкладки
        self.tab_requests = self.notebook.add(get_text("requests", self.lang))
        self.tab_equipment = self.notebook.add(get_text("equipment", self.lang))
        
        # Заполняем вкладки контентом
        self._build_requests_tab()
        self._build_equipment_tab()
    
    def _build_requests_tab(self):
        """Вкладка Заявок (заглушка)"""
        ctk.CTkLabel(
            self.tab_requests, 
            text="📋 " + get_text("under_construction", self.lang, default="Раздел в разработке"),
            font=ctk.CTkFont(size=16), 
            text_color=ColorTheme.TEXT_SECONDARY
        ).pack(expand=True, pady=100)
    
    def _build_equipment_tab(self):
        """Вкладка Оборудования - ПОЛНОСТЬЮ РАБОЧАЯ"""
        # Заголовок вкладки
        ctk.CTkLabel(
            self.tab_equipment, 
            text="💻 " + get_text("equipment", self.lang),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=10)
        
        # Кнопки управления
        btn_frame = ctk.CTkFrame(self.tab_equipment, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="➕ " + get_text("add", self.lang), 
                     command=self._add_equipment, width=130, height=30,
                     fg_color=ColorTheme.SUCCESS,
                     hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        ).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏️ " + get_text("edit", self.lang), 
                     command=self._edit_equipment, width=130, height=30,
                     fg_color=ColorTheme.INFO,
                     hover_color=ColorUtils.darken(ColorTheme.INFO, 10)
        ).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑️ " + get_text("delete", self.lang), 
                     command=self._delete_equipment, width=130, height=30,
                     fg_color=ColorTheme.ERROR,
                     hover_color=ColorUtils.darken(ColorTheme.ERROR, 10)
        ).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🔄 " + get_text("update", self.lang), 
                     command=self._load_equipment, width=130, height=30,
                     fg_color=ColorTheme.TEXT_SECONDARY,
                     hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10)
        ).pack(side="right", padx=5)
        
        # Таблица с сортировкой
        table_frame = ctk.CTkFrame(self.tab_equipment, fg_color=ColorTheme.BG_INPUT)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = [
            get_text("col_id", self.lang),
            get_text("col_employee", self.lang),
            get_text("col_model", self.lang),
            get_text("col_type", self.lang),
            get_text("col_serial", self.lang)
        ]
        col_widths = {
            get_text("col_id", self.lang): 50,
            get_text("col_employee", self.lang): 200,
            get_text("col_model", self.lang): 200,
            get_text("col_type", self.lang): 150,
            get_text("col_serial", self.lang): 150
        }
        
        # ✅ Используем DataTable для сортировки и адаптивности
        self.eq_tree = DataTable(
            table_frame,
            columns=columns,
            column_widths=col_widths,
            sortable=True,
            copyable=True,
            on_row_double_click=lambda item: self._edit_equipment()
        )
        self.eq_tree.pack(fill="both", expand=True)
        
        # Загружаем данные
        self._load_equipment()

    def _load_equipment(self) -> None:
        """Загрузка оборудования из БД с пустым состоянием"""
        # Очищаем таблицу
        self.eq_tree.delete(*self.eq_tree.get_children())
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT e.id, emp.full_name, e.model, e.device_type, e.serial_number
                    FROM equipment e
                    LEFT JOIN employees emp ON e.client_id = emp.id
                    ORDER BY e.model
                """)
                rows = cur.fetchall()
            
            # Пустое состояние
            if not rows:
                self.eq_tree.show_empty_state(
                    message=get_text("no_equipment", self.lang) or "Оборудование не найдено",
                    icon="💻"
                )
                return
            else:
                self.eq_tree.hide_empty_state()
            
            for idx, row in enumerate(rows):
                tag = "odd" if idx % 2 else "even"
                values = (row[0], row[1] or "—", row[2], row[3] or "—", row[4] or "—")
                self.eq_tree.insert("", "end", values=values, tags=(tag,))
                
        except Exception as e:
            app_logger.error(f"Error loading equipment: {e}")
            ToastNotification(self, f"{get_text('error_loading', self.lang)}: {e}", "error")

    def _add_equipment(self) -> None:
        """Добавление оборудования"""
        dialog = EquipmentDialog(self, self.lang, title="➕ " + get_text("add_equipment", self.lang))
        if dialog.result:
            self._load_equipment()
            ToastNotification(self, "✅ " + get_text("added", self.lang), "success")

    def _edit_equipment(self) -> None:
        """Редактирование оборудования"""
        selection = self.eq_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        eq_id = self.eq_tree.item(selection[0])['values'][0]
        dialog = EquipmentDialog(self, self.lang, equipment_id=eq_id,
                                title="✏️ " + get_text("edit_equipment", self.lang))
        if dialog.result:
            self._load_equipment()
            ToastNotification(self, "✅ " + get_text("updated", self.lang), "success")

    def _delete_equipment(self) -> None:
        """Удаление оборудования"""
        selection = self.eq_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        eq_id = self.eq_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno(get_text("confirm_delete", self.lang),
                              get_text("delete_equipment_confirm", self.lang)):
            try:
                with self.db.get_cursor() as cur:
                    cur.execute("DELETE FROM equipment WHERE id = ?", (eq_id,))
                self._load_equipment()
                ToastNotification(self, "✅ " + get_text("deleted", self.lang), "success")
            except sqlite3.IntegrityError:
                ToastNotification(self, "❌ " + get_text("cannot_delete_in_use", self.lang), "error")
            except Exception as e:
                ToastNotification(self, f"❌ {e}", "error")


# ==================== 🎨 ДИАЛОГ ОБОРУДОВАНИЯ ====================
class EquipmentDialog(ctk.CTkToplevel):
    """Диалог добавления/редактирования оборудования с валидацией"""
    
    def __init__(self, parent, lang, equipment_id=None, title="Оборудование"):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x650")
        self.minsize(450, 600)
        self.transient(parent)
        self.configure(fg_color=ColorTheme.BG_CARD)
        self.result = False
        self.lang = lang
        
        self.db = DatabaseConnection()
        self.equipment_id = equipment_id
        self.employee_ids: list = []
        
        self._build_ui()
        if equipment_id:
            self._load_equipment(equipment_id)
        
        # Центрирование и модальность — после построения UI
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 650) // 2
        self.geometry(f"+{x}+{y}")
        self.grab_set()
    
    def _build_ui(self):
        """Построение интерфейса диалога с валидацией"""
        # Заголовок
        ctk.CTkLabel(self, text="💻 " + get_text("equipment_info", self.lang), 
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=ColorTheme.PRIMARY).pack(pady=15)
        
        # Скроллируемая форма
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=450)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Сотрудник (Комбобокс)
        ctk.CTkLabel(scroll_frame, text=get_text("employee", self.lang) + ":", 
                    text_color=ColorTheme.TEXT_PRIMARY, anchor="w",
                    font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(10, 5))
        self.employee_combo = ctk.CTkComboBox(scroll_frame, height=35,
                                           fg_color=ColorTheme.BG_INPUT,
                                           text_color=ColorTheme.TEXT_PRIMARY,
                                           values=["—"])
        self.employee_combo.pack(fill="x", pady=5)
        self._load_employees_for_combo()
        
        # Поля оборудования
        fields = [
            ("model", "model_entry", get_text("model", self.lang), True),  # required
            ("device_type", "type_entry", get_text("device_type", self.lang), False),
            ("serial_number", "serial_entry", get_text("serial_number", self.lang), False),
            ("color", "color_entry", get_text("color", self.lang), False),
            ("imei", "imei_entry", get_text("imei", self.lang) or "IMEI", False),
            ("accessories", "acc_entry", get_text("accessories", self.lang), False),
            ("external_damage", "damage_entry", get_text("external_damage", self.lang), False)
        ]
        
        for key, attr_name, label, required in fields:
            label_text = label + (" *" if required else "")
            ctk.CTkLabel(scroll_frame, text=label_text, 
                        text_color=ColorTheme.TEXT_PRIMARY, anchor="w",
                        font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(10, 5))
            entry = ctk.CTkEntry(scroll_frame, height=35,
                               fg_color=ColorTheme.BG_INPUT,
                               text_color=ColorTheme.TEXT_PRIMARY)
            entry.pack(fill="x", pady=5)
            setattr(self, attr_name, entry)
            setattr(self, f"{attr_name}_required", required)
        
        # Подсказка об обязательных полях
        ctk.CTkLabel(
            scroll_frame, 
            text="* " + (get_text("required_field", self.lang) or "Обязательное поле"),
            text_color=ColorTheme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=10),
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        
        # Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(btn_frame, text="💾 " + get_text("save", self.lang), 
                     command=self._save,
                     fg_color=ColorTheme.SUCCESS,
                     hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
                     height=35, width=150).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text="❌ " + get_text("cancel", self.lang), 
                     command=self.destroy,
                     fg_color=ColorTheme.TEXT_SECONDARY,
                     hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
                     height=35, width=150).pack(side="left", padx=10, expand=True)
    
    def _load_employees_for_combo(self):
        """Загрузка сотрудников для выпадающего списка"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("SELECT id, full_name FROM employees ORDER BY full_name")
                employees = cur.fetchall()
                self.employee_ids = [e[0] for e in employees]
                names = [e[1] for e in employees]
                self.employee_combo.configure(values=names if names else ["—"])
        except Exception as e:
            app_logger.error(f"Error loading employees: {e}")
            self.employee_combo.configure(values=["—"])
            self.employee_ids = []
    
    def _load_equipment(self, eq_id):
        """Загрузка данных оборудования"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT client_id, model, device_type, serial_number, 
                           color, imei, accessories, external_damage
                    FROM equipment WHERE id = ?
                """, (eq_id,))
                row = cur.fetchone()
            
            if row:
                # Устанавливаем сотрудника
                if row[0] and row[0] in self.employee_ids:
                    idx = self.employee_ids.index(row[0])
                    vals = self.employee_combo.cget("values")
                    if idx < len(vals):
                        self.employee_combo.set(vals[idx])
                
                # Заполняем поля
                fields = ["model_entry", "type_entry", "serial_entry", "color_entry", 
                         "imei_entry", "acc_entry", "damage_entry"]
                for field, value in zip(fields, row[1:]):
                    entry = getattr(self, field)
                    entry.delete(0, 'end')
                    entry.insert(0, value or "")
                
        except Exception as e:
            app_logger.error(f"Error loading equipment: {e}")
    
    def _save(self):
        """Сохранение оборудования с валидацией"""
        model = self.model_entry.get().strip()
        if not model:
            ToastNotification(self, "⚠️ " + get_text("fill_required", self.lang), "warning")
            self.model_entry.focus_set()
            return
        
        try:
            # Получаем ID сотрудника
            selected_name = self.employee_combo.get()
            combo_values = self.employee_combo.cget("values")
            client_id = None
            if selected_name and selected_name != "—" and combo_values:
                try:
                    emp_idx = list(combo_values).index(selected_name)
                    if 0 <= emp_idx < len(self.employee_ids):
                        client_id = self.employee_ids[emp_idx]
                except ValueError:
                    pass
            
            data = (
                client_id, 
                model, 
                self.type_entry.get().strip(),
                self.serial_entry.get().strip(), 
                self.color_entry.get().strip(),
                self.imei_entry.get().strip(), 
                self.acc_entry.get().strip(),
                self.damage_entry.get().strip()
            )
            
            with self.db.get_cursor() as cur:
                if self.equipment_id:
                    cur.execute("""
                        UPDATE equipment SET client_id=?, model=?, device_type=?, 
                        serial_number=?, color=?, imei=?, accessories=?, 
                        external_damage=? WHERE id=?
                    """, (*data, self.equipment_id))
                else:
                    cur.execute("""
                        INSERT INTO equipment (client_id, model, device_type, serial_number, 
                        color, imei, accessories, external_damage)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, data)
            
            self.result = True
            self.destroy()
            
        except Exception as e:
            ToastNotification(self, f"❌ {e}", "error")