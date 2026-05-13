# ui/views/__init__.py
"""
Пакет экранов и представлений для PC Repair CRM Pro

✅ Экспортирует публичный API: все основные экраны
✅ Облегчает импорт: from ui.views import DashboardView, ReportsView, ...
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Оптимизирует загрузку через ленивые импорты
"""

from typing import TYPE_CHECKING, Any, Optional
import customtkinter as ctk

# ==================== 📊 ОСНОВНЫЕ ЭКРАНЫ ====================
# Прямые импорты для часто используемых экранов
from .dashboard import DashboardView
from .reference import ReferenceView
from .documents import DocumentsView
from .settings import SettingsView

# ==================== 📈 ДОПОЛНИТЕЛЬНЫЕ ЭКРАНЫ ====================
# Ленивые импорты для экранов, которые используются реже
def __getattr__(name: str) -> Any:
    """
    Ленивая загрузка экранов при первом обращении
    
    ✅ Избегает циклических импортов
    ✅ Ускоряет начальную загрузку модуля
    ✅ Поддерживает автодополнение в IDE через TYPE_CHECKING
    
    Example:
        from ui.views import ReportsView  # Импортируется только здесь
    """
    if name == "ReportsView":
        from .reports_view import ReportsView
        return ReportsView
    
    elif name == "UsersView":
        from .users_view import UsersView
        return UsersView
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 📊 Основные экраны (прямой импорт)
    "DashboardView",
    "ReferenceView", 
    "DocumentsView",
    "SettingsView",
    
    # 📈 Дополнительные экраны (ленивый импорт)
    "ReportsView",
    "UsersView",
]


# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "UI views/screens for PC Repair CRM Pro"


# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы
if TYPE_CHECKING:
    from .dashboard import DashboardView
    from .reference import ReferenceView
    from .documents import DocumentsView
    from .settings import SettingsView
    from .reports_view import ReportsView
    from .users_view import UsersView


# ==================== 🛠️ HELPER FUNCTIONS ====================

def create_view(
    view_name: str,
    parent: ctk.CTkBaseClass,
    lang: str = "ru",
    on_navigate: Optional[callable] = None,
    **kwargs
) -> Optional[ctk.CTkFrame]:
    """
    Быстрое создание экрана по имени
    
    ✅ Удобно для динамической навигации
    ✅ Возвращает None если экран не найден
    
    Args:
        view_name: Имя экрана ("dashboard", "reference", etc.)
        parent: Родительский виджет
        lang: Язык интерфейса
        on_navigate: Callback для навигации
        **kwargs: Дополнительные аргументы для конструктора
        
    Returns:
        Optional[ctk.CTkFrame]: Созданный экран или None
        
    Example:
        >>> view = create_view("dashboard", parent_frame, lang="ru", on_navigate=show_view)
        >>> if view: view.pack(fill="both", expand=True)
    """
    view_map = {
        "dashboard": DashboardView,
        "reference": ReferenceView,
        "documents": DocumentsView,
        "settings": SettingsView,
        "reports": ReportsView,  # type: ignore
        "users": UsersView,      # type: ignore
    }
    
    view_class = view_map.get(view_name)
    if not view_class:
        from core.logger import app_logger
        app_logger.warning(f"⚠️ Unknown view: {view_name}")
        return None
    
    # Создаём экран с общими параметрами
    common_kwargs = {"parent": parent, "lang": lang}
    if on_navigate:
        common_kwargs["on_navigate"] = on_navigate
    common_kwargs.update(kwargs)
    
    return view_class(**common_kwargs)  # type: ignore


def get_available_views() -> list[str]:
    """
    Получить список доступных экранов
    
    Returns:
        list[str]: Список имён доступных экранов
        
    Example:
        >>> get_available_views()
        ['dashboard', 'reference', 'documents', 'settings', 'reports', 'users']
    """
    return ["dashboard", "reference", "documents", "settings", "reports", "users"]