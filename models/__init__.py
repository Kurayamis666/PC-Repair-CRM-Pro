# models/__init__.py
"""
PC Repair CRM - Business Models
Бизнес-модели приложения с методами валидации и сериализации

✅ Экспортирует все модели и Enums для удобного импорта
✅ Синхронизировано с заменой Client → Employee
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Содержит метаданные для документации
"""

from typing import TYPE_CHECKING

# ==================== 📦 ОСНОВНЫЕ МОДЕЛИ ====================
from .user import User, UserRole
from .employee import Employee  # ✅ Исправлено: Client → Employee
from .request import Request, RequestStatus, RequestPriority
from .part import Part, PartCategory
from .equipment import Equipment, EquipmentType
from .report import Report, DashboardStats, ReportType

# ==================== 📋 PUBLIC API ====================
__all__ = [
    # 👤 Пользователи системы
    "User", "UserRole",
    
    # 👨‍💼 Сотрудники (бывш. клиенты)
    "Employee",
    
    # 📝 Заявки на ремонт
    "Request", "RequestStatus", "RequestPriority",
    
    # 🔧 Запчасти и номенклатура
    "Part", "PartCategory",
    
    # 💻 Оборудование
    "Equipment", "EquipmentType",
    
    # 📊 Отчёты и статистика
    "Report", "DashboardStats", "ReportType",
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Business models for PC Repair CRM Pro"

# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы (уже импортированы выше)
if TYPE_CHECKING:
    from .user import User, UserRole
    from .employee import Employee
    from .request import Request, RequestStatus, RequestPriority
    from .part import Part, PartCategory
    from .equipment import Equipment, EquipmentType
    from .report import Report, DashboardStats, ReportType