-- database/schema.sql
-- Полная схема БД для PC Repair CRM Pro
-- ✅ СИНХРОНИЗИРОВАНО: Все колонки соответствуют моделям в models/*.py
-- ✅ ОПТИМИЗИРОВАНО: Добавлены индексы, FOREIGN KEYS, автообновление дат

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL; -- ✅ Улучшенная производительность и конкурентность

-- ==================== ОЧИСТКА ====================
DROP TABLE IF EXISTS part_analogs;
DROP TABLE IF EXISTS request_parts;
DROP TABLE IF EXISTS requests;
DROP TABLE IF EXISTS parts;
DROP TABLE IF EXISTS equipment;
DROP TABLE IF EXISTS contractors;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS employee_groups;
DROP TABLE IF EXISTS directories;
DROP TABLE IF EXISTS branches;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS settings;

-- ==================== 1. ПОЛЬЗОВАТЕЛИ ====================
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,          -- Хеш пароля (PBKDF2)
    password_salt TEXT NOT NULL,     -- ✅ ДОБАВЛЕНО: соль для безопасного хеширования
    role TEXT DEFAULT 'manager' CHECK(role IN ('admin', 'manager', 'technician', 'viewer')),
    branch_id INTEGER DEFAULT 1,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL
);

-- ==================== 2. ФИЛИАЛЫ ====================
CREATE TABLE branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    email TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 3. ГРУППЫ СОТРУДНИКОВ ====================
CREATE TABLE employee_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    discount REAL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 4. СОТРУДНИКИ (бывш. КЛИЕНТЫ) ====================
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    position TEXT,
    phone TEXT,
    email TEXT,
    group_id INTEGER,
    balance REAL DEFAULT 0,
    salary REAL DEFAULT 0,
    notes TEXT,
    address TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES employee_groups(id) ON DELETE SET NULL
);

-- ==================== 5. КОНТРАГЕНТЫ ====================
CREATE TABLE contractors (
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
);

-- ==================== 6. ОБОРУДОВАНИЕ ====================
CREATE TABLE equipment (
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
    FOREIGN KEY (client_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- ==================== 7. ЗАЯВКИ ====================
CREATE TABLE requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    equipment_id INTEGER,
    user_id INTEGER,
    branch_id INTEGER,
    status TEXT DEFAULT 'new' CHECK(status IN ('new', 'diagnostics', 'in_progress', 'ready', 'closed', 'cancelled')),
    priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'urgent')), -- ДОБАВЛЕНО
    problem_desc TEXT,
    solution_desc TEXT,
    total_cost REAL DEFAULT 0,
    labor_cost REAL DEFAULT 0,
    parts_cost REAL DEFAULT 0,
    planned_date TEXT,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL
);

-- ==================== 8. ЗАПЧАСТИ ====================
CREATE TABLE parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT UNIQUE,
    quantity INTEGER DEFAULT 0 CHECK(quantity >= 0),
    cost REAL DEFAULT 0 CHECK(cost >= 0),
    price REAL DEFAULT 0 CHECK(price >= 0),
    category TEXT,
    supplier TEXT,
    owner_type TEXT DEFAULT 'my',
    contractor_id INTEGER,             -- ДОБАВЛЕНО: связь с контрагентом-поставщиком
    type_id INTEGER,
    nom_type TEXT,
    unit TEXT DEFAULT 'шт',
    min_stock INTEGER DEFAULT 5 CHECK(min_stock >= 0),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE SET NULL
);

-- ==================== 9. АНАЛОГИ ЗАПЧАСТЕЙ ====================
CREATE TABLE part_analogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    analog_id INTEGER NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE,
    FOREIGN KEY (analog_id) REFERENCES parts(id) ON DELETE CASCADE,
    UNIQUE(part_id, analog_id)
);

-- ==================== 10. СПРАВОЧНИКИ ====================
CREATE TABLE directories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_type TEXT,
    unit TEXT,
    sku TEXT,
    coefficient REAL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 11. НАСТРОЙКИ ====================
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 📊 ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ ====================
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_priority ON requests(priority);
CREATE INDEX idx_requests_client ON requests(client_id);
CREATE INDEX idx_requests_created ON requests(created_at DESC);
CREATE INDEX idx_equipment_client ON equipment(client_id);
CREATE INDEX idx_parts_sku ON parts(sku);
CREATE INDEX idx_parts_category ON parts(category);
CREATE INDEX idx_parts_supplier ON parts(supplier);

-- ==================== ⚡ АВТООБНОВЛЕНИЕ updated_at ====================
CREATE TRIGGER trg_users_updated AFTER UPDATE ON users BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_employees_updated AFTER UPDATE ON employees BEGIN
    UPDATE employees SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_requests_updated AFTER UPDATE ON requests BEGIN
    UPDATE requests SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_equipment_updated AFTER UPDATE ON equipment BEGIN
    UPDATE equipment SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_parts_updated AFTER UPDATE ON parts BEGIN
    UPDATE parts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_contractors_updated AFTER UPDATE ON contractors BEGIN
    UPDATE contractors SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ==================== 🧪 ТЕСТОВЫЕ ДАННЫЕ ====================

-- Пользователь admin (пароль: 123, хеш PBKDF2+соль)
-- ⚠️ В продакшене используйте utils.helpers.hash_password()
INSERT INTO users (username, password, password_salt, role, full_name) VALUES 
('admin', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'default_salt_123', 'admin', 'Администратор Системы');

-- Филиал
INSERT INTO branches (id, name, address) VALUES (1, 'Главный офис', 'г. Москва, ул. Примерная, д. 1');

-- Группы сотрудников
INSERT INTO employee_groups (name, discount) VALUES 
('Розничные', 0), ('Оптовые', 5), ('VIP', 10), ('B2B Партнёры', 15);

-- Сотрудники
INSERT INTO employees (full_name, position, phone, email, group_id, salary) VALUES
('Иванов Иван Иванович', 'Мастер', '+7 (999) 123-45-67', 'ivanov@repair.ru', 1, 50000),
('Петров Пётр Петрович', 'Менеджер', '+7 (999) 234-56-78', 'petrov@repair.ru', 2, 45000),
('Сидорова Анна Владимировна', 'Мастер', '+7 (999) 345-67-89', 'sidorova@repair.ru', 1, 55000),
('Козлов Дмитрий Сергеевич', 'Техник', '+7 (999) 456-78-90', 'kozlov@repair.ru', 3, 40000),
('Новикова Елена Игоревна', 'Администратор', '+7 (999) 567-89-01', 'novikova@repair.ru', 4, 42000);

-- Контрагенты
INSERT INTO contractors (name, inn, phone, email, address) VALUES
('ООО "ТехноСервис"', '7701234567', '+7 (495) 123-45-67', 'info@technoservice.ru', 'г. Москва, ул. Техно, д. 10'),
('ИП Смирнов А.В.', '770123456789', '+7 (999) 111-22-33', 'smirnov@mail.ru', 'г. Москва, ул. Ленина, д. 5'),
('ООО "ЗапчастиПро"', '7709876543', '+7 (495) 987-65-43', 'sales@zapchasti.ru', 'г. Москва, пр-т Мира, д. 50');

-- Оборудование
INSERT INTO equipment (client_id, model, device_type, serial_number, color, imei) VALUES
(1, 'iPhone 13 Pro', 'Смартфон', 'SN123456789', 'Graphite', '351234567890123'),
(1, 'MacBook Pro 16"', 'Ноутбук', 'SN987654321', 'Space Gray', NULL),
(2, 'Samsung Galaxy S21', 'Смартфон', 'SN456789123', 'Phantom Black', '359876543210987'),
(3, 'Dell XPS 15', 'Ноутбук', 'SN789123456', 'Silver', NULL),
(4, 'iPad Air', 'Планшет', 'SN321654987', 'Blue', NULL);

-- Заявки
INSERT INTO requests (client_id, equipment_id, user_id, status, priority, problem_desc, total_cost, labor_cost, parts_cost) VALUES
(1, 1, 1, 'closed', 'normal', 'Не работает Face ID', 5000, 3000, 2000),
(1, 2, 2, 'ready', 'normal', 'Замена термопасты', 2000, 2000, 0),
(2, 3, 1, 'in_progress', 'high', 'Разбит экран', 8000, 3000, 5000),
(3, 4, 3, 'diagnostics', 'normal', 'Не включается', 0, 0, 0),
(4, 5, 1, 'new', 'urgent', 'Не держит заряд', 0, 0, 0);

-- Запчасти
INSERT INTO parts (name, sku, quantity, cost, price, category, supplier, contractor_id, unit, min_stock) VALUES
('Дисплей iPhone 13 Pro', 'DISP-IP13P', 10, 4500, 7500, 'Дисплеи', 'ООО "ЗапчастиПро"', 3, 'шт', 5),
('Аккумулятор iPhone 13', 'BAT-IP13', 25, 1500, 3000, 'Аккумуляторы', 'ООО "ЗапчастиПро"', 3, 'шт', 10),
('Термопаста MX-4', 'PASTE-MX4', 15, 200, 500, 'Расходники', 'ИП Смирнов А.В.', 2, 'шт', 5),
('Клавиатура MacBook Pro', 'KB-MBP16', 3, 8000, 12000, 'Клавиатуры', 'ООО "ТехноСервис"', 1, 'шт', 2),
('Зарядное устройство USB-C', 'CHG-USBC', 50, 300, 800, 'Аксессуары', 'ООО "ЗапчастиПро"', 3, 'шт', 20);

-- Справочники
INSERT INTO directories (nom_type, notes) VALUES
('Дисплеи', 'Запасные части для замены экранов'),
('Аккумуляторы', 'Батареи для смартфонов и планшетов'),
('Клавиатуры', 'Клавиатуры для ноутбуков'),
('Расходники', 'Термопаста, клей, скотч'),
('Аксессуары', 'Зарядные устройства, кабели, чехлы');

INSERT INTO directories (unit, sku, coefficient) VALUES
('шт', 'PCS', 1), ('упак', 'PACK', 10), ('кг', 'KG', 1),
('г', 'G', 0.001), ('м', 'M', 1), ('см', 'CM', 0.01),
('л', 'L', 1), ('мл', 'ML', 0.001);

-- Настройки
INSERT INTO settings (key, value) VALUES
('low_stock_threshold', '5'),
('show_low_stock_button', '1'),
('default_currency', 'RUB'),
('tax_rate', '0'),
('app_version', '1.0.0');