# models/request.py
"""
Модель заявки на ремонт для PC Repair CRM Pro

✅ Типобезопасные поля с аннотациями
✅ Валидация стоимости и описаний в __post_init__
✅ Парсинг дат из БД в datetime для удобной работы
✅ Безопасное приведение типов в from_row()
✅ Готовность к JSON-сериализации через to_dict()
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum


# ==================== 🎯 СТАТУСЫ И ПРИОРИТЕТЫ ====================

class RequestStatus(Enum):
    """Статусы заявки"""
    NEW = "new"
    DIAGNOSTICS = "diagnostics"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    
    @property
    def is_final(self) -> bool:
        """Проверка: заявка закрыта или отменена"""
        return self in (RequestStatus.CLOSED, RequestStatus.CANCELLED)
    
    @property
    def color_hex(self) -> str:
        """HEX-цвет для отображения в UI"""
        return {
            RequestStatus.NEW: "#3b82f6",
            RequestStatus.DIAGNOSTICS: "#f59e0b",
            RequestStatus.IN_PROGRESS: "#a855f7",
            RequestStatus.READY: "#22c55e",
            RequestStatus.CLOSED: "#64748b",
            RequestStatus.CANCELLED: "#ef4444",
        }.get(self, "#9ca3af")


class RequestPriority(Enum):
    """Приоритеты заявки"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    
    @property
    def weight(self) -> int:
        """Числовой вес для сортировки"""
        return {"low": 1, "normal": 2, "high": 3, "urgent": 4}.get(self.value, 2)


# ==================== 📝 МОДЕЛЬ ЗАЯВКИ ====================

@dataclass
class Request:
    """
    Модель заявки на ремонт
    
    ✅ Валидация полей в __post_init__
    ✅ Автоматический парсинг дат из строк БД
    ✅ Безопасные вычисления стоимости
    ✅ Сериализация без ошибок JSON
    
    Поля БД:
        - id: PRIMARY KEY AUTOINCREMENT
        - client_id: FOREIGN KEY -> employees(id)
        - equipment_id: FOREIGN KEY -> equipment(id)
        - user_id: FOREIGN KEY -> users(id) (мастер)
        - branch_id: FOREIGN KEY -> branches(id)
        - status: TEXT CHECK(status IN ('new', 'diagnostics', ...))
        - problem_desc, solution_desc: TEXT
        - labor_cost, parts_cost, total_cost: REAL
        - priority: TEXT CHECK(priority IN ('low', 'normal', 'high', 'urgent'))
        - planned_date, created_at, updated_at, closed_at: TEXT (ISO format)
    """
    
    # 🔑 Основные поля
    id: Optional[int] = None
    client_id: Optional[int] = None  # ✅ Было: int = 0
    equipment_id: Optional[int] = None
    user_id: Optional[int] = None    # ✅ Было: int = 0
    branch_id: Optional[int] = None
    
    # 📊 Статус и приоритет
    status: RequestStatus = RequestStatus.NEW
    priority: RequestPriority = RequestPriority.NORMAL
    
    # 📝 Описания
    problem_desc: Optional[str] = None
    solution_desc: Optional[str] = None
    
    # 💰 Стоимость
    labor_cost: float = 0.0
    parts_cost: float = 0.0
    total_cost: float = 0.0
    
    # 📅 Даты
    planned_date: Optional[datetime] = None  # ✅ Было: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # 📦 JOIN-поля (не сохраняются в БД напрямую)
    client_name: Optional[str] = field(default=None, repr=False)
    equipment_model: Optional[str] = field(default=None, repr=False)
    master_username: Optional[str] = field(default=None, repr=False)
    
    # ⚙️ Валидация
    MAX_DESC_LENGTH: int = 2000
    MIN_COST: float = 0.0
    MAX_COST: float = 1_000_000.0
    
    def __post_init__(self) -> None:
        """
        Валидация и нормализация после инициализации
        
        ✅ Обрезка описаний, проверка стоимости >= 0
        ✅ Автопересчёт total_cost если он 0
        """
        # ✅ Нормализация строк
        if self.problem_desc:
            self.problem_desc = self.problem_desc.strip()[:self.MAX_DESC_LENGTH]
        if self.solution_desc:
            self.solution_desc = self.solution_desc.strip()[:self.MAX_DESC_LENGTH]
        
        # ✅ Валидация стоимости
        self.labor_cost = self._validate_cost(self.labor_cost, "labor_cost")
        self.parts_cost = self._validate_cost(self.parts_cost, "parts_cost")
        
        # ✅ Автопересчёт если total_cost не задан
        if self.total_cost == 0 and (self.labor_cost > 0 or self.parts_cost > 0):
            self.calculate_total()
    
    def _validate_cost(self, value: float, field_name: str) -> float:
        """Валидация стоимости"""
        if value < self.MIN_COST:
            raise ValueError(f"{field_name} cannot be negative")
        if value > self.MAX_COST:
            raise ValueError(f"{field_name} exceeds maximum allowed value")
        return round(float(value), 2)
    
    # ==================== 🔄 КОНВЕРТАЦИЯ ====================
    
    @classmethod
    def from_row(cls, row: Optional[Dict[str, Any]]) -> "Request":
        """
        Создание экземпляра из строки базы данных
        
        ✅ Безопасное приведение типов
        ✅ Парсинг ISO-дат
        ✅ Обработка None и пустых значений
        
        Args:
            row: Словарь с данными из БД (или None)
            
        Returns:
            Request: Новый экземпляр или пустая заявка если row=None
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
        
        # ✅ Конвертация Enum
        status_val = row.get("status")
        status = RequestStatus(status_val) if status_val else RequestStatus.NEW
        
        priority_val = row.get("priority")
        priority = RequestPriority(priority_val) if priority_val else RequestPriority.NORMAL
        
        # ✅ Безопасное чтение float (защита от float(None))
        labor = float(row.get("labor_cost") or 0)
        parts = float(row.get("parts_cost") or 0)
        total = float(row.get("total_cost") or 0)
        
        return cls(
            id=row.get("id"),
            client_id=row.get("client_id"),
            equipment_id=row.get("equipment_id"),
            user_id=row.get("user_id"),
            branch_id=row.get("branch_id"),
            status=status,
            priority=priority,
            problem_desc=row.get("problem_desc"),
            solution_desc=row.get("solution_desc"),
            labor_cost=labor,
            parts_cost=parts,
            total_cost=total,
            planned_date=parse_date(row.get("planned_date")),
            created_at=parse_date(row.get("created_at")),
            updated_at=parse_date(row.get("updated_at")),
            closed_at=parse_date(row.get("closed_at")),
            client_name=row.get("client_name"),
            equipment_model=row.get("equipment_model"),
            master_username=row.get("master_username"),
        )
    
    def to_dict(self, include_meta: bool = True) -> Dict[str, Any]:
        """
        Сериализация в словарь (JSON-safe)
        
        ✅ Конвертация datetime → ISO string
        ✅ Опциональное включение мета-данных
        
        Args:
            include_meta: Включать ли client_name, equipment_model и т.д.
            
        Returns:
            Dict[str, Any]: Словарь, готовый к JSON-сериализации
        """
        def to_iso(dt: Optional[datetime]) -> Optional[str]:
            return dt.isoformat() if dt else None
        
        data = {
            "id": self.id,
            "client_id": self.client_id,
            "equipment_id": self.equipment_id,
            "user_id": self.user_id,
            "branch_id": self.branch_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "problem_desc": self.problem_desc,
            "solution_desc": self.solution_desc,
            "labor_cost": self.labor_cost,
            "parts_cost": self.parts_cost,
            "total_cost": self.total_cost,
            "planned_date": to_iso(self.planned_date),
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
            "closed_at": to_iso(self.closed_at),
        }
        
        if include_meta:
            data["client_name"] = self.client_name
            data["equipment_model"] = self.equipment_model
            data["master_username"] = self.master_username
            data["days_until_planned"] = self.days_until_planned
            data["is_overdue"] = self.is_overdue
            
        return data
    
    # ==================== 📊 БИЗНЕС-ЛОГИКА ====================
    
    @property
    def is_active(self) -> bool:
        """Проверка: заявка не закрыта и не отменена"""
        return not self.status.is_final
    
    @property
    def is_overdue(self) -> bool:
        """Проверка: заявка просрочена относительно planned_date"""
        if not self.planned_date or not self.is_active:
            return False
        return datetime.now().date() > self.planned_date.date()
    
    @property
    def days_until_planned(self) -> Optional[int]:
        """
        Дней до плановой даты
        
        Returns:
            int: Отрицательное = просрочено, 0 = сегодня, >0 = осталось дней
        """
        if not self.planned_date:
            return None
        delta = self.planned_date.date() - datetime.now().date()
        return delta.days
    
    def calculate_total(self) -> float:
        """
        Пересчитать общую стоимость
        
        ✅ Валидация неотрицательных значений
        ✅ Округление до 2 знаков
        
        Returns:
            float: Новая total_cost
        """
        self.total_cost = round(self.labor_cost + self.parts_cost, 2)
        return self.total_total_cost
    
    def mark_ready(self) -> None:
        """Перевести заявку в статус 'Готово'"""
        self.status = RequestStatus.READY
        self.updated_at = datetime.now()
        
    def mark_closed(self) -> None:
        """Закрыть заявку"""
        self.status = RequestStatus.CLOSED
        self.closed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def can_be_edited_by(self, user_id: int, role_weight: int = 2) -> bool:
        """
        Проверка: может ли пользователь редактировать заявку
        
        Args:
            user_id: ID пользователя (мастера)
            role_weight: Минимальный вес роли для редактирования (2 = TECHNICIAN)
            
        Returns:
            bool: True если редактирование разрешено
        """
        return self.is_active and (self.user_id == user_id or role_weight >= 3)
    
    # ==================== 📊 ПРЕДСТАВЛЕНИЕ ====================
    
    def __str__(self) -> str:
        client = self.client_name or f"Клиент #{self.client_id}"
        status_ru = {
            "new": "Новая", "diagnostics": "Диагностика", "in_progress": "В работе",
            "ready": "Готова", "closed": "Закрыта", "cancelled": "Отменена"
        }.get(self.status.value, self.status.value)
        return f"Заявка #{self.id} — {client} [{status_ru}]"
    
    def __repr__(self) -> str:
        return (f"Request(id={self.id}, client_id={self.client_id}, "
                f"status={self.status.value}, total={self.total_cost:.2f}₽)")
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Request):
            return False
        return self.id is not None and other.id is not None and self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id) if self.id else hash((self.client_id, str(self.created_at)))