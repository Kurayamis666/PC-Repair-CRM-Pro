# ui/widgets/__init__.py
"""
Пакет переиспользуемых виджетов для PC Repair CRM Pro

✅ Экспортирует публичный API: классы, менеджеры, хелперы
✅ Облегчает импорт: from ui.widgets import toast, create_form, ...
✅ Поддерживает Type Checkers (mypy, pyright)
"""

# ==================== 📊 ТАБЛИЦЫ ====================
from .tables import (
    TableStyle,
    DataTable,
    create_table,  # ✅ Хелпер для быстрого создания
)

# ==================== 📝 ФОРМЫ ====================
from .forms import (
    FormField,
    FormPanel,
    create_form,  # ✅ Хелпер для создания формы из конфига
)

# ==================== 🔍 ПОИСК ====================
from .search_bar import (
    SearchBar,
    create_search_bar,  # ✅ Хелпер для быстрого создания
)

# ==================== 🍞 УВЕДОМЛЕНИЯ ====================
from .toast import (
    ToastNotification,
    ToastManager,  # ✅ Менеджер очереди уведомлений
    toast,  # ✅ Хелпер для быстрого показа: toast(parent, "Text")
    show_toast,  # ✅ Алиас для совместимости
    Toast,  # ✅ Алиас для совместимости
)

# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 📊 Tables
    "TableStyle",
    "DataTable",
    "create_table",
    
    # 📝 Forms
    "FormField",
    "FormPanel",
    "create_form",
    
    # 🔍 Search
    "SearchBar",
    "create_search_bar",
    
    # 🍞 Toasts
    "ToastNotification",
    "ToastManager",
    "toast",
    "show_toast",
    "Toast",
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Reusable UI widgets for PC Repair CRM Pro"