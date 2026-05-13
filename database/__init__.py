# database/__init__.py
"""
Database module for PC Repair CRM Pro

✅ Экспортирует DatabaseConnection — singleton для работы с SQLite
✅ Поддерживает обратную совместимость через алиас `Database`
✅ Готов к типизации через TYPE_CHECKING для IDE
"""

from typing import TYPE_CHECKING

# ==================== 🗄️ ОСНОВНОЙ КЛАСС ====================
from .connection import DatabaseConnection

# ==================== 🔗 ОБРАТНАЯ СОВМЕСТИМОСТЬ ====================
# 🔗 Алиас для старого кода:
# • Старый код: from database import Database
# • Новый код: from database import DatabaseConnection (рекомендуется)
Database = DatabaseConnection

# ==================== 📦 PUBLIC API ====================
__all__ = [
    "DatabaseConnection",  # ✅ Основной класс (рекомендуется)
    "Database",            # 🔗 Алиас для совместимости
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Database connection module for PC Repair CRM Pro"

# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода (mypy, pyright),
# не выполняются при запуске программы (уже импортированы выше)
if TYPE_CHECKING:
    from .connection import DatabaseConnection