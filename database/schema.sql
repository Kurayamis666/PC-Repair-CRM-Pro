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

-- ==================== 8.1. ЗАПЧАСТИ В ЗАЯВКАХ ====================
CREATE TABLE request_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1 CHECK(quantity > 0),
    price REAL DEFAULT 0 CHECK(price >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
    FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE
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

-- ==================== 🧪 ТЕСТОВЫЕ ДАННЫЕ (ПОЛНЫЕ) ====================

-- Филиалы (ПЕРВЫМ — от них зависят users)
INSERT INTO branches (id, name, address, phone, email) VALUES 
(1, 'Главный офис', 'г. Москва, ул. Тверская, д. 15', '+7 (495) 100-10-10', 'main@repair-crm.ru'),
(2, 'Филиал Юг', 'г. Москва, ул. Каширское ш., д. 24', '+7 (495) 200-20-20', 'south@repair-crm.ru'),
(3, 'Филиал Север', 'г. Москва, Ленинградский пр-т, д. 80', '+7 (495) 300-30-30', 'north@repair-crm.ru');

-- Пользователь admin (пароль: 123, хеш PBKDF2+соль)
INSERT INTO users (username, password, password_salt, role, full_name, email, phone, branch_id) VALUES 
('admin', '2e6af479515abed56a23a68edfa976fb53650349eb3ce13980ee8a4d463de0a8', 'default_salt_123', 'admin', 'Главный Администратор', 'admin@repair-crm.ru', '+7 (495) 100-00-01', 1);

-- Группы сотрудников
INSERT INTO employee_groups (name, discount, notes) VALUES 
('Розничные', 0, 'Стандартная группа без скидок'),
('Оптовые', 5, 'Скидка 5% для оптовых заказов'),
('VIP', 10, 'Привилегированные клиенты со скидкой 10%'),
('B2B Партнёры', 15, 'Корпоративные партнёры');

-- Сотрудники (расширенный набор)
INSERT INTO employees (full_name, position, phone, email, group_id, salary, address, notes) VALUES
('Иванов Иван Иванович', 'Старший мастер', '+7 (999) 123-45-67', 'ivanov@repair-crm.ru', 1, 65000, 'г. Москва, ул. Арбат, д. 5, кв. 12', 'Опыт работы 7 лет, специализация — Apple'),
('Петров Пётр Петрович', 'Менеджер по приёмке', '+7 (999) 234-56-78', 'petrov@repair-crm.ru', 2, 48000, 'г. Москва, ул. Садовая, д. 10', 'Ответственный за приёмку оборудования'),
('Сидорова Анна Владимировна', 'Мастер по ремонту', '+7 (999) 345-67-89', 'sidorova@repair-crm.ru', 1, 58000, 'г. Москва, пр-т Вернадского, д. 33', 'Специализация — ноутбуки и ПК'),
('Козлов Дмитрий Сергеевич', 'Техник-диагност', '+7 (999) 456-78-90', 'kozlov@repair-crm.ru', 3, 42000, 'г. Москва, ул. Ленина, д. 8', 'Диагностика и пайка микросхем'),
('Новикова Елена Игоревна', 'Офис-менеджер', '+7 (999) 567-89-01', 'novikova@repair-crm.ru', 4, 44000, 'г. Москва, Кутузовский пр-т, д. 22', 'Ведение документации и отчётности'),
('Морозов Алексей Павлович', 'Мастер по ремонту', '+7 (916) 111-22-33', 'morozov@repair-crm.ru', 1, 55000, 'г. Москва, ул. Профсоюзная, д. 44', 'Специализация — Samsung и Xiaomi'),
('Волкова Мария Сергеевна', 'Приёмщик', '+7 (926) 222-33-44', 'volkova@repair-crm.ru', 2, 38000, 'г. Москва, Бульварное кольцо, д. 7', 'Приём заказов и выдача оборудования'),
('Соколов Артём Дмитриевич', 'Инженер', '+7 (903) 333-44-55', 'sokolov@repair-crm.ru', 1, 62000, 'г. Москва, ул. Шаболовка, д. 19', 'Ремонт планшетов и игровых консолей'),
('Кузнецова Ольга Николаевна', 'Бухгалтер', '+7 (915) 444-55-66', 'kuznetsova@repair-crm.ru', 4, 50000, 'г. Москва, Нахимовский пр-т, д. 31', 'Финансовая отчётность'),
('Лебедев Максим Игоревич', 'Курьер', '+7 (977) 555-66-77', 'lebedev@repair-crm.ru', 2, 35000, 'г. Москва, ул. Новослободская, д. 14', 'Доставка оборудования клиентам');

-- Контрагенты (расширенный набор)
INSERT INTO contractors (name, inn, kpp, phone, email, address, position, notes) VALUES
('ООО "ТехноСервис"', '7701234567', '770101001', '+7 (495) 123-45-67', 'info@technoservice.ru', 'г. Москва, ул. Техническая, д. 10', 'Поставщик', 'Основной поставщик комплектующих Apple'),
('ИП Смирнов А.В.', '770123456789', NULL, '+7 (999) 111-22-33', 'smirnov@mail.ru', 'г. Москва, ул. Ленина, д. 5', 'Поставщик', 'Расходные материалы и инструменты'),
('ООО "ЗапчастиПро"', '7709876543', '770901001', '+7 (495) 987-65-43', 'sales@zapchasti-pro.ru', 'г. Москва, пр-т Мира, д. 50', 'Поставщик', 'Дисплеи, аккумуляторы, шлейфы'),
('ООО "МобилТех"', '7712345678', '771201001', '+7 (495) 555-11-22', 'info@mobiltech.ru', 'г. Санкт-Петербург, Невский пр-т, д. 100', 'Поставщик', 'Запчасти для Samsung и Xiaomi'),
('ООО "ПартнёрСофт"', '7715678901', '771501001', '+7 (495) 777-88-99', 'support@partnersoft.ru', 'г. Москва, ул. Бауманская, д. 33', 'Сервисный центр', 'Аутсорсинг сложных ремонтов'),
('ООО "ЭлектроМир"', '7718901234', '771801001', '+7 (495) 444-55-66', 'zakaz@electromir.ru', 'г. Екатеринбург, ул. 8 Марта, д. 46', 'Поставщик', 'Силовая электроника и блоки питания');

-- Оборудование (расширенный набор — 15 единиц)
INSERT INTO equipment (client_id, model, device_type, serial_number, color, imei, accessories, external_damage) VALUES
(1, 'iPhone 14 Pro Max', 'Смартфон', 'SN-IP14PM-001', 'Deep Purple', '351234567890123', 'Чехол, зарядка', 'Царапина на задней крышке'),
(1, 'MacBook Pro 16" M2', 'Ноутбук', 'SN-MBP16-002', 'Space Gray', NULL, 'Зарядка USB-C', 'Без повреждений'),
(2, 'Samsung Galaxy S23 Ultra', 'Смартфон', 'SN-SGS23U-003', 'Phantom Black', '359876543210987', 'S Pen, чехол', 'Трещина экрана'),
(3, 'Dell XPS 15 9530', 'Ноутбук', 'SN-DXPS15-004', 'Platinum Silver', NULL, 'Зарядка, сумка', 'Без повреждений'),
(4, 'iPad Air 5', 'Планшет', 'SN-IPAD5-005', 'Blue', NULL, 'Apple Pencil', 'Вмятина на корпусе'),
(5, 'Xiaomi 13 Pro', 'Смартфон', 'SN-XM13P-006', 'Ceramic Black', '862345678901234', 'Зарядка 120W', 'Без повреждений'),
(6, 'ASUS ROG Phone 7', 'Смартфон', 'SN-ASROG7-007', 'Phantom Black', '867890123456789', 'Кулер AeroActive', 'Сколы по углам'),
(7, 'HP Spectre x360', 'Ноутбук', 'SN-HPSX360-008', 'Nightfall Black', NULL, 'Стилус, зарядка', 'Без повреждений'),
(8, 'Google Pixel 7 Pro', 'Смартфон', 'SN-GP7P-009', 'Obsidian', '354567890123456', 'Зарядка', 'Потёртости на рамке'),
(3, 'Lenovo ThinkPad X1 Carbon', 'Ноутбук', 'SN-LTPX1-010', 'Black', NULL, 'Док-станция, зарядка', 'Без повреждений'),
(2, 'Apple Watch Series 8', 'Умные часы', 'SN-AW8-011', 'Midnight', NULL, 'Магнитная зарядка', 'Царапина на стекле'),
(1, 'AirPods Pro 2', 'Наушники', 'SN-APP2-012', 'White', NULL, 'Кейс MagSafe', 'Без повреждений'),
(4, 'Nintendo Switch OLED', 'Игровая консоль', 'SN-NSW-013', 'White', NULL, 'Joy-Con, зарядка', 'Сколы на Joy-Con'),
(5, 'Sony PlayStation 5', 'Игровая консоль', 'SN-PS5-014', 'White', NULL, 'DualSense, кабели', 'Без повреждений'),
(9, 'Huawei MateBook 14s', 'Ноутбук', 'SN-HWMB14-015', 'Space Gray', NULL, 'Зарядка USB-C', 'Потёртости на клавиатуре');

-- Заявки (расширенный набор — 25 заявок с разными статусами)
INSERT INTO requests (client_id, equipment_id, user_id, branch_id, status, priority, problem_desc, solution_desc, total_cost, labor_cost, parts_cost, created_at) VALUES
(1, 1, 1, 1, 'closed', 'normal', 'Не работает Face ID после падения', 'Заменён модуль Face ID, калибровка выполнена', 8500, 3500, 5000, '2025-04-01 10:30:00'),
(1, 2, 1, 1, 'closed', 'normal', 'Перегрев при нагрузке, шум вентилятора', 'Замена термопасты, чистка системы охлаждения', 3500, 2500, 1000, '2025-04-05 14:00:00'),
(2, 3, 1, 1, 'in_progress', 'high', 'Разбит экран — не реагирует на касания', 'Заказан оригинальный дисплей AMOLED', 15000, 5000, 10000, '2025-04-10 09:15:00'),
(3, 4, 1, 1, 'diagnostics', 'normal', 'Ноутбук не включается, индикатор не горит', NULL, 0, 0, 0, '2025-04-15 11:45:00'),
(4, 5, 1, 1, 'new', 'urgent', 'Планшет не держит заряд более 1 часа', NULL, 0, 0, 0, '2025-04-20 16:30:00'),
(5, 6, 1, 2, 'ready', 'normal', 'Не заряжается, разъём расшатан', 'Замена разъёма зарядки', 4500, 2000, 2500, '2025-04-22 10:00:00'),
(6, 7, 1, 2, 'in_progress', 'high', 'Перегрев при играх, тротлинг процессора', 'Замена термопрокладок и пасты', 6000, 3000, 3000, '2025-04-25 13:20:00'),
(7, 8, 1, 3, 'closed', 'low', 'Скрипит петля экрана', 'Смазка петель, подтяжка винтов', 1500, 1500, 0, '2025-03-15 08:00:00'),
(8, 9, 1, 3, 'new', 'normal', 'Камера перестала фокусироваться', NULL, 0, 0, 0, '2025-05-01 12:00:00'),
(3, 10, 1, 1, 'ready', 'normal', 'Не работает клавиатура — залита кофе', 'Чистка ультразвуком, замена клавиатурного модуля', 9500, 3000, 6500, '2025-03-20 15:30:00'),
(2, 11, 1, 1, 'closed', 'low', 'Не синхронизируются данные с iPhone', 'Перепривязка через Apple ID, обновление watchOS', 2000, 2000, 0, '2025-03-25 09:00:00'),
(1, 12, 1, 1, 'diagnostics', 'normal', 'Один наушник не работает', NULL, 0, 0, 0, '2025-05-05 14:15:00'),
(4, 13, 1, 2, 'in_progress', 'normal', 'Дрифт джойстика, самопроизвольное движение', 'Замена аналогового стика Joy-Con', 3500, 1500, 2000, '2025-04-28 17:00:00'),
(5, 14, 1, 2, 'new', 'high', 'Артефакты изображения на экране ТВ', NULL, 0, 0, 0, '2025-05-08 10:30:00'),
(9, 15, 1, 3, 'diagnostics', 'normal', 'Мерцание экрана при яркости ниже 50%', NULL, 0, 0, 0, '2025-05-10 11:00:00'),
(1, 1, 1, 1, 'new', 'low', 'Замена защитного стекла', NULL, 0, 0, 0, '2025-05-12 09:00:00'),
(2, 3, 1, 1, 'cancelled', 'normal', 'Замена корпуса — клиент отказался', NULL, 0, 0, 0, '2025-03-10 10:00:00'),
(6, 7, 1, 2, 'closed', 'urgent', 'Не включается после обновления прошивки', 'Перепрошивка через EDL, восстановление данных', 5000, 4000, 1000, '2025-02-20 14:00:00'),
(7, 8, 1, 3, 'ready', 'normal', 'Замена SSD — мало места', 'Установлен Samsung 980 Pro 1TB', 12000, 2000, 10000, '2025-04-02 16:00:00'),
(8, 9, 1, 3, 'in_progress', 'normal', 'Замена экрана — выгорание OLED', 'Заказан оригинальный OLED-дисплей', 18000, 3000, 15000, '2025-05-02 13:00:00'),
(3, 10, 1, 1, 'closed', 'high', 'Не загружается ОС, синий экран', 'Переустановка Windows 11, восстановление данных', 4000, 3500, 500, '2025-01-15 09:30:00'),
(4, 5, 1, 1, 'closed', 'normal', 'Замена стекла экрана', 'Установлено закалённое стекло', 6000, 2000, 4000, '2025-02-10 11:00:00'),
(5, 6, 1, 2, 'diagnostics', 'urgent', 'Попала влага, не включается', NULL, 0, 0, 0, '2025-05-11 08:30:00'),
(9, 15, 1, 3, 'new', 'normal', 'Тихий звук динамиков', NULL, 0, 0, 0, '2025-05-13 10:00:00'),
(10, 15, 1, 3, 'new', 'low', 'Установка Linux, двойная загрузка', NULL, 0, 0, 0, '2025-05-13 14:00:00');

-- Запчасти (расширенный набор — 15 позиций)
INSERT INTO parts (name, sku, quantity, cost, price, category, supplier, contractor_id, unit, min_stock, notes) VALUES
('Дисплей iPhone 14 Pro Max (OLED)', 'DISP-IP14PM', 8, 12000, 18000, 'Дисплеи', 'ООО "ЗапчастиПро"', 3, 'шт', 3, 'Оригинальный OLED Super Retina XDR'),
('Дисплей Samsung S23 Ultra (AMOLED)', 'DISP-SGS23U', 5, 10000, 16000, 'Дисплеи', 'ООО "МобилТех"', 4, 'шт', 2, 'Оригинальный Dynamic AMOLED 2X'),
('Аккумулятор iPhone 14 Pro Max', 'BAT-IP14PM', 20, 2500, 4500, 'Аккумуляторы', 'ООО "ЗапчастиПро"', 3, 'шт', 8, 'Оригинал, 4323 мАч'),
('Аккумулятор iPad Air 5', 'BAT-IPAD5', 10, 3000, 5500, 'Аккумуляторы', 'ООО "ЗапчастиПро"', 3, 'шт', 5, 'Оригинал, 28.6 Вт·ч'),
('Термопаста Arctic MX-6', 'PASTE-MX6', 30, 350, 800, 'Расходники', 'ИП Смирнов А.В.', 2, 'шт', 10, 'Высокоэффективная, 8.5 Вт/мК'),
('Термопрокладки Thermal Grizzly 1мм', 'TPAD-TG1', 25, 200, 500, 'Расходники', 'ИП Смирнов А.В.', 2, 'упак', 8, 'Размер 120x20мм'),
('Клавиатура MacBook Pro 16" M2', 'KB-MBP16M2', 4, 9000, 14000, 'Клавиатуры', 'ООО "ТехноСервис"', 1, 'шт', 2, 'Русская раскладка, подсветка'),
('Клавиатура Lenovo ThinkPad X1', 'KB-TPX1', 6, 5500, 8500, 'Клавиатуры', 'ООО "ТехноСервис"', 1, 'шт', 3, 'Русская раскладка, TrackPoint'),
('Зарядное устройство USB-C 65W', 'CHG-USBC65', 40, 450, 1200, 'Аксессуары', 'ООО "ЗапчастиПро"', 3, 'шт', 15, 'GaN, Type-C PD 3.0'),
('Зарядное устройство MagSafe 15W', 'CHG-MAGSAFE', 15, 800, 2000, 'Аксессуары', 'ООО "ЗапчастиПро"', 3, 'шт', 5, 'Беспроводная зарядка Apple'),
('SSD Samsung 980 Pro 1TB', 'SSD-S980P1T', 7, 6500, 10000, 'Накопители', 'ООО "ЭлектроМир"', 6, 'шт', 3, 'NVMe M.2, 7000 МБ/с'),
('Модуль Face ID iPhone 14', 'FACEID-IP14', 3, 4500, 7000, 'Модули', 'ООО "ЗапчастиПро"', 3, 'шт', 2, 'Оригинальный модуль TrueDepth'),
('Разъём зарядки Type-C (универсал)', 'CONN-USBC', 50, 80, 300, 'Разъёмы', 'ИП Смирнов А.В.', 2, 'шт', 20, 'Совместим с большинством моделей'),
('Стик аналоговый Joy-Con', 'STICK-JOYCON', 12, 250, 600, 'Игровые', 'ООО "МобилТех"', 4, 'шт', 5, 'Совместим с Nintendo Switch'),
('Защитное стекло iPhone 14 Pro Max', 'GLASS-IP14PM', 100, 150, 500, 'Аксессуары', 'ООО "ЗапчастиПро"', 3, 'шт', 30, '9H, олеофобное покрытие');

-- Запчасти в заявках (связи)
INSERT INTO request_parts (request_id, part_id, quantity, price) VALUES
(1, 12, 1, 7000),
(2, 5, 1, 800),
(3, 2, 1, 16000),
(6, 13, 1, 300),
(7, 5, 1, 800),
(7, 6, 2, 500),
(10, 8, 1, 8500),
(13, 14, 2, 600),
(19, 11, 1, 10000),
(20, 2, 1, 16000);

-- Аналоги запчастей
INSERT INTO part_analogs (part_id, analog_id) VALUES
(1, 2),
(3, 4),
(5, 6),
(9, 10);

-- Справочники — типы номенклатуры
INSERT INTO directories (nom_type, notes) VALUES
('Дисплеи', 'Экраны для смартфонов, планшетов и ноутбуков'),
('Аккумуляторы', 'Батареи для мобильных устройств'),
('Клавиатуры', 'Клавиатурные модули для ноутбуков'),
('Расходники', 'Термопаста, термопрокладки, клей, скотч'),
('Аксессуары', 'Зарядные устройства, кабели, чехлы, стёкла'),
('Накопители', 'SSD, HDD, карты памяти'),
('Модули', 'Камеры, датчики, модули связи'),
('Разъёмы', 'Разъёмы зарядки, USB, аудио'),
('Игровые', 'Компоненты для игровых консолей');

-- Справочники — единицы измерения
INSERT INTO directories (unit, sku, coefficient) VALUES
('шт', 'PCS', 1), ('упак', 'PACK', 10), ('кг', 'KG', 1),
('г', 'G', 0.001), ('м', 'M', 1), ('см', 'CM', 0.01),
('л', 'L', 1), ('мл', 'ML', 0.001), ('компл', 'SET', 1);

-- Настройки
INSERT INTO settings (key, value) VALUES
('low_stock_threshold', '5'),
('show_low_stock_button', '1'),
('default_currency', 'RUB'),
('tax_rate', '0'),
('app_version', '2.0.0'),
('company_name', 'PC Repair CRM Pro'),
('company_phone', '+7 (495) 100-10-10'),
('company_email', 'info@repair-crm.ru');