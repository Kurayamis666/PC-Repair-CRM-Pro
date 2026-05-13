# ui/widgets/search_bar.py
"""
Панель поиска для PC Repair CRM Pro
✅ УЛУЧШЕНО: Адаптивная ширина, перевод плейсхолдера, визуальная обратная связь
✅ ГИБКОСТЬ: Живой поиск, горячие клавиши, валидация, история
✅ СОВМЕСТИМО: Интеграция с системой тем и переводов
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional, List
from ui.theme import ColorTheme, ColorUtils
from translations import get_text


class SearchBar(ctk.CTkFrame):
    """
    Адаптивная панель поиска с расширенной функциональностью
    
    ✅ Адаптивная ширина под родительский виджет
    ✅ Перевод плейсхолдера и подсказок
    ✅ Визуальная обратная связь при поиске
    ✅ Поддержка "живого поиска" (опционально)
    ✅ Горячие клавиши: Enter, Ctrl+F, Esc
    ✅ Валидация и санитизация ввода
    ✅ История поиска (опционально)
    """
    
    # Максимальная длина поискового запроса
    MAX_QUERY_LENGTH: int = 200
    
    def __init__(
        self,
        parent,
        placeholder: Optional[str] = None,
        on_search: Optional[Callable[[str], None]] = None,
        on_reset: Optional[Callable[[], None]] = None,
        on_query_change: Optional[Callable[[str], None]] = None,  # Для live search
        show_find_button: bool = True,
        show_reset_button: bool = True,
        live_search: bool = False,
        live_search_delay: int = 300,  # мс задержки перед поиском
        history: Optional[List[str]] = None,
        lang: str = "ru",
        **kwargs
    ):
        """
        Инициализация панели поиска
        
        Args:
            parent: Родительский виджет
            placeholder: Текст подсказки (переводится автоматически если не указан)
            on_search: Callback при поиске (Enter или кнопка)
            on_reset: Callback при сбросе поиска
            on_query_change: Callback при изменении текста (для live search)
            show_find_button: Показать кнопку "Найти"
            show_reset_button: Показать кнопку "Сброс"
            live_search: Включить поиск при вводе (с задержкой)
            live_search_delay: Задержка в мс перед вызовом on_query_change
            history: Список предыдущих запросов для автодополнения
            lang: Код языка для переводов
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.lang = lang
        self.on_search = on_search
        self.on_reset = on_reset
        self.on_query_change = on_query_change
        self.live_search = live_search
        self._history = history or []
        self._search_after_id: Optional[str] = None
        
        # 🌐 Перевод плейсхолдера
        self.placeholder = placeholder or get_text("search_placeholder", self.lang) or "Search..."
        
        # 🔧 Построение интерфейса
        self._build_ui(show_find_button, show_reset_button)
        
        # ⌨️ Горячие клавиши
        self._bind_hotkeys()
    
    def _build_ui(self, show_find: bool, show_reset: bool):
        """Построение интерфейса с адаптивной компоновкой"""
        
        # 📦 Контейнер для выравнивания
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", expand=True)
        
        # 🔍 Иконка/метка "Поиск"
        ctk.CTkLabel(
            container,
            text="🔍",  # Эмодзи вместо текста — универсально
            font=ctk.CTkFont(size=16),
            text_color=ColorTheme.TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 5))
        
        # ✏️ Поле ввода (адаптивная ширина)
        self.entry = ctk.CTkEntry(
            container,
            placeholder_text=self.placeholder,
            # ✅ Адаптивная ширина: заполняет доступное пространство
            width=200,  # Базовая ширина
            corner_radius=10,
            fg_color=ColorTheme.BG_INPUT,
            border_color=ColorTheme.BORDER,
            text_color=ColorTheme.TEXT_PRIMARY,
            placeholder_text_color=ColorTheme.TEXT_SECONDARY,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # ⌨️ Обработчики ввода
        self.entry.bind("<Return>", lambda e: self._trigger_search())
        self.entry.bind("<Escape>", lambda e: self.clear())
        
        # 🔄 Живой поиск (опционально)
        if self.live_search and self.on_query_change:
            self.entry.bind("<KeyRelease>", self._on_query_change_live)
        
        # 🔘 Кнопка "Найти"
        if show_find and self.on_search:
            self.find_btn = ctk.CTkButton(
                container,
                text=get_text("find", self.lang),
                width=80,
                height=32,
                command=self._trigger_search,
                fg_color=ColorTheme.SUCCESS,
                hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),  # ✅ Из ColorTheme
                text_color=ColorTheme.TEXT_PRIMARY,
                corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.find_btn.pack(side="left", padx=(0, 5))
        
        # 🔘 Кнопка "Сброс"
        if show_reset and self.on_reset:
            self.reset_btn = ctk.CTkButton(
                container,
                text=get_text("reset", self.lang),
                width=80,
                height=32,
                command=self._trigger_reset,  # ✅ Единый метод
                fg_color=ColorTheme.TEXT_SECONDARY,
                hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
                text_color=ColorTheme.TEXT_PRIMARY,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
            )
            self.reset_btn.pack(side="left", padx=(0, 5))
            # Скрыть кнопку если поле пустое
            self.entry.bind("<KeyRelease>", self._update_reset_visibility)
            self._update_reset_visibility()
        
        # 📊 Индикатор загрузки (скрыт по умолчанию)
        self._loading_label = ctk.CTkLabel(
            container,
            text="⏳",
            text_color=ColorTheme.INFO,
            font=ctk.CTkFont(size=14),
        )
        # Не pack'им сразу — показываем при поиске
    
    def _bind_hotkeys(self):
        """Привязка горячих клавиш"""
        # Ctrl+F — фокус на поле поиска
        self.entry.bind("<Control-f>", lambda e: self.focus_search())
        self.entry.bind("<Control-F>", lambda e: self.focus_search())
        
        # Ctrl+K — альтернативный фокус (как в многих приложениях)
        self.entry.bind("<Control-k>", lambda e: self.focus_search())
        self.entry.bind("<Control-K>", lambda e: self.focus_search())
    
    def _on_query_change_live(self, event=None):
        """Обработчик для живого поиска с задержкой"""
        # Отменяем предыдущий таймер
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        
        # Запускаем новый с задержкой
        query = self.entry.get().strip()
        self._search_after_id = self.after(
            self.live_search_delay,
            lambda: self._trigger_live_search(query)
        )
    
    def _trigger_live_search(self, query: str):
        """Вызов callback для живого поиска"""
        # Санитизация запроса
        query = self._sanitize_query(query)
        
        if self.on_query_change:
            try:
                self.on_query_change(query)
            except Exception as e:
                from core.logger import app_logger
                app_logger.error(f"❌ Live search callback error: {e}")
    
    def _trigger_search(self):
        """Запустить поиск с визуальной обратной связью"""
        query = self._sanitize_query(self.entry.get())
        
        if not query and self.on_search:
            # Пустой запрос — возможно, показать все данные
            self.on_search("")
            return
        
        # 🎬 Визуальная обратная связь
        self._show_loading(True)
        
        if self.on_search:
            try:
                self.on_search(query)
                # Добавляем в историю если успешно
                self._add_to_history(query)
            except Exception as e:
                from core.logger import app_logger
                app_logger.error(f"❌ Search callback error: {e}")
            finally:
                self._show_loading(False)
    
    def _trigger_reset(self):
        """Сброс поиска с визуальной обратной связью"""
        self.clear()
        if self.on_reset:
            try:
                self.on_reset()
            except Exception as e:
                from core.logger import app_logger
                app_logger.error(f"❌ Reset callback error: {e}")
    
    def _show_loading(self, show: bool):
        """Показать/скрыть индикатор загрузки"""
        if show:
            # Меняем текст кнопки если есть
            if hasattr(self, 'find_btn') and self.find_btn.winfo_exists():
                self.find_btn.configure(text="⏳", state="disabled")
            # Показываем индикатор
            self._loading_label.pack(side="left", padx=5)
            self.entry.configure(state="disabled")
        else:
            if hasattr(self, 'find_btn') and self.find_btn.winfo_exists():
                self.find_btn.configure(text=get_text("find", self.lang), state="normal")
            self._loading_label.pack_forget()
            self.entry.configure(state="normal")
            self.entry.focus_set()  # Возвращаем фокус
    
    def _update_reset_visibility(self, event=None):
        """Показывать кнопку сброса только если есть текст"""
        if hasattr(self, 'reset_btn') and self.reset_btn.winfo_exists():
            if self.entry.get().strip():
                self.reset_btn.pack(side="left", padx=(0, 5))
            else:
                self.reset_btn.pack_forget()
    
    def _sanitize_query(self, query: str) -> str:
        """
        Очистка и валидация поискового запроса
        
        ✅ Удаляет лишние пробелы
        ✅ Ограничивает длину
        ✅ Экранирует потенциально опасные символы
        """
        # Удаляем лишние пробелы
        query = " ".join(query.split())
        
        # Ограничиваем длину
        if len(query) > self.MAX_QUERY_LENGTH:
            query = query[:self.MAX_QUERY_LENGTH]
        
        # Базовая санитизация (защита от инъекций если запрос идёт в БД)
        # Для SQLite параметризованные запросы решают проблему, но на всякий случай:
        dangerous_chars = [";", "--", "/*", "*/", "'"]
        for char in dangerous_chars:
            query = query.replace(char, "")
        
        return query
    
    def _add_to_history(self, query: str):
        """Добавить запрос в историю"""
        if not query or query in self._history:
            return
        
        # Добавляем в начало, ограничиваем размер
        self._history.insert(0, query)
        if len(self._history) > 10:
            self._history.pop()
    
    def get_history(self) -> List[str]:
        """Получить историю поиска"""
        return self._history.copy()
    
    def clear_history(self):
        """Очистить историю поиска"""
        self._history.clear()
    
    # ==================== 🎯 ПУБЛИЧНЫЕ МЕТОДЫ ====================
    
    def focus_search(self):
        """Установить фокус на поле поиска и выделить текст"""
        self.entry.focus_set()
        self.entry.select_range(0, "end")
        return self  # Для цепочки вызовов
    
    def get_query(self) -> str:
        """Получить текущий поисковый запрос (очищенный)"""
        return self._sanitize_query(self.entry.get())
    
    def set_query(self, query: str, trigger_search: bool = False):
        """
        Установить поисковый запрос
        
        Args:
            query: Текст запроса
            trigger_search: Запустить ли поиск автоматически
        """
        self.entry.delete(0, "end")
        self.entry.insert(0, query)
        self._update_reset_visibility()
        
        if trigger_search and self.on_search:
            self._trigger_search()
    
    def clear(self):
        """Очистить поле поиска"""
        self.entry.delete(0, "end")
        self._update_reset_visibility()
        # Не вызываем on_reset автоматически — только по явному действию пользователя
    
    def enable(self, state: bool = True):
        """Включить/отключить панель поиска"""
        new_state = "normal" if state else "disabled"
        self.entry.configure(state=new_state)
        if hasattr(self, 'find_btn'):
            self.find_btn.configure(state=new_state)
        if hasattr(self, 'reset_btn'):
            self.reset_btn.configure(state=new_state)
    
    def set_placeholder(self, text: str):
        """Установить текст плейсхолдера"""
        self.entry.configure(placeholder_text=text)
    
    def bind_search(self, callback: Callable[[str], None]):
        """Установить callback для поиска"""
        self.on_search = callback
    
    def bind_reset(self, callback: Callable[[], None]):
        """Установить callback для сброса"""
        self.on_reset = callback
    
    def bind_query_change(self, callback: Callable[[str], None]):
        """Установить callback для изменения запроса (live search)"""
        self.on_query_change = callback
        if callback and not self.live_search:
            # Включаем live search если установлен callback
            self.entry.bind("<KeyRelease>", self._on_query_change_live)
            self.live_search = True
    
    def destroy(self):
        """Корректное удаление виджета"""
        # Отменяем отложенные вызовы
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        super().destroy()


# ==================== 🚀 QUICK ACCESS ====================

def create_search_bar(parent, **kwargs) -> SearchBar:
    """
    Быстрое создание панели поиска
    
    >>> search = create_search_bar(frame, on_search=my_search_func, live_search=True)
    """
    return SearchBar(parent, **kwargs)