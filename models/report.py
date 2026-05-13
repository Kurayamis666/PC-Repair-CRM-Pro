# models/report.py
"""
Модели для отчётов и статистики для PC Repair CRM Pro

✅ Синхронизировано с заменой clients → employees
✅ Автоматический парсинг JSON из SQLite в dict
✅ Валидация дат и типов в __post_init__
✅ Готовность к JSON-сериализации для API и UI
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum


# ==================== 📊 ТИПЫ ОТЧЁТОВ ====================

class ReportType(Enum):
    """Типы отчётов с отображаемыми названиями для UI"""
    DASHBOARD = "dashboard"
    FINANCIAL = "financial"
    INVENTORY = "inventory"
    EMPLOYEE_ACTIVITY = "employee_activity"  # ✅ Было: client_activity
    TECHNICIAN_PERFORMANCE = "technician_performance"
    
    @property
    def display_name(self) -> str:
        """Читаемое название для интерфейса"""
        return {
            ReportType.DASHBOARD: "Дашборд",
            ReportType.FINANCIAL: "Финансы",
            ReportType.INVENTORY: "Склад/Запасы",
            ReportType.EMPLOYEE_ACTIVITY: "Активность сотрудников",
            ReportType.TECHNICIAN_PERFORMANCE: "Эффективность мастеров",
        }.get(self, self.value.replace("_", " ").title())
    
    @property
    def is_cacheable(self) -> bool:
        """Можно ли кэшировать этот тип отчёта"""
        return self in (ReportType.DASHBOARD, ReportType.INVENTORY)


# ==================== 📈 СТАТИСТИКА ДАШБОРДА ====================

@dataclass
class DashboardStats:
    """
    Статистика для главной панели
    
    ✅ Синхронизировано с ReportService.get_dashboard_stats()
    ✅ JSON-safe сериализация
    """
    total_requests: int = 0
    active_requests: int = 0
    completed_requests: int = 0
    total_costs: float = 0.0
    low_stock_parts: int = 0
    new_employees_this_month: int = 0  # ✅ Синхронизировано с проектом
    revenue_this_month: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь для передачи в UI или API"""
        return {
            "total_requests": self.total_requests,
            "active_requests": self.active_requests,
            "completed_requests": self.completed_requests,
            "total_costs": round(self.total_costs, 2),
            "low_stock_parts": self.low_stock_parts,
            "new_employees_this_month": self.new_employees_this_month,
            "revenue_this_month": round(self.revenue_this_month, 2),
        }
    
    def is_empty(self) -> bool:
        """Проверка: все метрики равны нулю"""
        return all(v == 0 for v in self.to_dict().values())


# ==================== 📄 МОДЕЛЬ ОТЧЁТА ====================

@dataclass
class Report:
    """
    Модель отчёта с поддержкой JSON-хранения в SQLite
    
    ✅ Автоматический парсинг JSON-строк в dict при загрузке из БД
    ✅ Валидация полей в __post_init__
    ✅ Готовность к экспорту и кешированию
    """
    id: Optional[int] = None
    report_type: ReportType = ReportType.DASHBOARD
    title: str = ""
    description: Optional[str] = None
    generated_by: Optional[int] = None
    generated_at: str = ""  # Заполняется в __post_init__
    parameters: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """
        Валидация и нормализация после инициализации
        
        ✅ Установка generated_at если не задан
        ✅ Парсинг JSON из строк (при загрузке из БД)
        """
        # ✅ Установка времени генерации
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()
            
        # ✅ Парсинг JSON если данные пришли из БД как строки
        if isinstance(self.parameters, str):
            try:
                self.parameters = json.loads(self.parameters)
            except json.JSONDecodeError:
                self.parameters = {}
                
        if isinstance(self.data, str):
            try:
                self.data = json.loads(self.data)
            except json.JSONDecodeError:
                self.data = {}
    
    # ==================== 🔄 КОНВЕРТАЦИЯ ====================
    
    @classmethod
    def from_row(cls, row: Optional[Dict[str, Any]]) -> "Report":
        """
        Создание экземпляра из строки базы данных
        
        ✅ Безопасная обработка None
        ✅ Конвертация enum из строки
        ✅ Автоматический парсинг JSON через __post_init__
        """
        if not row:
            return cls()
        
        # ✅ Конвертация типа отчёта
        type_val = row.get("report_type")
        try:
            report_type = ReportType(type_val) if type_val else ReportType.DASHBOARD
        except ValueError:
            report_type = ReportType.DASHBOARD
        
        return cls(
            id=row.get("id"),
            report_type=report_type,
            title=row.get("title", ""),
            description=row.get("description"),
            generated_by=row.get("generated_by"),
            generated_at=row.get("generated_at"),
            parameters=row.get("parameters", {}),  # Будет распарсен в __post_init__
            data=row.get("data", {}),               # Будет распарсен в __post_init__
        )
    
    def to_dict(self, include_data: bool = True) -> Dict[str, Any]:
        """
        Сериализация в словарь (JSON-safe)
        
        Args:
            include_data: Включать ли тяжёлое поле data (по умолчанию True)
            
        Returns:
            Dict[str, Any]: Словарь, готовый к json.dumps()
        """
        result = {
            "id": self.id,
            "report_type": self.report_type.value,
            "title": self.title,
            "description": self.description,
            "generated_by": self.generated_by,
            "generated_at": self.generated_at,
            "parameters": self.parameters,
        }
        if include_data:
            result["data"] = self.data
        return result
    
    def to_json(self, pretty: bool = True) -> str:
        """Экспорт в JSON строку"""
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    # ==================== 📊 УТИЛИТЫ ====================
    
    def set_parameters(self, **kwargs) -> None:
        """Безопасное обновление параметров отчёта"""
        self.parameters.update(kwargs)
    
    def mark_as_exported(self, exported_to: str) -> None:
        """Отметить отчёт как экспортированный"""
        self.data.setdefault("_metadata", {})["exported_to"] = exported_to
        self.data["_metadata"]["exported_at"] = datetime.now(timezone.utc).isoformat()
    
    def is_generated_today(self) -> bool:
        """Проверка: отчёт сгенерирован сегодня"""
        if not self.generated_at:
            return False
        try:
            gen_date = datetime.fromisoformat(self.generated_at).date()
            return gen_date == datetime.now(timezone.utc).date()
        except ValueError:
            return False
    
    # ==================== 📝 ПРЕДСТАВЛЕНИЕ ====================
    
    def __str__(self) -> str:
        return f"{self.title or self.report_type.display_name} ({self.generated_at[:10]})"
    
    def __repr__(self) -> str:
        return (f"Report(id={self.id}, type={self.report_type.value}, "
                f"title='{self.title}', generated='{self.generated_at[:19]}')")
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Report):
            return False
        return self.id is not None and other.id is not None and self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id) if self.id else hash(self.generated_at)