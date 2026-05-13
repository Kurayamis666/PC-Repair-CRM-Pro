# ui/main_window/__init__.py
"""
Пакет главного окна для PC Repair CRM Pro

✅ Экспортирует публичный API: MainWindow, MenuBar
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Содержит метаданные для документации
"""

from typing import TYPE_CHECKING, Optional, Dict, Any
import customtkinter as ctk

# ==================== 🖥️ ОСНОВНЫЕ КОМПОНЕНТЫ ====================
from .main_window import MainWindow
from .menu_bar import MenuBar

# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 🖥️ Основные компоненты
    "MainWindow",
    "MenuBar",
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Main window components for PC Repair CRM Pro"

# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы
if TYPE_CHECKING:
    from .main_window import MainWindow
    from .menu_bar import MenuBar

# ==================== 🛠️ HELPER FUNCTIONS ====================

def create_main_window(
    parent: ctk.CTkBaseClass,
    user: Dict[str, Any],
    on_logout: Optional[callable] = None,
    **kwargs
) -> MainWindow:
    """
    Быстрое создание главного окна
    
    ✅ Удобно для динамического создания после входа
    
    Args:
        parent: Родительский виджет (обычно App)
        user: Данные авторизованного пользователя
        on_logout: Callback при выходе из системы
        **kwargs: Дополнительные аргументы для MainWindow
        
    Returns:
        MainWindow: Созданный экземпляр главного окна
        
    Example:
        >>> main = create_main_window(app, user_data, on_logout=show_login)
        >>> main.pack(fill="both", expand=True)
    """
    return MainWindow(
        parent=parent,
        user=user,
        on_logout=on_logout,
        **kwargs
    )


def create_menu_bar(
    parent: ctk.CTkBaseClass,
    user: Dict[str, Any],
    lang: str = "ru",
    on_logout: Optional[callable] = None,
    on_language_change: Optional[callable] = None,
    **kwargs
) -> MenuBar:
    """
    Быстрое создание верхней панели меню
    
    ✅ Удобно для переиспользования в разных контекстах
    
    Args:
        parent: Родительский виджет
        user: Данные пользователя
        lang: Язык интерфейса
        on_logout: Callback при выходе
        on_language_change: Callback при смене языка
        **kwargs: Дополнительные аргументы для MenuBar
        
    Returns:
        MenuBar: Созданный экземпляр панели меню
        
    Example:
        >>> menu = create_menu_bar(header_frame, user, lang="en", on_logout=logout)
        >>> menu.pack(fill="x")
    """
    return MenuBar(
        parent=parent,
        user=user,
        lang=lang,
        on_logout=on_logout,
        on_language_change=on_language_change,
        **kwargs
    )