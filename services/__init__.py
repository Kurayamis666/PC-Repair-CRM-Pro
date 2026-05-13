# services/__init__.py
"""
Пакет сервисов для PC Repair CRM Pro

✅ Экспортирует публичный API: все бизнес-сервисы
✅ Облегчает импорт: from services import NotificationService, BarcodeService, ...
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Оптимизирует загрузку через ленивые импорты для тяжёлых сервисов
"""

from typing import TYPE_CHECKING, Any, Optional, Dict
from database.connection import DatabaseConnection

# ==================== 📧 ОСНОВНЫЕ СЕРВИСЫ ====================
# Прямые импорты для часто используемых сервисов
from .notification_service import NotificationService
from .report_service import ReportService
from .stock_service import StockService
from .barcode_service import BarcodeService  # ✅ Добавлен новый сервис

# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 📧 Основные сервисы (прямой импорт)
    "NotificationService",
    "ReportService",
    "StockService",
    "BarcodeService",  # ✅ Добавлен в публичный API
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Business logic services for PC Repair CRM Pro"

# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы
if TYPE_CHECKING:
    from .notification_service import NotificationService
    from .report_service import ReportService
    from .stock_service import StockService
    from .barcode_service import BarcodeService

# ==================== 🛠️ CONVENIENCE FUNCTIONS ====================

def create_notification_service(
    db: Optional[DatabaseConnection] = None,
    smtp_config: Optional[Dict] = None,
    sms_config: Optional[Dict] = None,
) -> NotificationService:
    """
    Быстрое создание сервиса уведомлений
    
    ✅ Удобно для инициализации в App
    
    Example:
        >>> service = create_notification_service(db=db_conn)
        >>> service.notify_client(...)
    """
    return NotificationService(
        smtp_config=smtp_config,
        sms_config=sms_config,
    )


def create_report_service(
    db: Optional[DatabaseConnection] = None,
) -> ReportService:
    """
    Быстрое создание сервиса отчётов
    
    ✅ Автоматически использует переданное подключение к БД
    
    Example:
        >>> service = create_report_service(db=db_conn)
        >>> stats = service.get_dashboard_stats()
    """
    return ReportService(db=db)


def create_stock_service(
    db: Optional[DatabaseConnection] = None,
) -> StockService:
    """
    Быстрое создание сервиса управления запасами
    
    ✅ Использует то же подключение к БД что и другие сервисы
    
    Example:
        >>> service = create_stock_service(db=db_conn)
        >>> alerts = service.check_stock_levels()
    """
    return StockService(db=db)


def create_barcode_service(
    output_dir: str = "reports/barcodes",
) -> BarcodeService:
    """
    Быстрое создание сервиса генерации кодов
    
    ✅ Настраиваемая директория для сохранения файлов
    
    Example:
        >>> service = create_barcode_service(output_dir="exports/labels")
        >>> path = service.generate_equipment_label(...)
    """
    return BarcodeService(output_dir=output_dir)