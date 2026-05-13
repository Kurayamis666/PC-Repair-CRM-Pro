# core/__init__.py
"""
Core module for PC Repair CRM Pro
Основные компоненты приложения: логирование, конфигурация, утилиты

✅ Экспортирует публичный API всех подмодулей core/
✅ Поддерживает Type Checkers (mypy, pyright)
✅ Содержит метаданные для документации
✅ Предоставляет удобные алиасы для частого использования
"""

from typing import TYPE_CHECKING

# ==================== 📝 ЛОГИРОВАНИЕ ====================
from .logger import AppLogger, app_logger

# ==================== ⚙️ КОНФИГУРАЦИЯ ====================
# Runtime-конфиг (из config.py) — для настроек приложения
from .config import AppConfig, config as app_config

# Загрузчик .env (из config_loader.py) — для переменных окружения
from .config_loader import Config as EnvConfig, config as env_config, init_config

# ==================== 🔢 УТИЛИТЫ ====================
from .unit_converter import UnitConverter

# ==================== 📦 PUBLIC API ====================
__all__ = [
    # 📝 Логирование
    "AppLogger",
    "app_logger",
    
    # ⚙️ Конфигурация (runtime)
    "AppConfig",
    "app_config",  # ✅ Удобный алиас: from core import app_config
    
    # ⚙️ Конфигурация (.env loader)
    "EnvConfig",
    "env_config",   # ✅ Удобный алиас: from core import env_config
    "init_config",  # ✅ Функция инициализации при старте
    
    # 🔢 Утилиты
    "UnitConverter",
]

# ==================== 🏷️ MODULE METADATA ====================
__version__ = "1.0.0"
__author__ = "PC Repair CRM Team"
__description__ = "Core components for PC Repair CRM Pro: logging, config, utilities"

# ==================== 🔍 TYPE HINTS FOR LSP/IDE ====================
# Эти импорты нужны только для статических анализаторов кода,
# не выполняются при запуске программы (уже импортированы выше)
if TYPE_CHECKING:
    from .logger import AppLogger, app_logger
    from .config import AppConfig, config as app_config
    from .config_loader import Config as EnvConfig, config as env_config, init_config
    from .unit_converter import UnitConverter

# ==================== 🛠️ CONVENIENCE ALIASES ====================

# ✅ Короткие имена для частого использования
logger = app_logger  # from core import logger
config = app_config  # from core import config (runtime config)

# ✅ Функция для инициализации всего ядра при старте приложения
def init_core(env_path: str | None = None) -> None:
    """
    Инициализировать все компоненты ядра
    
    ✅ Вызывать один раз в main.py при старте приложения
    ✅ Загружает конфиг из .env, инициализирует логгер
    
    Args:
        env_path: Путь к .env файлу (по умолчанию авто-поиск)
        
    Example:
        >>> from core import init_core
        >>> init_core()  # Готово!
    """
    # ✅ Инициализация загрузчика конфига (.env)
    init_config(env_path)
    
    # ✅ Логгер инициализируется автоматически при первом импорте
    # ✅ AppConfig инициализируется автоматически как Singleton
    
    logger.debug("🚀 Core module initialized")