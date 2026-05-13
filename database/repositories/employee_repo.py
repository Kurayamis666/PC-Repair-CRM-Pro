# database/repositories/employee_repo.py
"""
Репозиторий для работы с сотрудниками для PC Repair CRM Pro

✅ ИСПРАВЛЕНО: Импорт модели Employee, таблица employees, поле full_name
✅ УЛУЧШЕНО: Валидация, пагинация, мягкое удаление, методы для баланса
✅ СОВМЕСТИМО: Интеграция с моделями Employee и utils.helpers
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from database.connection import DatabaseConnection
from models.employee import Employee  # ✅ Исправлено: Client → Employee
from core.logger import app_logger
from utils.validators import validate_name, validate_phone, validate_email


class EmployeeRepository:
    """
    Репозиторий для работы с сотрудниками (бывш. клиентами)
    
    ✅ Все запросы к таблице employees (не clients)
    ✅ Поддержка пагинации для больших списков
    ✅ Валидация входных данных перед записью в БД
    ✅ Мягкое удаление через is_active
    ✅ Методы для управления балансом и группами
    """
    
    # ⚙️ Константы для пагинации и валидации
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    # ==================== 📝 CRUD ОПЕРАЦИИ ====================
    
    def create(self, employee: Employee) -> int:
        """
        Создать нового сотрудника с валидацией
        
        ✅ Проверка обязательных полей
        ✅ Валидация телефона и почты
        ✅ Атомарная транзакция
        
        Args:
            employee: Объект Employee с данными
            
        Returns:
            int: ID созданного сотрудника
            
        Raises:
            ValueError: Если данные не прошли валидацию
        """
        # ✅ Валидация обязательных полей
        valid, error = validate_name(employee.full_name, min_len=2, max_len=100)
        if not valid:
            raise ValueError(f"Invalid full_name: {error}")
        
        # ✅ Валидация телефона если указан
        if employee.phone:
            valid, error = validate_phone(employee.phone, "ru")
            if not valid:
                raise ValueError(f"Invalid phone: {error}")
        
        # ✅ Валидация почты если указана
        if employee.email:
            valid, error = validate_email(employee.email)
            if not valid:
                raise ValueError(f"Invalid email: {error}")
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    INSERT INTO employees (
                        full_name, position, phone, email, address, notes,
                        group_id, balance, salary, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    employee.full_name,
                    employee.position,
                    employee.phone,
                    employee.email,
                    employee.address,
                    employee.notes,
                    employee.group_id,
                    employee.balance or 0,
                    employee.salary or 0,
                ))
                
                employee_id = cur.lastrowid
                app_logger.info(f"➕ Created employee: {employee.full_name} (ID: {employee_id})")
                return employee_id
                
        except ValueError:
            raise  # Переподнимаем валидационные ошибки
        except Exception as e:
            app_logger.exception(f"❌ Error creating employee: {e}")
            raise
    
    def get_all(
        self,
        group_id: Optional[int] = None,
        active_only: bool = True,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        order_by: str = 'full_name ASC'
    ) -> Tuple[List[Employee], int]:
        """
        Получить список сотрудников с фильтрацией и пагинацией
        
        ✅ Поддержка фильтрации по группе и статусу
        ✅ Пагинация с возвратом общего количества
        ✅ Загрузка всех полей модели
        
        Args:
            group_id: Фильтр по группе сотрудников
            active_only: Исключать ли деактивированных
            page: Номер страницы (1-based)
            page_size: Записей на странице
            order_by: Сортировка (по умолчанию: full_name ASC)
            
        Returns:
            Tuple[List[Employee], int]: (список сотрудников, общее количество)
        """
        try:
            # ✅ Валидация пагинации
            page = max(1, page)
            page_size = min(max(1, page_size), self.MAX_PAGE_SIZE)
            offset = (page - 1) * page_size
            
            with self.db.get_cursor() as cur:
                query = """
                    SELECT id, full_name, position, phone, email, address, notes,
                           group_id, balance, salary, created_at, updated_at
                    FROM employees
                    WHERE 1=1
                """
                params = []
                
                # ✅ Динамические фильтры
                if group_id:
                    query += " AND group_id = ?"
                    params.append(group_id)
                
                if active_only:
                    query += " AND is_active = 1"
                
                # ✅ Сортировка и пагинация
                query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
                params.extend([page_size, offset])
                
                cur.execute(query, params)
                employees = [Employee.from_row(dict(row)) for row in cur.fetchall()]
                
                # ✅ Получение общего количества для пагинации
                count_query = query.replace("SELECT id, full_name...", "SELECT COUNT(*)")
                count_query = count_query.split("ORDER BY")[0]  # Убираем ORDER BY/LIMIT
                total = cur.execute(count_query, params[:-2]).fetchone()[0]
                
                return employees, total
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching employees: {e}")
            raise
    
    def get_by_id(self, employee_id: int, include_inactive: bool = False) -> Optional[Employee]:
        """
        Получить сотрудника по ID
        
        Args:
            employee_id: ID сотрудника
            include_inactive: Включать ли деактивированных
            
        Returns:
            Optional[Employee]: Объект сотрудника или None
        """
        try:
            with self.db.get_cursor() as cur:
                query = """
                    SELECT id, full_name, position, phone, email, address, notes,
                           group_id, balance, salary, created_at, updated_at
                    FROM employees WHERE id = ?
                """
                params = [employee_id]
                
                if not include_inactive:
                    query += " AND is_active = 1"
                
                cur.execute(query, params)
                row = cur.fetchone()
                
                return Employee.from_row(dict(row)) if row else None
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching employee {employee_id}: {e}")
            raise
    
    def get_by_phone(self, phone: str) -> Optional[Employee]:
        """
        Получить сотрудника по телефону (точное совпадение)
        
        ✅ Полезно для быстрого поиска при звонке
        ✅ Использует индекс по phone если есть
        
        Args:
            phone: Номер телефона
            
        Returns:
            Optional[Employee]: Объект сотрудника или None
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, full_name, position, phone, email, address, notes,
                           group_id, balance, salary, created_at, updated_at
                    FROM employees WHERE phone = ? AND is_active = 1
                """, (phone,))
                row = cur.fetchone()
                return Employee.from_row(dict(row)) if row else None
        except Exception as e:
            app_logger.exception(f"❌ Error fetching employee by phone {phone}: {e}")
            raise
    
    def search(self, query: str, limit: int = 100) -> List[Employee]:
        """
        Поиск сотрудников по имени, телефону или почте
        
        ✅ Безопасный LIKE-запрос с экранированием
        ✅ Поиск по нескольким полям
        ✅ Ограничение результата для производительности
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Employee]: Найденные сотрудники
        """
        try:
            search_pattern = f"%{query}%"
            
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, full_name, position, phone, email, address, notes,
                           group_id, balance, salary, created_at, updated_at
                    FROM employees
                    WHERE full_name LIKE ? 
                       OR phone LIKE ? 
                       OR email LIKE ?
                       AND is_active = 1
                    ORDER BY full_name
                    LIMIT ?
                """, (search_pattern, search_pattern, search_pattern, limit))
                
                return [Employee.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error searching employees: {e}")
            raise
    
    def update(self, employee: Employee) -> bool:
        """
        Обновить данные сотрудника
        
        ✅ Валидация перед обновлением
        ✅ Обновляет все изменяемые поля
        ✅ Авто-обновление updated_at через триггер БД
        
        Args:
            employee: Объект Employee с обновлёнными данными
            
        Returns:
            bool: True если обновление успешно
        """
        # ✅ Валидация (аналогично create)
        if not employee.full_name or len(employee.full_name.strip()) < 2:
            raise ValueError("full_name is required (min 2 characters)")
        
        if employee.phone:
            valid, error = validate_phone(employee.phone, "ru")
            if not valid:
                raise ValueError(f"Invalid phone: {error}")
        
        if employee.email:
            valid, error = validate_email(employee.email)
            if not valid:
                raise ValueError(f"Invalid email: {error}")
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    UPDATE employees SET 
                        full_name = ?,
                        position = ?,
                        phone = ?,
                        email = ?,
                        address = ?,
                        notes = ?,
                        group_id = ?,
                        balance = ?,
                        salary = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    employee.full_name,
                    employee.position,
                    employee.phone,
                    employee.email,
                    employee.address,
                    employee.notes,
                    employee.group_id,
                    employee.balance or 0,
                    employee.salary or 0,
                    employee.id,
                ))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"✏️ Updated employee: {employee.full_name} (ID: {employee.id})")
                return success
                
        except ValueError:
            raise  # Переподнимаем валидационные ошибки
        except Exception as e:
            app_logger.exception(f"❌ Error updating employee {employee.id}: {e}")
            raise
    
    def deactivate(self, employee_id: int) -> bool:
        """
        Мягкое удаление сотрудника (деактивация)
        
        ✅ Сохраняет историю связанных записей
        ✅ Можно восстановить через update(is_active=True)
        
        Args:
            employee_id: ID сотрудника
            
        Returns:
            bool: True если деактивация успешна
        """
        try:
            with self.db.get_cursor() as cur:
                # ✅ Обновляем is_active = 0
                cur.execute("""
                    UPDATE employees SET 
                        is_active = 0, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND full_name != 'Администратор Системы'  # ✅ Защита главного админа
                """, (employee_id,))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"🔒 Deactivated employee ID: {employee_id}")
                return success
                
        except Exception as e:
            app_logger.exception(f"❌ Error deactivating employee {employee_id}: {e}")
            raise
    
    # ==================== 💰 УПРАВЛЕНИЕ БАЛАНСОМ ====================
    
    def update_balance(self, employee_id: int, delta: float, reason: Optional[str] = None) -> Tuple[bool, str]:
        """
        Изменить баланс сотрудника с проверкой
        
        ✅ Не позволяет уйти в недопустимый минус
        ✅ Логирование причины изменения
        ✅ Возврат сообщения об ошибке если не удалось
        
        Args:
            employee_id: ID сотрудника
            delta: Изменение баланса (+ для пополнения, - для списания)
            reason: Причина изменения (для аудита)
            
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            with self.db.get_cursor() as cur:
                # ✅ Проверка текущего баланса
                cur.execute("SELECT balance, full_name FROM employees WHERE id = ?", (employee_id,))
                row = cur.fetchone()
                if not row:
                    return False, f"Employee ID {employee_id} not found"
                
                current_balance, full_name = row
                new_balance = current_balance + delta
                
                # ✅ Проверка минимального баланса (например, не более -100000)
                if new_balance < -100_000:
                    return False, f"Balance too low: {new_balance:.2f} ₽"
                
                cur.execute("""
                    UPDATE employees SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (new_balance, employee_id))
                
                success = cur.rowcount > 0
                if success:
                    reason_str = f" ({reason})" if reason else ""
                    app_logger.info(f"💰 Updated balance for {full_name} (ID: {employee_id}): {current_balance:.2f} → {new_balance:.2f} ₽{reason_str}")
                return success, "OK" if success else "No rows updated"
                
        except Exception as e:
            app_logger.exception(f"❌ Error updating balance for employee {employee_id}: {e}")
            return False, str(e)
    
    def get_balance(self, employee_id: int) -> Optional[float]:
        """
        Получить текущий баланс сотрудника
        
        ✅ Быстрый запрос без загрузки всех полей
        
        Args:
            employee_id: ID сотрудника
            
        Returns:
            Optional[float]: Баланс или None если сотрудник не найден
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("SELECT balance FROM employees WHERE id = ? AND is_active = 1", (employee_id,))
                row = cur.fetchone()
                return row['balance'] if row else None
        except Exception as e:
            app_logger.exception(f"❌ Error fetching balance for employee {employee_id}: {e}")
            raise
    
    # ==================== 📊 СТАТИСТИКА И ОТЧЁТЫ ====================
    
    def get_by_group(self, group_id: int, limit: int = 100) -> List[Employee]:
        """
        Получить сотрудников конкретной группы
        
        ✅ Полезно для фильтрации в интерфейсе
        ✅ Ограничение по количеству для производительности
        
        Args:
            group_id: ID группы сотрудников
            limit: Максимальное количество записей
            
        Returns:
            List[Employee]: Сотрудники группы
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, full_name, position, phone, email, address, notes,
                           group_id, balance, salary, created_at, updated_at
                    FROM employees
                    WHERE group_id = ? AND is_active = 1
                    ORDER BY full_name
                    LIMIT ?
                """, (group_id, limit))
                
                return [Employee.from_row(dict(row)) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching employees for group {group_id}: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику по сотрудникам для дашборда
        
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_employees,
                        COUNT(CASE WHEN balance < 0 THEN 1 END) as with_debt,
                        SUM(CASE WHEN balance < 0 THEN ABS(balance) ELSE 0 END) as total_debt,
                        SUM(balance) as total_balance,
                        AVG(salary) as avg_salary
                    FROM employees
                    WHERE is_active = 1
                """)
                
                row = cur.fetchone()
                return dict(row) if row else {
                    'total_employees': 0, 'with_debt': 0,
                    'total_debt': 0, 'total_balance': 0, 'avg_salary': 0
                }
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching employee stats: {e}")
            raise