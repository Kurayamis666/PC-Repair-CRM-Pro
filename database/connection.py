# database/connection.py
"""
Модуль подключения и управления базой данных SQLite для PC Repair CRM Pro

✅ СИНХРОНИЗАЦИЯ: Полное соответствие database/schema.sql
✅ БЕЗОПАСНОСТЬ: Поддержка PBKDF2 хеширования паролей
✅ НАДЁЖНОСТЬ: Retry logic, проверка диска, авто-восстановление
✅ ПРОИЗВОДИТЕЛЬНОСТЬ: Индексы, WAL режим, кэширование
"""

import sqlite3
import os
import sys
import hashlib
import time
import shutil
import pathlib
from contextlib import contextmanager
from typing import Optional

from core.logger import app_logger
from utils.helpers import hash_password  # ✅ Импорт для PBKDF2


class DatabaseConnection:
    """
    Singleton класс для работы с базой данных.
    
    ✅ Гарантирует единственное подключение
    ✅ Корректные пути в .exe и скрипт-режиме
    ✅ Авто-перенаправление в AppData при отсутствии прав
    ✅ Проверка целостности и авто-восстановление схемы
    """
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        # 🔍 ОПРЕДЕЛЕНИЕ ПУТИ К БД
        if getattr(sys, 'frozen', False):
            base_dir = pathlib.Path(os.path.dirname(sys.executable))
        else:
            base_dir = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # ✅ Проверка прав и получение пути
        self.db_path = self._get_writable_db_path(base_dir)

        app_logger.debug(
            f"📁 Database path: {self.db_path} "
            f"(frozen={getattr(sys, 'frozen', False)}, writable={os.access(str(self.db_path.parent), os.W_OK)})"
        )

        # ✅ Проверка места на диске
        if not self._check_disk_space(min_mb=50):
            app_logger.error(f"❌ Недостаточно места на диске: {self.db_path.parent}")
            raise RuntimeError(f"Недостаточно места. Требуется: 50 MB, свободно: {self._get_free_space_mb():.1f} MB")

        # ✅ Проверка и создание БД
        if not os.path.exists(self.db_path) or not self._check_tables_exist():
            app_logger.warning(f"📦 База данных не найдена или повреждена. Создаю: {self.db_path}")
            self._create_database()

        # 🔒 Подключение с повторами
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
                self.conn.execute("PRAGMA journal_mode = WAL;")
                self.conn.execute("PRAGMA foreign_keys = ON;")
                self.conn.execute("PRAGMA cache_size = -2000;")  # ✅ 2MB кэш
                self._initialized = True
                self._migrate_database()
                app_logger.info(f"✅ Database connected: {self.db_path}")
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    app_logger.warning(f"⚠️ DB locked, retrying ({attempt+1}/{max_retries})...")
                    time.sleep(1)
                else:
                    raise

    def _get_writable_db_path(self, base_dir: pathlib.Path) -> pathlib.Path:
        """Получить путь к БД с проверкой прав на запись"""
        db_filename = "repair_shop.db"
        
        if os.access(str(base_dir), os.W_OK):
            return base_dir / db_filename
        
        app_logger.warning(f"⚠️ Нет прав на запись в {base_dir}. Перенаправляю БД в AppData.")
        
        try:
            appdata_dir = pathlib.Path(os.environ.get('APPDATA', pathlib.Path.home())) / "PC_Repair_CRM"
            appdata_dir.mkdir(parents=True, exist_ok=True)
            return appdata_dir / db_filename
        except Exception as e:
            app_logger.error(f"❌ Failed to create AppData directory: {e}")
            fallback_dir = pathlib.Path.home() / "PC_Repair_CRM"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            return fallback_dir / db_filename

    def _check_disk_space(self, min_mb: int = 50) -> bool:
        """Проверить наличие минимального места на диске"""
        try:
            total, used, free = shutil.disk_usage(self.db_path.parent if hasattr(self, 'db_path') else os.getcwd())
            free_mb = free // (1024 * 1024)
            app_logger.debug(f"💾 Disk space: {free_mb} MB free (required: {min_mb} MB)")
            return free_mb >= min_mb
        except Exception as e:
            app_logger.warning(f"⚠️ Could not check disk space: {e}")
            return True

    def _get_free_space_mb(self) -> float:
        """Получить свободное место на диске в MB"""
        try:
            total, used, free = shutil.disk_usage(self.db_path.parent if hasattr(self, 'db_path') else os.getcwd())
            return free / (1024 * 1024)
        except:
            return 0.0

    def _check_tables_exist(self) -> bool:
        """Проверка наличия критических таблиц"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # ✅ ОБНОВЛЕНО: employees вместо clients
            critical_tables = ['users', 'branches', 'employees', 'employee_groups', 'requests', 'parts', 'contractors']
            for table in critical_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cursor.fetchone():
                    conn.close()
                    return False
            conn.close()
            return True
        except Exception as e:
            app_logger.warning(f"⚠️ Error checking tables: {e}")
            return False

    def _migrate_database(self):
        """Применить безопасные миграции для существующей БД"""
        try:
            with self.get_cursor() as cur:
                cur.execute("PRAGMA table_info(users)")
                user_columns = {row[1] for row in cur.fetchall()}
                if "branch_id" not in user_columns:
                    cur.execute("ALTER TABLE users ADD COLUMN branch_id INTEGER DEFAULT 1")
                    app_logger.info("✅ Migration applied: users.branch_id")
                cur.execute("UPDATE users SET branch_id = 1 WHERE branch_id IS NULL")
                cur.execute("PRAGMA table_info(employees)")
                employee_columns = {row[1] for row in cur.fetchall()}
                for column, sql in {
                    "address": "ALTER TABLE employees ADD COLUMN address TEXT",
                    "notes": "ALTER TABLE employees ADD COLUMN notes TEXT",
                    "is_active": "ALTER TABLE employees ADD COLUMN is_active INTEGER DEFAULT 1",
                }.items():
                    if column not in employee_columns:
                        cur.execute(sql)
                        app_logger.info(f"✅ Migration applied: employees.{column}")
                # Создаём request_parts если не существует
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='request_parts'")
                if not cur.fetchone():
                    cur.execute('''CREATE TABLE IF NOT EXISTS request_parts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER NOT NULL, part_id INTEGER NOT NULL,
                        quantity INTEGER DEFAULT 1 CHECK(quantity > 0), price REAL DEFAULT 0 CHECK(price >= 0),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
                        FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE)''')
                    app_logger.info("✅ Migration applied: request_parts table created")

                cur.execute("PRAGMA table_info(parts)")
                part_columns = {row[1] for row in cur.fetchall()}
                for column, sql in {
                    "owner_type": "ALTER TABLE parts ADD COLUMN owner_type TEXT DEFAULT 'my'",
                    "type_id": "ALTER TABLE parts ADD COLUMN type_id INTEGER",
                    "nom_type": "ALTER TABLE parts ADD COLUMN nom_type TEXT",
                }.items():
                    if column not in part_columns:
                        cur.execute(sql)
                        app_logger.info(f"✅ Migration applied: parts.{column}")
        except Exception as e:
            app_logger.error(f"❌ Database migration failed: {e}")
            raise

    def _create_database(self):
        """Создание всех таблиц, индексов, триггеров и начальных данных"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            app_logger.error(f"❌ Failed to create directory for database: {e}")
            raise

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # ==================== ТАБЛИЦЫ ====================
        
        # 1. Пользователи ✅ с password_salt
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, password_salt TEXT NOT NULL,
            role TEXT DEFAULT 'manager' CHECK(role IN ('admin', 'manager', 'technician', 'viewer')),
            branch_id INTEGER DEFAULT 1, full_name TEXT, email TEXT, phone TEXT, is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # 2. Филиалы
        cursor.execute('''CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            address TEXT, phone TEXT, email TEXT, is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # 3. Группы сотрудников ✅ (не client_groups!)
        cursor.execute('''CREATE TABLE IF NOT EXISTS employee_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            discount REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 4. Сотрудники ✅ (не clients!)
        cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL,
            position TEXT, phone TEXT, email TEXT,
            address TEXT, group_id INTEGER, balance REAL DEFAULT 0, salary REAL DEFAULT 0, notes TEXT, is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES employee_groups(id))''')

        # 5. Контрагенты
        cursor.execute('''CREATE TABLE IF NOT EXISTS contractors (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, inn TEXT, kpp TEXT,
            phone TEXT, email TEXT, address TEXT, position TEXT, notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # 6. Оборудование
        cursor.execute('''CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER,
            model TEXT NOT NULL, device_type TEXT, serial_number TEXT, color TEXT,
            imei TEXT, password TEXT, accessories TEXT, external_damage TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES employees(id))''')

        # 7. Заявки ✅ с priority
        cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER,
            equipment_id INTEGER, user_id INTEGER, branch_id INTEGER,
            status TEXT DEFAULT 'new' CHECK(status IN ('new', 'diagnostics', 'in_progress', 'ready', 'closed', 'cancelled')),
            priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'urgent')),
            problem_desc TEXT, solution_desc TEXT,
            total_cost REAL DEFAULT 0, labor_cost REAL DEFAULT 0, parts_cost REAL DEFAULT 0,
            planned_date TEXT, closed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES employees(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id))''')

        # 8. Запчасти ✅ с contractor_id
        cursor.execute('''CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, sku TEXT UNIQUE,
            quantity INTEGER DEFAULT 0 CHECK(quantity >= 0),
            cost REAL DEFAULT 0 CHECK(cost >= 0), price REAL DEFAULT 0 CHECK(price >= 0),
            category TEXT, supplier TEXT, owner_type TEXT DEFAULT 'my', contractor_id INTEGER, type_id INTEGER, nom_type TEXT,
            unit TEXT DEFAULT 'шт', min_stock INTEGER DEFAULT 5 CHECK(min_stock >= 0),
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contractor_id) REFERENCES contractors(id))''')

        # 9. Запчасти в заявках
        cursor.execute('''CREATE TABLE IF NOT EXISTS request_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER NOT NULL, part_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1 CHECK(quantity > 0), price REAL DEFAULT 0 CHECK(price >= 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
            FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE)''')

        # 10. Справочники
        cursor.execute('''CREATE TABLE IF NOT EXISTS directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom_type TEXT, unit TEXT, sku TEXT,
            coefficient REAL DEFAULT 1, notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # 10. Аналоги запчастей
        cursor.execute('''CREATE TABLE IF NOT EXISTS part_analogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, part_id INTEGER NOT NULL, analog_id INTEGER NOT NULL,
            FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE,
            FOREIGN KEY (analog_id) REFERENCES parts(id) ON DELETE CASCADE,
            UNIQUE(part_id, analog_id))''')

        # 11. Настройки
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE NOT NULL,
            value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # ==================== ИНДЕКСЫ ====================
        app_logger.debug("📊 Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)",
            "CREATE INDEX IF NOT EXISTS idx_requests_priority ON requests(priority)",
            "CREATE INDEX IF NOT EXISTS idx_requests_client ON requests(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_requests_created ON requests(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_equipment_client ON equipment(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_parts_sku ON parts(sku)",
            "CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category)",
        ]
        for idx in indexes:
            cursor.execute(idx)

        # ==================== ТРИГГЕРЫ (автообновление updated_at) ====================
        app_logger.debug("⚡ Creating triggers...")
        for tbl in ['users', 'employees', 'requests', 'equipment', 'parts', 'contractors']:
            cursor.execute(f'''
                CREATE TRIGGER IF NOT EXISTS trg_{tbl}_updated 
                AFTER UPDATE ON {tbl} 
                BEGIN UPDATE {tbl} SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;
            ''')

        # ==================== НАЧАЛЬНЫЕ ДАННЫЕ ====================
        app_logger.debug("🌱 Inserting initial data...")

        # Настройки
        cursor.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                          [("low_stock_threshold", "5"), ("show_low_stock_button", "1"), ("app_version", "1.0.0")])

        # Филиал
        cursor.execute("INSERT OR IGNORE INTO branches (id, name) VALUES (?, ?)", (1, 'Главный офис'))

        # Группы сотрудников
        for g in ['Розница', 'Опт', 'VIP', 'B2B']:
            cursor.execute("INSERT OR IGNORE INTO employee_groups (name) VALUES (?)", (g,))

        # ✅ Администратор с PBKDF2 хешем
        try:
            # Используем ту же функцию что и в приложении
            pwd_hash, salt = hash_password("123")
            cursor.execute("""
                INSERT INTO users (username, password, password_salt, role, branch_id, full_name) 
                VALUES (?, ?, ?, 'admin', 1, 'Администратор')
            """, ('admin', pwd_hash, salt))
            app_logger.info("✅ Default user 'admin' created with PBKDF2 password")
        except sqlite3.IntegrityError:
            app_logger.info("ℹ️  User 'admin' already exists")

        conn.commit()
        conn.close()
        app_logger.info("🎉 Database schema initialized successfully.")

    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для безопасных транзакций"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            app_logger.error(f"❌ Database transaction failed: {e}")
            raise e

    def commit(self):
        """Явный коммит транзакции"""
        self.conn.commit()

    def optimize(self):
        """Оптимизация базы данных"""
        try:
            with self.get_cursor() as cur:
                cur.execute("VACUUM;")
                cur.execute("ANALYZE;")
                cur.execute("PRAGMA journal_mode=WAL;")
                cur.execute("PRAGMA cache_size=-2000;")
            app_logger.info("✅ Database optimized successfully")
        except Exception as e:
            app_logger.error(f"❌ Database optimization failed: {e}")
            raise

    def close(self):
        """Закрытие соединения"""
        if hasattr(self, 'conn'):
            self.conn.close()
            app_logger.info("🔌 Database connection closed.")