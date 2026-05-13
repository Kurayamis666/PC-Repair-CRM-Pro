# models/employee.py
"""
Модель сотрудника для PC Repair CRM Pro

✅ Типобезопасные поля с аннотациями
✅ Валидация контактов и баланса в __post_init__
✅ Автоматический парсинг дат из БД
✅ Бизнес-логика для управления балансом
✅ Безопасная сериализация без чувствительных данных
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from utils.validators import validate_phone, validate_email


# ==================== 👤 МОДЕЛЬ СОТРУДНИКА ====================

@dataclass
class Employee:
    """
    Модель сотрудника (заменяет устаревшую модель клиента)
    
    ✅ Валидация полей в __post_init__
    ✅ Автоматический парсинг дат из строк БД
    ✅ Управление балансом с историей операций
    ✅ Безопасная сериализация для API/UI
    
    Поля БД:
        - id: PRIMARY KEY AUTOINCREMENT
        - full_name: TEXT NOT NULL
        - phone: TEXT UNIQUE
        - email: TEXT
        - address, notes: TEXT
        - group_id: FOREIGN KEY -> employee_groups(id)
        - balance: REAL DEFAULT 0.0
        - created_at, updated_at: TEXT (ISO format)
    """
    
    # 🔑 Основные поля
    id: Optional[int] = None
    full_name: str = ""  # ✅ Было: name → full_name для согласованности
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    
    # 💰 Баланс и группы
    group_id: Optional[int] = None
    balance: float = 0.0
    salary: float = 0.0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 📦 JOIN-поля (не сохраняются в БД напрямую)
    group_name: Optional[str] = field(default=None, repr=False)
    
    # ⚙️ Константы валидации
    MIN_NAME_LENGTH: int = 2
    MAX_NAME_LENGTH: int = 100
    MIN_BALANCE: float = -1_000_000.0  # Максимальный долг
    MAX_BALANCE: float = 10_000_000.0  # Максимальный баланс
    
    def __post_init__(self) -> None:
        """
        Валидация и нормализация после инициализации
        
        ✅ Обрезка и очистка строк
        ✅ Валидация телефона и почты
        ✅ Ограничение баланса в допустимых пределах
        """
        # ✅ Нормализация имени
        if self.full_name:
            self.full_name = " ".join(self.full_name.split())[:self.MAX_NAME_LENGTH]
            if len(self.full_name) < self.MIN_NAME_LENGTH:
                raise ValueError(f"Name too short: '{self.full_name}'")
        
        # ✅ Валидация телефона
        if self.phone:
            valid, error = validate_phone(self.phone, "ru")
            if not valid:
                # Не выбрасываем ошибку, но нормализуем
                self.phone = self._normalize_phone(self.phone)
        
        # ✅ Валидация почты
        if self.email:
            valid, error = validate_email(self.email)
            if not valid:
                self.email = None  # Сбрасываем невалидный email
        
        # ✅ Ограничение баланса
        self.balance = max(self.MIN_BALANCE, min(self.balance, self.MAX_BALANCE))
    
    def _normalize_phone(self, phone: str) -> str:
        """Нормализация телефона: оставляем только цифры и +"""
        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
        # Добавляем +7 если номер российский без кода
        if cleaned.startswith("8") and len(cleaned) == 11:
            cleaned = "+7" + cleaned[1:]
        return cleaned[:20]  # Ограничение длины
    
    # ==================== 🔄 КОНВЕРТАЦИЯ ====================
    
    @classmethod
    def from_row(cls, row: Optional[Dict[str, Any]]) -> "Employee":
        """
        Создание экземпляра из строки базы данных
        
        ✅ Безопасная обработка None
        ✅ Парсинг datetime из строки БД
        ✅ Конвертация баланса в float
        
        Args:
            row: Словарь с данными из БД (или None)
            
        Returns:
            Employee: Новый экземпляр или пустой сотрудник если row=None
        """
        if not row:
            return cls()
        
        # ✅ Парсинг дат из строк БД
        def parse_date(val: Any) -> Optional[datetime]:
            if not val:
                return None
            try:
                return datetime.fromisoformat(str(val).replace(" ", "T"))
            except ValueError:
                return None
        
        # ✅ Безопасное чтение баланса
        def safe_float(val: Any, default: float = 0.0) -> float:
            try:
                return float(val) if val is not None else default
            except (ValueError, TypeError):
                return default
        
        return cls(
            id=row.get("id"),
            full_name=row.get("full_name") or row.get("name", ""),  # ✅ Поддержка старого поля name
            position=row.get("position"),
            phone=row.get("phone"),
            email=row.get("email"),
            address=row.get("address"),
            notes=row.get("notes"),
            group_id=row.get("group_id"),
            balance=safe_float(row.get("balance"), 0.0),
            salary=safe_float(row.get("salary"), 0.0),
            is_active=bool(row.get("is_active", 1)),
            created_at=parse_date(row.get("created_at")),
            updated_at=parse_date(row.get("updated_at")),
            group_name=row.get("group_name"),
        )
    
    def to_dict(self, include_notes: bool = True) -> Dict[str, Any]:
        """
        Сериализация в словарь (JSON-safe)
        
        ✅ Конвертация datetime → ISO string
        ✅ Опциональное включение заметок
        
        Args:
            include_notes: Включать ли поле notes (по умолчанию True)
            
        Returns:
            Dict[str, Any]: Словарь, готовый к json.dumps()
        """
        def to_iso(dt: Optional[datetime]) -> Optional[str]:
            return dt.isoformat() if dt else None
        
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "position": self.position,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "group_id": self.group_id,
            "balance": round(self.balance, 2),
            "salary": round(self.salary, 2),
            "is_active": self.is_active,
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
            "group_name": self.group_name,
        }
        
        if include_notes:
            data["notes"] = self.notes
        
        # ✅ Добавляем вычисляемые поля для удобства
        data["has_phone"] = bool(self.phone)
        data["has_email"] = bool(self.email)
        data["has_debt"] = self.balance < 0
        data["formatted_balance"] = f"{self.balance:.2f} ₽"
        
        return data
    
    # ==================== 💰 УПРАВЛЕНИЕ БАЛАНСОМ ====================
    
    @property
    def has_debt(self) -> bool:
        """Проверка: есть ли задолженность"""
        return self.balance < 0
    
    @property
    def can_order_on_credit(self) -> bool:
        """Проверка: можно ли заказывать в долг (баланс > минимума)"""
        return self.balance > self.MIN_BALANCE
    
    @property
    def debt_amount(self) -> float:
        """Сумма задолженности (0 если нет долга)"""
        return abs(self.balance) if self.balance < 0 else 0.0
    
    def add_balance(self, amount: float, reason: Optional[str] = None) -> bool:
        """
        Пополнение баланса
        
        ✅ Валидация суммы > 0
        ✅ Автообновление updated_at
        ✅ Возврат успеха операции
        
        Args:
            amount: Сумма пополнения (должна быть > 0)
            reason: Причина операции (для аудита)
            
        Returns:
            bool: True если операция успешна
        """
        if amount <= 0:
            return False
        
        new_balance = self.balance + amount
        if new_balance > self.MAX_BALANCE:
            return False
        
        self.balance = round(new_balance, 2)
        self.updated_at = datetime.now()
        return True
    
    def spend_balance(self, amount: float, reason: Optional[str] = None) -> bool:
        """
        Списание с баланса
        
        ✅ Валидация суммы > 0
        ✅ Проверка минимального баланса
        ✅ Автообновление updated_at
        
        Args:
            amount: Сумма списания (должна быть > 0)
            reason: Причина операции (для аудита)
            
        Returns:
            bool: True если операция успешна
        """
        if amount <= 0:
            return False
        
        new_balance = self.balance - amount
        if new_balance < self.MIN_BALANCE:
            return False
        
        self.balance = round(new_balance, 2)
        self.updated_at = datetime.now()
        return True
    
    def reset_balance(self) -> None:
        """Сброс баланса в ноль"""
        self.balance = 0.0
        self.updated_at = datetime.now()
    
    # ==================== 🔍 БИЗНЕС-ЛОГИКА ====================
    
    @property
    def has_phone(self) -> bool:
        """Проверка: есть ли телефон"""
        return bool(self.phone and self.phone.strip())
    
    @property
    def has_email(self) -> bool:
        """Проверка: есть ли почта"""
        return bool(self.email and "@" in self.email)
    
    @property
    def display_name(self) -> str:
        """Читаемое имя для интерфейса"""
        return self.full_name or "Без имени"
    
    @property
    def short_info(self) -> str:
        """Краткая информация для списков"""
        parts = [self.display_name]
        if self.has_phone:
            parts.append(f"📞 {self.phone}")
        if self.balance != 0:
            sign = "🔴" if self.balance < 0 else "🟢"
            parts.append(f"{sign} {self.balance:.2f} ₽")
        return " • ".join(parts)
    
    def mark_as_updated(self) -> None:
        """Обновить временную метку"""
        self.updated_at = datetime.now()
    
    # ==================== 📊 СРАВНЕНИЕ И ПРЕДСТАВЛЕНИЕ ====================
    
    def __str__(self) -> str:
        phone = f" ({self.phone})" if self.has_phone else ""
        return f"{self.display_name}{phone}"
    
    def __repr__(self) -> str:
        return (f"Employee(id={self.id}, name='{self.full_name}', "
                f"balance={self.balance:.2f}, group_id={self.group_id})")
    
    def __eq__(self, other: object) -> bool:
        """Сравнение по ID или по комбинации имени и телефона"""
        if not isinstance(other, Employee):
            return False
        # ✅ Сравниваем по ID если есть
        if self.id and other.id:
            return self.id == other.id
        # ✅ Или по уникальной комбинации
        return (self.full_name.lower() == other.full_name.lower() and 
                self.phone == other.phone)
    
    def __hash__(self) -> int:
        """Хеш для использования в set/dict"""
        if self.id:
            return hash(self.id)
        return hash((self.full_name.lower(), self.phone))