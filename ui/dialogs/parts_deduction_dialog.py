# ui/dialogs/parts_deduction_dialog.py
"""
Диалог выбора запчастей для списания при закрытии заявки для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Убран несуществующий values_dict, добавлен кэш цен, переводы
✅ УЛУЧШЕНО: Поиск запчастей, редактирование количества, пустое состояние
✅ СОВМЕСТИМО: Интеграция с системой тем, переводов и утилит
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, List, Any
import re

from database.connection import DatabaseConnection
from core.logger import app_logger
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.toast import ToastNotification
from ui.widgets.tables import TableStyle
from ui.widgets.search_bar import SearchBar
from utils.helpers import format_currency


class PartsDeductionDialog(ctk.CTkToplevel):
    """
    Диалог выбора запчастей для списания с полным функционалом
    
    ✅ Корректное хранение метаданных через _parts_metadata (не values_dict!)
    ✅ Кэширование цен для производительности
    ✅ Полный перевод всех текстов через get_text()
    ✅ Поиск запчастей в реальном времени
    ✅ Редактирование количества после выбора
    ✅ Пустое состояние с подсказкой
    """
    
    def __init__(
        self,
        parent,
        request_id: int,
        lang: str = "ru",
        on_confirm: Optional[Callable[[Dict[int, int]], None]] = None,
    ):
        super().__init__(parent)
        
        self.request_id = request_id
        self.lang = lang
        self.on_confirm = on_confirm
        self.db = DatabaseConnection()
        
        # 🔧 UI элементы
        self._parts_tree: Optional[ttk.Treeview] = None
        self._total_label: Optional[ctk.CTkLabel] = None
        self._search_bar: Optional[SearchBar] = None
        self._loading_label: Optional[ctk.CTkLabel] = None
        
        # 📦 Данные
        self._selected_parts: Dict[int, int] = {}  # part_id → quantity
        self._parts_metadata: Dict[str, Dict[str, Any]] = {}  # item_id → {part_id, quantity, price, ...}
        self._parts_cache: Dict[int, Dict[str, Any]] = {}  # part_id → {name, sku, quantity, price}
        
        # ✅ Переведённый заголовок
        title = get_text("deduct_parts_title", self.lang) or "📦 Списание запчастей"
        self.title(f"{title} #{request_id}")
        
        self.geometry("650x550")
        self.minsize(550, 480)  # ✅ Адаптивный минимальный размер
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        # 🎯 Центрирование
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 650) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        
        self._build_ui()
        self._load_available_parts()
    
    def _build_ui(self) -> None:
        """Построение интерфейса с полным переводом"""
        
        # 🏷️ Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.WARNING, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, 
            text=f"{get_text('deduct_parts_for', self.lang) or '📦 Заявка'} #{self.request_id}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=15)
        
        # 📋 Инструкция
        ctk.CTkLabel(
            self, 
            text=get_text("select_parts_instruction", self.lang) or "Отметьте запчасти, которые были использованы:",
            text_color=ColorTheme.TEXT_SECONDARY
        ).pack(pady=(15, 10))
        
        # 🔍 Поиск запчастей
        self._search_bar = SearchBar(
            self,
            placeholder=get_text("search_parts", self.lang) or "Поиск запчастей...",
            on_search=self._filter_parts,
            on_reset=self._filter_parts,
            show_find_button=False,
            lang=self.lang,
            live_search=True,
            live_search_delay=200
        )
        self._search_bar.pack(fill="x", padx=20, pady=(0, 10))
        
        # 📊 Таблица запчастей
        table_frame = ctk.CTkFrame(self, fg_color=ColorTheme.BG_INPUT)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        TableStyle.setup()
        
        # ✅ Используем имена колонок для надёжности
        cols = [
            get_text("col_checkbox", self.lang) or "✓",
            get_text("col_id", self.lang) or "ID",
            get_text("col_name", self.lang) or "Название",
            get_text("col_sku", self.lang) or "Артикул",
            get_text("col_stock", self.lang) or "Остаток",
            get_text("col_quantity", self.lang) or "Кол-во"
        ]
        
        self._parts_tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="none")
        
        # Настройка ширины колонок
        col_widths = {
            get_text("col_checkbox", self.lang): 40,
            get_text("col_id", self.lang): 50,
            get_text("col_name", self.lang): 200,
            get_text("col_sku", self.lang): 100,
            get_text("col_stock", self.lang): 80,
            get_text("col_quantity", self.lang): 80
        }
        
        for col in cols:
            self._parts_tree.heading(col, text=col)
            self._parts_tree.column(col, width=col_widths.get(col, 100), anchor="center" if col in [cols[0], cols[1], cols[4], cols[5]] else "w")
        
        self._parts_tree.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(table_frame, orient="vertical", command=self._parts_tree.yview).pack(side="right", fill="y")
        
        # ✅ Обработчики событий
        self._parts_tree.bind("<Button-1>", self._on_tree_click)
        self._parts_tree.bind("<Double-1>", self._on_tree_double_click)  # Двойной клик для редактирования количества
        
        # 🎨 Теги для строк
        self._parts_tree.tag_configure("even", background=ColorTheme.BG_INPUT, foreground=ColorTheme.TEXT_PRIMARY)
        self._parts_tree.tag_configure("odd", background="#253346", foreground=ColorTheme.TEXT_PRIMARY)
        self._parts_tree.tag_configure("selected", background=ColorUtils.darken(ColorTheme.SUCCESS, 20), foreground=ColorTheme.TEXT_PRIMARY)
        
        # ⏳ Индикатор загрузки (скрыт по умолчанию)
        self._loading_label = ctk.CTkLabel(
            table_frame,
            text="",
            text_color=ColorTheme.INFO,
            font=ctk.CTkFont(size=12)
        )
        self._loading_label.pack(expand=True)
        
        # 💰 Итоговая сумма
        self._total_label = ctk.CTkLabel(
            self, 
            text="",
            font=ctk.CTkFont(weight="bold", size=14),
            text_color=ColorTheme.SUCCESS
        )
        self._total_label.pack(pady=10)
        self._update_total()
        
        # 🔘 Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame, 
            text=get_text("cancel", self.lang), 
            command=self.destroy,
            width=120, 
            height=35, 
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="✅ " + get_text("confirm_deduction", self.lang), 
            command=self._confirm,
            width=220, 
            height=35, 
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="right", padx=10)
    
    def _set_loading(self, loading: bool) -> None:
        """Показать/скрыть индикатор загрузки"""
        if loading:
            if self._loading_label:
                self._loading_label.configure(text="🔄 " + (get_text("loading_parts", self.lang) or "Загрузка запчастей..."))
                self._loading_label.pack(expand=True)
            if self._parts_tree:
                self._parts_tree.pack_forget()
        else:
            if self._loading_label:
                self._loading_label.pack_forget()
            if self._parts_tree:
                self._parts_tree.pack(side="left", fill="both", expand=True)
    
    def _load_available_parts(self) -> None:
        """Загрузить доступные запчасти с кэшированием"""
        self._set_loading(True)
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, name, sku, quantity, price 
                    FROM parts 
                    WHERE quantity > 0 
                    ORDER BY name
                """)
                parts = cur.fetchall()
            
            # ✅ Очищаем таблицу и кэш
            self._parts_tree.delete(*self._parts_tree.get_children())
            self._parts_metadata.clear()
            self._parts_cache.clear()
            
            # ✅ Пустое состояние
            if not parts:
                self._show_empty_state()
                self._set_loading(False)
                return
            else:
                self._hide_empty_state()
            
            # ✅ Заполняем таблицу и кэш
            for idx, row in enumerate(parts):
                part_id, name, sku, quantity, price = row
                
                # Кэшируем данные запчасти
                self._parts_cache[part_id] = {
                    "name": name,
                    "sku": sku,
                    "quantity": quantity,
                    "price": price or 0
                }
                
                tag = "odd" if idx % 2 else "even"
                item_id = self._parts_tree.insert(
                    "", "end", 
                    values=("☐", part_id, name, sku, quantity, ""),
                    tags=(tag,)
                )
                
                # ✅ Сохраняем метаданные через item_id (НЕ values_dict!)
                self._parts_metadata[item_id] = {
                    "part_id": part_id,
                    "quantity": quantity,
                    "price": price or 0,
                    "selected_qty": 0
                }
            
            self._set_loading(False)
            
        except Exception as e:
            app_logger.error(f"Error loading parts: {e}")
            ToastNotification(self, f"{get_text('error_loading', self.lang)}: {e}", "error")
            self._set_loading(False)
    
    def _show_empty_state(self) -> None:
        """Показать сообщение при отсутствии запчастей"""
        if self._parts_tree:
            self._parts_tree.pack_forget()
        
        empty_label = ctk.CTkLabel(
            self,
            text=f"📭 {get_text('no_available_parts', self.lang) or 'Нет доступных запчастей'}",
            text_color=ColorTheme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=14)
        )
        empty_label.pack(expand=True)
    
    def _hide_empty_state(self) -> None:
        """Скрыть пустое состояние и показать таблицу"""
        # Удаляем пустое состояние если есть
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and "📭" in widget.cget("text"):
                widget.pack_forget()
        
        if self._parts_tree:
            self._parts_tree.pack(side="left", fill="both", expand=True)
    
    def _filter_parts(self, query: str) -> None:
        """Фильтрация запчастей по поисковому запросу"""
        query = query.lower().strip()
        
        # Показываем/скрываем строки
        for item_id in self._parts_tree.get_children():
            values = self._parts_tree.item(item_id)["values"]
            # values: [checkbox, id, name, sku, stock, qty]
            row_text = " ".join(str(v).lower() for v in values[2:4])  # name + sku
            if not query or query in row_text:
                self._parts_tree.reattach(item_id, "", "end")
            else:
                self._parts_tree.detach(item_id)
    
    def _on_tree_click(self, event) -> str:
        """Обработчик клика по таблице (чекбоксы)"""
        # ✅ Определяем колонку по имени, а не позиции
        col_id = self._parts_tree.identify_column(event.x)
        checkbox_col = self._parts_tree["columns"][0]  # Первая колонка = чекбокс
        
        if self._parts_tree.identify_column(event.x) != f"#{self._parts_tree["columns"].index(checkbox_col) + 1}":
            return "break"
        
        item_id = self._parts_tree.identify_row(event.y)
        if not item_id or item_id not in self._parts_metadata:
            return "break"
        
        # Переключаем чекбокс
        values = list(self._parts_tree.item(item_id)["values"])
        current = values[0]
        new_state = "☑" if current == "☐" else "☐"
        values[0] = new_state
        
        part_id = self._parts_metadata[item_id]["part_id"]
        
        if new_state == "☑":
            # Открываем диалог для ввода количества
            self._ask_quantity(part_id, item_id)
        else:
            # Снимаем выделение
            if part_id in self._selected_parts:
                del self._selected_parts[part_id]
            self._parts_metadata[item_id]["selected_qty"] = 0
            values[5] = ""  # Очищаем колонку количества
            self._parts_tree.item(item_id, tags=[t for t in self._parts_tree.item(item_id)["tags"] if t != "selected"])
        
        self._parts_tree.item(item_id, values=values)
        self._update_total()
        return "break"
    
    def _on_tree_double_click(self, event) -> str:
        """Двойной клик по строке для редактирования количества"""
        item_id = self._parts_tree.identify_row(event.y)
        if not item_id or item_id not in self._parts_metadata:
            return "break"
        
        # Проверяем, что клик по колонке количества
        col_id = self._parts_tree.identify_column(event.x)
        qty_col_index = 5  # Индекс колонки "Кол-во"
        
        if col_id == f"#{qty_col_index + 1}":
            part_id = self._parts_metadata[item_id]["part_id"]
            if part_id in self._selected_parts:
                # Открываем диалог редактирования количества
                self._ask_quantity(part_id, item_id, edit_mode=True)
        
        return "break"
    
    def _ask_quantity(self, part_id: int, item_id: str, edit_mode: bool = False) -> None:
        """Запрос количества для списания"""
        max_qty = self._parts_metadata[item_id]["quantity"]
        current_qty = self._selected_parts.get(part_id, 0) if edit_mode else 0
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(get_text("enter_quantity", self.lang) or "Количество")
        dialog.geometry("320x180")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=ColorTheme.BG_CARD)
        
        # Центрирование диалога
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 320) // 2
        y = self.winfo_y() + (self.winfo_height() - 180) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        
        ctk.CTkLabel(
            dialog, 
            text=f"{get_text('max_available', self.lang) or 'Макс. доступно'}: {max_qty}", 
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=10)
        
        qty_entry = ctk.CTkEntry(
            dialog, 
            placeholder_text=get_text("enter_quantity", self.lang) or "Введите количество", 
            width=200,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY
        )
        qty_entry.pack(pady=5)
        qty_entry.insert(0, str(current_qty) if current_qty > 0 else "")
        qty_entry.focus_set()
        qty_entry.select_range(0, "end")
        
        # Подсказка о допустимом диапазоне
        ctk.CTkLabel(
            dialog,
            text=f"1 — {max_qty}",
            text_color=ColorTheme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=10)
        ).pack(pady=(0, 10))
        
        def on_submit():
            try:
                qty_str = qty_entry.get().strip()
                if not qty_str:
                    ToastNotification(dialog, get_text("quantity_required", self.lang) or "Введите количество", "warning")
                    return
                
                qty = int(qty_str)
                if 0 < qty <= max_qty:
                    # ✅ Обновляем выбранные запчасти
                    self._selected_parts[part_id] = qty
                    self._parts_metadata[item_id]["selected_qty"] = qty
                    
                    # Обновляем отображение в таблице
                    values = list(self._parts_tree.item(item_id)["values"])
                    values[5] = str(qty)  # Колонка количества
                    self._parts_tree.item(item_id, values=values, tags=["selected"])
                    
                    self._update_total()
                    dialog.destroy()
                else:
                    ToastNotification(dialog, get_text("invalid_quantity_range", self.lang).format(1, max_qty) or f"Введите число от 1 до {max_qty}", "warning")
            except ValueError:
                ToastNotification(dialog, get_text("invalid_quantity", self.lang) or "Введите корректное число", "error")
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(
            btn_frame, 
            text=get_text("cancel", self.lang), 
            command=dialog.destroy, 
            width=80,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame, 
            text=get_text("ok", self.lang), 
            command=on_submit, 
            width=80, 
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        ).pack(side="left", padx=5)
        
        qty_entry.bind("<Return>", lambda e: on_submit())
        qty_entry.bind("<Escape>", lambda e: dialog.destroy())
    
    def _update_total(self) -> None:
        """Обновить итоговую информацию с кэшированными ценами"""
        total_qty = sum(self._selected_parts.values())
        
        # ✅ Используем кэш цен вместо запросов к БД
        total_cost = sum(
            qty * self._parts_cache.get(pid, {}).get("price", 0)
            for pid, qty in self._selected_parts.items()
        )
        
        if self._total_label:
            # ✅ Используем format_currency для согласованности
            formatted_cost = format_currency(total_cost, "RUB", self.lang)
            self._total_label.configure(
                text=f"{get_text('selected_summary', self.lang) or 'Выбрано'}: {total_qty} {get_text('pieces', self.lang) or 'шт.'} | {get_text('total', self.lang) or 'Сумма'}: {formatted_cost}"
            )
    
    def _confirm(self) -> None:
        """Подтверждение списания с валидацией"""
        if not self._selected_parts:
            ToastNotification(self, get_text("select_at_least_one_part", self.lang) or "Выберите хотя бы одну запчасть", "warning")
            return
        
        # ✅ Дополнительная валидация: проверка остатков (на случай изменения в БД)
        for part_id, qty in self._selected_parts.items():
            cached = self._parts_cache.get(part_id, {})
            if qty > cached.get("quantity", 0):
                ToastNotification(
                    self, 
                    get_text("insufficient_stock", self.lang).format(cached.get("name", part_id)) or f"Недостаточно запаса: {cached.get('name', part_id)}",
                    "error"
                )
                return
        
        if self.on_confirm:
            try:
                self.on_confirm(self._selected_parts)
            except Exception as e:
                app_logger.error(f"❌ Error in on_confirm callback: {e}")
                ToastNotification(self, f"{get_text('error', self.lang)}: {e}", "error")
                return
        
        self.destroy()
    
    def destroy(self) -> None:
        """Корректное закрытие диалога"""
        # Очищаем кэш
        self._parts_cache.clear()
        self._parts_metadata.clear()
        super().destroy()