# database/repositories/user_repo.py
"""
Репозиторий для работы с пользователями для PC Repair CRM Pro

✅ ИСПРАВЛЕНО: Убран branch_id из запросов (нет в схеме БД)
✅ ИСПРАВЛЕНО: Хеширование паролей через utils.helpers (PBKDF2)
✅ УЛУЧШЕНО: Полная загрузка полей User, валидация, поиск
✅ СОВМЕСТИМО: Интеграция с системой безопасности и валидации
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from database.connection import DatabaseConnection
from models.user import User, UserRole
from core.logger import app_logger
from utils.helpers import hash_password, verify_password
from utils.validators import validate_username, validate_email, validate_phone


class UserRepository:
    """
    Репозиторий для работы с пользователями
    
    ✅ Использует PBKDF2 хеширование через utils.helpers
    ✅ Загружает все поля модели User из БД (без branch_id)
    ✅ Поддерживает soft delete через is_active
    ✅ Валидирует входные данные перед записью в БД
    ✅ Предоставляет методы поиска и фильтрации
    """
    
    # ⚙️ Константы для пагинации и поиска
    DEFAULT_PAGE_SIZE: int = 50
    MAX_USERNAME_LENGTH: int = 50
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    # ==================== 🔐 РАБОТА С ПАРОЛЯМИ ====================
    
    def _hash_password_secure(self, password: str) -> tuple[str, str]:
        """Безопасное хеширование пароля через PBKDF2"""
        return hash_password(password)
    
    def _verify_password_secure(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """Проверка пароля через PBKDF2"""
        return verify_password(password, stored_hash, stored_salt)
    
    # ==================== 📝 CRUD ОПЕРАЦИИ ====================
    
    def create(self, user: User, password: str) -> int:
        """Создать нового пользователя с безопасным хешированием"""
        # ✅ Валидация входных данных
        valid, error = validate_username(user.username)
        if not valid:
            raise ValueError(f"Invalid username: {error}")
        
        if user.email and not validate_email(user.email)[0]:
            raise ValueError(f"Invalid email: {user.email}")
        
        if user.phone and not validate_phone(user.phone, "ru")[0]:
            raise ValueError(f"Invalid phone: {user.phone}")
        
        # ✅ Хеширование пароля ДО начала транзакции
        password_hash, password_salt = self._hash_password_secure(password)
        
        try:
            with self.db.get_cursor() as cur:
                # ✅ БЕЗ branch_id (нет в схеме)
                cur.execute("""
                    INSERT INTO users (
                        username, password, password_salt, role,
                        full_name, email, phone, is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    user.username,
                    password_hash,
                    password_salt,
                    user.role.value,
                    user.full_name,
                    user.email,
                    user.phone,
                    int(user.is_active),
                ))
                
                user_id = cur.lastrowid
                app_logger.info(f"➕ Created user: {user.username} (ID: {user_id})")
                return user_id
                
        except Exception as e:
            app_logger.exception(f"❌ Error creating user: {e}")
            raise
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя с проверкой через PBKDF2"""
        try:
            with self.db.get_cursor() as cur:
                # ✅ БЕЗ branch_id (нет в схеме)
                cur.execute("""
                    SELECT id, username, password, password_salt, role,
                           full_name, email, phone, is_active, created_at
                    FROM users
                    WHERE username = ? AND is_active = 1
                """, (username,))
                
                row = cur.fetchone()
                if not row:
                    app_logger.warning(f"⚠️ Failed login attempt for: {username}")
                    return None
                
                # ✅ Проверка пароля через PBKDF2
                stored_hash = row['password']
                stored_salt = row['password_salt']
                
                if not self._verify_password_secure(password, stored_hash, stored_salt):
                    app_logger.warning(f"⚠️ Invalid password for: {username}")
                    return None
                
                # ✅ Создаём объект User БЕЗ branch_id
                user = User(
                    id=row['id'],
                    username=row['username'],
                    password_hash=row['password'],
                    role=UserRole(row['role']),
                    full_name=row['full_name'],
                    email=row['email'],
                    phone=row['phone'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                )
                
                app_logger.info(f"✅ User authenticated: {username}")
                return user
                
        except Exception as e:
            app_logger.exception(f"❌ Error authenticating user {username}: {e}")
            raise
    
    def get_all(self, active_only: bool = True, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> List[User]:
        """Получить список пользователей с пагинацией"""
        try:
            offset = (page - 1) * page_size
            
            with self.db.get_cursor() as cur:
                query = """
                    SELECT id, username, password, password_salt, role,
                           full_name, email, phone, is_active, created_at, updated_at
                    FROM users
                """
                params = []
                
                if active_only:
                    query += " WHERE is_active = 1"
                
                query += " ORDER BY username LIMIT ? OFFSET ?"
                params.extend([page_size, offset])
                
                cur.execute(query, params)
                
                return [self._row_to_user(row) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching users: {e}")
            raise
    
    def get_by_id(self, user_id: int, include_inactive: bool = False) -> Optional[User]:
        """Получить пользователя по ID"""
        try:
            with self.db.get_cursor() as cur:
                query = """
                    SELECT id, username, password, password_salt, role,
                           full_name, email, phone, is_active, created_at, updated_at
                    FROM users WHERE id = ?
                """
                params = [user_id]
                
                if not include_inactive:
                    query += " AND is_active = 1"
                
                cur.execute(query, params)
                row = cur.fetchone()
                
                return self._row_to_user(row) if row else None
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching user {user_id}: {e}")
            raise
    
    def get_by_username(self, username: str, include_inactive: bool = False) -> Optional[User]:
        """Получить пользователя по имени"""
        try:
            with self.db.get_cursor() as cur:
                query = """
                    SELECT id, username, password, password_salt, role,
                           full_name, email, phone, is_active, created_at, updated_at
                    FROM users WHERE username = ?
                """
                params = [username]
                
                if not include_inactive:
                    query += " AND is_active = 1"
                
                cur.execute(query, params)
                row = cur.fetchone()
                
                return self._row_to_user(row) if row else None
                
        except Exception as e:
            app_logger.exception(f"❌ Error fetching user {username}: {e}")
            raise
    
    def search(self, query: str, active_only: bool = True) -> List[User]:
        """Поиск пользователей по подстроке"""
        try:
            search_pattern = f"%{query}%"
            
            with self.db.get_cursor() as cur:
                sql = """
                    SELECT id, username, password, password_salt, role,
                           full_name, email, phone, is_active, created_at, updated_at
                    FROM users
                    WHERE (username LIKE ? OR full_name LIKE ? OR email LIKE ?)
                """
                params = [search_pattern, search_pattern, search_pattern]
                
                if active_only:
                    sql += " AND is_active = 1"
                
                sql += " ORDER BY username"
                
                cur.execute(sql, params)
                return [self._row_to_user(row) for row in cur.fetchall()]
                
        except Exception as e:
            app_logger.exception(f"❌ Error searching users: {e}")
            raise
    
    def _row_to_user(self, row: Dict[str, Any]) -> User:
        """Внутренний метод: конвертация строки БД в объект User"""
        return User(
            id=row['id'],
            username=row['username'],
            password_hash=row['password'],
            role=UserRole(row['role']),
            full_name=row['full_name'],
            email=row['email'],
            phone=row['phone'],
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            updated_at=row.get('updated_at'),
        )
    
    def update(self, user: User) -> bool:
        """Обновить данные пользователя"""
        try:
            with self.db.get_cursor() as cur:
                # ✅ БЕЗ branch_id (нет в схеме)
                cur.execute("""
                    UPDATE users SET 
                        username = ?,
                        role = ?,
                        full_name = ?,
                        email = ?,
                        phone = ?,
                        is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    user.username,
                    user.role.value,
                    user.full_name,
                    user.email,
                    user.phone,
                    int(user.is_active),
                    user.id,
                ))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"✏️ Updated user: {user.username} (ID: {user.id})")
                return success
                
        except Exception as e:
            app_logger.exception(f"❌ Error updating user {user.id}: {e}")
            raise
    
    def deactivate(self, user_id: int) -> bool:
        """Мягкое удаление пользователя (деактивация)"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND username != 'admin'
                """, (user_id,))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"🔒 Deactivated user ID: {user_id}")
                return success
                
        except Exception as e:
            app_logger.exception(f"❌ Error deactivating user {user_id}: {e}")
            raise
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """Сменить пароль пользователя с безопасным хешированием"""
        if len(new_password) < 6:
            raise ValueError("Password too short")
        
        password_hash, password_salt = self._hash_password_secure(new_password)
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    UPDATE users SET 
                        password = ?, 
                        password_salt = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (password_hash, password_salt, user_id))
                
                success = cur.rowcount > 0
                if success:
                    app_logger.info(f"🔐 Password changed for user ID: {user_id}")
                return success
                
        except Exception as e:
            app_logger.exception(f"❌ Error changing password for user {user_id}: {e}")
            raise
    
    def count(self, active_only: bool = True) -> int:
        """Получить общее количество пользователей"""
        try:
            with self.db.get_cursor() as cur:
                query = "SELECT COUNT(*) FROM users"
                if active_only:
                    query += " WHERE is_active = 1"
                
                return cur.execute(query).fetchone()[0]
                
        except Exception as e:
            app_logger.exception(f"❌ Error counting users: {e}")
            raise