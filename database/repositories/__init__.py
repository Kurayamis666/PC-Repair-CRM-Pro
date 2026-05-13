# database/repositories/__init__.py
"""
PC Repair CRM - Repository Layer
Репозитории для работы с сущностями базы данных

✅ Экспортирует все репозитории для удобного импорта
✅ Синхронизировано с заменой Client → Employee
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Содержит метаданные для документации
"""

from typing import TYPE_CHECKING
from database.connection import DatabaseConnection

# ==================== 🗄️ ОСНОВНЫЕ РЕПОЗИТОРИИ ====================
from .employee_repo import EmployeeRepository  # ✅ Исправлено: ClientRepository → EmployeeRepository
from .request_repo import RequestRepository
from .part_repo import PartRepository
from .user_repo import UserRepository

# ==================== 📋 PUBLIC API ====================
__all__ = [
    # 👤 Пользователи системы
    "UserRepository",
    
    # 👨‍💼 Сотрудники (бывш. клиенты)
    "EmployeeRepository",
    
    # 📝 Заявки на ремонт
    "RequestRepository",
    
    # 🔧 Запчасти и номенклатура
    "PartRepository",
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Repository layer for database entities in PC Repair CRM Pro"

# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы (уже импортированы выше)
if TYPE_CHECKING:
    from .employee_repo import EmployeeRepository
    from .request_repo import RequestRepository
    from .part_repo import PartRepository
    from .user_repo import UserRepository

# ==================== 🛠️ CONVENIENCE FACTORIES ====================

def create_employee_repo(db: DatabaseConnection) -> EmployeeRepository:
    """
    Быстрое создание репозитория сотрудников
    
    ✅ Удобно для инициализации в App
    
    Example:
        >>> repo = create_employee_repo(db_conn)
        >>> employees = repo.get_all()
    """
    return EmployeeRepository(db)


def create_request_repo(db: DatabaseConnection) -> RequestRepository:
    """
    Быстрое создание репозитория заявок
    
    ✅ Автоматически использует переданное подключение к БД
    
    Example:
        >>> repo = create_request_repo(db_conn)
        >>> requests = repo.get_all(status=RequestStatus.NEW)
    """
    return RequestRepository(db)


def create_part_repo(db: DatabaseConnection) -> PartRepository:
    """
    Быстрое создание репозитория запчастей
    
    ✅ Использует то же подключение к БД что и другие репозитории
    
    Example:
        >>> repo = create_part_repo(db_conn)
        >>> parts = repo.get_low_stock()
    """
    return PartRepository(db)


def create_user_repo(db: DatabaseConnection) -> UserRepository:
    """
    Быстрое создание репозитория пользователей
    
    ✅ Удобно для аутентификации и управления правами
    
    Example:
        >>> repo = create_user_repo(db_conn)
        >>> user = repo.authenticate("admin", "password")
    """
    return UserRepository(db)