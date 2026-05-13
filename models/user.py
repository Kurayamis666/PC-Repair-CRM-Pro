# models/user.py
"""
Модель пользователя системы для PC Repair CRM Pro

✅ Типобезопасная модель с валидацией
✅ Иерархия прав через уровень доступа
✅ Метод проверки пароля с использованием utils.helpers
✅ Полное соответствие схеме БД (добавлены full_name, email, phone)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import re

from utils.helpers import verify_password, hash_password


# ==================== 🎯 РОЛИ ПОЛЬЗОВАТЕЛЕЙ ====================

class UserRole(str, Enum):
    """
    Роли пользователей (совместимы с CHECK-ограничениями БД)
    
    ✅ Значения совпадают с записями в БД ('admin', 'manager'...)
    ✅ Уровень доступа: чем больше число, тем больше прав
    """
    VIEWER = "viewer"
    TECHNICIAN = "technician"
    MANAGER = "manager"
    ADMIN = "admin"
    
    # Карта уровней доступа
    _LEVELS: dict = {"viewer": 1, "technician": 2, "manager": 3, "admin": 4}
    
    @property
    def level(self) -> int:
        """Получить уровень доступа роли (1-4)"""
        return self._LEVELS.get(self.value, 0)
    
    def can_access(self, required_level: int) -> bool:
        """Проверка: имеет ли роль достаточный уровень доступа"""
        return self.level >= required_level
    
    @classmethod
    def from_string(cls, value: str) -> "UserRole":
        """Безопасная конвертация строки БД в UserRole"""
        try:
            return cls(value.lower().strip())
        except (ValueError, KeyError):
            return cls.VIEWER


# ==================== 👤 МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ ====================

@dataclass
class User:
    """
    Модель пользователя системы
    
    ✅ Все поля соответствуют таблице users в database/schema.sql
    ✅ password_hash хранит только хеш (не пароль в открытом виде)
    """
    
    # 🔑 Основные поля (соответствуют колонкам БД)
    id: Optional[int] = None
    username: str = ""
    full_name: str = ""        # ✅ ДОБАВЛЕНО: Полное имя
    email: str = ""            # ✅ ДОБАВЛЕНО: Почта
    phone: str = ""            # ✅ ДОБАВЛЕНО: Телефон
    password_hash: str = field(default="", repr=False)  # 🔐 Не показывать в repr
    role: UserRole = UserRole.VIEWER
    branch_id: Optional[int] = None  # Виртуальное поле (в таблице users нет branch_id, но может быть в JOIN)
    is_active: bool = True     # ✅ Для soft-delete
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    # 📦 Дополнительные поля (не в БД)
    branch_name: Optional[str] = field(default=None, repr=False)
    
    # ⚙️ Константы валидации
    MIN_USERNAME_LENGTH: int = 3
    MAX_USERNAME_LENGTH: int = 50
    
    def __post_init__(self) -> None:
        """Валидация после инициализации"""
        # ✅ Нормализация username
        if self.username:
            self.username = self.username.strip()
        
        # ✅ Валидация username если он задан
        if self.username and not self._validate_username():
            raise ValueError(f"Invalid username: '{self.username}'")
    
    def _validate_username(self) -> bool:
        """Валидация имени пользователя"""
        if not self.username:
            return False
        if len(self.username) < self.MIN_USERNAME_LENGTH:
            return False
        if len(self.username) > self.MAX_USERNAME_LENGTH:
            return False
        # ✅ Разрешены: буквы, цифры, _, -, ., @
        return bool(re.match(r'^[a-zA-Z0-9_\-.@]+$', self.username))
    
    # ==================== 🔄 КОНВЕРТАЦИЯ ====================
    
    @classmethod
    def from_row(cls, row: Optional[Dict[str, Any]]) -> "User":
        """Создать объект User из строки БД"""
        if not row:
            return cls()
        
        # ✅ Безопасная конвертация роли
        role_value = row.get("role", "viewer")
        role = UserRole.from_string(role_value)
        
        # ✅ Парсинг datetime из строки БД
        def parse_datetime(value: Optional[str]) -> Optional[datetime]:
            if not value:
                return None
            try:
                return datetime.fromisoformat(str(value).replace(" ", "T"))
            except ValueError:
                return None
        
        return cls(
            id=row.get("id"),
            username=row.get("username", ""),
            full_name=row.get("full_name", ""),  # ✅ Чтение из БД
            email=row.get("email", ""),          # ✅ Чтение из БД
            phone=row.get("phone", ""),          # ✅ Чтение из БД
            password_hash=row.get("password", ""),
            role=role,
            branch_id=row.get("branch_id"),      # Будет None, т.к. в таблице users нет branch_id
            is_active=bool(row.get("is_active", True)),
            created_at=parse_datetime(row.get("created_at")),
            updated_at=parse_datetime(row.get("updated_at")),
            last_login=parse_datetime(row.get("last_login")),
        )
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Сериализация в словарь"""
        data = {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role.value,
            "role_name": self.role.name.lower(),
            "branch_id": self.branch_id,
            "branch_name": self.branch_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data["password_hash"] = self.password_hash
        
        return data
    
    # ==================== 🔐 РАБОТА С ПАРОЛЕМ ====================
    
    def check_password(self, plain_password: str) -> bool:
        """Проверка пароля через PBKDF2"""
        if not self.password_hash:
            return False
        return verify_password(plain_password, self.password_hash)
    
    def set_password(self, plain_password: str) -> None:
        """Установка нового пароля с хешированием"""
        if not plain_password:
            raise ValueError("Password cannot be empty")
        self.password_hash, _ = hash_password(plain_password)
    
    # ==================== 🔑 ПРОВЕРКА ПРАВ ====================
    
    @property
    def is_admin(self) -> bool:
        """Проверка: администратор"""
        return self.role == UserRole.ADMIN
    
    @property
    def access_level(self) -> int:
        """Получить уровень доступа пользователя"""
        return self.role.level
    
    def has_permission(self, required_level: int) -> bool:
        """Проверка прав через уровень"""
        return self.is_active and self.role.can_access(required_level)
    
    def can_edit_requests(self) -> bool:
        return self.has_permission(UserRole.TECHNICIAN.level)
    
    def can_manage_references(self) -> bool:
        return self.has_permission(UserRole.MANAGER.level)
    
    def can_manage_users(self) -> bool:
        return self.has_permission(UserRole.ADMIN.level)
    
    # ==================== 🔄 ОБНОВЛЕНИЕ ПОЛЕЙ ====================
    
    def update(self, **kwargs) -> None:
        """Безопасное обновление полей пользователя"""
        # ✅ Разрешены все основные поля + branch_id
        allowed_fields = {"username", "full_name", "email", "phone", "role", "branch_id", "is_active", "branch_name"}
        
        for key, value in kwargs.items():
            if key not in allowed_fields:
                raise ValueError(f"Cannot update field: {key}")
            
            if key == "username":
                self.username = str(value).strip()
                if not self._validate_username():
                    raise ValueError(f"Invalid username: '{self.username}'")
            
            elif key == "full_name":
                self.full_name = str(value).strip()
            
            elif key == "email":
                self.email = str(value).strip()
            
            elif key == "phone":
                self.phone = str(value).strip()
            
            elif key == "role":
                self.role = UserRole.from_string(str(value))
            
            elif key == "is_active":
                self.is_active = bool(value)
            
            elif key in ("branch_id", "branch_name"):
                setattr(self, key, value)
        
        self.updated_at = datetime.now()
    
    # ==================== 📊 СРАВНЕНИЕ И ПРЕДСТАВЛЕНИЕ ====================
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        if self.id and other.id:
            return self.id == other.id
        return self.username.lower() == other.username.lower()
    
    def __hash__(self) -> int:
        return hash((self.id, self.username.lower()))
    
    def __str__(self) -> str:
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.full_name or self.username} ({self.role.value})"
    
    def __repr__(self) -> str:
        return (f"User(id={self.id}, username='{self.username}', "
                f"role={self.role.value}, active={self.is_active})")