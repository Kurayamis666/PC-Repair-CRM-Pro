# core/config_loader.py
"""
Загрузчик конфигурации для PC Repair CRM Pro

✅ БЕЗОПАСНОСТЬ: Генерация соли, предупреждения о дефолтных значениях
✅ ТИПИЗАЦИЯ: Полная аннотация с поддержкой секций (корректный синтаксис)
✅ ГИБКОСТЬ: Префикс переменных, вложенные ключи, авто-сохранение
✅ НАДЁЖНОСТЬ: Логирование вместо print(), валидация с исключениями
"""

import os
import re
import secrets
import logging
from pathlib import Path
from typing import Optional, Any, Dict, Union, List, TypeVar, overload, TYPE_CHECKING

try:
    from dotenv import load_dotenv, set_key, dotenv_values
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    def load_dotenv(path: str) -> None:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        os.environ[key.strip()] = value.strip().strip('"\'')

from core.logger import app_logger

# ==================== 🎯 ТИПЫ И КОНСТАНТЫ ====================

T = TypeVar('T')
EnvValue = Union[str, int, float, bool, List[str]]

ENV_PREFIX = "PC_REPAIR_"

CONFIG_SCHEMA: Dict[str, Dict[str, Any]] = {
    "DB_PATH": {"type": str, "default": "data/repair_shop.db", "required": True},
    "DB_TIMEOUT": {"type": int, "default": 30, "min": 1, "max": 300},
    "DB_WAL_MODE": {"type": bool, "default": True},
    "SMTP_HOST": {"type": str, "default": "smtp.gmail.com"},
    "SMTP_PORT": {"type": int, "default": 587, "min": 1, "max": 65535},
    "SMTP_TLS": {"type": bool, "default": True},
    "SMTP_USERNAME": {"type": str, "default": "", "sensitive": True},
    "SMTP_PASSWORD": {"type": str, "default": "", "sensitive": True, "required": False},
    "SMS_PROVIDER": {"type": str, "default": ""},
    "SMS_API_KEY": {"type": str, "default": "", "sensitive": True},
    "DEFAULT_LANGUAGE": {"type": str, "default": "ru", "choices": ["ru", "en"]},
    "SUPPORTED_LANGUAGES": {"type": list, "default": ["ru", "en"]},
    "THEME": {"type": str, "default": "dark", "choices": ["dark", "light", "system"]},
    "PASSWORD_SALT": {"type": str, "default": None, "required": True, "min_length": 32, "sensitive": True},
    "SESSION_TIMEOUT": {"type": int, "default": 480, "min": 1},
    "LOG_LEVEL": {"type": str, "default": "INFO", "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
    "LOG_FILE": {"type": str, "default": "logs/app.log"},
    "LOG_MAX_SIZE_MB": {"type": int, "default": 10, "min": 1},
    "LOG_BACKUP_COUNT": {"type": int, "default": 5, "min": 1},
    "AUTO_BACKUP": {"type": bool, "default": True},
    "BACKUP_DIR": {"type": str, "default": "data/backups"},
    "BACKUP_KEEP_DAYS": {"type": int, "default": 30, "min": 1},
    "DEFAULT_CURRENCY": {"type": str, "default": "RUB"},
    "TAX_RATE": {"type": float, "default": 0.0, "min": 0.0, "max": 100.0},
    "DEBUG": {"type": bool, "default": False},
    "LOAD_DEMO_ON_EMPTY": {"type": bool, "default": True},
}


class Config:
    """
    Глобальный конфиг приложения (Singleton)
    
    ✅ Загрузка из .env с префиксом PC_REPAIR_*
    ✅ Валидация по схеме с типами и ограничениями
    ✅ Безопасная работа с чувствительными данными
    ✅ Поддержка вложенных ключей: "database.path"
    """
    
    _instance: Optional["Config"] = None
    _loaded: bool = False
    
    # ✅ Объявление атрибутов для IDE (не выполняется при запуске)
    if TYPE_CHECKING:
        _values: Dict[str, EnvValue]
        _env_path: Optional[str]
    
    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            # ✅ Корректное присваивание без аннотаций
            cls._instance._values = {}
            cls._instance._env_path = None
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_loaded', False):
            return
        self._loaded = True
        app_logger.debug("🔧 Config singleton initialized")
    
    def load(self, env_path: Optional[str] = None, strict: bool = False) -> bool:
        """Загрузить конфигурацию из .env файла"""
        if env_path is None:
            env_path = self._find_env_file()
        
        if env_path and Path(env_path).exists():
            self._env_path = env_path
            app_logger.info(f"📄 Loading config from: {env_path}")
            load_dotenv(env_path)
        else:
            app_logger.warning("⚠️ .env file not found, using defaults")
        
        for key, schema in CONFIG_SCHEMA.items():
            prefixed_key = f"{ENV_PREFIX}{key}"
            value = os.getenv(prefixed_key) or os.getenv(key)
            
            if value is None:
                value = schema.get("default")
                if value is None and schema.get("required"):
                    msg = f"❌ Required config key missing: {key}"
                    if strict:
                        raise ValueError(msg)
                    app_logger.error(msg)
                    continue
            
            try:
                parsed = self._parse_value(key, value, schema)
                self._validate_value(key, parsed, schema)
                self._values[key] = parsed
            except Exception as e:
                msg = f"❌ Invalid config value for {key}: {value} ({e})"
                if strict:
                    raise ValueError(msg) from e
                app_logger.error(msg)
                self._values[key] = schema.get("default")
        
        self._check_sensitive_settings()
        app_logger.info(f"✅ Config loaded: {len(self._values)} settings")
        return True
    
    def _find_env_file(self) -> Optional[str]:
        """Поиск .env файла в стандартных путях"""
        candidates = [
            Path(__file__).parent.parent / ".env",
            Path.cwd() / ".env",
            Path(os.getenv("APP_ROOT", ".")) / ".env",
        ]
        for path in candidates:
            if path.exists():
                return str(path.resolve())
        return None
    
    def _parse_value(self, key: str, value: Any, schema: Dict[str, Any]) -> EnvValue:
        """Парсинг значения согласно схеме"""
        if value is None:
            return schema.get("default")
        
        target_type = schema.get("type", str)
        
        if target_type == bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1", "on")
            return bool(value)
        
        if target_type == int:
            try:
                return int(value)
            except (ValueError, TypeError):
                return int(schema.get("default", 0))
        
        if target_type == float:
            try:
                return float(value)
            except (ValueError, TypeError):
                return float(schema.get("default", 0.0))
        
        if target_type == list:
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                return [v.strip() for v in value.split(",") if v.strip()]
            return schema.get("default", [])
        
        return str(value).strip() if value is not None else schema.get("default", "")
    
    def _validate_value(self, key: str, value: Any, schema: Dict[str, Any]) -> None:
        """Валидация значения по ограничениям схемы"""
        if "choices" in schema and value not in schema["choices"]:
            raise ValueError(f"Must be one of {schema['choices']}")
        
        if isinstance(value, (int, float)):
            if "min" in schema and value < schema["min"]:
                raise ValueError(f"Must be >= {schema['min']}")
            if "max" in schema and value > schema["max"]:
                raise ValueError(f"Must be <= {schema['max']}")
        
        if isinstance(value, str) and "min_length" in schema:
            if len(value) < schema["min_length"]:
                raise ValueError(f"Length must be >= {schema['min_length']}")
    
    def _check_sensitive_settings(self) -> None:
        """Проверка и предупреждения о чувствительных настройках"""
        salt = self.get("PASSWORD_SALT", "")
        if not salt or salt == "default_salt_change_me" or len(salt) < 32:
            app_logger.critical(
                "🔐 PASSWORD_SALT is missing or weak! "
                "Generate a secure salt: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
            if self.get_bool("DEBUG"):
                temp_salt = secrets.token_hex(32)
                app_logger.warning(f"🔧 Using temporary salt for DEBUG mode: {temp_salt[:16]}...")
                self._values["PASSWORD_SALT"] = temp_salt
        
        if self.get("SMTP_PASSWORD") and self.get_bool("notifications.email_enabled"):
            app_logger.warning("⚠️ SMTP_PASSWORD is set but email notifications may not work without proper config")
    
    @overload
    def get(self, key: str, default: None = None) -> Optional[EnvValue]: ...
    @overload
    def get(self, key: str, default: T) -> Union[EnvValue, T]: ...
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации"""
        if "." in key:
            parts = key.split(".")
            value = self._values
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        return self._values.get(key, default)
    
    def get_str(self, key: str, default: str = "") -> str:
        value = self.get(key, default)
        return str(value) if value is not None else default
    
    def get_int(self, key: str, default: int = 0) -> int:
        try:
            val = self.get(key, default)
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            app_logger.warning(f"⚠️ Cannot convert {key} to int: {val}")
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        try:
            val = self.get(key, default)
            return float(val) if val is not None else default
        except (ValueError, TypeError):
            app_logger.warning(f"⚠️ Cannot convert {key} to float: {val}")
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        return bool(value)
    
    def get_list(self, key: str, default: Optional[List[str]] = None) -> List[str]:
        value = self.get(key, default or [])
        if isinstance(value, list):
            return [str(v) for v in value]
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return default or []
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """Установить значение конфигурации"""
        schema = CONFIG_SCHEMA.get(key, {})
        
        try:
            parsed = self._parse_value(key, value, schema)
            self._validate_value(key, parsed, schema)
        except Exception as e:
            app_logger.error(f"❌ Cannot set {key}={value}: {e}")
            return False
        
        old_value = self._values.get(key)
        self._values[key] = parsed
        app_logger.debug(f"✏️ Config changed: {key} = {parsed} (was: {old_value})")
        
        if save and self._env_path:
            return self._save_to_env(key, str(value))
        return True
    
    def _save_to_env(self, key: str, value: str) -> bool:
        """Сохранить одно значение в .env файл"""
        if not DOTENV_AVAILABLE or not self._env_path:
            app_logger.warning("⚠️ Cannot save config: dotenv not available or no env path")
            return False
        
        try:
            if " " in value or "=" in value or "#" in value:
                value = f'"{value}"'
            set_key(self._env_path, f"{ENV_PREFIX}{key}", value)
            app_logger.debug(f"💾 Saved to .env: {ENV_PREFIX}{key}={value}")
            return True
        except Exception as e:
            app_logger.error(f"❌ Failed to save {key} to .env: {e}")
            return False
    
    def reload(self) -> bool:
        """Перезагрузить конфиг из файла"""
        app_logger.info("🔄 Reloading config...")
        self._values.clear()
        self._loaded = False
        return self.load(self._env_path)
    
    @property
    def is_debug(self) -> bool:
        return self.get_bool("DEBUG", False)
    
    @property
    def language(self) -> str:
        return self.get_str("DEFAULT_LANGUAGE", "ru")
    
    @property
    def theme(self) -> str:
        return self.get_str("THEME", "dark")
    
    @property
    def db_path(self) -> Path:
        """Нормализованный абсолютный путь к БД"""
        path = Path(self.get_str("DB_PATH", "data/repair_shop.db"))
        if not path.is_absolute():
            app_dir = Path(__file__).parent.parent
            path = app_dir / path
        return path.resolve()
    
    @property
    def smtp_config(self) -> Dict[str, Any]:
        """Конфигурация SMTP (без пароля в логах)"""
        return {
            "host": self.get_str("SMTP_HOST"),
            "port": self.get_int("SMTP_PORT", 587),
            "use_tls": self.get_bool("SMTP_TLS", True),
            "username": self.get_str("SMTP_USERNAME"),
        }
    
    @property
    def smtp_password(self) -> str:
        """Безопасный доступ к паролю SMTP"""
        return self.get_str("SMTP_PASSWORD", "")
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Экспорт конфига в словарь"""
        result = dict(self._values)
        if not include_sensitive:
            for key, schema in CONFIG_SCHEMA.items():
                if schema.get("sensitive") and key in result:
                    result[key] = "***"
        return result
    
    def __repr__(self) -> str:
        return f"Config(language={self.language}, theme={self.theme}, debug={self.is_debug})"


# ✅ Глобальный экземпляр (Singleton)
config = Config()


def init_config(env_path: Optional[str] = None, strict: bool = False) -> Config:
    """Инициализировать конфиг (вызывать один раз при старте приложения)"""
    cfg = Config()
    if not cfg.load(env_path, strict):
        app_logger.warning("⚠️ Config loaded with warnings")
    return cfg