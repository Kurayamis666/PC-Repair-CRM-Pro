# ui/dialogs/__init__.py
"""
Пакет диалоговых окон для PC Repair CRM Pro

✅ Экспортирует публичный API: все диалоги и хелпер-функции
✅ Облегчает импорт: from ui.dialogs import ask_confirm, ask_date, ...
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Оптимизирует загрузку через ленивые импорты для тяжёлых диалогов
"""

from typing import TYPE_CHECKING, Any, Optional, Callable, Dict, List
import customtkinter as ctk

# ==================== 🗓️ ОСНОВНЫЕ ДИАЛОГИ ====================
# Прямые импорты для часто используемых диалогов
from .calendar import CalendarPopup, ask_date
from .confirm import ConfirmDialog, ask_confirm
from .editor import RecordEditor

# ==================== 📋 СПЕЦИАЛИЗИРОВАННЫЕ ДИАЛОГИ ====================
# Ленивые импорты для диалогов, которые используются реже
def __getattr__(name: str) -> Any:
    """
    Ленивая загрузка диалогов при первом обращении
    
    ✅ Избегает циклических импортов
    ✅ Ускоряет начальную загрузку модуля
    ✅ Поддерживает автодополнение в IDE через TYPE_CHECKING
    
    Example:
        from ui.dialogs import UserEditorDialog  # Импортируется только здесь
    """
    if name == "UserEditorDialog":
        from .user_editor import UserEditorDialog
        return UserEditorDialog
    
    elif name == "RequestEditorDialog":
        from .request_editor import RequestEditorDialog
        return RequestEditorDialog
    
    elif name == "ReferenceEditorDialog":
        from .reference_editor import ReferenceEditorDialog
        return ReferenceEditorDialog
    
    elif name == "PartsDeductionDialog":
        from .parts_deduction_dialog import PartsDeductionDialog
        return PartsDeductionDialog
    
    elif name == "PartAnalogsDialog":
        from .part_analogs_dialog import PartAnalogsDialog
        return PartAnalogsDialog
    
    elif name == "EquipmentEditorDialog":
        from .equipment_editor import EquipmentEditorDialog
        return EquipmentEditorDialog
    
    elif name == "CsvImportDialog":
        from .csv_import_dialog import CsvImportDialog
        return CsvImportDialog
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 🗓️ Основные диалоги (прямой импорт)
    "CalendarPopup",
    "ask_date",
    "ConfirmDialog", 
    "ask_confirm",
    "RecordEditor",
    
    # 📋 Специализированные диалоги (ленивый импорт)
    "UserEditorDialog",
    "RequestEditorDialog",
    "ReferenceEditorDialog",
    "PartsDeductionDialog",
    "PartAnalogsDialog",
    "EquipmentEditorDialog",
    "CsvImportDialog",
]


# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Dialog windows for PC Repair CRM Pro"


# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы
if TYPE_CHECKING:
    from .calendar import CalendarPopup, ask_date
    from .confirm import ConfirmDialog, ask_confirm
    from .editor import RecordEditor
    from .user_editor import UserEditorDialog
    from .request_editor import RequestEditorDialog
    from .reference_editor import ReferenceEditorDialog
    from .parts_deduction_dialog import PartsDeductionDialog
    from .part_analogs_dialog import PartAnalogsDialog
    from .equipment_editor import EquipmentEditorDialog
    from .csv_import_dialog import CsvImportDialog


# ==================== 🛠️ CONVENIENCE FUNCTIONS ====================

def show_confirm(
    parent: ctk.CTkBaseClass,
    message: str,
    on_confirm: Callable[[], None],
    **kwargs
) -> ConfirmDialog:
    """
    Быстрое создание диалога подтверждения
    
    ✅ Обёртка над ask_confirm для удобства
    
    Example:
        >>> show_confirm(parent, "Удалить запись?", on_confirm=delete_record, danger=True)
    """
    return ask_confirm(parent, message, on_confirm, **kwargs)


def show_calendar(
    parent: ctk.CTkBaseClass,
    callback: Callable[[Optional[str]], None],
    **kwargs
) -> CalendarPopup:
    """
    Быстрое создание календаря
    
    ✅ Обёртка над ask_date для удобства
    
    Example:
        >>> show_calendar(parent, on_date_selected, initial_date="2024-01-01")
    """
    return ask_date(parent, callback, **kwargs)


def show_import_dialog(
    parent: ctk.CTkBaseClass,
    on_import: Callable[[Dict[str, int]], None],
    lang: str = "ru",
    **kwargs
) -> "CsvImportDialog":  # type: ignore
    """
    Быстрое создание диалога импорта CSV
    
    ✅ Ленивый импорт CsvImportDialog
    
    Example:
        >>> show_import_dialog(parent, on_import_complete, lang="ru")
    """
    from .csv_import_dialog import CsvImportDialog
    return CsvImportDialog(parent, lang=lang, on_import=on_import, **kwargs)