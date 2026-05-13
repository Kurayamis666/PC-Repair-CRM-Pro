# services/stock_service.py
"""
Сервис управления запасами для PC Repair CRM Pro

✅ Автоматическое списание при закрытии заявок
✅ Контроль уровней остатков с предупреждениями
✅ Прогнозирование потребности и предложения к заказу
✅ Экспорт отчётов в CSV/JSON
✅ Полная типизация и обработка ошибок
"""

import csv
import io
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict

from core.logger import app_logger
from database.connection import DatabaseConnection
from database.repositories.part_repo import PartRepository
from models.part import Part, PartCategory


# ==================== 🎯 ТИПЫ И КОНСТАНТЫ ====================

class StockAlertLevel(Enum):
    """Уровни предупреждений о запасах"""
    OK = "ok"
    LOW = "low"              # quantity <= min_stock
    CRITICAL = "critical"    # quantity <= min_stock * 0.5
    OUT = "out"              # quantity == 0


class ReorderPriority(Enum):
    """Приоритет заказа"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# 🔧 Конфигурационные константы сервиса
@dataclass
class StockServiceConfig:
    """Конфигурация сервиса управления запасами"""
    # Пороги для уровней предупреждений
    critical_threshold: float = 0.5      # quantity <= min_stock * 0.5 → CRITICAL
    low_threshold: float = 1.0           # quantity <= min_stock → LOW
    
    # Параметры прогнозирования
    default_lead_time_days: int = 7      # Стандартный срок поставки
    safety_stock_multiplier: float = 1.5 # Коэффициент страхового запаса
    
    # Эвристики для оценки расхода (заглушка)
    base_usage_consumable: float = 0.5   # Расход в день для расходников
    base_usage_cheap: float = 0.3        # Расход для запчастей < 1000₽
    base_usage_default: float = 0.05     # Расход по умолчанию
    high_stock_threshold: int = 10       # Если min_stock > 10 → удвоить базовый расход


@dataclass
class StockAlert:
    """Предупреждение о запасах"""
    part_id: int
    part_name: str
    sku: str
    current_quantity: int
    min_stock: int
    alert_level: StockAlertLevel
    recommended_order: int = 0
    supplier: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON/экспорта"""
        return {
            "part_id": self.part_id,
            "part_name": self.part_name,
            "sku": self.sku,
            "current_quantity": self.current_quantity,
            "min_stock": self.min_stock,
            "alert_level": self.alert_level.value,
            "recommended_order": self.recommended_order,
            "supplier": self.supplier,
        }


@dataclass
class ReorderSuggestion:
    """Предложение к заказу"""
    part_id: int
    part_name: str
    current_stock: int
    suggested_quantity: int
    estimated_cost: float
    priority: ReorderPriority
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON/экспорта"""
        return {
            "part_id": self.part_id,
            "part_name": self.part_name,
            "current_stock": self.current_stock,
            "suggested_quantity": self.suggested_quantity,
            "estimated_cost": round(self.estimated_cost, 2),
            "priority": self.priority.value,
            "reason": self.reason,
        }


# Тип для статистики склада
StockStats = TypedDict('StockStats', {
    'total_items': int,
    'total_quantity': int,
    'total_value': float,
})


class StockService:
    """
    Сервис управления запасами
    
    ✅ Автоматическое списание при закрытии заявок
    ✅ Контроль уровней с предупреждениями (LOW/CRITICAL/OUT)
    ✅ Прогнозирование потребности на основе эвристик
    ✅ Генерация предложений к заказу с приоритетами
    ✅ Экспорт отчётов в CSV/JSON
    
    Пример использования:
        >>> service = StockService()
        >>> # Автосписание при закрытии заявки
        >>> success, messages = service.deduct_parts_for_request(123, {45: 2, 67: 1})
        >>> 
        >>> # Проверка уровней запасов
        >>> alerts = service.check_stock_levels()
        >>> for alert in alerts:
        ...     print(f"{alert.part_name}: {alert.alert_level.value}")
    """
    
    def __init__(
        self,
        db: Optional[DatabaseConnection] = None,
        config: Optional[StockServiceConfig] = None,
    ):
        """
        Инициализация сервиса
        
        Args:
            db: Подключение к БД (по умолчанию создаётся новое)
            config: Конфигурация сервиса (по умолчанию стандартная)
        """
        self.db = db or DatabaseConnection()
        self.part_repo = PartRepository(self.db)
        self.config = config or StockServiceConfig()
        
        app_logger.info("📦 StockService initialized")
    
    # ==================== 🔄 АВТОСПИСАНИЕ ПРИ ЗАКРЫТИИ ЗАЯВКИ ====================
    
    def deduct_parts_for_request(
        self, 
        request_id: int, 
        parts_map: Dict[int, int]
    ) -> tuple[bool, List[str]]:
        """
        Автоматическое списание запчастей при закрытии заявки
        
        ✅ Атомарная операция: все списания или ни одного (транзакция)
        ✅ Возвращает список предупреждений если какие-то записи пропущены
        
        Args:
            request_id: ID заявки для закрытия
            parts_map: Словарь {part_id: quantity} — сколько какой запчасти списать
            
        Returns:
            tuple[bool, List[str]]: 
                - True если все списания успешны, False если ошибка
                - Список сообщений о предупреждениях/ошибках
        """
        warnings: List[str] = []
        
        # ✅ Валидация входных данных
        if request_id <= 0:
            error_msg = f"Invalid request_id: {request_id}"
            app_logger.error(f"❌ {error_msg}")
            return False, [error_msg]
        
        if not parts_map:
            app_logger.warning(f"⚠️ Empty parts_map for request #{request_id}")
            return True, []
        
        try:
            with self.db.get_cursor() as cur:
                for part_id, qty in parts_map.items():
                    # ✅ Валидация количества
                    if qty <= 0:
                        warnings.append(f"⚠️ Пропущено списание части #{part_id}: количество {qty} <= 0")
                        continue
                    
                    if part_id <= 0:
                        warnings.append(f"⚠️ Пропущено списание: invalid part_id {part_id}")
                        continue
                    
                    # Проверяем текущий остаток
                    cur.execute("SELECT quantity, name FROM parts WHERE id = ?", (part_id,))
                    row = cur.fetchone()
                    
                    if not row:
                        warning = f"⚠️ Запчасть ID {part_id} не найдена в базе"
                        warnings.append(warning)
                        app_logger.warning(warning)
                        continue
                    
                    current_qty, part_name = row
                    
                    if current_qty < qty:
                        error = f"❌ Недостаточно запчасти '{part_name}' (ID {part_id}). Остаток: {current_qty}, Нужно: {qty}"
                        app_logger.error(error)
                        return False, [error]  # ❌ Откатываем всю транзакцию при нехватке
                    
                    # Списываем
                    cur.execute(
                        "UPDATE parts SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (qty, part_id)
                    )
                    app_logger.info(f"📦 Списана запчасть '{part_name}' (ID {part_id}): {qty} шт.")
                
                # Обновляем статус заявки на закрытую
                cur.execute(
                    "UPDATE requests SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (request_id,)
                )
                
                app_logger.info(f"✅ Request #{request_id} closed with parts deducted")
                return True, warnings
                
        except Exception as e:
            error_msg = f"❌ Error deducting parts for request #{request_id}: {e}"
            app_logger.exception(error_msg)
            return False, [error_msg]
    
    def add_parts_stock(self, part_id: int, quantity: int, reason: Optional[str] = None) -> tuple[bool, str]:
        """
        Добавить запчасти на склад (приход)
        
        ✅ Логирование причины прихода для аудита
        
        Args:
            part_id: ID запчасти
            quantity: Количество для добавления (должно быть > 0)
            reason: Причина прихода (опционально, для лога)
            
        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        if quantity <= 0:
            msg = f"Invalid quantity: {quantity}"
            return False, msg
        
        try:
            with self.db.get_cursor() as cur:
                # Проверяем существование запчасти
                cur.execute("SELECT name FROM parts WHERE id = ?", (part_id,))
                row = cur.fetchone()
                
                if not row:
                    msg = f"Part ID {part_id} not found"
                    app_logger.warning(f"⚠️ {msg}")
                    return False, msg
                
                part_name = row[0]
                
                cur.execute(
                    "UPDATE parts SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (quantity, part_id)
                )
                
                reason_str = f" ({reason})" if reason else ""
                app_logger.info(f"📥 Приход: '{part_name}' (ID {part_id}) +{quantity} шт.{reason_str}")
                return True, f"Added {quantity} to '{part_name}'"
                
        except Exception as e:
            error_msg = f"❌ Error adding stock for part #{part_id}: {e}"
            app_logger.exception(error_msg)
            return False, error_msg
    
    # ==================== 📊 КОНТРОЛЬ УРОВНЕЙ ====================
    
    def check_stock_levels(self, threshold: Optional[int] = None) -> List[StockAlert]:
        """
        Проверка уровней запасов и генерация предупреждений
        
        ✅ Сортировка по критичности: OUT → CRITICAL → LOW
        ✅ Расчёт рекомендуемого заказа на основе min_stock
        
        Args:
            threshold: Порог min_stock для фильтрации (по умолчанию использует part.min_stock)
            
        Returns:
            List[StockAlert]: Отсортированный список предупреждений
        """
        try:
            parts = self.part_repo.get_all()
            alerts: List[StockAlert] = []
            
            for part in parts:
                # ✅ Пропускаем записи без ID
                if part.id is None:
                    app_logger.warning(f"⚠️ Part without ID skipped: {part.name}")
                    continue
                
                min_stock = threshold if threshold is not None else (part.min_stock or 0)
                qty = part.quantity or 0
                
                # ✅ Определяем уровень предупреждения
                if qty <= 0:
                    level = StockAlertLevel.OUT
                    recommended = max(min_stock * 2, 10)
                elif qty <= min_stock * self.config.critical_threshold:
                    level = StockAlertLevel.CRITICAL
                    recommended = int(min_stock * 2 - qty)
                elif qty <= min_stock * self.config.low_threshold:
                    level = StockAlertLevel.LOW
                    recommended = int(min_stock - qty)
                else:
                    continue  # ✅ Запас в норме — не создаём алерт
                
                alerts.append(StockAlert(
                    part_id=part.id,
                    part_name=part.name,
                    sku=part.sku or "",
                    current_quantity=qty,
                    min_stock=min_stock,
                    alert_level=level,
                    recommended_order=max(recommended, 1),  # ✅ Минимум 1 шт.
                    supplier=part.supplier,
                ))
            
            # ✅ Сортировка по критичности
            priority_order = {
                StockAlertLevel.OUT: 0, 
                StockAlertLevel.CRITICAL: 1, 
                StockAlertLevel.LOW: 2
            }
            alerts.sort(key=lambda x: (priority_order[x.alert_level], x.part_name))
            
            app_logger.info(f"📊 Stock check: {len(alerts)} alerts generated")
            return alerts
            
        except Exception as e:
            app_logger.exception(f"❌ Error checking stock levels: {e}")
            raise
    
    def get_low_stock_items(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Получить список запчастей с низким остатком
        
        ✅ Прямой SQL-запрос для производительности
        
        Args:
            threshold: Порог количества для фильтрации
            
        Returns:
            List[Dict]: Список словарей с данными о запчастях
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, name, sku, quantity, min_stock, supplier
                    FROM parts 
                    WHERE quantity <= min_stock AND quantity > 0
                    ORDER BY quantity ASC, name ASC
                """)
                # ✅ Конвертируем row в dict с явными ключами
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "sku": row[2],
                        "quantity": row[3],
                        "min_stock": row[4],
                        "supplier": row[5],
                    }
                    for row in cur.fetchall()
                ]
        except Exception as e:
            app_logger.exception(f"❌ Error getting low stock: {e}")
            return []
    
    def get_stock_statistics(self) -> StockStats:
        """
        Общая статистика по складу
        
        Returns:
            StockStats: Словарь с ключами total_items, total_quantity, total_value
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_items,
                        COALESCE(SUM(quantity), 0) as total_quantity,
                        COALESCE(SUM(quantity * cost), 0) as total_value
                    FROM parts
                """)
                row = cur.fetchone()
                return {
                    'total_items': row[0] or 0,
                    'total_quantity': row[1] or 0,
                    'total_value': float(row[2] or 0),
                }
        except Exception as e:
            app_logger.exception(f"❌ Error getting stats: {e}")
            return {'total_items': 0, 'total_quantity': 0, 'total_value': 0.0}
    
    # ==================== 📈 ПРОГНОЗИРОВАНИЕ И ЗАКАЗЫ ====================
    
    def calculate_reorder_point(
        self, 
        part: Part, 
        avg_daily_usage: float, 
        lead_time_days: Optional[int] = None
    ) -> int:
        """
        Расчёт точки заказа (reorder point)
        
        Формула: (avg_daily_usage * lead_time) + safety_stock
        
        Args:
            part: Объект запчасти (для min_stock)
            avg_daily_usage: Средний дневной расход
            lead_time_days: Срок поставки в днях
            
        Returns:
            int: Рекомендуемый минимальный остаток для заказа
        """
        lead_time = lead_time_days or self.config.default_lead_time_days
        lead_time_stock = avg_daily_usage * lead_time
        safety_stock = avg_daily_usage * self.config.safety_stock_multiplier
        return int(lead_time_stock + safety_stock)
    
    def generate_reorder_suggestions(self, lookback_days: int = 90) -> List[ReorderSuggestion]:
        """
        Генерация предложений к заказу на основе анализа запасов
        
        ✅ Фильтрация: только запчасти с quantity <= min_stock * 2
        ✅ Приоритет: HIGH если quantity <= min_stock, иначе MEDIUM
        ✅ Сортировка: по приоритету, затем по стоимости
        
        Args:
            lookback_days: Период для анализа истории (заглушка)
            
        Returns:
            List[ReorderSuggestion]: Отсортированный список предложений
        """
        try:
            parts = self.part_repo.get_all()
            suggestions: List[ReorderSuggestion] = []
            
            for part in parts:
                if part.id is None:
                    continue
                
                # ✅ Пропускаем запчасти с достаточным запасом
                if part.quantity and part.quantity > (part.min_stock or 0) * 2:
                    continue
                
                avg_daily_usage = self._estimate_daily_usage(part, lookback_days)
                if avg_daily_usage == 0:
                    continue
                
                reorder_point = self.calculate_reorder_point(part, avg_daily_usage)
                current_qty = part.quantity or 0
                
                if current_qty <= reorder_point:
                    # ✅ Расчёт рекомендуемого количества заказа
                    suggested_qty = max(
                        reorder_point - current_qty,
                        int(avg_daily_usage * self.config.default_lead_time_days * 2),
                        1  # ✅ Минимум 1 шт.
                    )
                    
                    # ✅ Определение приоритета
                    if current_qty <= 0:
                        priority = ReorderPriority.HIGH
                        reason = "Нет в наличии"
                    elif current_qty <= (part.min_stock or 0):
                        priority = ReorderPriority.HIGH
                        reason = "Критически низкий остаток"
                    else:
                        priority = ReorderPriority.MEDIUM
                        reason = "Ниже точки заказа"
                    
                    part_cost = part.cost or 0
                    suggestions.append(ReorderSuggestion(
                        part_id=part.id,
                        part_name=part.name,
                        current_stock=current_qty,
                        suggested_quantity=suggested_qty,
                        estimated_cost=suggested_qty * part_cost,
                        priority=priority,
                        reason=reason,
                    ))
            
            # ✅ Сортировка: приоритет → стоимость (убывание)
            priority_weight = {
                ReorderPriority.HIGH: 0, 
                ReorderPriority.MEDIUM: 1, 
                ReorderPriority.LOW: 2
            }
            suggestions.sort(key=lambda x: (priority_weight[x.priority], -x.estimated_cost))
            
            app_logger.info(f"📋 Generated {len(suggestions)} reorder suggestions")
            return suggestions
            
        except Exception as e:
            app_logger.exception(f"❌ Error generating reorder suggestions: {e}")
            raise
    
    def _estimate_daily_usage(self, part: Part, lookback_days: int) -> float:
        """
        Оценка среднего дневного расхода (ЗАГЛУШКА)
        
        ⚠️ В продакшене заменить на реальный расчёт из истории заявок:
        - Анализ закрытых заявок за lookback_days
        - Учёт сезонности и трендов
        - Машинное обучение для прогнозирования
        
        Текущая эвристика:
        - Расходники: 0.5 шт./день
        - Дешёвые запчасти (<1000₽): 0.3 шт./день
        - Остальные: 0.05 шт./день
        - Если min_stock > 10: удвоить базовый расход
        """
        # ✅ Используем константы из конфига
        if part.category == PartCategory.CONSUMABLE:
            base_usage = self.config.base_usage_consumable
        elif part.price and part.price < 1000:
            base_usage = self.config.base_usage_cheap
        else:
            base_usage = self.config.base_usage_default
        
        # ✅ Коррекция для запчастей с высоким min_stock
        if (part.min_stock or 0) > self.config.high_stock_threshold:
            base_usage *= 2
        
        return base_usage
    
    def get_stock_forecast(self, part_id: int, forecast_days: int = 30) -> Dict[str, Any]:
        """
        Прогноз уровня запаса на заданный период
        
        ✅ Возвращает структурированный прогноз с рекомендациями
        """
        try:
            part = self.part_repo.get_by_id(part_id)
            if not part or part.id is None:
                app_logger.warning(f"⚠️ Part #{part_id} not found for forecast")
                return {"error": f"Part #{part_id} not found"}
            
            avg_daily = self._estimate_daily_usage(part, lookback_days=90)
            min_stock = part.min_stock or 0
            current_stock = part.quantity or 0
            
            # ✅ Генерация прогноза по дням
            forecast: List[Dict[str, Any]] = []
            for day in range(forecast_days + 1):
                projected = max(0, current_stock - avg_daily * day)
                forecast.append({
                    "day": day,
                    "projected_stock": projected,
                    "status": self._get_stock_status(projected, min_stock),
                })
            
            # ✅ Расчёт дней до критических уровней
            days_until_low = None
            days_until_out = None
            
            if avg_daily > 0:
                if current_stock > min_stock:
                    days_until_low = int((current_stock - min_stock) / avg_daily)
                days_until_out = int(current_stock / avg_daily)
            
            return {
                "part_id": part_id,
                "part_name": part.name,
                "current_stock": current_stock,
                "min_stock": min_stock,
                "avg_daily_usage": round(avg_daily, 2),
                "days_until_low": days_until_low if days_until_low and days_until_low > 0 else None,
                "days_until_out": days_until_out if days_until_out and days_until_out > 0 else None,
                "forecast": forecast,
                "recommendation": self._get_reorder_recommendation(part, avg_daily),
            }
            
        except Exception as e:
            app_logger.exception(f"❌ Error generating stock forecast for part #{part_id}: {e}")
            return {"error": str(e)}
    
    def _get_stock_status(self, quantity: int, min_stock: int) -> str:
        """Определить статус запаса по количеству"""
        if quantity <= 0:
            return "out"
        if quantity <= min_stock * self.config.critical_threshold:
            return "critical"
        if quantity <= min_stock * self.config.low_threshold:
            return "low"
        if quantity <= min_stock * 2:
            return "adequate"
        return "good"
    
    def _get_reorder_recommendation(self, part: Part, avg_daily: float) -> str:
        """Сгенерировать текстовую рекомендацию по заказу"""
        qty = part.quantity or 0
        min_stock = part.min_stock or 0
        
        if qty <= 0:
            return "🔴 СРОЧНО заказать — нет в наличии!"
        if qty <= min_stock * self.config.critical_threshold:
            needed = int(min_stock * 2 - qty)
            return f"🟠 Заказать {needed} шт. в ближайшее время"
        if qty <= min_stock:
            needed = int(min_stock - qty)
            return f"🟡 Планировать заказ ~{needed} шт."
        
        if avg_daily > 0:
            days_left = qty / avg_daily
            if days_left < 14:
                return f"🔵 Запас на {int(days_left)} дней — рассмотреть заказ"
        
        return "🟢 Запас достаточный"
    
    # ==================== 📤 ЭКСПОРТ ====================
    
    def export_stock_report(
        self, 
        format: str = "csv", 
        include_forecast: bool = False,
        filename_prefix: str = "stock_report"
    ) -> str:
        """
        Экспорт отчёта по запасам
        
        ✅ Поддержка CSV и JSON форматов
        ✅ Экранирование специальных символов в CSV
        ✅ Опциональное включение прогнозов
        """
        alerts = self.check_stock_levels()
        parts = self.part_repo.get_all()
        generated_at = datetime.now()
        
        if format.lower() == "json":
            return self._export_json(alerts, parts, generated_at, include_forecast)
        else:
            return self._export_csv(alerts, parts, generated_at)
    
    def _export_json(
        self, 
        alerts: List[StockAlert], 
        parts: List[Part], 
        generated_at: datetime,
        include_forecast: bool
    ) -> str:
        """Экспорт в JSON формат"""
        data = {
            "metadata": {
                "generated_at": generated_at.isoformat(),
                "report_type": "stock_report",
                "version": "1.0",
            },
            "summary": {
                "total_parts": len(parts),
                "alerts_count": len(alerts),
                "critical_count": len([a for a in alerts if a.alert_level == StockAlertLevel.CRITICAL]),
                "out_of_stock": len([a for a in alerts if a.alert_level == StockAlertLevel.OUT]),
            },
            "alerts": [a.to_dict() for a in alerts],
            "parts": [
                {
                    "id": p.id,
                    "name": p.name,
                    "sku": p.sku,
                    "quantity": p.quantity,
                    "min_stock": p.min_stock,
                    "status": self._get_stock_status(p.quantity or 0, p.min_stock or 0),
                }
                for p in parts if p.id is not None
            ],
        }
        
        if include_forecast and alerts:
            # ✅ Добавляем прогнозы только для первых 5 алертов
            data["forecasts"] = [
                self.get_stock_forecast(a.part_id, forecast_days=14)
                for a in alerts[:5]
                if "error" not in self.get_stock_forecast(a.part_id, forecast_days=14)
            ]
        
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)
    
    def _export_csv(
        self, 
        alerts: List[StockAlert], 
        parts: List[Part], 
        generated_at: datetime
    ) -> str:
        """Экспорт в CSV формат с правильным экранированием"""
        output = io.StringIO()
        # ✅ Используем excel диалект для правильного экранирования запятых и кавычек
        writer = csv.writer(output, dialect='excel', quoting=csv.QUOTE_MINIMAL)
        
        # Заголовок отчёта
        writer.writerow(["PC Repair CRM - Stock Report"])
        writer.writerow([f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([])  # Пустая строка
        
        # Сводка
        writer.writerow(["Summary"])
        writer.writerow(["Total Parts", len(parts)])
        writer.writerow(["Alerts", len(alerts)])
        writer.writerow(["Critical", len([a for a in alerts if a.alert_level == StockAlertLevel.CRITICAL])])
        writer.writerow(["Out of Stock", len([a for a in alerts if a.alert_level == StockAlertLevel.OUT])])
        writer.writerow([])
        
        # Таблица предупреждений
        writer.writerow(["Stock Alerts"])
        writer.writerow([
            "Part Name", "SKU", "Current Qty", "Min Stock", 
            "Alert Level", "Recommended Order", "Supplier"
        ])
        for alert in alerts:
            writer.writerow([
                alert.part_name,
                alert.sku,
                alert.current_quantity,
                alert.min_stock,
                alert.alert_level.value,
                alert.recommended_order,
                alert.supplier or "",
            ])
        
        return output.getvalue()
    
    # ==================== 🧹 УТИЛИТЫ ====================
    
    def get_stock_health_summary(self) -> Dict[str, Any]:
        """
        Краткая сводка о здоровье склада
        
        Returns:
            Dict: Сводка с ключами: health_score, critical_count, recommendations
        """
        alerts = self.check_stock_levels()
        stats = self.get_stock_statistics()
        
        # ✅ Простой расчёт "здоровья" склада (0-100)
        total_parts = stats['total_items'] or 1
        critical_ratio = len([a for a in alerts if a.alert_level in (StockAlertLevel.CRITICAL, StockAlertLevel.OUT)]) / total_parts
        health_score = max(0, int(100 - critical_ratio * 100))
        
        return {
            "health_score": health_score,
            "health_label": "🟢 Отлично" if health_score >= 80 else "🟡 Нормально" if health_score >= 50 else "🔴 Критично",
            "total_parts": total_parts,
            "critical_alerts": len([a for a in alerts if a.alert_level == StockAlertLevel.CRITICAL]),
            "out_of_stock": len([a for a in alerts if a.alert_level == StockAlertLevel.OUT]),
            "total_value": stats['total_value'],
            "top_recommendations": [
                f"Заказать {a.recommended_order} шт. '{a.part_name}'" 
                for a in alerts[:3] if a.alert_level == StockAlertLevel.OUT
            ],
        }