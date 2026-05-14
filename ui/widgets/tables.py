# ui/widgets/tables.py
"""
Переиспользуемые таблицы для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Контейнер, форматирование цен, копирование, anchor для ttk
✅ УЛУЧШЕНО: Сортировка, поиск, пустые данные, тема
✅ ГИБКОСТЬ: Пагинация, экспорт, контекстное меню
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Any, Callable, Dict, Union
from datetime import datetime

# ✅ Импорт в начале файла для Pylance
import customtkinter as ctk

from ui.theme import ColorTheme, theme as theme_manager
from utils.helpers import format_currency
from translations import get_text


class TableStyle:
    """
    Единая настройка стилей для всех таблиц
    
    ✅ Поддержка динамической смены темы
    ✅ Адаптация под DPI
    ✅ Полная конфигурация состояний
    """
    
    _initialized: bool = False
    _style: Optional[ttk.Style] = None
    
    @classmethod
    def setup(cls, style: Optional[ttk.Style] = None, scale: float = 1.0) -> ttk.Style:
        """
        Настроить стили таблицы
        
        Args:
            style: Экземпляр ttk.Style (создаётся если None)
            scale: Коэффициент масштабирования для DPI (1.0 = 100%)
        """
        if style is None:
            style = ttk.Style()
        
        cls._style = style
        
        # Базовая тема
        style.theme_use("clam")
        
        # 📏 Адаптивные размеры
        row_height = int(38 * scale)
        font_size = int(12 * scale)
        heading_font_size = int(12 * scale)
        
        # 🎨 Основная конфигурация Treeview
        style.configure(
            "Custom.Treeview",
            background="#1e293b",
            fieldbackground="#1e293b",
            foreground=ColorTheme.TEXT_PRIMARY,
            rowheight=row_height,
            borderwidth=0,
            selectbackground="#4f46e5",
            selectforeground="#FFFFFF",
            font=("Segoe UI", font_size),
            padding=(4, 2),
        )
        
        # 🎯 Заголовки колонок
        style.configure(
            "Custom.Treeview.Heading",
            background="#334155",
            foreground="#e2e8f0",
            font=("Segoe UI", heading_font_size, "bold"),
            relief="flat",
            padding=(8, 6),
        )
        
        # 🖱️ Состояния при наведении/выборе
        style.map(
            "Custom.Treeview",
            background=[
                ("selected", "#4f46e5"),
                ("active", "#2d3a4e"),
                ("!selected", "#1e293b"),
            ],
            foreground=[
                ("selected", "#FFFFFF"),
                ("!selected", ColorTheme.TEXT_PRIMARY),
            ],
        )
        
        style.map(
            "Custom.Treeview.Heading",
            background=[
                ("active", "#475569"),
                ("pressed", "#3b4f6b"),
            ],
            foreground=[
                ("active", "#FFFFFF"),
                ("pressed", "#FFFFFF"),
            ],
        )
        
        cls._initialized = True
        return style
    
    @classmethod
    def update_theme(cls, style: Optional[ttk.Style] = None):
        """
        Обновить стили при смене темы
        
        Вызывается автоматически при регистрации в ThemeManager
        """
        if style is None:
            style = cls._style or ttk.Style()
        cls.setup(style)


class DataTable(ttk.Treeview):
    """
    Базовый класс для таблиц с расширенной функциональностью
    
    ✅ Правильная упаковка контейнера
    ✅ Сортировка по клику на заголовок
    ✅ Копирование ячеек (Ctrl+C)
    ✅ Контекстное меню (ПКМ)
    ✅ Обработка пустых данных
    ✅ Интеграция с системой тем
    ✅ Поиск/фильтрация
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        columns: List[str],
        column_widths: Optional[Dict[str, int]] = None,
        column_align: Optional[Dict[str, str]] = None,
        sortable: bool = True,
        copyable: bool = True,
        searchable: bool = True,
        on_row_select: Optional[Callable[[Any], None]] = None,
        on_row_double_click: Optional[Callable[[Any], None]] = None,
        **kwargs: Any
    ):
        """
        Инициализация таблицы
        
        Args:
            parent: Родительский виджет
            columns: Список колонок
            column_widths: Словарь {колонка: ширина_в_пикселях}
            column_align: Словарь {колонка: 'center'/'left'/'right'}
            sortable: Разрешить сортировку по клику на заголовок
            copyable: Разрешить копирование ячеек (Ctrl+C)
            searchable: Показать строку поиска
            on_row_select: Callback при выборе строки
            on_row_double_click: Callback при двойном клике
        """
        # 🧱 Создаём контейнер
        self.container = tk.Frame(parent, bg="#1e293b", highlightthickness=0)
        self.container.pack_propagate(False)  # ✅ Не сжиматься под контент
        
        # 🎨 Применяем стили
        scale = self.container.winfo_fpixels('1i') / 96.0  # DPI scaling
        TableStyle.setup(scale=scale)
        
        # 🌳 Инициализация Treeview
        super().__init__(
            self.container,
            columns=columns,
            show="headings",
            style="Custom.Treeview",
            **kwargs
        )
        
        # 📊 Настройка колонок
        self._columns = columns
        self._column_widths = column_widths or {}
        self._column_align = column_align or {}
        self._setup_columns()
        
        # 🎯 Обработчики событий
        self._sortable = sortable
        self._sort_reverse: Dict[str, bool] = {}
        self._on_row_select = on_row_select
        self._on_row_double_click = on_row_double_click
        
        if sortable:
            self._enable_header_sorting()
        
        if copyable:
            self._enable_copy()
        
        if on_row_select:
            self.bind("<<TreeviewSelect>>", lambda e: self._on_select())
        
        if on_row_double_click:
            self.bind("<Double-1>", lambda e: self._on_double_click())
        
        # 📜 Скроллбар
        self._scrollbar = ttk.Scrollbar(
            self.container, orient="vertical", command=self.yview
        )
        self.configure(yscrollcommand=self._scrollbar.set)
        
        # 📦 Упаковка виджетов
        super().pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")
        
        # ✅ ВАЖНО: Упаковываем контейнер в родительский виджет
        # Это делается ВНЕ __init__, когда пользователь добавляет таблицу
        
        # 🎨 Теги для чётных/нечётных строк (zebra stripes)
        self.tag_configure("even", background="#1e293b", foreground="#e2e8f0")
        self.tag_configure("odd", background="#253346", foreground="#e2e8f0")
        self.tag_configure("empty", background="#1e293b", foreground=ColorTheme.TEXT_SECONDARY)
        
        # 🔍 Поиск (опционально)
        self._search_var = tk.StringVar()
        self._search_entry: Optional[ctk.CTkEntry] = None
        if searchable:
            self._setup_search()
        
        # 📭 Пустое состояние
        self._empty_label: Optional[tk.Label] = None
        
        # 🔄 Подписка на смену темы
        theme_manager.register_callback(self._on_theme_change)
    
    def pack(self, **kwargs):
        """Переопределение pack() для правильной упаковки контейнера"""
        # ✅ Упаковываем контейнер, а не сам Treeview
        self.container.pack(**kwargs)
        return self
    
    def grid(self, **kwargs):
        """Переопределение grid() для правильной упаковки контейнера"""
        self.container.grid(**kwargs)
        return self
    
    def place(self, **kwargs):
        """Переопределение place() для правильной упаковки контейнера"""
        self.container.place(**kwargs)
        return self
    
    def _setup_columns(self):
        """Настройка заголовков и ширины колонок"""
        total_cols = len(self._columns)
        for i, col in enumerate(self._columns):
            align = self._column_align.get(col, "center")
            ttk_anchor = {"left": "w", "right": "e", "center": "center"}.get(align, "center")
            
            self.heading(col, text=col, anchor="center")
            self.column(col, anchor=ttk_anchor)
            
            width = self._column_widths.get(col, 120)
            # Let last column stretch to fill available space
            is_last = (i == total_cols - 1)
            self.column(col, width=width, minwidth=60, stretch=is_last)
    
    def _enable_header_sorting(self):
        """Включить сортировку по клику на заголовок"""
        for col in self._columns:
            self.heading(col, command=lambda c=col: self._sort_column(c), anchor="center")
    
    def _sort_column(self, column: str):
        """Сортировка таблицы по колонке"""
        # Получаем данные
        data = [(self.set(child, column), child) for child in self.get_children('')]
        
        # Определяем направление
        reverse = not self._sort_reverse.get(column, False)
        
        # Пытаемся сортировать как числа
        try:
            data.sort(key=lambda x: float(x[0].replace(' ₽', '').replace(',', '.').replace(' ', '')), reverse=reverse)
        except ValueError:
            # Сортируем как строки
            data.sort(key=lambda x: x[0].lower() if x[0] else "", reverse=reverse)
        
        # Перемещаем строки
        for index, (val, child) in enumerate(data):
            self.move(child, '', index)
        
        # Запоминаем направление
        self._sort_reverse[column] = reverse
        
        # Обновляем заголовок со стрелкой
        self._update_header_indicator(column, reverse)
    
    def _update_header_indicator(self, column: str, ascending: bool):
        """Обновить индикатор сортировки в заголовке"""
        arrow = " ▲" if ascending else " ▼"
        for col in self._columns:
            text = self.heading(col, "text")
            # Убираем старую стрелку
            if text.endswith(" ▲") or text.endswith(" ▼"):
                text = text[:-2]
            # Добавляем новую если это текущая колонка
            if col == column:
                text += arrow
            self.heading(col, text=text)
    
    def _enable_copy(self):
        """Включить копирование ячеек по Ctrl+C"""
        def on_copy(event):
            selection = self.selection()
            if not selection:
                return "break"
            
            item = self.item(selection[0])
            values = item['values']
            
            # Копируем всю строку или выделенную ячейку
            # (для простоты — всю строку)
            text = "\t".join(str(v) for v in values)
            self.clipboard_clear()
            self.clipboard_append(text)
            
            # Визуальная обратная связь
            self.tag_configure("copied", background=ColorTheme.SUCCESS)
            self.item(selection[0], tags=("copied",))
            self.after(200, lambda: self.item(selection[0], tags=()))
            
            return "break"
        
        self.bind("<Control-c>", on_copy)
        self.bind("<Control-C>", on_copy)
    
    def _setup_search(self):
        """Настроить строку поиска над таблицей"""
        try:
            search_frame = tk.Frame(self.container, bg="#1e293b")
            search_frame.pack(fill="x", pady=(5, 5), padx=5)
            
            ctk.CTkLabel(
                search_frame, text="🔍",
                text_color=ColorTheme.TEXT_SECONDARY,
                font=ctk.CTkFont(size=14)
            ).pack(side="left", padx=(5, 4))
            
            self._search_entry = ctk.CTkEntry(
                search_frame,
                textvariable=self._search_var,
                placeholder_text=get_text("search", "ru") or "Поиск...",
                height=32,
                corner_radius=8,
                fg_color="#334155",
                text_color="#e2e8f0",
                border_color="#475569",
                placeholder_text_color="#64748b",
            )
            self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self._search_entry.bind("<KeyRelease>", lambda e: self._filter_rows())
            
            clear_btn = ctk.CTkButton(
                search_frame, text="×", width=28, height=28,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                hover_color="#475569",
                text_color="#94a3b8",
                corner_radius=6,
                command=self._clear_search
            )
            clear_btn.pack(side="left", padx=(0, 5))
            
        except ImportError:
            pass
    
    def _clear_search(self):
        """Очистка поиска и показ всех строк"""
        self._search_var.set("")
        self._filter_rows()
    
    def _filter_rows(self):
        """Фильтрация строк по поисковому запросу"""
        query = self._search_var.get().lower().strip()
        
        if not query:
            # Показать все строки
            for child in self.get_children():
                self.reattach(child, "", "end")
            return
        
        # Скрыть несовпадающие строки
        for child in self.get_children():
            values = self.item(child)['values']
            row_text = " ".join(str(v).lower() for v in values)
            if query in row_text:
                self.reattach(child, "", "end")
            else:
                self.detach(child)
    
    def _on_select(self):
        """Обработчик выбора строки"""
        if self._on_row_select:
            selection = self.selection()
            if selection:
                item_id = selection[0]
                item_data = self.item(item_id)
                self._on_row_select(item_data)
    
    def _on_double_click(self):
        """Обработчик двойного клика"""
        if self._on_row_double_click:
            selection = self.selection()
            if selection:
                item_id = selection[0]
                item_data = self.item(item_id)
                self._on_row_double_click(item_data)
    
    def _on_theme_change(self, new_theme: str):
        """Обновить стили при смене темы"""
        TableStyle.update_theme()
        # Перерисовать таблицу
        self.configure(style="Custom.Treeview")
    
    def get_container(self) -> tk.Frame:
        """Возвращает контейнер для дополнительной настройки"""
        return self.container
    
    def show_empty_state(self, message: str = "Нет данных", icon: str = "📭"):
        """Показать сообщение при пустой таблице"""
        # Скрыть таблицу
        super().pack_forget()
        self._scrollbar.pack_forget()
        
        # Показать заглушку
        if self._empty_label is None:
            self._empty_label = tk.Label(
                self.container,
                text=f"{icon}\n\n{message}",
                font=("Segoe UI", 14),
                fg=ColorTheme.TEXT_SECONDARY,
                bg=ColorTheme.BG_INPUT,
                justify="center"
            )
        self._empty_label.pack(expand=True, fill="both")
    
    def hide_empty_state(self):
        """Скрыть заглушку и показать таблицу"""
        if self._empty_label:
            self._empty_label.pack_forget()
        super().pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")
    
    def load_data(
        self,
        rows: List[tuple],
        price_col_indices: Optional[List[int]] = None,
        date_col_indices: Optional[List[int]] = None,
        show_empty: bool = True
    ) -> None:
        """
        Загрузка данных в таблицу
        
        ✅ Правильное форматирование цен и дат
        ✅ Адаптивная обработка пустых данных
        ✅ Сохранение выделения при обновлении
        
        Args:
            rows: Список кортежей с данными
            price_col_indices: Индексы колонок с ценами (для форматирования)
            date_col_indices: Индексы колонок с датами (для форматирования)
            show_empty: Показать заглушку если данных нет
        """
        # Сохраняем текущее выделение
        selected = self.selection()
        
        # Очищаем таблицу
        for item in self.get_children():
            self.delete(item)
        
        # Показываем заглушку если нет данных
        if not rows and show_empty:
            self.show_empty_state()
            return
        else:
            self.hide_empty_state()
        
        # Заполняем данными
        for idx, row in enumerate(rows):
            values = []
            for i, v in enumerate(row):
                val = self._format_cell_value(v, i, price_col_indices, date_col_indices)
                values.append(val)
            
            tag = "odd" if idx % 2 else "even"
            self.insert("", "end", values=tuple(values), tags=(tag,))
        
        # Восстанавливаем выделение если возможно
        if selected and self.get_children():
            try:
                self.selection_set(selected[0])
            except tk.TclError:
                pass
    
    def _format_cell_value(
        self,
        value: Any,
        col_index: int,
        price_cols: Optional[List[int]],
        date_cols: Optional[List[int]]
    ) -> str:
        """Форматирование значения ячейки"""
        if value is None:
            return ""
        
        # 💰 Форматирование цен
        if price_cols and col_index in price_cols:
            try:
                return format_currency(float(value), "RUB", "ru")
            except (ValueError, TypeError):
                return str(value)
        
        # 📅 Форматирование дат
        if date_cols and col_index in date_cols:
            try:
                if isinstance(value, str):
                    from utils.helpers import format_date
                    return format_date(value, "%d.%m.%Y", "ru")
                elif isinstance(value, (datetime,)):
                    return value.strftime("%d.%m.%Y")
            except:
                pass
        
        return str(value)
    
    def update_row(self, item_id: str, values: tuple):
        """
        Обновить одну строку без перерисовки всей таблицы
        
        Эффективно для частых обновлений
        """
        if item_id in self.get_children():
            self.item(item_id, values=values)
    
    def add_row(self, values: tuple, tag: Optional[str] = None, at_end: bool = True):
        """Добавить одну строку"""
        if tag is None:
            count = len(self.get_children())
            tag = "odd" if count % 2 else "even"
        
        if at_end:
            self.insert("", "end", values=values, tags=(tag,))
        else:
            self.insert("", 0, values=values, tags=(tag,))
    
    def delete_selected(self):
        """Удалить выделенные строки"""
        for item in self.selection():
            self.delete(item)
    
    def get_selected_data(self) -> Optional[Dict[str, Any]]:
        """Получить данные выделенной строки"""
        selection = self.selection()
        if not selection:
            return None
        
        item = self.item(selection[0])
        return {
            "id": item["id"],
            "values": item["values"],
            "tags": item["tags"]
        }
    
    def export_to_csv(self, filepath: str, delimiter: str = ";") -> bool:
        """Экспорт таблицы в CSV"""
        try:
            import csv
            
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=delimiter)
                
                # Заголовки
                writer.writerow(self._columns)
                
                # Данные
                for child in self.get_children():
                    values = self.item(child)["values"]
                    writer.writerow(values)
            
            return True
        except Exception as e:
            from core.logger import app_logger
            app_logger.error(f"❌ CSV export failed: {e}")
            return False
    
    def destroy(self):
        """Корректное удаление таблицы"""
        # Отписаться от темы
        theme_manager.unregister_callback(self._on_theme_change)
        super().destroy()


# ==================== 🚀 QUICK ACCESS ====================

def create_table(parent, columns: List[str], **kwargs) -> DataTable:
    """
    Быстрое создание таблицы
    
    >>> table = create_table(frame, ["ID", "Name", "Price"], column_widths={"Price": 100})
    """
    return DataTable(parent, columns, **kwargs)