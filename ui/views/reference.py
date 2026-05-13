# ui/views/reference.py (исправленные импорты)
"""
Экран справочников для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Оборудование → сотрудники, валидация, переводы
✅ УЛУЧШЕНО: Пустое состояние, адаптивные диалоги, обработка ошибок
✅ СОВМЕСТИМО: Интеграция с системой тем, переводов и виджетов
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.tables import DataTable
from ui.widgets.toast import ToastNotification

# ✅ ДОБАВЛЕНО: Импорт validate_inn
from utils.validators import validate_email, validate_phone, validate_number, validate_inn  # ← validate_inn добавлен!


class ReferenceView(ctk.CTkFrame):
    """
    Главный экран справочников с объединёнными разделами
    
    ✅ Полный перевод всех текстов (RU ↔ EN)
    ✅ Корректные запросы к таблице employees (не clients)
    ✅ Валидация входных данных в диалогах
    ✅ Пустое состояние для всех таблиц
    ✅ Адаптивные диалоги с центрированием
    ✅ Подсветка ошибок в полях формы
    """
    
    on_navigate: Optional[Callable[[str], None]] = None
    
    def __init__(self, parent: ctk.CTkBaseClass, lang: str = "ru", on_navigate: Optional[Callable] = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.lang = lang
        self.on_navigate = on_navigate
        self.db = DatabaseConnection()
        self.current_section: Optional[str] = None
        self.sort_reverse: Dict[str, bool] = {}
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Построение интерфейса с полным переводом"""
        header = ctk.CTkFrame(self, fg_color=ColorTheme.INFO, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=get_text("reference", self.lang),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=20)
        
        ctk.CTkButton(
            self, text=get_text("back", self.lang),
            command=self._go_back,
            width=150, height=35, 
            fg_color=ColorTheme.TEXT_SECONDARY,
            corner_radius=10
        ).pack(padx=20, pady=20, anchor="w")
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self._show_menu()
    
    def _go_back(self) -> None:
        """Возврат на главный экран"""
        if self.on_navigate:
            self.on_navigate("dashboard")
    
    def _clear_content(self) -> None:
        """Очистка контента"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_menu(self) -> None:
        """Показ главного меню справочников"""
        self._clear_content()
        self.current_section = None
        
        items = [
            ("👥", get_text("contacts", self.lang), self._show_contacts, ColorTheme.STATUS_NEW),
            ("📦", get_text("nomenclature", self.lang), self._show_nomenclature, ColorTheme.STATUS_READY),
            ("📏", get_text("units", self.lang), self._show_units, ColorTheme.PRIMARY),
        ]
        
        grid_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        for i, (icon, name, command, color) in enumerate(items):
            row, col = divmod(i, 2)
            btn = ctk.CTkButton(
                grid_frame, 
                text=f"{icon} {name}",
                height=100, 
                command=command,
                font=ctk.CTkFont(size=14, weight="bold"),
                corner_radius=12, 
                fg_color=ColorTheme.BG_INPUT,
                hover_color=ColorUtils.darken(color, 10) if color else ColorTheme.PRIMARY_HOVER
            )
            btn.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        grid_frame.grid_columnconfigure((0, 1), weight=1)
        grid_frame.grid_rowconfigure((0, 1), weight=1)

    # ==================== ↕️ СОРТИРОВКА ТАБЛИЦ ====================
    def _enable_sorting(self, tree, col_index: int, is_numeric: bool = False):
        """Включить сортировку для колонки с обработкой None"""
        def sort_column():
            data = []
            for child in tree.get_children(''):
                val = tree.set(child, col_index)
                # Обрабатываем пустые/None значения
                sort_val = "" if val in ("", "—", None) else val
                if is_numeric:
                    try:
                        sort_val = float(sort_val.replace(' ₽', '').replace(',', '.').replace(' %', ''))
                    except ValueError:
                        sort_val = 0
                data.append((sort_val, child))
            
            reverse = self.sort_reverse.get(col_index, False)
            
            try:
                data.sort(key=lambda x: x[0], reverse=reverse)
            except TypeError:
                # Если смешанные типы — сортируем как строки
                data.sort(key=lambda x: str(x[0]).lower(), reverse=reverse)
            
            for index, (val, child) in enumerate(data):
                tree.move(child, '', index)
            
            self.sort_reverse[col_index] = not reverse
            
            # Обновляем заголовок со стрелкой
            current_heading = tree.heading(col_index, 'text')
            arrow = ' ▲' if self.sort_reverse[col_index] else ' ▼'
            if current_heading.endswith(' ▲') or current_heading.endswith(' ▼'):
                current_heading = current_heading[:-2]
            tree.heading(col_index, text=current_heading + arrow)
        
        return sort_column

    # ==================== 👥 КОНТАКТЫ (СОТРУДНИКИ + КОНТРАГЕНТЫ) ====================
    def _show_contacts(self) -> None:
        """Показ контактов (вкладки: Сотрудники, Контрагенты)"""
        self._clear_content()
        self.current_section = "contacts"
        
        header = ctk.CTkFrame(self.content_frame, fg_color=ColorTheme.STATUS_NEW, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=get_text("contacts", self.lang), 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=10)
        
        # Вкладки
        notebook = ctk.CTkTabview(self.content_frame, fg_color="transparent")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        employees_tab = notebook.add(get_text("employees", self.lang))
        contractors_tab = notebook.add(get_text("contractors", self.lang))
        
        self._build_employees_tab(employees_tab)
        self._build_contractors_tab(contractors_tab)

    def _build_employees_tab(self, parent):
        """Вкладка Сотрудники"""
        # Кнопки
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="➕ " + get_text("add", self.lang), 
                     command=self._add_employee, width=130, height=30,
                     fg_color=ColorTheme.SUCCESS,
                     hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✏️ " + get_text("edit", self.lang), 
                     command=self._edit_employee, width=130, height=30,
                     fg_color=ColorTheme.INFO,
                     hover_color=ColorUtils.darken(ColorTheme.INFO, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ " + get_text("delete", self.lang), 
                     command=self._delete_employee, width=130, height=30,
                     fg_color=ColorTheme.ERROR,
                     hover_color=ColorUtils.darken(ColorTheme.ERROR, 10)
        ).pack(side="left", padx=10)
        
        # Таблица
        table_frame = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_INPUT)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = [
            get_text("col_id", self.lang),
            get_text("col_name", self.lang),
            get_text("position", self.lang),
            get_text("phone", self.lang),
            get_text("email", self.lang),
            get_text("salary", self.lang)
        ]
        col_widths = {
            get_text("col_id", self.lang): 50,
            get_text("col_name", self.lang): 200,
            get_text("position", self.lang): 150,
            get_text("phone", self.lang): 120,
            get_text("email", self.lang): 200,
            get_text("salary", self.lang): 100
        }
        
        self.emp_tree = DataTable(
            table_frame,
            columns=columns,
            column_widths=col_widths,
            sortable=True,
            copyable=True
        )
        self.emp_tree.pack(fill="both", expand=True)
        
        self._load_employees()

    def _load_employees(self) -> None:
        """Загрузка сотрудников с пустым состоянием"""
        self.emp_tree.delete(*self.emp_tree.get_children())
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, full_name, position, phone, email, salary 
                    FROM employees 
                    ORDER BY full_name
                """)
                rows = cur.fetchall()
            
            if not rows:
                self.emp_tree.show_empty_state(
                    message=get_text("no_employees", self.lang) or "Сотрудники не найдены",
                    icon="👥"
                )
                return
            else:
                self.emp_tree.hide_empty_state()
            
            for idx, row in enumerate(rows):
                tag = "odd" if idx % 2 else "even"
                values = (
                    row[0], 
                    row[1], 
                    row[2] or "—", 
                    row[3] or "—", 
                    row[4] or "—", 
                    f"{row[5] or 0:.2f} ₽"
                )
                self.emp_tree.insert("", "end", values=values, tags=(tag,))
        except Exception as e:
            app_logger.error(f"Error loading employees: {e}")
            ToastNotification(self, f"{get_text('error_loading', self.lang)}: {e}", "error")

    def _add_employee(self) -> None:
        """Добавление сотрудника"""
        dialog = EmployeeDialog(self, self.lang, title="➕ " + get_text("add_employee", self.lang))
        if dialog.result:
            self._load_employees()
            ToastNotification(self, "✅ " + get_text("added", self.lang), "success")

    def _edit_employee(self) -> None:
        """Редактирование сотрудника"""
        selection = self.emp_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        emp_id = self.emp_tree.item(selection[0])['values'][0]
        dialog = EmployeeDialog(self, self.lang, employee_id=emp_id, 
                               title="✏️ " + get_text("edit_employee", self.lang))
        if dialog.result:
            self._load_employees()
            ToastNotification(self, "✅ " + get_text("updated", self.lang), "success")

    def _delete_employee(self) -> None:
        """Удаление сотрудника"""
        selection = self.emp_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        emp_id = self.emp_tree.item(selection[0])['values'][0]
        emp_name = self.emp_tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno(get_text("confirm_delete", self.lang), 
                              f"{get_text('delete', self.lang)} '{emp_name}'?"):
            try:
                with self.db.get_cursor() as cur:
                    cur.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
                self._load_employees()
                ToastNotification(self, "✅ " + get_text("deleted", self.lang), "success")
            except Exception as e:
                ToastNotification(self, f"❌ {e}", "error")

    def _build_contractors_tab(self, parent):
        """Вкладка Контрагенты"""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="➕ " + get_text("add", self.lang), 
                     command=self._add_contractor, width=130, height=30,
                     fg_color=ColorTheme.SUCCESS,
                     hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✏️ " + get_text("edit", self.lang), 
                     command=self._edit_contractor, width=130, height=30,
                     fg_color=ColorTheme.INFO,
                     hover_color=ColorUtils.darken(ColorTheme.INFO, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ " + get_text("delete", self.lang), 
                     command=self._delete_contractor, width=130, height=30,
                     fg_color=ColorTheme.ERROR,
                     hover_color=ColorUtils.darken(ColorTheme.ERROR, 10)
        ).pack(side="left", padx=10)
        
        table_frame = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_INPUT)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = [
            get_text("col_id", self.lang),
            get_text("col_name", self.lang),
            get_text("inn", self.lang),
            get_text("phone", self.lang),
            get_text("email", self.lang),
            get_text("address", self.lang)
        ]
        col_widths = {
            get_text("col_id", self.lang): 50,
            get_text("col_name", self.lang): 200,
            get_text("inn", self.lang): 100,
            get_text("phone", self.lang): 120,
            get_text("email", self.lang): 180,
            get_text("address", self.lang): 200
        }
        
        self.cont_tree = DataTable(
            table_frame,
            columns=columns,
            column_widths=col_widths,
            sortable=True,
            copyable=True
        )
        self.cont_tree.pack(fill="both", expand=True)
        
        self._load_contractors()

    def _load_contractors(self) -> None:
        """Загрузка контрагентов с пустым состоянием"""
        self.cont_tree.delete(*self.cont_tree.get_children())
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, name, inn, phone, email, address 
                    FROM contractors 
                    ORDER BY name
                """)
                rows = cur.fetchall()
            
            if not rows:
                self.cont_tree.show_empty_state(
                    message=get_text("no_contractors", self.lang) or "Контрагенты не найдены",
                    icon="🏢"
                )
                return
            else:
                self.cont_tree.hide_empty_state()
            
            for idx, row in enumerate(rows):
                tag = "odd" if idx % 2 else "even"
                values = (row[0], row[1], row[2] or "—", row[3] or "—", 
                         row[4] or "—", row[5] or "—")
                self.cont_tree.insert("", "end", values=values, tags=(tag,))
        except Exception as e:
            app_logger.error(f"Error loading contractors: {e}")

    def _add_contractor(self) -> None:
        """Добавление контрагента"""
        dialog = ContractorDialog(self, self.lang, title="➕ " + get_text("add_contractor", self.lang))
        if dialog.result:
            self._load_contractors()
            ToastNotification(self, "✅ " + get_text("added", self.lang), "success")

    def _edit_contractor(self) -> None:
        """Редактирование контрагента"""
        selection = self.cont_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        cont_id = self.cont_tree.item(selection[0])['values'][0]
        dialog = ContractorDialog(self, self.lang, contractor_id=cont_id,
                                 title="✏️ " + get_text("edit_contractor", self.lang))
        if dialog.result:
            self._load_contractors()
            ToastNotification(self, "✅ " + get_text("updated", self.lang), "success")

    def _delete_contractor(self) -> None:
        """Удаление контрагента"""
        selection = self.cont_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        cont_id = self.cont_tree.item(selection[0])['values'][0]
        cont_name = self.cont_tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno(get_text("confirm_delete", self.lang),
                              f"{get_text('delete', self.lang)} '{cont_name}'?"):
            try:
                with self.db.get_cursor() as cur:
                    cur.execute("DELETE FROM contractors WHERE id = ?", (cont_id,))
                self._load_contractors()
                ToastNotification(self, "✅ " + get_text("deleted", self.lang), "success")
            except Exception as e:
                ToastNotification(self, f"❌ {e}", "error")

    # ==================== 📦 НОМЕНКЛАТУРА (ТИПЫ + ЗАПЧАСТИ) ====================
    def _show_nomenclature(self) -> None:
        """Показ номенклатуры (вкладки: Типы, Запчасти)"""
        self._clear_content()
        self.current_section = "nomenclature"
        
        header = ctk.CTkFrame(self.content_frame, fg_color=ColorTheme.STATUS_READY, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=get_text("nomenclature", self.lang), 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=10)
        
        notebook = ctk.CTkTabview(self.content_frame, fg_color="transparent")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        types_tab = notebook.add(get_text("nom_types", self.lang))
        parts_tab = notebook.add(get_text("parts", self.lang))
        
        self._build_nom_types_tab(types_tab)
        self._build_parts_tab(parts_tab)

    def _build_nom_types_tab(self, parent):
        """Вкладка Типы номенклатуры"""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="➕ " + get_text("add", self.lang), 
                     command=self._add_nom_type, width=130, height=30,
                     fg_color=ColorTheme.SUCCESS,
                     hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✏️ " + get_text("edit", self.lang), 
                     command=self._edit_nom_type, width=130, height=30,
                     fg_color=ColorTheme.INFO,
                     hover_color=ColorUtils.darken(ColorTheme.INFO, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ " + get_text("delete", self.lang), 
                     command=self._delete_nom_type, width=130, height=30,
                     fg_color=ColorTheme.ERROR,
                     hover_color=ColorUtils.darken(ColorTheme.ERROR, 10)
        ).pack(side="left", padx=10)
        
        table_frame = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_INPUT)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = [
            get_text("col_id", self.lang),
            get_text("nom_type", self.lang),
            get_text("description", self.lang)
        ]
        col_widths = {
            get_text("col_id", self.lang): 50,
            get_text("nom_type", self.lang): 250,
            get_text("description", self.lang): 400
        }
        
        self.nom_tree = DataTable(
            table_frame,
            columns=columns,
            column_widths=col_widths,
            sortable=True,
            copyable=True
        )
        self.nom_tree.pack(fill="both", expand=True)
        
        self._load_nom_types()

    def _load_nom_types(self) -> None:
        """Загрузка типов номенклатуры"""
        self.nom_tree.delete(*self.nom_tree.get_children())
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, nom_type, notes 
                    FROM directories 
                    WHERE nom_type IS NOT NULL 
                    ORDER BY nom_type
                """)
                rows = cur.fetchall()
            
            if not rows:
                self.nom_tree.show_empty_state(
                    message=get_text("no_nom_types", self.lang) or "Типы не найдены",
                    icon="📦"
                )
                return
            else:
                self.nom_tree.hide_empty_state()
            
            for idx, row in enumerate(rows):
                tag = "odd" if idx % 2 else "even"
                values = (row[0], row[1], row[2] or "—")
                self.nom_tree.insert("", "end", values=values, tags=(tag,))
        except Exception as e:
            app_logger.error(f"Error loading nom types: {e}")

    def _add_nom_type(self) -> None:
        """Добавление типа"""
        dialog = NomTypeDialog(self, self.lang, title="➕ " + get_text("add_nom_type", self.lang))
        if dialog.result:
            self._load_nom_types()
            ToastNotification(self, "✅ " + get_text("added", self.lang), "success")

    def _edit_nom_type(self) -> None:
        """Редактирование типа"""
        selection = self.nom_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        nom_id = self.nom_tree.item(selection[0])['values'][0]
        dialog = NomTypeDialog(self, self.lang, nom_type_id=nom_id,
                              title="✏️ " + get_text("edit_nom_type", self.lang))
        if dialog.result:
            self._load_nom_types()
            ToastNotification(self, "✅ " + get_text("updated", self.lang), "success")

    def _delete_nom_type(self) -> None:
        """Удаление типа"""
        selection = self.nom_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        nom_id = self.nom_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno(get_text("confirm_delete", self.lang),
                              get_text("delete_nom_type_confirm", self.lang)):
            try:
                with self.db.get_cursor() as cur:
                    cur.execute("DELETE FROM directories WHERE id = ?", (nom_id,))
                self._load_nom_types()
                ToastNotification(self, "✅ " + get_text("deleted", self.lang), "success")
            except Exception as e:
                ToastNotification(self, f"❌ {e}", "error")

    def _build_parts_tab(self, parent):
        """Вкладка Запчасти"""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="➕ " + get_text("add", self.lang), 
                     command=self._add_part, width=130, height=30,
                     fg_color=ColorTheme.SUCCESS,
                     hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✏️ " + get_text("edit", self.lang), 
                     command=self._edit_part, width=130, height=30,
                     fg_color=ColorTheme.INFO,
                     hover_color=ColorUtils.darken(ColorTheme.INFO, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ " + get_text("delete", self.lang), 
                     command=self._delete_part, width=130, height=30,
                     fg_color=ColorTheme.ERROR,
                     hover_color=ColorUtils.darken(ColorTheme.ERROR, 10)
        ).pack(side="left", padx=10)
        
        table_frame = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_INPUT)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = [
            get_text("col_id", self.lang),
            get_text("col_name", self.lang),
            get_text("sku", self.lang),
            get_text("quantity", self.lang),
            get_text("unit", self.lang),
            get_text("price", self.lang),
            get_text("markup", self.lang)
        ]
        col_widths = {
            get_text("col_id", self.lang): 50,
            get_text("col_name", self.lang): 200,
            get_text("sku", self.lang): 100,
            get_text("quantity", self.lang): 80,
            get_text("unit", self.lang): 60,
            get_text("price", self.lang): 100,
            get_text("markup", self.lang): 80
        }
        
        self.parts_tree = DataTable(
            table_frame,
            columns=columns,
            column_widths=col_widths,
            sortable=True,
            copyable=True
        )
        self.parts_tree.pack(fill="both", expand=True)
        
        # Теги для низкого остатка
        self.parts_tree.tag_configure("low_stock", background=ColorUtils.darken(ColorTheme.WARNING, 30), foreground="#fdba74")
        
        self._load_parts()

    def _load_parts(self) -> None:
        """Загрузка запчастей с пустым состоянием"""
        self.parts_tree.delete(*self.parts_tree.get_children())
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, name, sku, quantity, unit, price,
                           CASE WHEN cost > 0 THEN ((price - cost) / cost * 100) ELSE 0 END as markup
                    FROM parts 
                    ORDER BY name
                """)
                rows = cur.fetchall()
            
            if not rows:
                self.parts_tree.show_empty_state(
                    message=get_text("no_parts", self.lang) or "Запчасти не найдены",
                    icon="🔧"
                )
                return
            else:
                self.parts_tree.hide_empty_state()
            
            for idx, row in enumerate(rows):
                tag = "low_stock" if row[3] and row[3] < 5 else ("odd" if idx % 2 else "even")
                values = (
                    row[0], row[1], row[2], row[3], row[4],
                    f"{row[5]:.2f} ₽", f"{row[6]:.0f}%"
                )
                self.parts_tree.insert("", "end", values=values, tags=(tag,))
        except Exception as e:
            app_logger.error(f"Error loading parts: {e}")

    def _add_part(self) -> None:
        """Добавление запчасти"""
        dialog = PartDialog(self, self.lang, title="➕ " + get_text("add_part", self.lang))
        if dialog.result:
            self._load_parts()
            ToastNotification(self, "✅ " + get_text("added", self.lang), "success")

    def _edit_part(self) -> None:
        """Редактирование запчасти"""
        selection = self.parts_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        part_id = self.parts_tree.item(selection[0])['values'][0]
        dialog = PartDialog(self, self.lang, part_id=part_id,
                           title="✏️ " + get_text("edit_part", self.lang))
        if dialog.result:
            self._load_parts()
            ToastNotification(self, "✅ " + get_text("updated", self.lang), "success")

    def _delete_part(self) -> None:
        """Удаление запчасти"""
        selection = self.parts_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        part_id = self.parts_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno(get_text("confirm_delete", self.lang),
                              get_text("delete_part_confirm", self.lang)):
            try:
                with self.db.get_cursor() as cur:
                    cur.execute("DELETE FROM parts WHERE id = ?", (part_id,))
                self._load_parts()
                ToastNotification(self, "✅ " + get_text("deleted", self.lang), "success")
            except Exception as e:
                ToastNotification(self, f"❌ {e}", "error")

    # ==================== 📏 ЕДИНИЦЫ ИЗМЕРЕНИЯ ====================
    def _show_units(self) -> None:
        """Показ единиц измерения"""
        self._clear_content()
        self.current_section = "units"
        
        header = ctk.CTkFrame(self.content_frame, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=get_text("units", self.lang), 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="➕ " + get_text("add", self.lang), 
                     command=self._add_unit, width=130, height=30,
                     fg_color=ColorTheme.SUCCESS,
                     hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✏️ " + get_text("edit", self.lang), 
                     command=self._edit_unit, width=130, height=30,
                     fg_color=ColorTheme.INFO,
                     hover_color=ColorUtils.darken(ColorTheme.INFO, 10)
        ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ " + get_text("delete", self.lang), 
                     command=self._delete_unit, width=130, height=30,
                     fg_color=ColorTheme.ERROR,
                     hover_color=ColorUtils.darken(ColorTheme.ERROR, 10)
        ).pack(side="left", padx=10)
        
        table_frame = ctk.CTkFrame(self.content_frame, fg_color=ColorTheme.BG_INPUT)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = [
            get_text("col_id", self.lang),
            get_text("col_name", self.lang),
            get_text("sku", self.lang),
            get_text("coefficient", self.lang)
        ]
        col_widths = {
            get_text("col_id", self.lang): 50,
            get_text("col_name", self.lang): 200,
            get_text("sku", self.lang): 100,
            get_text("coefficient", self.lang): 100
        }
        
        self.units_tree = DataTable(
            table_frame,
            columns=columns,
            column_widths=col_widths,
            sortable=True,
            copyable=True
        )
        self.units_tree.pack(fill="both", expand=True)
        
        self._load_units()

    def _load_units(self) -> None:
        """Загрузка единиц"""
        self.units_tree.delete(*self.units_tree.get_children())
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, unit, sku, coefficient 
                    FROM directories 
                    WHERE unit IS NOT NULL 
                    ORDER BY unit
                """)
                rows = cur.fetchall()
            
            if not rows:
                self.units_tree.show_empty_state(
                    message=get_text("no_units", self.lang) or "Единицы не найдены",
                    icon="📏"
                )
                return
            else:
                self.units_tree.hide_empty_state()
            
            for idx, row in enumerate(rows):
                tag = "odd" if idx % 2 else "even"
                values = (row[0], row[1], row[2] or "—", row[3] or "1")
                self.units_tree.insert("", "end", values=values, tags=(tag,))
        except Exception as e:
            app_logger.error(f"Error loading units: {e}")

    def _add_unit(self) -> None:
        """Добавление единицы"""
        dialog = UnitDialog(self, self.lang, title="➕ " + get_text("add_unit", self.lang))
        if dialog.result:
            self._load_units()
            ToastNotification(self, "✅ " + get_text("added", self.lang), "success")

    def _edit_unit(self) -> None:
        """Редактирование единицы"""
        selection = self.units_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        unit_id = self.units_tree.item(selection[0])['values'][0]
        dialog = UnitDialog(self, self.lang, unit_id=unit_id,
                           title="✏️ " + get_text("edit_unit", self.lang))
        if dialog.result:
            self._load_units()
            ToastNotification(self, "✅ " + get_text("updated", self.lang), "success")

    def _delete_unit(self) -> None:
        """Удаление единицы"""
        selection = self.units_tree.selection()
        if not selection:
            ToastNotification(self, "⚠️ " + get_text("select_row", self.lang), "warning")
            return
        
        unit_id = self.units_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno(get_text("confirm_delete", self.lang),
                              get_text("delete_unit_confirm", self.lang)):
            try:
                with self.db.get_cursor() as cur:
                    cur.execute("DELETE FROM directories WHERE id = ?", (unit_id,))
                self._load_units()
                ToastNotification(self, "✅ " + get_text("deleted", self.lang), "success")
            except Exception as e:
                ToastNotification(self, f"❌ {e}", "error")


# ==================== 🎨 ДИАЛОГИ ====================

class EmployeeDialog(ctk.CTkToplevel):
    """Диалог сотрудника с валидацией и переводом"""
    
    def __init__(self, parent, lang, employee_id=None, title="Сотрудник"):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x600")
        self.minsize(450, 550)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        self.result = False
        self.lang = lang
        
        self.db = DatabaseConnection()
        self.employee_id = employee_id
        
        # Центрирование
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"+{x}+{y}")
        
        self._build_ui()
        
        if employee_id:
            self._load_employee(employee_id)
    
    def _build_ui(self):
        """Построение интерфейса с валидацией"""
        # Заголовок
        ctk.CTkLabel(
            self, text="👥 " + get_text("employee_info", self.lang), 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.PRIMARY
        ).pack(pady=15)
        
        # Скроллируемая форма
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=400)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ФИО (обязательное)
        ctk.CTkLabel(
            scroll_frame, 
            text=get_text("full_name", self.lang) + " *", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        self.name_entry = ctk.CTkEntry(
            scroll_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.name_entry.pack(fill="x", pady=2)
        
        # Должность
        ctk.CTkLabel(
            scroll_frame, text=get_text("position", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.position_entry = ctk.CTkEntry(
            scroll_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.position_entry.pack(fill="x", pady=2)
        
        # Телефон (с валидацией)
        ctk.CTkLabel(
            scroll_frame, text=get_text("phone", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.phone_entry = ctk.CTkEntry(
            scroll_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            placeholder_text="+7 (999) 123-45-67"
        )
        self.phone_entry.pack(fill="x", pady=2)
        
        # Email (с валидацией)
        ctk.CTkLabel(
            scroll_frame, text=get_text("email", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.email_entry = ctk.CTkEntry(
            scroll_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            placeholder_text="employee@company.ru"
        )
        self.email_entry.pack(fill="x", pady=2)
        
        # Зарплата (числовая валидация)
        ctk.CTkLabel(
            scroll_frame, text=get_text("salary", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.salary_entry = ctk.CTkEntry(
            scroll_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.salary_entry.pack(fill="x", pady=2)
        self.salary_entry.insert(0, "0")
        
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
        
        ctk.CTkButton(
            btn_frame, text="💾 " + get_text("save", self.lang), 
            command=self._save,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
        
        ctk.CTkButton(
            btn_frame, text="❌ " + get_text("cancel", self.lang), 
            command=self.destroy,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
    
    def _load_employee(self, emp_id):
        """Загрузка данных"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT full_name, position, phone, email, salary 
                    FROM employees WHERE id = ?
                """, (emp_id,))
                row = cur.fetchone()
            
            if row:
                self.name_entry.delete(0, 'end')
                self.name_entry.insert(0, row[0] or "")
                self.position_entry.delete(0, 'end')
                self.position_entry.insert(0, row[1] or "")
                self.phone_entry.delete(0, 'end')
                self.phone_entry.insert(0, row[2] or "")
                self.email_entry.delete(0, 'end')
                self.email_entry.insert(0, row[3] or "")
                self.salary_entry.delete(0, 'end')
                self.salary_entry.insert(0, str(row[4] or 0))
        except Exception as e:
            app_logger.error(f"Error loading employee: {e}")
    
    def _save(self):
        """Сохранение с валидацией"""
        name = self.name_entry.get().strip()
        if not name:
            ToastNotification(self, "⚠️ " + get_text("fill_required", self.lang), "warning")
            self.name_entry.focus_set()
            return
        
        # Валидация телефона
        phone = self.phone_entry.get().strip()
        if phone:
            valid, msg = validate_phone(phone, "ru")
            if not valid:
                ToastNotification(self, f"⚠️ {msg}", "warning")
                self.phone_entry.focus_set()
                return
        
        # Валидация email
        email = self.email_entry.get().strip()
        if email:
            valid, msg = validate_email(email)
            if not valid:
                ToastNotification(self, f"⚠️ {msg}", "warning")
                self.email_entry.focus_set()
                return
        
        # Валидация зарплаты
        try:
            salary = float(self.salary_entry.get() or 0)
            if salary < 0:
                raise ValueError()
        except ValueError:
            ToastNotification(self, get_text("invalid_salary", self.lang) or "Зарплата должна быть числом >= 0", "warning")
            self.salary_entry.focus_set()
            return
        
        try:
            data = (name, self.position_entry.get().strip(), phone, email, salary)
            
            with self.db.get_cursor() as cur:
                if self.employee_id:
                    cur.execute("""
                        UPDATE employees SET full_name=?, position=?, 
                        phone=?, email=?, salary=? WHERE id=?
                    """, (*data, self.employee_id))
                else:
                    cur.execute("""
                        INSERT INTO employees (full_name, position, phone, email, salary)
                        VALUES (?, ?, ?, ?, ?)
                    """, data)
            
            self.result = True
            self.destroy()
        except Exception as e:
            ToastNotification(self, f"❌ {e}", "error")


class ContractorDialog(ctk.CTkToplevel):
    """Диалог контрагента с валидацией"""
    
    def __init__(self, parent, lang, contractor_id=None, title="Контрагент"):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x600")
        self.minsize(450, 550)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        self.result = False
        self.lang = lang
        
        self.db = DatabaseConnection()
        self.contractor_id = contractor_id
        self._build_ui()
        
        if contractor_id:
            self._load_contractor(contractor_id)
    
    def _build_ui(self):
        ctk.CTkLabel(
            self, text="🏢 " + get_text("contractor_info", self.lang), 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.PRIMARY
        ).pack(pady=15)
        
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=400)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        fields = [
            ("contractor_name", "name_entry", True),  # required
            ("inn", "inn_entry", False),
            ("phone", "phone_entry", False),
            ("email", "email_entry", False),
            ("address", "address_entry", False)
        ]
        
        for key, attr_name, required in fields:
            label_text = get_text(key, self.lang) + (" *" if required else "")
            ctk.CTkLabel(
                scroll_frame, text=label_text, 
                text_color=ColorTheme.TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", pady=(10, 2))
            entry = ctk.CTkEntry(
                scroll_frame, height=35,
                fg_color=ColorTheme.BG_INPUT,
                text_color=ColorTheme.TEXT_PRIMARY
            )
            entry.pack(fill="x", pady=2)
            setattr(self, attr_name, entry)
            setattr(self, f"{attr_name}_required", required)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame, text="💾 " + get_text("save", self.lang), 
            command=self._save,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(
            btn_frame, text="❌ " + get_text("cancel", self.lang), 
            command=self.destroy,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
    
    def _load_contractor(self, cont_id):
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT name, inn, phone, email, address 
                    FROM contractors WHERE id = ?
                """, (cont_id,))
                row = cur.fetchone()
            
            if row:
                entries = [self.name_entry, self.inn_entry, self.phone_entry, 
                          self.email_entry, self.address_entry]
                for entry, value in zip(entries, row):
                    entry.delete(0, 'end')
                    entry.insert(0, value or "")
        except Exception as e:
            app_logger.error(f"Error loading contractor: {e}")
    
    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            ToastNotification(self, "⚠️ " + get_text("fill_required", self.lang), "warning")
            self.name_entry.focus_set()
            return
        
        # Валидация ИНН если указан
        inn = self.inn_entry.get().strip()
        if inn:
            valid, msg = validate_inn(inn, "legal")
            if not valid:
                ToastNotification(self, f"⚠️ {msg}", "warning")
                self.inn_entry.focus_set()
                return
        
        # Валидация телефона
        phone = self.phone_entry.get().strip()
        if phone:
            valid, msg = validate_phone(phone, "ru")
            if not valid:
                ToastNotification(self, f"⚠️ {msg}", "warning")
                self.phone_entry.focus_set()
                return
        
        try:
            data = (name, inn, phone, self.email_entry.get().strip(), self.address_entry.get().strip())
            
            with self.db.get_cursor() as cur:
                if self.contractor_id:
                    cur.execute("""
                        UPDATE contractors SET name=?, inn=?, phone=?, 
                        email=?, address=? WHERE id=?
                    """, (*data, self.contractor_id))
                else:
                    cur.execute("""
                        INSERT INTO contractors (name, inn, phone, email, address)
                        VALUES (?, ?, ?, ?, ?)
                    """, data)
            
            self.result = True
            self.destroy()
        except Exception as e:
            ToastNotification(self, f"❌ {e}", "error")


class EquipmentDialog(ctk.CTkToplevel):
    """Диалог оборудования — ИСПРАВЛЕНО: employees вместо clients"""
    
    def __init__(self, parent, lang, equipment_id=None, title="Оборудование"):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x650")
        self.minsize(450, 600)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        self.result = False
        self.lang = lang
        
        self.db = DatabaseConnection()
        self.equipment_id = equipment_id
        self.client_ids: List[int] = []
        self._build_ui()
        
        if equipment_id:
            self._load_equipment(equipment_id)
    
    def _build_ui(self):
        ctk.CTkLabel(
            self, text="💻 " + get_text("equipment_info", self.lang), 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.PRIMARY
        ).pack(pady=15)
        
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=450)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ✅ ИСПРАВЛЕНО: Сотрудник (не клиент)
        ctk.CTkLabel(
            scroll_frame, text=get_text("employee", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        self.employee_combo = ctk.CTkComboBox(
            scroll_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.employee_combo.pack(fill="x", pady=2)
        self._load_employees_for_combo()
        
        fields = [
            ("model", "model_entry", True),
            ("device_type", "type_entry", False),
            ("serial_number", "serial_entry", False),
            ("color", "color_entry", False),
            ("imei", "imei_entry", False),
            ("accessories", "acc_entry", False),
            ("external_damage", "damage_entry", False)
        ]
        
        for key, attr_name, required in fields:
            label_text = get_text(key, self.lang) + (" *" if required else "")
            ctk.CTkLabel(
                scroll_frame, text=label_text, 
                text_color=ColorTheme.TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", pady=(10, 2))
            entry = ctk.CTkEntry(
                scroll_frame, height=35,
                fg_color=ColorTheme.BG_INPUT,
                text_color=ColorTheme.TEXT_PRIMARY
            )
            entry.pack(fill="x", pady=2)
            setattr(self, attr_name, entry)
            setattr(self, f"{attr_name}_required", required)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame, text="💾 " + get_text("save", self.lang), 
            command=self._save,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(
            btn_frame, text="❌ " + get_text("cancel", self.lang), 
            command=self.destroy,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
    
    def _load_employees_for_combo(self):
        """✅ ИСПРАВЛЕНО: Загрузка сотрудников (не клиентов)"""
        try:
            with self.db.get_cursor() as cur:
                # ✅ employees.full_name вместо clients.name
                cur.execute("SELECT id, full_name FROM employees ORDER BY full_name")
                employees = cur.fetchall()
                self.client_ids = [e[0] for e in employees]  # Оставляем имя переменной для совместимости
                names = [e[1] for e in employees]
                self.employee_combo.configure(values=names if names else ["—"])
        except Exception as e:
            app_logger.error(f"Error loading employees: {e}")
            self.employee_combo.configure(values=["—"])
            self.client_ids = []
    
    def _load_equipment(self, eq_id):
        try:
            with self.db.get_cursor() as cur:
                # ✅ employees вместо clients
                cur.execute("""
                    SELECT client_id, model, device_type, serial_number, 
                           color, imei, accessories, external_damage
                    FROM equipment WHERE id = ?
                """, (eq_id,))
                row = cur.fetchone()
            
            if row:
                # ✅ Устанавливаем сотрудника через full_name
                if row[0] and row[0] in self.client_ids:
                    idx = self.client_ids.index(row[0])
                    values = self.employee_combo.cget("values")
                    if idx < len(values):
                        self.employee_combo.set(values[idx])
                
                entries = [self.model_entry, self.type_entry, self.serial_entry,
                          self.color_entry, self.imei_entry, self.acc_entry, self.damage_entry]
                for entry, value in zip(entries, row[1:]):
                    entry.delete(0, 'end')
                    entry.insert(0, value or "")
        except Exception as e:
            app_logger.error(f"Error loading equipment: {e}")
    
    def _save(self):
        model = self.model_entry.get().strip()
        if not model:
            ToastNotification(self, "⚠️ " + get_text("fill_required", self.lang), "warning")
            self.model_entry.focus_set()
            return
        
        try:
            # ✅ Получаем ID сотрудника
            emp_idx = self.employee_combo.current()
            client_id = self.client_ids[emp_idx] if 0 <= emp_idx < len(self.client_ids) else None
            
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


class NomTypeDialog(ctk.CTkToplevel):
    """Диалог типа номенклатуры"""
    
    def __init__(self, parent, lang, nom_type_id=None, title="Тип"):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x400")
        self.minsize(400, 350)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        self.result = False
        self.lang = lang
        
        self.db = DatabaseConnection()
        self.nom_type_id = nom_type_id
        self._build_ui()
        
        if nom_type_id:
            self._load_nom_type(nom_type_id)
    
    def _build_ui(self):
        ctk.CTkLabel(
            self, text="📦 " + get_text("nom_type_info", self.lang), 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.PRIMARY
        ).pack(pady=15)
        
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            form_frame, text=get_text("nom_type", self.lang) + " *", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.name_entry = ctk.CTkEntry(
            form_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.name_entry.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            form_frame, text=get_text("description", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.desc_entry = ctk.CTkTextbox(
            form_frame, height=80,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.desc_entry.pack(fill="x", pady=2)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame, text="💾 " + get_text("save", self.lang), 
            command=self._save,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(
            btn_frame, text="❌ " + get_text("cancel", self.lang), 
            command=self.destroy,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
    
    def _load_nom_type(self, nom_id):
        try:
            with self.db.get_cursor() as cur:
                cur.execute("SELECT nom_type, notes FROM directories WHERE id = ?", (nom_id,))
                row = cur.fetchone()
            
            if row:
                self.name_entry.delete(0, 'end')
                self.name_entry.insert(0, row[0] or "")
                self.desc_entry.delete("1.0", 'end')
                self.desc_entry.insert("1.0", row[1] or "")
        except Exception as e:
            app_logger.error(f"Error loading nom type: {e}")
    
    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            ToastNotification(self, "⚠️ " + get_text("fill_required", self.lang), "warning")
            self.name_entry.focus_set()
            return
        
        desc = self.desc_entry.get("1.0", 'end').strip()
        
        try:
            with self.db.get_cursor() as cur:
                if self.nom_type_id:
                    cur.execute("""
                        UPDATE directories SET nom_type=?, notes=? WHERE id=?
                    """, (name, desc, self.nom_type_id))
                else:
                    cur.execute("""
                        INSERT INTO directories (nom_type, notes) VALUES (?, ?)
                    """, (name, desc))
            
            self.result = True
            self.destroy()
        except Exception as e:
            ToastNotification(self, f"❌ {e}", "error")


class PartDialog(ctk.CTkToplevel):
    """Диалог запчасти с валидацией"""
    
    def __init__(self, parent, lang, part_id=None, title="Запчасть"):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x650")
        self.minsize(450, 600)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        self.result = False
        self.lang = lang
        
        self.db = DatabaseConnection()
        self.part_id = part_id
        self._build_ui()
        
        if part_id:
            self._load_part(part_id)
    
    def _build_ui(self):
        ctk.CTkLabel(
            self, text="🔧 " + get_text("part_info", self.lang), 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.PRIMARY
        ).pack(pady=15)
        
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=450)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        fields = [
            ("part_name", "name_entry", True),
            ("sku", "sku_entry", False),
            ("quantity", "qty_entry", False, "0"),
            ("unit", "unit_entry", False, "шт"),
            ("cost_price", "cost_entry", False, "0"),
            ("retail_price", "price_entry", False, "0"),
            ("category", "cat_entry", False),
            ("supplier", "supp_entry", False),
            ("min_stock", "min_entry", False, "5"),
            ("notes", "notes_entry", False)
        ]
        
        for field in fields:
            key = field[0]
            attr = field[1]
            required = field[2] if len(field) > 2 else False
            default = field[3] if len(field) > 3 else ""
            
            label_text = get_text(key, self.lang) + (" *" if required else "")
            ctk.CTkLabel(
                scroll_frame, text=label_text, 
                text_color=ColorTheme.TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", pady=(10, 2))
            entry = ctk.CTkEntry(
                scroll_frame, height=35,
                fg_color=ColorTheme.BG_INPUT,
                text_color=ColorTheme.TEXT_PRIMARY
            )
            entry.pack(fill="x", pady=2)
            if default:
                entry.insert(0, default)
            setattr(self, attr, entry)
            setattr(self, f"{attr}_required", required)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame, text="💾 " + get_text("save", self.lang), 
            command=self._save,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(
            btn_frame, text="❌ " + get_text("cancel", self.lang), 
            command=self.destroy,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
    
    def _load_part(self, part_id):
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT name, sku, quantity, unit, cost, price, 
                           category, supplier, min_stock, notes
                    FROM parts WHERE id = ?
                """, (part_id,))
                row = cur.fetchone()
            
            if row:
                entries = [self.name_entry, self.sku_entry, self.qty_entry, 
                          self.unit_entry, self.cost_entry, self.price_entry,
                          self.cat_entry, self.supp_entry, self.min_entry, self.notes_entry]
                for entry, value in zip(entries, row):
                    entry.delete(0, 'end')
                    entry.insert(0, str(value) if value is not None else "")
        except Exception as e:
            app_logger.error(f"Error loading part: {e}")
    
    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            ToastNotification(self, "⚠️ " + get_text("fill_required", self.lang), "warning")
            self.name_entry.focus_set()
            return
        
        try:
            # Валидация числовых полей
            quantity = int(self.qty_entry.get() or 0)
            cost = float(self.cost_entry.get() or 0)
            price = float(self.price_entry.get() or 0)
            min_stock = int(self.min_entry.get() or 5)
            
            if quantity < 0 or cost < 0 or price < 0 or min_stock < 0:
                raise ValueError("Values cannot be negative")
            
            data = (
                name,
                self.sku_entry.get().strip(),
                quantity,
                self.unit_entry.get().strip() or "шт",
                cost,
                price,
                self.cat_entry.get().strip(),
                self.supp_entry.get().strip(),
                min_stock,
                self.notes_entry.get().strip()
            )
            
            with self.db.get_cursor() as cur:
                if self.part_id:
                    cur.execute("""
                        UPDATE parts SET name=?, sku=?, quantity=?, unit=?, 
                        cost=?, price=?, category=?, supplier=?, min_stock=?, 
                        notes=? WHERE id=?
                    """, (*data, self.part_id))
                else:
                    cur.execute("""
                        INSERT INTO parts (name, sku, quantity, unit, cost, price, 
                        category, supplier, min_stock, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, data)
            
            self.result = True
            self.destroy()
        except ValueError:
            ToastNotification(self, get_text("invalid_number", self.lang) or "Неверное числовое значение", "warning")
        except Exception as e:
            ToastNotification(self, f"❌ {e}", "error")


class UnitDialog(ctk.CTkToplevel):
    """Диалог единицы измерения"""
    
    def __init__(self, parent, lang, unit_id=None, title="Единица"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x400")
        self.minsize(350, 350)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        self.result = False
        self.lang = lang
        
        self.db = DatabaseConnection()
        self.unit_id = unit_id
        self._build_ui()
        
        if unit_id:
            self._load_unit(unit_id)
    
    def _build_ui(self):
        ctk.CTkLabel(
            self, text="📏 " + get_text("unit_info", self.lang), 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.PRIMARY
        ).pack(pady=15)
        
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            form_frame, text=get_text("col_name", self.lang) + " *", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.name_entry = ctk.CTkEntry(
            form_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.name_entry.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            form_frame, text=get_text("sku", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.code_entry = ctk.CTkEntry(
            form_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.code_entry.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            form_frame, text=get_text("coefficient", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 2))
        self.coeff_entry = ctk.CTkEntry(
            form_frame, height=35,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.coeff_entry.pack(fill="x", pady=2)
        self.coeff_entry.insert(0, "1")
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame, text="💾 " + get_text("save", self.lang), 
            command=self._save,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(
            btn_frame, text="❌ " + get_text("cancel", self.lang), 
            command=self.destroy,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            height=35, width=150
        ).pack(side="left", padx=10, expand=True)
    
    def _load_unit(self, unit_id):
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT unit, sku, coefficient 
                    FROM directories WHERE id = ?
                """, (unit_id,))
                row = cur.fetchone()
            
            if row:
                self.name_entry.delete(0, 'end')
                self.name_entry.insert(0, row[0] or "")
                self.code_entry.delete(0, 'end')
                self.code_entry.insert(0, row[1] or "")
                self.coeff_entry.delete(0, 'end')
                self.coeff_entry.insert(0, str(row[2] or 1))
        except Exception as e:
            app_logger.error(f"Error loading unit: {e}")
    
    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            ToastNotification(self, "⚠️ " + get_text("fill_required", self.lang), "warning")
            self.name_entry.focus_set()
            return
        
        try:
            coefficient = float(self.coeff_entry.get() or 1)
            if coefficient <= 0:
                raise ValueError()
            
            data = (name, self.code_entry.get().strip(), coefficient)
            
            with self.db.get_cursor() as cur:
                if self.unit_id:
                    cur.execute("""
                        UPDATE directories SET unit=?, sku=?, coefficient=? 
                        WHERE id=?
                    """, (*data, self.unit_id))
                else:
                    cur.execute("""
                        INSERT INTO directories (unit, sku, coefficient) 
                        VALUES (?, ?, ?)
                    """, data)
            
            self.result = True
            self.destroy()
        except ValueError:
            ToastNotification(self, get_text("invalid_coefficient", self.lang) or "Коэффициент должен быть числом > 0", "warning")
        except Exception as e:
            ToastNotification(self, f"❌ {e}", "error")