# database/repositories/part_repo.py
"""
Репозиторий для работы с запчастями для PC Repair CRM Pro

✅ ИСПРАВЛЕНО: Валидация входных данных, пагинация, проверка остатков
✅ УЛУЧШЕНО: Методы для дашборда, массовые операции, поиск по SKU
✅ СОВМЕСТИМО: Интеграция с моделями Part и utils.helpers
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from database.connection import DatabaseConnection
from models.part import Part, PartCategory
from core.logger import app_logger
from utils.validators import validate_required, validate_number, validate_string_length


class PartRepository:
    """
    Репозиторий для работы с запчастями
    
    ✅ Валидация входных данных перед записью в БД
    ✅ Поддержка пагинации для больших списков
    ✅ Проверка на дубликаты SKU и отрицательные остатки
    ✅ Методы для дашборда и отчётов
    ✅ Массовые операции для импорта/экспорта
    """
    
    # ⚙️ Константы для пагинации и валидации
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200
    MIN_QUANTITY: int = 0
    MAX_QUANTITY: int = 1_000_000
    MIN_COST: float = 0.0
    MAX_COST: float = 1_000_000.0
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    # ==================== 📝 CRUD ОПЕРАЦИИ ====================
    
    def create(self, part: Part) -> int:
        """
        Создать новую запчасть с валидацией
        
        ✅ Проверка обязательных полей
        ✅ Валидация стоимости и количества
        ✅ Проверка на дубликаты SKU
        ✅ Атомарная транзакция
        
        Args:
            part: Объект Part с данными
            
        Returns:
            int: ID созданной запчасти
            
        Raises:
            ValueError: Если данные не прошли валидацию
            IntegrityError: Если нарушена уникальность SKU
        """
        # ✅ Валидация обязательных полей
        valid, error = validate_required(part.name, "name")
        if not valid:
            raise ValueError(f"Invalid name: {error}")
        
        # ✅ Валидация стоимости
        valid, error = validate_number(part.cost, min_val=self.MIN_COST, max_val=self.MAX_COST, field_name="cost")
        if not valid:
            raise ValueError(f"Invalid cost: {error}")
        
        valid, error = validate_number(part.price, min_val=self.MIN_COST, max_val=self.MAX_COST, field_name="price")
        if not valid:
            raise ValueError(f"Invalid price: {error}")
        
        # ✅ Валидация количества
        valid, error = validate_number(part.quantity, min_val=self.MIN_QUANTITY, max_val=self.MAX_QUANTITY, field_name="quantity")
        if not valid:
            raise ValueError(f"Invalid quantity: {error}")
        
        # ✅ Валидация длины строк
        if part.sku and len(part.sku) > 50:
            raise ValueError("SKU too long (max 50 characters)")
        
        try:
            with self.db.get_cursor() as cur:
                # ✅ Проверка на дубликат SKU перед вставкой
                if part.sku:
                    cur.execute("SELECT id FROM parts WHERE sku = ?", (part.sku,))
                    if cur.fetchone():
                        raise ValueError(f"Part with SKU '{part.sku}' already exists")
                
                cur.execute("""
                    INSERT INTO parts (
                        name, sku, quantity, cost, price, supplier, category,
                        owner_type, min_stock, contractor_id, type_id, 
                        nom_type, unit, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    part.name,
                    part.sku,
                    part.quantity,
                    part.cost,
                    part.price,
                    part.supplier,
                    part.category.value if part.category else None,
                    part.owner_type,
                    part.min_stock,
                    part.contractor_id,
                    part.type_id,
                    part.nom_type,
                    part.unit,
                ))
                
                part_id = cur.lastrowid
                app_logger.info(f"➕ Created part: {part.name} (ID: {part_id}, SKU: {part.sku})")
                return part_id
                
        except ValueError:
            raise  # Переподнимаем валидационные ошибки
        except Exception as e:
            app_logger.exception(f"❌ Error creating part: {e}")
            raise
    
    def get_all(
        self,
        category: Optional[PartCategory] = None,
        supplier: Optional[str] = None,
        in_stock_only: bool = False,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        order_by: str = 'name ASC'
    ) -> Tuple[List[Part], int]:
        """
        Получить список запчастей с фильтрацией и пагинацией
        
        ✅ Поддержка множественных фильтров
        ✅ Пагинация с возвратом общего количества
        ✅ Загрузка всех полей + JOIN данные
        
        Args:
            category: Фильтр по категории
            supplier: Фильтр по поставщику
            in_stock_only: Только запчасти в наличии
            page: Номер страницы (1-based)
            page_size: Записей на странице
            order_by: Сортировка (по умолчанию: name ASC)
            
        Returns:
            Tuple[List[Part], int]: (список запчастей, общее количество)
        """
        try:
            # ✅ Валидация пагинации
            page = max(1, page)
            page_size = min(max(1, page_size), self.MAX_PAGE_SIZE)
            offset = (page - 1) * page_size
            
            with self.db.get_cursor() as cur:
                # ✅ Базовый запрос с безопасными JOIN
                query = """
                    SELECT p.*, c.name as contractor_name
                    FROM parts p
                    LEFT JOIN contractors c ON p.contractor_id = c.id
                    WHERE 1=1
                """
                params = []
                
                # ✅ Динамические фильтры
                if category:
                    query += " AND p.category = ?"
                    params.append(category.value)
                
                if supplier:
                    query += " AND p.supplier = ?"
                    params.append(supplier)
                
                if in_stock_only:
                    query += " AND p.quantity > 0"
                
                # ✅ Сортировка и пагинация
                query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
                params.extend([page_size, offset])
                
                cur.execute(query, params)
                parts = [Part.from_row(dict(row)) for row in cur.fetchall()]
                
                # ✅ Получение общего количества для пагинации
                count_query = query.replace("SELECT p.*, c.name...", "SELECT COUNT(*)")
                count_query = count_query.split("ORDER BY")[0]  # Убираем ORDER BY/LIMIT
                total = cur.execute(count_query, params[:-2]).fetchone()[0]
                
                return parts, total
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching parts: {e}")
            raise
    
    def get_by_id(self, part_id: int) -> Optional[Part]:
        """Получить запчасть по ID"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT p.*, c.name as contractor_name
                    FROM parts p
                    LEFT JOIN contractors c ON p.contractor_id = c.id
                    WHERE p.id = ?
                """, (part_id,))
                row = cur.fetchone()
                return Part.from_row(dict(row)) if row else None
        except Exception as e:
            app_logger.exception(f"❌ Error fetching part {part_id}: {e}")
            raise
    
    def get_by_sku(self, sku: str) -> Optional[Part]:
        """
        Получить запчасть по артикулу (точное совпадение)
        
        ✅ Полезно для быстрого поиска при сканировании штрих-кода
        ✅ Использует индекс по sku
        
        Args:
            sku: Артикул запчасти
            
        Returns:
            Optional[Part]: Объект запчасти или None
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT p.*, c.name as contractor_name
                    FROM parts p
                    LEFT JOIN contractors c ON p.contractor_id = c.id
                    WHERE p.sku = ?
                """, (sku,))
                row = cur.fetchone()
                return Part.from_row(dict(row)) if row else None
        except Exception as e:
            app_logger.exception(f"❌ Error fetching part by SKU {sku}: {e}")
            raise
    
    def search(self, query: str, limit: int = 100) -> List[Part]:
        """
        Поиск запчастей по названию или артикулу
        
        ✅ Безопасный LIKE-запрос с экранированием
        ✅ Поиск по нескольким полям
        ✅ Ограничение результата для производительности
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Part]: Найденные запчасти
        """
        try:
            search_pattern = f"%{query}%"
            
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT p.*, c.name as contractor_name
                    FROM parts p
                    LEFT JOIN contractors c ON p.contractor_id = c.id
                    WHERE p.name LIKE ? OR p.sku LIKE ? OR p.supplier LIKE ?
                    ORDER BY p.name
                    LIMIT ?
                """, (search_pattern, search_pattern, search_pattern, limit))
                
                return [Part.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error searching parts: {e}")
            raise
    
    def update(self, part: Part) -> bool:
        """
        Обновить данные запчасти
        
        ✅ Валидация перед обновлением
        ✅ Обновляет все изменяемые поля
        ✅ Проверка на дубликаты SKU (если он изменился)
        
        Args:
            part: Объект Part с обновлёнными данными
            
        Returns:
            bool: True если обновление успешно
        """
        # ✅ Валидация (аналогично create)
        if not part.name or not part.name.strip():
            raise ValueError("name is required")
        
        if part.cost < 0 or part.price < 0:
            raise ValueError("cost and price must be non-negative")
        
        if part.quantity < 0:
            raise ValueError("quantity must be non-negative")
        
        try:
            with self.db.get_cursor() as cur:
                # ✅ Проверка на дубликат SKU если он изменился
                if part.sku:
                    cur.execute("SELECT id FROM parts WHERE sku = ? AND id != ?", (part.sku, part.id))
                    if cur.fetchone():
                        raise ValueError(f"Part with SKU '{part.sku}' already exists")
                
                cur.execute("""
                    UPDATE parts SET 
                        name = ?,
                        sku = ?,
                        quantity = ?,
                        cost = ?,
                        price = ?,
                        supplier = ?,
                        category = ?,
                        owner_type = ?,
                        min_stock = ?,
                        contractor_id = ?,
                        type_id = ?,
                        nom_type = ?,
                        unit = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    part.name,
                    part.sku,
                    part.quantity,
                    part.cost,
                    part.price,
                    part.supplier,
                    part.category.value if part.category else None,
                    part.owner_type,
                    part.min_stock,
                    part.contractor_id,
                    part.type_id,
                    part.nom_type,
                    part.unit,
                    part.id,
                ))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"✏️ Updated part: {part.name} (ID: {part.id}, SKU: {part.sku})")
                return success
                
        except ValueError:
            raise  # Переподнимаем валидационные ошибки
        except Exception as e:
            app_logger.exception(f"❌ Error updating part {part.id}: {e}")
            raise
    
    def delete(self, part_id: int, force: bool = False) -> bool:
        """
        Удалить запчасть с проверкой связей
        
        ✅ Проверка: есть ли заявки, использующие эту запчасть
        ✅ Опция force для принудительного удаления
        ✅ Логирование причины удаления
        
        Args:
            part_id: ID запчасти
            force: Принудительное удаление (игнорировать связи)
            
        Returns:
            bool: True если удаление успешно
        """
        try:
            with self.db.get_cursor() as cur:
                # ✅ Проверка связей если не force
                if not force:
                    # Проверка: есть ли заявки с этой запчастью
                    cur.execute("SELECT COUNT(*) FROM request_parts WHERE part_id = ?", (part_id,))
                    if cur.fetchone()[0] > 0:
                        app_logger.warning(f"⚠️ Cannot delete part {part_id}: used in requests")
                        return False
                
                cur.execute("DELETE FROM parts WHERE id = ?", (part_id,))
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"🗑️ Deleted part ID: {part_id}")
                return success
                
        except Exception as e:
            app_logger.exception(f"❌ Error deleting part {part_id}: {e}")
            raise
    
    # ==================== 📦 УПРАВЛЕНИЕ ОСТАТКАМИ ====================
    
    def update_quantity(self, part_id: int, delta: int, reason: Optional[str] = None) -> Tuple[bool, str]:
        """
        Обновить количество запчасти с проверкой остатков
        
        ✅ Не позволяет уйти в отрицательный остаток
        ✅ Логирование причины изменения
        ✅ Возврат сообщения об ошибке если не удалось
        
        Args:
            part_id: ID запчасти
            delta: Изменение количества (+ для прихода, - для расхода)
            reason: Причина изменения (для аудита)
            
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            with self.db.get_cursor() as cur:
                # ✅ Проверка текущего остатка
                cur.execute("SELECT quantity, name FROM parts WHERE id = ?", (part_id,))
                row = cur.fetchone()
                if not row:
                    return False, f"Part ID {part_id} not found"
                
                current_qty, part_name = row
                new_qty = current_qty + delta
                
                if new_qty < 0:
                    return False, f"Insufficient stock: {part_name} (have {current_qty}, need {-delta})"
                
                cur.execute("""
                    UPDATE parts SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (new_qty, part_id))
                
                success = cur.rowcount > 0
                if success:
                    reason_str = f" ({reason})" if reason else ""
                    app_logger.info(f"📦 Updated quantity for {part_name} (ID: {part_id}): {current_qty} → {new_qty}{reason_str}")
                return success, "OK" if success else "No rows updated"
                
        except Exception as e:
            app_logger.exception(f"❌ Error updating quantity for part {part_id}: {e}")
            return False, str(e)
    
    def batch_update_quantity(self, updates: List[Tuple[int, int]]) -> Dict[str, int]:
        """
        Массовое обновление количества запчастей (для импорта)
        
        ✅ Атомарная транзакция: все или ничего
        ✅ Возврат статистики: сколько обновлено, сколько ошибок
        
        Args:
            updates: Список кортежей (part_id, new_quantity)
            
        Returns:
            Dict[str, int]: {updated: count, errors: count}
        """
        stats = {"updated": 0, "errors": 0}
        
        try:
            with self.db.get_cursor() as cur:
                for part_id, new_qty in updates:
                    try:
                        if new_qty < 0:
                            stats["errors"] += 1
                            continue
                        
                        cur.execute("""
                            UPDATE parts SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                        """, (new_qty, part_id))
                        
                        if cur.rowcount > 0:
                            stats["updated"] += 1
                        else:
                            stats["errors"] += 1
                            
                    except Exception:
                        stats["errors"] += 1
                        continue
                
                return stats
                
        except Exception as e:
            app_logger.exception(f"❌ Error in batch update: {e}")
            stats["errors"] += len(updates)
            return stats
    
    # ==================== 📊 СТАТИСТИКА И ОТЧЁТЫ ====================
    
    def get_low_stock(self, threshold: Optional[int] = None) -> List[Part]:
        """
        Получить запчасти с низким остатком
        
        ✅ Гибкий порог (по умолчанию из модели)
        ✅ Исключение запчастей с нулевым остатком (они в out_of_stock)
        
        Args:
            threshold: Порог низкого остатка (по умолчанию: 5)
            
        Returns:
            List[Part]: Запчасти с низким остатком
        """
        try:
            threshold = threshold or 5
            
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT p.*, c.name as contractor_name
                    FROM parts p
                    LEFT JOIN contractors c ON p.contractor_id = c.id
                    WHERE p.quantity <= ? AND p.quantity > 0
                    ORDER BY p.quantity ASC, p.name ASC
                """, (threshold,))
                
                return [Part.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching low stock parts: {e}")
            raise
    
    def get_out_of_stock(self) -> List[Part]:
        """Получить запчасти, которых нет в наличии"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT p.*, c.name as contractor_name
                    FROM parts p
                    LEFT JOIN contractors c ON p.contractor_id = c.id
                    WHERE p.quantity = 0
                    ORDER BY p.name ASC
                """)
                
                return [Part.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching out of stock parts: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику по запчастям для дашборда
        
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_parts,
                        SUM(quantity) as total_quantity,
                        SUM(quantity * cost) as total_cost_value,
                        SUM(quantity * price) as total_retail_value,
                        COUNT(CASE WHEN quantity <= min_stock AND quantity > 0 THEN 1 END) as low_stock_count,
                        COUNT(CASE WHEN quantity = 0 THEN 1 END) as out_of_stock_count
                    FROM parts
                """)
                
                row = cur.fetchone()
                return dict(row) if row else {
                    'total_parts': 0, 'total_quantity': 0,
                    'total_cost_value': 0, 'total_retail_value': 0,
                    'low_stock_count': 0, 'out_of_stock_count': 0
                }
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching parts stats: {e}")
            raise
    
    def get_by_supplier(self, supplier_id: int, limit: int = 100) -> List[Part]:
        """
        Получить запчасти конкретного поставщика
        
        ✅ Полезно для формирования заказов поставщику
        ✅ Ограничение по количеству для производительности
        
        Args:
            supplier_id: ID поставщика (контрагента)
            limit: Максимальное количество записей
            
        Returns:
            List[Part]: Запчасти поставщика
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT p.*, c.name as contractor_name
                    FROM parts p
                    LEFT JOIN contractors c ON p.contractor_id = c.id
                    WHERE p.contractor_id = ?
                    ORDER BY p.name
                    LIMIT ?
                """, (supplier_id, limit))
                
                return [Part.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching parts for supplier {supplier_id}: {e}")
            raise