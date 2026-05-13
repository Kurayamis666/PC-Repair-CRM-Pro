# core/config.py
"""
Конфигурация приложения для PC Repair CRM Pro

✅ БЕЗОПАСНОСТЬ: Чтение чувствительных данных из .env (не из кода)
✅ ВАЛИДАЦИЯ: Проверка загруженных значений с fallback на дефолты
✅ ГИБКОСТЬ: Поддержка переменных окружения, глубокая загрузка конфига
✅ ТИПИЗАЦИЯ: Полная аннотация типов для всех методов
✅ НАДЁЖНОСТЬ: Защита от KeyError, логирование изменений
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dotenv import load_dotenv  # ✅ Для загрузки .env переменных

# ✅ Загружаем .env файл при импорте модуля
load_dotenv()

logger = logging.getLogger(__name__)


class AppConfig:
    """
    Класс конфигурации приложения с поддержкой:
    - Singleton паттерна
    - Загрузки из JSON-файла
    - Переменных окружения (.env)
    - Валидации значений
    - Глубокого слияния конфигов
    """
    
    _instance: Optional["AppConfig"] = None
    
    # ✅ Дефолтные значения (только нечувствительные!)
    # 🔐 Чувствительные данные (пароли, токены) читаются ТОЛЬКО из .env!
    _DEFAULTS: Dict[str, Dict[str, Any]] = {
        "general": {
            "language": "ru",
            "theme": "dark",
            "auto_backup": True,
            "backup_days": 7,
        },
        "database": {
            "path": "repair_shop.db",  # Относительный путь, будет преобразован
            "auto_backup": True,
            "timeout": 30,
        },
        "notifications": {
            "email_enabled": False,
            "sms_enabled": False,
            "low_stock_alert": True,
            "low_stock_threshold": 5,
        },
        "business": {
            "default_currency": "RUB",
            "tax_rate": 0.0,
            "default_warranty_days": 90,
        },
    }
    
    # ✅ Валидаторы для критических настроек
    _VALIDATORS: Dict[str, Dict[str, callable]] = {
        "general": {
            "language": lambda v: v in ("ru", "en"),
            "theme": lambda v: v in ("dark", "light", "system"),
            "backup_days": lambda v: isinstance(v, int) and 1 <= v <= 365,
        },
        "business": {
            "tax_rate": lambda v: isinstance(v, (int, float)) and 0 <= v <= 100,
            "default_warranty_days": lambda v: isinstance(v, int) and v >= 0,
        },
    }
    
    def __new__(cls) -> "AppConfig":
        """Singleton: гарантируем один экземпляр на приложение"""
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Инициализация только один раз"""
        if self._initialized:
            return
        
        # 📁 Пути приложения
        self.app_name = "PC Repair CRM Pro"
        self.version = "1.0.0"
        self.app_dir = Path(__file__).parent.parent
        
        # 📂 Директории для данных
        self.data_dir = self.app_dir / "data"
        self.logs_dir = self.app_dir / "logs"
        self.reports_dir = self.app_dir / "reports"
        self.backups_dir = self.data_dir / "backups"
        
        # ✅ Создаём директории
        for directory in [self.data_dir, self.logs_dir, self.reports_dir, self.backups_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 🔧 Основной конфиг (начинаем с дефолтов)
        self.config: Dict[str, Dict[str, Any]] = self._deep_copy(self._DEFAULTS)
        
        # 🗂️ Путь к файлу конфига
        self.config_file = self.data_dir / "config.json"
        
        # 🔄 Загружаем конфиг и применяем переменные окружения
        self.load_config()
        self._apply_env_overrides()
        
        # 🔐 Загружаем чувствительные настройки из .env (не сохраняем в файл!)
        self._load_sensitive_config()
        
        self._initialized = True
        logger.info(f"✅ AppConfig initialized: {self.config_file}")
    
    # ==================== 🔐 ЧУВСТВИТЕЛЬНЫЕ НАСТРОЙКИ (.env) ====================
    
    def _load_sensitive_config(self) -> None:
        """
        Загрузка чувствительных данных из переменных окружения
        
        🔐 Эти данные НЕ сохраняются в config.json для безопасности!
        """
        # SMTP настройки
        self.smtp_config = {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "use_tls": os.getenv("SMTP_TLS", "true").lower() == "true",
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),  # 🔐 Из .env!
            "from_email": os.getenv("SMTP_FROM", ""),
        }
        
        # SMS настройки
        self.sms_config = {
            "provider": os.getenv("SMS_PROVIDER", ""),
            "account_sid": os.getenv("SMS_ACCOUNT_SID", ""),
            "auth_token": os.getenv("SMS_AUTH_TOKEN", ""),  # 🔐 Из .env!
            "from_number": os.getenv("SMS_FROM_NUMBER", ""),
            "api_url": os.getenv("SMS_API_URL", ""),
        }
    
    @property
    def smtp(self) -> Dict[str, Any]:
        """Безопасный доступ к SMTP-конфигу"""
        return self.smtp_config.copy()  # Возвращаем копию для безопасности
    
    @property
    def sms(self) -> Dict[str, Any]:
        """Безопасный доступ к SMS-конфигу"""
        return self.sms_config.copy()
    
    # ==================== 🔄 ЗАГРУЗКА/СОХРАНЕНИЕ ====================
    
    def _deep_copy(self, data: Dict) -> Dict:
        """Глубокое копирование словаря (без импорта copy)"""
        result = {}
        for k, v in data.items():
            if isinstance(v, dict):
                result[k] = self._deep_copy(v)
            elif isinstance(v, list):
                result[k] = v.copy()
            else:
                result[k] = v
        return result
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """
        Глубокое слияние словарей
        
        ✅ Рекурсивно объединяет вложенные словари
        ✅ Не перезаписывает целые секции, а обновляет ключи
        """
        result = self._deep_copy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _validate_value(self, section: str, key: str, value: Any) -> bool:
        """Проверка значения через валидатор"""
        if section in self._VALIDATORS and key in self._VALIDATORS[section]:
            try:
                return self._VALIDATORS[section][key](value)
            except Exception:
                return False
        return True  # Если нет валидатора — считаем валидным
    
    def load_config(self) -> bool:
        """
        Загрузить конфиг из файла с валидацией и глубоким слиянием
        
        Returns:
            bool: True если загрузка успешна
        """
        if not self.config_file.exists():
            logger.debug(f"📄 Config file not found: {self.config_file}")
            return True  # Используем дефолты
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            # ✅ Глубокое слияние с дефолтами
            self.config = self._deep_merge(self.config, loaded)
            
            # ✅ Валидация критических настроек
            for section, validators in self._VALIDATORS.items():
                for key, validator in validators.items():
                    value = self.config.get(section, {}).get(key)
                    if value is not None and not self._validate_value(section, key, value):
                        default = self._DEFAULTS[section][key]
                        logger.warning(
                            f"⚠️ Invalid config value: {section}.{key}={value}. "
                            f"Using default: {default}"
                        )
                        self.config[section][key] = default
            
            logger.info(f"📄 Config loaded: {self.config_file}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in config file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return False
    
    def save_config(self) -> bool:
        """
        Сохранить конфиг в файл (без чувствительных данных!)
        
        Returns:
            bool: True если сохранение успешно
        """
        try:
            # ✅ Сохраняем только нечувствительные настройки
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.debug(f"💾 Config saved: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
            return False
    
    def _apply_env_overrides(self) -> None:
        """
        Переопределение настроек через переменные окружения
        
        Формат: PC_REPAIR_{SECTION}_{KEY} = value
        Пример: PC_REPAIR_GENERAL_LANGUAGE=en
        """
        prefix = "PC_REPAIR_"
        
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue
            
            # Парсим: PC_REPAIR_GENERAL_LANGUAGE → general.language
            parts = env_key[len(prefix):].lower().split("_", 1)
            if len(parts) != 2:
                continue
            
            section, key = parts
            
            if section in self.config and key in self.config[section]:
                # ✅ Конвертация типов
                current = self.config[section][key]
                if isinstance(current, bool):
                    value = env_value.lower() in ("true", "1", "yes")
                elif isinstance(current, int):
                    try:
                        value = int(env_value)
                    except ValueError:
                        continue
                elif isinstance(current, float):
                    try:
                        value = float(env_value)
                    except ValueError:
                        continue
                else:
                    value = env_value
                
                # ✅ Валидация перед применением
                if self._validate_value(section, key, value):
                    old_value = self.config[section][key]
                    self.config[section][key] = value
                    logger.debug(f"🔧 Env override: {section}.{key} = {value} (was: {old_value})")
    
    # ==================== 📖 GET/SET API ====================
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение настройки
        
        ✅ Поддержка вложенных ключей: "general.language"
        ✅ Безопасный доступ через .get() без KeyError
        
        Args:
            key: Ключ настройки ("general.language" или "database")
            default: Значение по умолчанию если ключ не найден
            
        Returns:
            Any: Значение настройки или default
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """
        Установить значение настройки
        
        ✅ Поддержка вложенных ключей: "general.language"
        ✅ Валидация перед сохранением
        ✅ Авто-сохранение (можно отключить параметром save=False)
        
        Args:
            key: Ключ настройки ("general.language")
            value: Новое значение
            save: Сохранить ли сразу в файл (по умолчанию True)
            
        Returns:
            bool: True если установка успешна
        """
        keys = key.split(".")
        
        # ✅ Проверяем валидацию если есть
        if len(keys) == 2:
            section, subkey = keys
            if not self._validate_value(section, subkey, value):
                logger.warning(f"⚠️ Invalid value for {key}: {value}")
                return False
        
        # ✅ Навигация по вложенной структуре
        current = self.config
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # ✅ Установка значения
        old_value = current.get(keys[-1])
        current[keys[-1]] = value
        
        logger.debug(f"✏️ Config changed: {key} = {value} (was: {old_value})")
        
        if save:
            return self.save_config()
        return True
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Получить все настройки секции
        
        ✅ Возвращает копию для безопасности
        ✅ Не позволяет модифицировать внутренний конфиг
        
        Args:
            section: Название секции ("general", "database", etc.)
            
        Returns:
            Dict[str, Any]: Копия настроек секции
        """
        return self._deep_copy(self.config.get(section, {}))
    
    def reload(self) -> bool:
        """
        Перезагрузить конфиг из файла (без рестарта приложения)
        
        ✅ Полезно для отладки или динамического обновления настроек
        
        Returns:
            bool: True если перезагрузка успешна
        """
        logger.info("🔄 Reloading config from file...")
        return self.load_config()
    
    # ==================== 🎯 СВОЙСТВА ДЛЯ ЧАСТОГО ДОСТУПА ====================
    
    @property
    def language(self) -> str:
        """Текущий язык интерфейса"""
        return self.config["general"].get("language", "ru")
    
    @property
    def theme(self) -> str:
        """Текущая тема оформления"""
        return self.config["general"].get("theme", "dark")
    
    @property
    def db_path(self) -> Path:
        """Полный путь к файлу базы данных"""
        db_path = self.config["database"].get("path", "repair_shop.db")
        path = Path(db_path)
        # ✅ Если путь относительный — делаем его относительно app_dir
        if not path.is_absolute():
            path = self.app_dir / path
        return path
    
    @property
    def is_email_enabled(self) -> bool:
        """Включены ли email-уведомления"""
        return self.config["notifications"].get("email_enabled", False)
    
    @property
    def is_sms_enabled(self) -> bool:
        """Включены ли SMS-уведомления"""
        return self.config["notifications"].get("sms_enabled", False)
    
    # ==================== 🛠️ УТИЛИТЫ ====================
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Экспорт конфига в словарь
        
        ✅ Опциональное включение чувствительных данных (только для отладки!)
        
        Args:
            include_sensitive: Включать ли SMTP/SMS пароли (по умолчанию False)
            
        Returns:
            Dict[str, Any]: Словарь с настройками
        """
        result = self._deep_copy(self.config)
        
        if include_sensitive:
            result["_smtp"] = self.smtp_config.copy()
            result["_sms"] = self.sms_config.copy()
        
        return result
    
    def __repr__(self) -> str:
        return f"AppConfig(version={self.version}, language={self.language}, theme={self.theme})"


# ✅ Глобальный экземпляр (Singleton)
config = AppConfig()

# 🔗 Алиас для обратной совместимости
Config = AppConfig