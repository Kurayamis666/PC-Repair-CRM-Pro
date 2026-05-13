# ui/__init__.py
"""
Пакет пользовательского интерфейса для PC Repair CRM Pro

✅ Экспортирует публичный API пакета
✅ Избегает циклических импортов через ленивую загрузку
✅ Поддерживает type checkers (mypy, pyright)
✅ Группирует компоненты по назначению

Примеры использования:
    >>> from ui import App, LoginWindow, MainWindow
    >>> from ui import theme, widgets, dialogs
    >>> from ui.theme import ColorTheme, theme_manager
"""

from typing import TYPE_CHECKING, Any

# ==================== 🎨 THEME (без циклических импортов) ====================
# Импортируем тему отдельно — она не зависит от остальных компонентов
from ui.theme import (
    ColorTheme,
    ColorUtils,
    ColorPalette,
    ThemeManager,
    DARK_THEME,
    LIGHT_THEME,
    theme as theme_manager,  # Быстрый доступ: ui.theme_manager
)

# ==================== 🚀 LAZY IMPORTS ДЛЯ ОСНОВНЫХ КОМПОНЕНТОВ ====================
# Ленивая загрузка тяжёлых компонентов (customtkinter, tkinter)
# Импортируются только при первом обращении

def __getattr__(name: str) -> Any:
    """
    Ленивая загрузка компонентов при первом импорте
    
    ✅ Избегает циклических импортов
    ✅ Ускоряет начальную загрузку модуля
    ✅ Поддерживает автодополнение в IDE через TYPE_CHECKING
    
    Example:
        from ui import App  # App импортируется только здесь, при первом использовании
    """
    if name == "App":
        from ui.app import App
        return App
    
    elif name == "LoginWindow":
        from ui.login.login_window import LoginWindow
        return LoginWindow
    
    elif name == "MainWindow":
        from ui.main_window.main_window import MainWindow
        return MainWindow
    
    elif name == "DocumentsView":
        from ui.views.documents import DocumentsView
        return DocumentsView
    
    elif name == "ReferenceView":
        from ui.views.reference import ReferenceView
        return ReferenceView
    
    elif name == "ReportsView":
        from ui.views.reports_view import ReportsView
        return ReportsView
    
    elif name == "SettingsView":
        from ui.views.settings import SettingsView
        return SettingsView
    
    elif name == "DashboardView":
        from ui.views.dashboard import DashboardView
        return DashboardView
    
    # Виджеты
    elif name == "ToastNotification":
        from ui.widgets.toast import ToastNotification
        return ToastNotification
    
    elif name == "TableStyle":
        from ui.widgets.tables import TableStyle
        return TableStyle
    
    # Диалоги
    elif name == "RequestEditorDialog":
        from ui.dialogs.request_editor import RequestEditorDialog
        return RequestEditorDialog
    
    elif name == "EquipmentDialog":
        from ui.views.documents import EquipmentDialog
        return EquipmentDialog
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 🎨 Theme
    "ColorTheme",
    "ColorUtils", 
    "ColorPalette",
    "ThemeManager",
    "DARK_THEME",
    "LIGHT_THEME",
    "theme_manager",
    
    # 🚀 Main components (lazy loaded)
    "App",
    "LoginWindow",
    "MainWindow",
    
    # 📄 Views
    "DashboardView",
    "ReferenceView", 
    "DocumentsView",
    "ReportsView",
    "SettingsView",
    
    # 🧩 Widgets
    "ToastNotification",
    "TableStyle",
    
    # 💬 Dialogs
    "RequestEditorDialog",
    "EquipmentDialog",
]


# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы
if TYPE_CHECKING:
    from ui.app import App
    from ui.login.login_window import LoginWindow
    from ui.main_window.main_window import MainWindow
    from ui.views.dashboard import DashboardView
    from ui.views.reference import ReferenceView
    from ui.views.documents import DocumentsView
    from ui.views.reports_view import ReportsView
    from ui.views.settings import SettingsView
    from ui.widgets.toast import ToastNotification
    from ui.widgets.tables import TableStyle
    from ui.dialogs.request_editor import RequestEditorDialog
    from ui.views.documents import EquipmentDialog
    from ui.theme import (
        ColorTheme,
        ColorUtils,
        ColorPalette,
        ThemeManager,
    )


# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "User interface components for PC Repair CRM Pro"


# ==================== 🛠️ HELPER FUNCTIONS ====================
def get_theme() -> ColorPalette:
    """Получить текущую палитру цветов"""
    return theme_manager.current


def set_theme(theme_name: str) -> None:
    """
    Установить тему оформления
    
    Args:
        theme_name: "dark" или "light"
    """
    theme_manager.set_theme(theme_name)  # type: ignore


def is_dark_theme() -> bool:
    """Проверка: активна ли тёмная тема"""
    return theme_manager.is_dark  # type: ignore