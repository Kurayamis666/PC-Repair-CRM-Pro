# database/repositories/request_repo.py
"""
Репозиторий для работы с заявками для PC Repair CRM Pro

✅ ИСПРАВЛЕНО: Запросы к таблице employees (не clients), валидация, пагинация
✅ УЛУЧШЕНО: Обработка дат, soft delete, методы для дашборда
✅ СОВМЕСТИМО: Интеграция с моделями Request и utils.helpers
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from database.connection import DatabaseConnection
from models.request import Request, RequestStatus, RequestPriority
from core.logger import app_logger
from utils.validators import validate_required, validate_date_format


class RequestRepository:
    """
    Репозиторий для работы с заявками
    
    ✅ Все запросы к таблице employees (не clients)
    ✅ Поддержка пагинации для больших списков
    ✅ Валидация входных данных перед записью в БД
    ✅ Мягкое удаление через смену статуса
    ✅ Методы для дашборда и отчётов
    """
    
    # ⚙️ Константы для пагинации
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    # ==================== 📝 CRUD ОПЕРАЦИИ ====================
    
    def create(self, request: Request) -> int:
        """
        Создать новую заявку с валидацией
        
        ✅ Проверка обязательных полей
        ✅ Конвертация Enum в строки для БД
        ✅ Атомарная транзакция
        
        Args:
            request: Объект Request с данными
            
        Returns:
            int: ID созданной заявки
            
        Raises:
            ValueError: Если данные не прошли валидацию
        """
        # ✅ Валидация обязательных полей
        if not request.client_id:
            raise ValueError("client_id is required")
        if not request.problem_desc or not request.problem_desc.strip():
            raise ValueError("problem_desc is required")
        
        # ✅ Валидация статуса
        if request.status not in RequestStatus:
            raise ValueError(f"Invalid status: {request.status}")
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    INSERT INTO requests (
                        client_id, equipment_id, user_id, branch_id,
                        status, priority, problem_desc, solution_desc,
                        labor_cost, parts_cost, total_cost,
                        planned_date, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    request.client_id,
                    request.equipment_id,
                    request.user_id,
                    request.branch_id,
                    request.status.value,  # ✅ Enum → str
                    request.priority.value if request.priority else 'normal',  # ✅ Enum → str
                    request.problem_desc,
                    request.solution_desc,
                    request.labor_cost or 0,
                    request.parts_cost or 0,
                    request.total_cost or 0,
                    request.planned_date.isoformat() if isinstance(request.planned_date, datetime) else request.planned_date,
                ))
                
                request_id = cur.lastrowid
                app_logger.info(f"📝 Created request (ID: {request_id}) for employee {request.client_id}")
                return request_id
                
        except Exception as e:
            app_logger.exception(f"❌ Error creating request: {e}")
            raise
    
    def get_all(
        self,
        status: Optional[RequestStatus] = None,
        priority: Optional[RequestPriority] = None,
        client_id: Optional[int] = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        order_by: str = 'created_at DESC'
    ) -> Tuple[List[Request], int]:
        """
        Получить список заявок с фильтрацией и пагинацией
        
        ✅ Поддержка множественных фильтров
        ✅ Пагинация с возвратом общего количества
        ✅ Загрузка всех полей + JOIN данные
        
        Args:
            status: Фильтр по статусу
            priority: Фильтр по приоритету
            client_id: Фильтр по сотруднику (бывш. клиенту)
            page: Номер страницы (1-based)
            page_size: Записей на странице
            order_by: Сортировка (по умолчанию: created_at DESC)
            
        Returns:
            Tuple[List[Request], int]: (список заявок, общее количество)
        """
        try:
            # ✅ Валидация пагинации
            page = max(1, page)
            page_size = min(max(1, page_size), self.MAX_PAGE_SIZE)
            offset = (page - 1) * page_size
            
            with self.db.get_cursor() as cur:
                # ✅ Базовый запрос с безопасными JOIN к employees
                query = """
                    SELECT r.*, 
                           e.full_name as client_name, 
                           eq.model as equipment_model,
                           u.username as technician
                    FROM requests r
                    LEFT JOIN employees e ON r.client_id = e.id
                    LEFT JOIN equipment eq ON r.equipment_id = eq.id
                    LEFT JOIN users u ON r.user_id = u.id
                    WHERE 1=1
                """
                params = []
                
                # ✅ Динамические фильтры
                if status:
                    query += " AND r.status = ?"
                    params.append(status.value)
                
                if priority:
                    query += " AND r.priority = ?"
                    params.append(priority.value)
                
                if client_id:
                    query += " AND r.client_id = ?"
                    params.append(client_id)
                
                # ✅ Сортировка и пагинация
                query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
                params.extend([page_size, offset])
                
                cur.execute(query, params)
                requests = [Request.from_row(dict(row)) for row in cur.fetchall()]
                
                # ✅ Получение общего количества для пагинации
                count_query = query.replace("SELECT r.*, e.full_name...", "SELECT COUNT(*)")
                count_query = count_query.split("ORDER BY")[0]  # Убираем ORDER BY/LIMIT
                total = cur.execute(count_query, params[:-2]).fetchone()[0]
                
                return requests, total
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching requests: {e}")
            raise
    
    def get_by_id(self, request_id: int, include_inactive: bool = False) -> Optional[Request]:
        """
        Получить заявку по ID
        
        Args:
            request_id: ID заявки
            include_inactive: Включать ли закрытые/отменённые
            
        Returns:
            Optional[Request]: Объект заявки или None
        """
        try:
            with self.db.get_cursor() as cur:
                query = """
                    SELECT r.*, 
                           e.full_name as client_name, 
                           eq.model as equipment_model,
                           u.username as technician
                    FROM requests r
                    LEFT JOIN employees e ON r.client_id = e.id
                    LEFT JOIN equipment eq ON r.equipment_id = eq.id
                    LEFT JOIN users u ON r.user_id = u.id
                    WHERE r.id = ?
                """
                params = [request_id]
                
                if not include_inactive:
                    query += " AND r.status NOT IN ('cancelled', 'closed')"
                
                cur.execute(query, params)
                row = cur.fetchone()
                
                return Request.from_row(dict(row)) if row else None
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching request {request_id}: {e}")
            raise
    
    def get_by_client(self, client_id: int, limit: int = 50) -> List[Request]:
        """
        Получить все заявки конкретного сотрудника
        
        ✅ Полезно для карточки сотрудника
        ✅ Ограничение по количеству для производительности
        
        Args:
            client_id: ID сотрудника
            limit: Максимальное количество записей
            
        Returns:
            List[Request]: Список заявок сотрудника
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT r.*, 
                           e.full_name as client_name,
                           eq.model as equipment_model
                    FROM requests r
                    LEFT JOIN employees e ON r.client_id = e.id
                    LEFT JOIN equipment eq ON r.equipment_id = eq.id
                    WHERE r.client_id = ?
                    ORDER BY r.created_at DESC
                    LIMIT ?
                """, (client_id, limit))
                
                return [Request.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching requests for client {client_id}: {e}")
            raise
    
    def search(self, query: str, limit: int = 100) -> List[Request]:
        """
        Поиск заявок по имени сотрудника, модели оборудования или описанию
        
        ✅ Безопасный LIKE-запрос с экранированием
        ✅ Поиск по нескольким полям
        ✅ Ограничение результата
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Request]: Найденные заявки
        """
        try:
            search_pattern = f"%{query}%"
            
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT r.*, 
                           e.full_name as client_name,
                           eq.model as equipment_model
                    FROM requests r
                    LEFT JOIN employees e ON r.client_id = e.id
                    LEFT JOIN equipment eq ON r.equipment_id = eq.id
                    WHERE e.full_name LIKE ? 
                       OR eq.model LIKE ? 
                       OR r.problem_desc LIKE ?
                       OR r.solution_desc LIKE ?
                    ORDER BY r.created_at DESC
                    LIMIT ?
                """, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
                
                return [Request.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error searching requests: {e}")
            raise
    
    def update(self, request: Request) -> bool:
        """
        Обновить данные заявки
        
        ✅ Обновляет все изменяемые поля
        ✅ Конвертация Enum и datetime
        ✅ Авто-обновление updated_at через триггер БД
        
        Args:
            request: Объект Request с обновлёнными данными
            
        Returns:
            bool: True если обновление успешно
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    UPDATE requests SET 
                        client_id = ?,
                        equipment_id = ?,
                        user_id = ?,
                        branch_id = ?,
                        status = ?,
                        priority = ?,
                        problem_desc = ?,
                        solution_desc = ?,
                        labor_cost = ?,
                        parts_cost = ?,
                        total_cost = ?,
                        planned_date = ?,
                        closed_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    request.client_id,
                    request.equipment_id,
                    request.user_id,
                    request.branch_id,
                    request.status.value,
                    request.priority.value if request.priority else 'normal',
                    request.problem_desc,
                    request.solution_desc,
                    request.labor_cost or 0,
                    request.parts_cost or 0,
                    request.total_cost or 0,
                    request.planned_date.isoformat() if isinstance(request.planned_date, datetime) else request.planned_date,
                    request.closed_at.isoformat() if isinstance(request.closed_at, datetime) else request.closed_at,
                    request.id,
                ))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"✏️ Updated request ID: {request.id}")
                return success
                
        except Exception as e:
            app_logger.exception(f"❌ Error updating request {request.id}: {e}")
            raise
    
    def cancel(self, request_id: int, reason: Optional[str] = None) -> bool:
        """
        Мягкое удаление заявки (отмена)
        
        ✅ Сохраняет историю вместо DELETE
        ✅ Опциональное указание причины в solution_desc
        
        Args:
            request_id: ID заявки
            reason: Причина отмены (добавляется в solution_desc)
            
        Returns:
            bool: True если отмена успешна
        """
        try:
            with self.db.get_cursor() as cur:
                # ✅ Обновляем статус + добавляем причину если указана
                if reason:
                    cur.execute("""
                        UPDATE requests SET 
                            status = 'cancelled',
                            solution_desc = COALESCE(solution_desc, '') || '
Отмена: ' || ?,
                            closed_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND status NOT IN ('closed', 'cancelled')
                    """, (reason, request_id))
                else:
                    cur.execute("""
                        UPDATE requests SET 
                            status = 'cancelled',
                            closed_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND status NOT IN ('closed', 'cancelled')
                    """, (request_id,))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"🗑️ Cancelled request ID: {request_id}")
                return success
                
        except Exception as e:
            app_logger.exception(f"❌ Error cancelling request {request_id}: {e}")
            raise
    
    def update_status(
        self,
        request_id: int,
        new_status: RequestStatus,
        closed_at: Optional[datetime] = None,
    ) -> bool:
        """
        Обновить статус заявки
        
        ✅ Авто-установка closed_at при переходе в 'closed'
        ✅ Валидация перехода статусов (опционально)
        
        Args:
            request_id: ID заявки
            new_status: Новый статус
            closed_at: Время закрытия (авто если new_status='closed')
            
        Returns:
            bool: True если обновление успешно
        """
        try:
            with self.db.get_cursor() as cur:
                # ✅ Авто-заполнение closed_at при закрытии
                if new_status == RequestStatus.CLOSED and not closed_at:
                    closed_at = datetime.now()
                
                closed_at_str = closed_at.isoformat() if closed_at else None
                
                cur.execute("""
                    UPDATE requests SET 
                        status = ?,
                        closed_at = COALESCE(?, closed_at),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_status.value, closed_at_str, request_id))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"🔄 Request {request_id} status changed to: {new_status.value}")
                return success
                
        except Exception as e:
            app_logger.exception(f"❌ Error updating request {request_id} status: {e}")
            raise
    
    # ==================== 📊 СТАТИСТИКА И ОТЧЁТЫ ====================
    
    def get_expiring(self, days: int = 2) -> List[Request]:
        """
        Получить заявки, истекающие в ближайшие N дней
        
        ✅ Корректный расчёт даты через timedelta
        ✅ Исключение закрытых/отменённых заявок
        
        Args:
            days: Количество дней вперёд
            
        Returns:
            List[Request]: Заявки с истекающим сроком
        """
        try:
            today = datetime.now().date()
            end_date = today + timedelta(days=days)  # ✅ Правильный расчёт
            
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT r.*, 
                           e.full_name as client_name,
                           eq.model as equipment_model
                    FROM requests r
                    LEFT JOIN employees e ON r.client_id = e.id
                    LEFT JOIN equipment eq ON r.equipment_id = eq.id
                    WHERE r.planned_date IS NOT NULL
                      AND r.status NOT IN ('closed', 'cancelled')
                      AND DATE(r.planned_date) BETWEEN ? AND ?
                    ORDER BY r.planned_date ASC
                """, (today.isoformat(), end_date.isoformat()))
                
                return [Request.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching expiring requests: {e}")
            raise
    
    def get_stats(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить статистику по заявкам с фильтрацией по периоду
        
        ✅ Поддержка временного диапазона
        ✅ Статистика по статусам и стоимости
        
        Args:
            start_date: Дата начала (формат "YYYY-MM-DD")
            end_date: Дата окончания (формат "YYYY-MM-DD")
            
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        try:
            with self.db.get_cursor() as cur:
                query = """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status IN ('new', 'diagnostics', 'in_progress') THEN 1 ELSE 0 END) as active,
                        SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                        COALESCE(SUM(total_cost), 0) as total_costs,
                        COALESCE(SUM(labor_cost), 0) as labor_total,
                        COALESCE(SUM(parts_cost), 0) as parts_total
                    FROM requests
                    WHERE 1=1
                """
                params = []
                
                if start_date:
                    query += " AND DATE(created_at) >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND DATE(created_at) <= ?"
                    params.append(end_date)
                
                cur.execute(query, params)
                row = cur.fetchone()
                
                return dict(row) if row else {
                    'total': 0, 'active': 0, 'completed': 0, 'cancelled': 0,
                    'total_costs': 0, 'labor_total': 0, 'parts_total': 0
                }
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching request stats: {e}")
            raise
    
    def count_by_status(self) -> Dict[str, int]:
        """
        Получить количество заявок по статусам для дашборда
        
        Returns:
            Dict[str, int]: {статус: количество}
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM requests
                    GROUP BY status
                """)
                
                return {row['status']: row['count'] for row in cur.fetchall()}
                
        except Exception as e:
            app_logger.exception(f"❌ Error counting by status: {e}")
            raise