# utils/__init__.py
"""
PC Repair CRM Pro — Utilities Module
Вспомогательные функции, валидаторы и форматировщики

✅ Экспортирует только публичный API модуля
✅ Сгруппировано по назначению для удобной навигации
✅ Совместимо с type checkers (mypy, pyright)
"""

# ==================== 🔐 SECURITY & IDS ====================
from .helpers import (
    generate_id,
    generate_secure_token,
    hash_password,
    verify_password,
)

# ==================== 📊 FORMATTING ====================
from .helpers import (
    format_currency,
    format_date,
    format_datetime,
    format_file_size,
    truncate_text,
)

from .formatters import (
    # Классы-форматировщики
    DateFormatter,
    CurrencyFormatter,
    PhoneFormatter,
    TextFormatter,
    SizeFormatter,
    # Константы форматов
    DateFormat,
    CurrencyCode,
)

# ==================== ✅ VALIDATION ====================
from .validators import (
    # Базовые валидаторы
    validate_required,
    validate_email,
    validate_phone,
    validate_number,
    validate_date,
    validate_string_length,
    # Специализированные валидаторы
    validate_sku,
    validate_inn,
    validate_password,
    validate_currency,
    validate_url,
    validate_date_range,
    validate_file_path,
    # Утилиты валидации
    ValidationError,
    raise_if_invalid,
    validate_multiple,
    # Комплексные валидаторы
    validate_employee_data,
    validate_part_data,
)

# ==================== 🗂️ DATA UTILS ====================
from .helpers import (
    safe_get,
    safe_set,
    chunk_list,
    flatten_list,
    merge_dicts,
    to_json_safe,
    safe_json_dumps,
)

# ==================== 🔄 DECORATORS ====================
from .helpers import (
    retry_on_error,
    measure_time,
    debounce,
    cache_result,
)

# ==================== 📁 FILE & PATH ====================
from .helpers import (
    ensure_dir,
    get_file_size,
    sanitize_filename,
)

# ==================== 🧩 GENERAL UTILS ====================
from .helpers import (
    raise_if,
    batch_process,
)

# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 🔐 Security & IDs
    "generate_id",
    "generate_secure_token",
    "hash_password",
    "verify_password",
    
    # 📊 Formatting functions
    "format_currency",
    "format_date",
    "format_datetime",
    "format_file_size",
    "truncate_text",
    
    # 🎨 Formatter classes
    "DateFormatter",
    "CurrencyFormatter",
    "PhoneFormatter",
    "TextFormatter",
    "SizeFormatter",
    
    # 📋 Format constants
    "DateFormat",
    "CurrencyCode",
    
    # ✅ Basic validators
    "validate_required",
    "validate_email",
    "validate_phone",
    "validate_number",
    "validate_date",
    "validate_string_length",
    
    # 🔍 Specialized validators
    "validate_sku",
    "validate_inn",
    "validate_password",
    "validate_currency",
    "validate_url",
    "validate_date_range",
    "validate_file_path",
    
    # 🧩 Validation utilities
    "ValidationError",
    "raise_if_invalid",
    "validate_multiple",
    
    # 👥 Complex validators
    "validate_employee_data",
    "validate_part_data",
    
    # 🗂️ Data utilities
    "safe_get",
    "safe_set",
    "chunk_list",
    "flatten_list",
    "merge_dicts",
    "to_json_safe",
    "safe_json_dumps",
    
    # 🔄 Decorators
    "retry_on_error",
    "measure_time",
    "debounce",
    "cache_result",
    
    # 📁 File & path utilities
    "ensure_dir",
    "get_file_size",
    "sanitize_filename",
    
    # 🧩 General utilities
    "raise_if",
    "batch_process",
]


# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Utility functions for PC Repair CRM Pro"


# ==================== 🚀 QUICK IMPORTS (convenience) ====================
# Для тех, кто хочет импортировать всё сразу (не рекомендуется для продакшена)
# from . import *  # использует __all__


# ==================== 🔍 TYPE HINTS FOR LSP ====================
# Помогает IDE с автодополнением при импорте из utils
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Эти импорты нужны только для type checkers, не выполняются при запуске
    from .helpers import T
    from .validators import Tuple