# ui/login/__init__.py
"""
Пакет окна авторизации для PC Repair CRM Pro

✅ Экспортирует публичный API: LoginWindow
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Содержит метаданные для документации
"""

from typing import TYPE_CHECKING, Optional, Callable, Dict, Any
import customtkinter as ctk

# ==================== 🔐 ОСНОВНОЙ КОМПОНЕНТ ====================
from .login_window import LoginWindow

# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 🔐 Основной компонент
    "LoginWindow",
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Login window component for PC Repair CRM Pro"

# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы
if TYPE_CHECKING:
    from .login_window import LoginWindow

# ==================== 🛠️ HELPER FUNCTIONS ====================

def create_login_window(
    parent: ctk.CTkBaseClass,
    on_success: Callable[[Dict[str, Any]], None],
    lang: str = "ru",
    **kwargs
) -> LoginWindow:
    """
    Быстрое создание окна авторизации
    
    ✅ Удобно для динамического создания после запуска приложения
    
    Args:
        parent: Родительский виджет (обычно App)
        on_success: Callback при успешной авторизации (получает dict с данными пользователя)
        lang: Язык интерфейса ("ru" или "en")
        **kwargs: Дополнительные аргументы для LoginWindow
        
    Returns:
        LoginWindow: Созданный экземпляр окна входа
        
    Example:
        >>> login = create_login_window(app, on_success=handle_login, lang="en")
        >>> login.transient(app)
        >>> login.grab_set()
    """
    return LoginWindow(
        parent=parent,
        on_success=on_success,
        lang=lang,
        **kwargs
    )