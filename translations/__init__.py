# translations/__init__.py
"""
PC Repair CRM - Translations Module
Система локализации и переводов

✅ Экспортирует публичный API: все функции перевода и утилиты
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Содержит метаданные для документации
"""

from typing import TYPE_CHECKING, Dict, List

# ==================== 🌐 ОСНОВНЫЕ ФУНКЦИИ ====================
# Прямые импорты для часто используемых функций
from .translations import (
    get_text, 
    set_language, 
    get_language,
    TRANSLATIONS,  # Экспортируем словарь для прямого доступа (если нужно)
)

# ==================== 🛠️ УТИЛИТЫ (ЛЕНИВЫЙ ИМПОРТ) ====================
# Ленивые импорты для редко используемых функций отладки
def __getattr__(name: str):
    """Ленивая загрузка утилит при первом обращении"""
    if name == "get_available_languages":
        from .translations import get_available_languages
        return get_available_languages
    
    elif name == "has_translation":
        from .translations import has_translation
        return has_translation
    
    elif name == "get_all_keys":
        from .translations import get_all_keys
        return get_all_keys
    
    elif name == "debug_missing_translations":
        from .translations import debug_missing_translations
        return debug_missing_translations
    
    elif name == "sync_translations":
        from .translations import sync_translations
        return sync_translations
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 🌐 Основные функции (прямой импорт)
    "get_text",
    "set_language",
    "get_language",
    "TRANSLATIONS",
    
    # 🛠️ Утилиты (ленивый импорт)
    "get_available_languages",
    "has_translation",
    "get_all_keys",
    "debug_missing_translations",
    "sync_translations",
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Localization system for PC Repair CRM Pro"


# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы
if TYPE_CHECKING:
    from .translations import (
        get_text, 
        set_language, 
        get_language,
        TRANSLATIONS,
        get_available_languages,
        has_translation,
        get_all_keys,
        debug_missing_translations,
        sync_translations,
    )