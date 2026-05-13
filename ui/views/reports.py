# ui/views/reports.py
"""
Экран отчётов для PC Repair CRM Pro
✅ Базовая реализация без ошибок SQL
"""

import customtkinter as ctk
from typing import Optional, Callable

from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme
from translations import get_text


class ReportsView(ctk.CTkFrame):
    """Экран отчётов"""
    
    on_navigate: Optional[Callable[[str], None]] = None
    
    def __init__(
        self, 
        parent: ctk.CTkBaseClass, 
        lang: str = "ru", 
        on_navigate: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        # ✅ Извлекаем параметры до super()
        self.on_navigate = on_navigate
        self.lang = lang
        self.db = DatabaseConnection()
        
        # ✅ Удаляем кастомные kwargs
        kwargs.pop('on_navigate', None)
        kwargs.pop('lang', None)
        
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Построение интерфейса"""
        # Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.INFO, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=get_text("reports", self.lang) or "Отчёты",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=15)
        
        # Кнопка назад
        ctk.CTkButton(
            self,
            text=get_text("back", self.lang) or "Назад",
            command=lambda: self.on_navigate("dashboard") if self.on_navigate else None,
            width=120,
            height=35,
            fg_color=ColorTheme.TEXT_SECONDARY,
            corner_radius=10
        ).pack(padx=30, pady=20, anchor="w")
        
        # Заглушка
        ctk.CTkLabel(
            self,
            text=get_text("section_under_construction", self.lang) or "📊 Раздел в разработке",
            font=ctk.CTkFont(size=16),
            text_color=ColorTheme.TEXT_SECONDARY
        ).pack(expand=True)
    
    def refresh(self) -> None:
        """Обновление данных"""
        pass