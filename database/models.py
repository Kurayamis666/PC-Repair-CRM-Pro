# models.py (Legacy Fallback)
"""
⚠️ ВНИМАНИЕ: Этот файл устарел.
Используйте модели из папки models/ и сервисы из services/.
Этот файл оставлен только для обратной совместимости старых скриптов.
"""

import hashlib
from typing import Optional, Dict, Any
from database.connection import DatabaseConnection
# ✅ Добавлена поддержка новой системы безопасности
from utils.helpers import verify_password

# Старый SALT для обратной совместимости (если есть старые записи)
LEGACY_SALT = "repair_shop_secure_salt_2024"


def _validate_table_name(table_name: str) -> bool:
    # ✅ ОБНОВЛЕНО: Добавлены employees, убраны clients
    allowed = {
        "users", "employees", "requests", "parts", "directories",
        "contractors", "equipment", "branches", "settings",
        "employee_groups", "part_analogs" 
    }
    return table_name in allowed and table_name.isidentifier()


class BaseModel:
    db = DatabaseConnection()

    @classmethod
    def get_all(cls, table: str, order_by: str = "id DESC"):
        try:
            if not _validate_table_name(table):
                raise ValueError(f"Invalid table: {table}")
            # Безопасный запрос (table validated)
            with cls.db.get_cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table} ORDER BY {order_by}")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting all from {table}: {e}")
            return []

    @classmethod
    def create(cls, table: str, data: Dict[str, Any]):
        try:
            if not _validate_table_name(table):
                raise ValueError(f"Invalid table: {table}")

            # Фильтрация служебных полей
            data = {k: v for k, v in data.items() if k not in ("id", "updated_at") and v is not None}
            if not data:
                return None

            cols = ", ".join(data.keys())
            vals = ", ".join(["?"] * len(data))
            
            with cls.db.get_cursor() as cursor:
                cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({vals})", tuple(data.values()))
                return cursor.lastrowid
        except Exception as e:
            print(f"Error creating {table}: {e}")
            return None

    @classmethod
    def update(cls, table: str, item_id: int, data: Dict[str, Any]) -> bool:
        try:
            if not _validate_table_name(table):
                raise ValueError(f"Invalid table: {table}")
            
            data = {k: v for k, v in data.items() if k not in ("id", "updated_at") and v is not None}
            if not data:
                return True

            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            values = list(data.values()) + [item_id]
            
            with cls.db.get_cursor() as cursor:
                cursor.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", values)
            return True
        except Exception as e:
            print(f"Error updating {table}: {e}")
            return False


class User(BaseModel):
    @classmethod
    def authenticate(cls, username: str, password: str):
        try:
            with cls.db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user_row = cursor.fetchone()
                
                if user_row:
                    user = dict(user_row)
                    db_hash = user.get("password")
                    db_salt = user.get("password_salt")

                    # ✅ НОВАЯ ЛОГИКА: Проверка через PBKDF2 (если есть соль)
                    if db_salt:
                        if verify_password(password, db_hash, db_salt):
                            return user
                    
                    # ⚠️ СТАРАЯ ЛОГИКА: Fallback на SHA256 (для старых записей без соли)
                    elif db_hash:
                        hashed_input = hashlib.sha256((password + LEGACY_SALT).encode()).hexdigest()
                        if hashed_input == db_hash:
                            # Миграция на новый хеш при входе (опционально)
                            return user
                            
        except Exception as e:
            print(f"Authentication error: {e}")
        return None


# ✅ Client переименован в Employee для соответствия схеме, 
# но оставлен алиас Client для старых скриптов
class Employee(BaseModel):
    pass

class Client(Employee):
    """Алиас для обратной совместимости"""
    pass


class Request(BaseModel):
    @classmethod
    def get_with_details(cls, request_id: int):
        try:
            with cls.db.get_cursor() as cursor:
                # ✅ ИСПРАВЛЕНО: JOIN employees вместо clients
                cursor.execute(
                    """SELECT r.*, e.full_name as client_name, eq.model as equipment_model, u.username as technician 
                     FROM requests r 
                     LEFT JOIN employees e ON r.client_id = e.id 
                     LEFT JOIN equipment eq ON r.equipment_id = eq.id 
                     LEFT JOIN users u ON r.user_id = u.id 
                     WHERE r.id = ?""",
                    (request_id,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None


class Part(BaseModel):
    pass


class Directory(BaseModel):
    pass


class Contractor(BaseModel):
    pass


class Report(BaseModel):
    @classmethod
    def get_dashboard_stats(cls):
        try:
            with cls.db.get_cursor() as cursor:
                # Статистика теперь учитывает статусы 'new', 'diagnostics', 'in_progress' как активные
                active = cursor.execute(
                    "SELECT COUNT(*) FROM requests WHERE status NOT IN ('closed','cancelled')"
                ).fetchone()[0] or 0
                
                completed = cursor.execute(
                    "SELECT COUNT(*) FROM requests WHERE status = 'closed'"
                ).fetchone()[0] or 0
                
                costs = cursor.execute(
                    "SELECT COALESCE(SUM(total_cost), 0) FROM requests"
                ).fetchone()[0] or 0.0
                
                # Низкий остаток
                low_stock = cursor.execute(
                    "SELECT COUNT(*) FROM parts WHERE quantity <= min_stock AND quantity > 0"
                ).fetchone()[0] or 0
                
                return {
                    "active": active,
                    "completed": completed,
                    "total_costs": float(costs),
                    "low_stock": low_stock,
                }
        except Exception as e:
            print(f"Stats error: {e}")
            return {"active": 0, "completed": 0, "total_costs": 0.0, "low_stock": 0}