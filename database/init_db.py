# database/init_db.py
"""
Инициализация базы данных для PC Repair CRM Pro
✅ СИНХРОНИЗАЦИЯ: Полное соответствие database/schema.sql
✅ БЕЗОПАСНОСТЬ: PBKDF2 хеширование паролей, поддержка соли
✅ ОПТИМИЗАЦИЯ: Добавлены индексы и триггеры
"""

import sqlite3
import os
import sys
import hashlib
import random
import string
from datetime import datetime

def get_db_path():
    """Получить путь к базе данных"""
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(application_path, "repair_shop.db")

def generate_pbkdf2_password(password: str) -> tuple[str, str]:
    """Генерация PBKDF2 хеша и соли (как в utils.helpers)"""
    salt = os.urandom(32).hex()  # 64 символа
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return pwd_hash, salt

def init_database():
    """Создание всех таблиц, индексов, триггеров и начальных данных"""
    
    db_path = get_db_path()
    print(f"📁 Путь к БД: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    
    print("📦 Создание структуры базы данных...")
    
    # ==================== ТАБЛИЦЫ ====================
    
    # 1. Пользователи
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            role TEXT DEFAULT 'manager' CHECK(role IN ('admin', 'manager', 'technician', 'viewer')),
            full_name TEXT,
            email TEXT,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Филиалы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Группы сотрудников
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            discount REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Сотрудники
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            position TEXT,
            phone TEXT,
            email TEXT,
            group_id INTEGER,
            balance REAL DEFAULT 0,
            salary REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES employee_groups(id)
        )
    """)

    # 5. Контрагенты
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contractors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            inn TEXT,
            kpp TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            position TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Оборудование
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            model TEXT NOT NULL,
            device_type TEXT,
            serial_number TEXT,
            color TEXT,
            imei TEXT,
            password TEXT,
            accessories TEXT,
            external_damage TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES employees(id)
        )
    """)

    # 7. Заявки
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            equipment_id INTEGER,
            user_id INTEGER,
            branch_id INTEGER,
            status TEXT DEFAULT 'new' CHECK(status IN ('new', 'diagnostics', 'in_progress', 'ready', 'closed', 'cancelled')),
            priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'urgent')),
            problem_desc TEXT,
            solution_desc TEXT,
            total_cost REAL DEFAULT 0,
            labor_cost REAL DEFAULT 0,
            parts_cost REAL DEFAULT 0,
            planned_date TEXT,
            closed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES employees(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
    """)

    # 8. Запчасти
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE,
            quantity INTEGER DEFAULT 0 CHECK(quantity >= 0),
            cost REAL DEFAULT 0 CHECK(cost >= 0),
            price REAL DEFAULT 0 CHECK(price >= 0),
            category TEXT,
            supplier TEXT,
            contractor_id INTEGER,
            unit TEXT DEFAULT 'шт',
            min_stock INTEGER DEFAULT 5 CHECK(min_stock >= 0),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contractor_id) REFERENCES contractors(id)
        )
    """)

    # 9. Справочники
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_type TEXT,
            unit TEXT,
            sku TEXT,
            coefficient REAL DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 10. Аналоги
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS part_analogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL,
            analog_id INTEGER NOT NULL,
            FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE,
            FOREIGN KEY (analog_id) REFERENCES parts(id) ON DELETE CASCADE,
            UNIQUE(part_id, analog_id)
        )
    """)

    # 11. Настройки
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==================== ИНДЕКСЫ ====================
    print("📊 Создание индексов...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_priority ON requests(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_client ON requests(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_created ON requests(created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_client ON equipment(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_sku ON parts(sku)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category)")

    # ==================== ТРИГГЕРЫ (Автообновление даты) ====================
    print("⚡ Создание триггеров...")
    triggers = {
        'users': 'users', 'employees': 'employees', 'requests': 'requests',
        'equipment': 'equipment', 'parts': 'parts', 'contractors': 'contractors'
    }
    for tbl in triggers.values():
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS trg_{tbl}_updated 
            AFTER UPDATE ON {tbl} 
            BEGIN UPDATE {tbl} SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;
        """)

    # ==================== НАЧАЛЬНЫЕ ДАННЫЕ ====================
    print("🌱 Загрузка начальных данных...")

    # Настройки
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('low_stock_threshold', '5')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('show_low_stock_button', '1')")

    # Филиал
    cursor.execute("INSERT OR IGNORE INTO branches (id, name) VALUES (1, 'Главный офис')")

    # Группы
    for g in ['Розница', 'Опт', 'VIP', 'B2B']:
        cursor.execute("INSERT OR IGNORE INTO employee_groups (name) VALUES (?)", (g,))

    # Администратор (PBKDF2)
    try:
        pwd, salt = generate_pbkdf2_password("123")
        cursor.execute("""
            INSERT INTO users (username, password, password_salt, role, full_name) 
            VALUES (?, ?, ?, 'admin', 'Администратор')
        """, ('admin', pwd, salt))
        print("✅ Пользователь admin создан (пароль: 123)")
    except sqlite3.IntegrityError:
        print("ℹ️  Пользователь admin уже существует")

    conn.commit()
    conn.close()
    
    print("\n🎉 База данных успешно инициализирована!")

if __name__ == "__main__":
    init_database()
    input("\nНажмите Enter для выхода...")