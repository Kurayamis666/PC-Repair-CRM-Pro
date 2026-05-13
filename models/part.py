# models/part.py
"""
Модель запчасти/номенклатуры для PC Repair CRM Pro

✅ Типобезопасные поля с аннотациями
✅ Валидация стоимости и остатков в __post_init__
✅ Автоматический парсинг дат и категорий из БД
✅ Безопасное приведение типов в from_row()
✅ Готовность к JSON-сериализации через to_dict()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class PartCategory(Enum):
    """Категории запчастей"""
    COMPONENT = "component"      # Компоненты (материнские платы, экраны)
    CONSUMABLE = "consumable"    # Расходники (паста, термопрокладки)
    ACCESSORY = "accessory"      # Аксессуары (чехлы, кабели)
    SERVICE = "service"          # Услуги (диагностика, чистка)
    
    @property
    def display_name(self) -> str:
        """Читаемое название для интерфейса"""
        return {
            PartCategory.COMPONENT: "Компонент",
            PartCategory.CONSUMABLE: "Расходник",
            PartCategory.ACCESSORY: "Аксессуар",
            PartCategory.SERVICE: "Услуга",
        }.get(self, self.value)


@dataclass
class Part:
    """
    Модель запчасти/номенклатуры
    
    ✅ Валидация полей в __post_init__
    ✅ Автоматический парсинг категорий и дат из БД
    ✅ Безопасные вычисления маржи и стоимости
    ✅ Сериализация без ошибок JSON
    
    Поля БД:
        - id: PRIMARY KEY AUTOINCREMENT
        - name: TEXT NOT NULL
        - sku: TEXT UNIQUE
        - quantity: INTEGER DEFAULT 0
        - cost, price: REAL (закупочная/розничная цена)
        - supplier, category, owner_type: TEXT
        - min_stock: INTEGER DEFAULT 5
        - contractor_id, type_id: FOREIGN KEY
        - created_at, updated_at: TEXT (ISO format)
    """
    
    # 🔑 Основные поля
    id: Optional[int] = None
    name: str = ""
    sku: Optional[str] = None
    quantity: int = 0
    cost: float = 0.0
    price: float = 0.0
    supplier: Optional[str] = None
    category: Optional[PartCategory] = None
    owner_type: str = "my"  # 'my' или 'client'
    min_stock: int = 5
    
    # 🔗 Внешние ключи
    contractor_id: Optional[int] = None
    type_id: Optional[int] = None
    
    # 📦 Справочные поля
    nom_type: Optional[str] = None
    unit: Optional[str] = "шт"
    
    # 📅 Даты
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 📦 JOIN-поля (не сохраняются в БД напрямую)
    contractor_name: Optional[str] = field(default=None, repr=False)
    
    # ⚙️ Константы валидации
    MIN_COST: float = 0.0
    MAX_COST: float = 1_000_000.0
    MIN_QUANTITY: int = 0
    MAX_QUANTITY: int = 100_000
    
    def __post_init__(self) -> None:
        """
        Валидация и нормализация после инициализации
        
        ✅ Проверка стоимости >= 0 и <= максимума
        ✅ Проверка количества >= 0
        ✅ Автообновление updated_at при изменении
        """
        # ✅ Валидация стоимости
        self.cost = self._validate_cost(self.cost, "cost")
        self.price = self._validate_cost(self.price, "price")
        
        # ✅ Валидация количества
        if self.quantity < self.MIN_QUANTITY:
            self.quantity = self.MIN_QUANTITY
        if self.quantity > self.MAX_QUANTITY:
            self.quantity = self.MAX_QUANTITY
        
        # ✅ Нормализация строк
        if self.name:
            self.name = self.name.strip()
        if self.sku:
            self.sku = self.sku.strip().upper()
        if self.unit:
            self.unit = self.unit.strip()
    
    def _validate_cost(self, value: float, field_name: str) -> float:
        """Валидация стоимости"""
        if value < self.MIN_COST:
            return self.MIN_COST
        if value > self.MAX_COST:
            return self.MAX_COST
        return round(float(value), 2)
    
    # ==================== 🔄 КОНВЕРТАЦИЯ ====================
    
    @classmethod
    def from_row(cls, row: Optional[Dict[str, Any]]) -> "Part":
        """
        Создание экземпляра из строки базы данных
        
        ✅ Безопасная обработка None
        ✅ Парсинг datetime из строки БД
        ✅ Конвертация категории из строки в PartCategory
        
        Args:
            row: Словарь с данными из БД (или None)
            
        Returns:
            Part: Новый экземпляр или пустая запчасть если row=None
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
        
        # ✅ Конвертация категории
        category_val = row.get("category")
        category = None
        if category_val:
            try:
                category = PartCategory(category_val)
            except ValueError:
                category = None
        
        # ✅ Безопасное чтение числовых полей
        def safe_int(val: Any, default: int = 0) -> int:
            try:
                return int(val) if val is not None else default
            except (ValueError, TypeError):
                return default
        
        def safe_float(val: Any, default: float = 0.0) -> float:
            try:
                return float(val) if val is not None else default
            except (ValueError, TypeError):
                return default
        
        return cls(
            id=row.get("id"),
            name=row.get("name", ""),
            sku=row.get("sku"),
            quantity=safe_int(row.get("quantity"), 0),
            cost=safe_float(row.get("cost"), 0.0),
            price=safe_float(row.get("price"), 0.0),
            supplier=row.get("supplier"),
            category=category,
            owner_type=row.get("owner_type", "my"),
            min_stock=safe_int(row.get("min_stock"), 5),
            contractor_id=row.get("contractor_id"),
            type_id=row.get("type_id"),
            nom_type=row.get("nom_type"),
            unit=row.get("unit", "шт"),
            created_at=parse_date(row.get("created_at")),
            updated_at=parse_date(row.get("updated_at")),
            contractor_name=row.get("contractor_name"),
        )
    
    def to_dict(self, include_meta: bool = True) -> Dict[str, Any]:
        """
        Сериализация в словарь (JSON-safe)
        
        ✅ Конвертация datetime → ISO string
        ✅ Опциональное включение мета-данных
        
        Args:
            include_meta: Включать ли contractor_name и т.д.
            
        Returns:
            Dict[str, Any]: Словарь, готовый к json.dumps()
        """
        def to_iso(dt: Optional[datetime]) -> Optional[str]:
            return dt.isoformat() if dt else None
        
        data = {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "quantity": self.quantity,
            "cost": self.cost,
            "price": self.price,
            "supplier": self.supplier,
            "category": self.category.value if self.category else None,
            "owner_type": self.owner_type,
            "min_stock": self.min_stock,
            "contractor_id": self.contractor_id,
            "type_id": self.type_id,
            "nom_type": self.nom_type,
            "unit": self.unit,
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
        }
        
        if include_meta:
            data["contractor_name"] = self.contractor_name
            data["is_low_stock"] = self.is_low_stock
            data["is_out_of_stock"] = self.is_out_of_stock
            data["profit_margin"] = round(self.profit_margin, 2)
            data["total_value"] = self.total_stock_value
            
        return data
    
    # ==================== 📊 БИЗНЕС-ЛОГИКА ====================
    
    @property
    def is_low_stock(self) -> bool:
        """Проверка: низкий остаток (0 < qty <= min_stock)"""
        return 0 < self.quantity <= self.min_stock
    
    @property
    def is_out_of_stock(self) -> bool:
        """Проверка: нет в наличии"""
        return self.quantity <= 0
    
    @property
    def profit_margin(self) -> float:
        """Маржа прибыли в процентах"""
        if self.cost <= 0:
            return 0.0
        return ((self.price - self.cost) / self.cost) * 100
    
    @property
    def markup(self) -> float:
        """Наценка в процентах (альтернативное название)"""
        return self.profit_margin
    
    @property
    def total_stock_value(self) -> float:
        """Общая стоимость запаса на складе"""
        return round(self.quantity * self.cost, 2)
    
    @property
    def potential_revenue(self) -> float:
        """Потенциальная выручка при продаже всего запаса"""
        return round(self.quantity * self.price, 2)
    
    def update_quantity(self, delta: int, reason: Optional[str] = None) -> bool:
        """
        Безопасное изменение количества
        
        ✅ Не позволяет уйти в минус
        ✅ Автообновление updated_at
        ✅ Логирование причины изменения
        
        Args:
            delta: Изменение количества (+ для прихода, - для расхода)
            reason: Причина изменения (для аудита)
            
        Returns:
            bool: True если изменение успешно
        """
        new_qty = self.quantity + delta
        if new_qty < 0:
            return False
        
        self.quantity = new_qty
        self.updated_at = datetime.now()
        return True
    
    def needs_reorder(self) -> bool:
        """Проверка: нужно ли заказать ещё"""
        return self.quantity <= self.min_stock
    
    def suggested_reorder_qty(self, multiplier: float = 2.0) -> int:
        """
        Рекомендуемое количество для заказа
        
        Args:
            multiplier: Коэффициент запаса (по умолчанию 2.0)
            
        Returns:
            int: Рекомендуемое количество для заказа
        """
        if self.quantity > self.min_stock:
            return 0
        return max(0, int((self.min_stock * multiplier) - self.quantity))
    
    # ==================== 📝 ПРЕДСТАВЛЕНИЕ ====================
    
    def __str__(self) -> str:
        status = "🔴" if self.is_out_of_stock else "🟡" if self.is_low_stock else "🟢"
        return f"{status} {self.name} ({self.sku}) — {self.quantity} {self.unit or 'шт'}"
    
    def __repr__(self) -> str:
        return (f"Part(id={self.id}, name='{self.name}', sku='{self.sku}', "
                f"qty={self.quantity}, cost={self.cost:.2f}, price={self.price:.2f})")
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Part):
            return False
        return self.id is not None and other.id is not None and self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id) if self.id else hash((self.sku, self.name))