# models/equipment.py
"""
Модель оборудования клиента для PC Repair CRM Pro

✅ Типобезопасные поля с аннотациями
✅ Валидация и нормализация в __post_init__
✅ Автоматический парсинг дат из БД
✅ Безопасная сериализация без чувствительных данных
✅ Бизнес-логика для проверки полей
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


# ==================== 🎯 ТИПЫ УСТРОЙСТВ ====================

class EquipmentType(Enum):
    """Типы оборудования с отображаемыми названиями"""
    LAPTOP = "Laptop"
    PC = "PC"
    TABLET = "Tablet"
    PHONE = "Phone"
    MONITOR = "Monitor"
    PRINTER = "Printer"
    ACCESSORY = "Accessory"
    OTHER = "Other"
    
    @property
    def display_name(self) -> str:
        """Читаемое название для интерфейса"""
        return {
            EquipmentType.LAPTOP: "💻 Ноутбук",
            EquipmentType.PC: "🖥️ ПК",
            EquipmentType.TABLET: "📱 Планшет",
            EquipmentType.PHONE: "📞 Телефон",
            EquipmentType.MONITOR: "🖥️ Монитор",
            EquipmentType.PRINTER: "🖨️ Принтер",
            EquipmentType.ACCESSORY: "🔌 Аксессуар",
            EquipmentType.OTHER: "📦 Другое",
        }.get(self, self.value)
    
    @classmethod
    def from_string(cls, value: Optional[str]) -> Optional["EquipmentType"]:
        """Безопасная конвертация строки в Enum"""
        if not value:
            return None
        try:
            return cls(value)
        except ValueError:
            return None


# ==================== 🔧 МОДЕЛЬ ОБОРУДОВАНИЯ ====================

@dataclass
class Equipment:
    """
    Модель оборудования клиента
    
    ✅ Валидация полей в __post_init__
    ✅ Автоматический парсинг дат из строк БД
    ✅ Исключение чувствительных данных из сериализации
    ✅ Бизнес-логика для проверки полей
    
    Поля БД:
        - id: PRIMARY KEY AUTOINCREMENT
        - client_id: FOREIGN KEY -> employees(id)
        - model: TEXT NOT NULL
        - serial_number: TEXT
        - device_type: TEXT CHECK(device_type IN ('Laptop', 'PC', ...))
        - color, imei, password: TEXT (чувствительные данные)
        - accessories, external_damage: TEXT
        - created_at, updated_at: TEXT (ISO format)
    """
    
    # 🔑 Основные поля
    id: Optional[int] = None
    client_id: Optional[int] = None  # ✅ Ссылка на сотрудника (не клиента!)
    model: str = ""
    serial_number: Optional[str] = None
    device_type: Optional[EquipmentType] = None
    color: Optional[str] = None
    imei: Optional[str] = None
    password: Optional[str] = field(default=None, repr=False)  # 🔐 Чувствительные данные
    accessories: Optional[str] = None
    external_damage: Optional[str] = None
    
    # 📅 Даты
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 📦 JOIN-поля (не сохраняются в БД напрямую)
    client_name: Optional[str] = field(default=None, repr=False)
    
    # ⚙️ Константы валидации
    MAX_MODEL_LENGTH: int = 100
    MAX_SERIAL_LENGTH: int = 100
    MAX_IMEI_LENGTH: int = 20
    
    def __post_init__(self) -> None:
        """
        Валидация и нормализация после инициализации
        
        ✅ Обрезка и очистка строк
        ✅ Конвертация device_type из строки в Enum
        """
        # ✅ Нормализация model
        if self.model:
            self.model = self.model.strip()[:self.MAX_MODEL_LENGTH]
        
        # ✅ Нормализация serial_number
        if self.serial_number:
            self.serial_number = self.serial_number.strip()[:self.MAX_SERIAL_LENGTH]
        
        # ✅ Нормализация IMEI (только цифры и дефисы)
        if self.imei:
            cleaned = "".join(c for c in self.imei.strip() if c.isdigit() or c in "-")
            self.imei = cleaned[:self.MAX_IMEI_LENGTH]
        
        # ✅ Конвертация device_type из строки если нужно
        if isinstance(self.device_type, str):
            self.device_type = EquipmentType.from_string(self.device_type)
    
    # ==================== 🔄 КОНВЕРТАЦИЯ ====================
    
    @classmethod
    def from_row(cls, row: Optional[Dict[str, Any]]) -> "Equipment":
        """
        Создание экземпляра из строки базы данных
        
        ✅ Безопасная обработка None
        ✅ Парсинг datetime из строки БД
        ✅ Конвертация device_type из строки в Enum
        
        Args:
            row: Словарь с данными из БД (или None)
            
        Returns:
            Equipment: Новый экземпляр или пустое оборудование если row=None
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
        
        # ✅ Конвертация device_type
        device_type_val = row.get("device_type")
        device_type = EquipmentType.from_string(device_type_val) if device_type_val else None
        
        return cls(
            id=row.get("id"),
            client_id=row.get("client_id"),
            model=row.get("model", ""),
            serial_number=row.get("serial_number"),
            device_type=device_type,
            color=row.get("color"),
            imei=row.get("imei"),
            password=row.get("password"),  # 🔐 Не показывать в repr благодаря field(repr=False)
            accessories=row.get("accessories"),
            external_damage=row.get("external_damage"),
            created_at=parse_date(row.get("created_at")),
            updated_at=parse_date(row.get("updated_at")),
            client_name=row.get("client_name"),
        )
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Сериализация в словарь (JSON-safe)
        
        ✅ По умолчанию исключает password и другие чувствительные данные
        ✅ Конвертация datetime → ISO string
        
        Args:
            include_sensitive: Включать ли пароль и другие чувствительные поля
            
        Returns:
            Dict[str, Any]: Словарь, готовый к json.dumps()
        """
        def to_iso(dt: Optional[datetime]) -> Optional[str]:
            return dt.isoformat() if dt else None
        
        data = {
            "id": self.id,
            "client_id": self.client_id,
            "model": self.model,
            "serial_number": self.serial_number,
            "device_type": self.device_type.value if self.device_type else None,
            "color": self.color,
            "imei": self.imei,
            "accessories": self.accessories,
            "external_damage": self.external_damage,
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
            "client_name": self.client_name,
        }
        
        # 🔐 Чувствительные данные только по явному запросу
        if include_sensitive:
            data["password"] = self.password
        
        return data
    
    # ==================== 🔍 БИЗНЕС-ЛОГИКА ====================
    
    @property
    def has_serial(self) -> bool:
        """Проверка: есть ли серийный номер"""
        return bool(self.serial_number and self.serial_number.strip())
    
    @property
    def has_imei(self) -> bool:
        """Проверка: есть ли IMEI"""
        return bool(self.imei and self.imei.strip())
    
    @property
    def has_password(self) -> bool:
        """Проверка: задан ли пароль устройства"""
        return bool(self.password and self.password.strip())
    
    @property
    def is_phone_or_tablet(self) -> bool:
        """Проверка: мобильное устройство (телефон или планшет)"""
        return self.device_type in (EquipmentType.PHONE, EquipmentType.TABLET)
    
    @property
    def is_laptop_or_pc(self) -> bool:
        """Проверка: компьютер (ноутбук или ПК)"""
        return self.device_type in (EquipmentType.LAPTOP, EquipmentType.PC)
    
    @property
    def display_name(self) -> str:
        """Читаемое название для интерфейса"""
        type_prefix = self.device_type.display_name if self.device_type else "📦 Устройство"
        return f"{type_prefix}: {self.model}"
    
    @property
    def short_description(self) -> str:
        """Краткое описание для списков"""
        parts = [self.model]
        if self.has_serial:
            parts.append(f"SN:{self.serial_number[:10]}")
        if self.color:
            parts.append(self.color)
        return " • ".join(parts)
    
    def mark_as_updated(self) -> None:
        """Обновить временную метку"""
        self.updated_at = datetime.now()
    
    # ==================== 📊 СРАВНЕНИЕ И ПРЕДСТАВЛЕНИЕ ====================
    
    def __str__(self) -> str:
        type_icon = self.device_type.display_name.split()[0] if self.device_type else "📦"
        serial = f" ({self.serial_number})" if self.has_serial else ""
        return f"{type_icon} {self.model}{serial}"
    
    def __repr__(self) -> str:
        return (f"Equipment(id={self.id}, model='{self.model}', "
                f"client_id={self.client_id}, type={self.device_type.value if self.device_type else None})")
    
    def __eq__(self, other: object) -> bool:
        """Сравнение по ID или по комбинации client_id + serial_number"""
        if not isinstance(other, Equipment):
            return False
        # ✅ Сравниваем по ID если есть
        if self.id and other.id:
            return self.id == other.id
        # ✅ Или по уникальной комбинации
        return (self.client_id == other.client_id and 
                self.serial_number == other.serial_number and
                self.model == other.model)
    
    def __hash__(self) -> int:
        """Хеш для использования в set/dict"""
        if self.id:
            return hash(self.id)
        return hash((self.client_id, self.serial_number, self.model))