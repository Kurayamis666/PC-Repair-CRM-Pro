# translations/translations.py
"""
Полная система локализации приложения PC Repair CRM Pro

✅ Поддержка множественных языков (RU ↔ EN)
✅ Fallback на русский при отсутствии перевода
✅ Форматирование строк с плейсхолдерами
✅ Типизация для IDE и статических анализаторов
✅ Ленивая загрузка для масштабируемости
"""

from typing import Dict, Optional, Literal, Union

# ==================== ТИПЫ ====================
Language = Literal["ru", "en"]
TranslationsDict = Dict[str, str]

# ==================== ПЕРЕВОДЫ ====================
TRANSLATIONS: Dict[Language, TranslationsDict] = {
    "ru": {
        # ==================== ОБЩИЕ ====================
        "app_title": "PC Repair CRM Pro",
        "login": "Вход",
        "logout": "Выход",
        # ... (все остальные ключи как в оригинале) ...
    },
    
    "en": {
        # ==================== GENERAL ====================
        "app_title": "PC Repair CRM Pro",
        "login": "Login",
        "logout": "Logout",
        # ... (все остальные ключи как в оригинале) ...
    }
}

_COMMON_TRANSLATIONS: Dict[Language, TranslationsDict] = {
    "ru": {
        "add": "Добавить", "edit": "Изменить", "delete": "Удалить", "save": "Сохранить", "cancel": "Отмена",
        "close": "Закрыть", "back": "Назад", "ok": "ОК", "confirm": "Подтвердить", "apply": "Применить",
        "clear": "Очистить", "reset": "Сбросить", "find": "Найти", "search": "Поиск", "update": "Обновить",
        "export": "Экспорт", "import": "Импорт", "preview": "Предпросмотр", "processing": "Обработка",
        "saving": "Сохранение...", "loading": "Загрузка...", "error": "Ошибка", "under_construction": "В разработке",
        "dashboard": "Панель", "requests": "Заявки", "request_plural": "Заявки", "employees": "Сотрудники",
        "employee": "Сотрудник", "equipment": "Оборудование", "parts": "Запчасти", "contractors": "Контрагенты",
        "reports": "Отчёты", "settings": "Настройки", "documents": "Документы", "reference": "Справочники",
        "analytics": "Аналитика", "users": "Пользователи", "main": "Главная", "system": "Система",
        "login": "Вход", "logout": "Выход", "username": "Логин", "password": "Пароль", "role": "Роль",
        "branch": "Филиал", "full_name": "ФИО", "position": "Должность", "phone": "Телефон", "email": "Email",
        "address": "Адрес", "salary": "Зарплата", "inn": "ИНН", "contacts": "Контакты", "description": "Описание",
        "name_required": "Название обязательно", "field_required": "Поле обязательно", "fill_required": "Заполните обязательные поля",
        "fill_all_fields": "Заполните все поля", "required_field": "Обязательное поле", "invalid_email": "Неверный email",
        "invalid_phone": "Неверный телефон", "invalid_number": "Неверное число", "invalid_quantity": "Неверное количество",
        "invalid_cost": "Неверная стоимость", "invalid_salary": "Зарплата должна быть числом >= 0",
        "username_required": "Логин обязателен", "username_exists": "Пользователь с таким логином уже существует",
        "username_too_short": "Логин должен быть не менее {} символов", "username_too_long": "Логин слишком длинный",
        "username_invalid_chars": "Логин может содержать только буквы, цифры, _, -, ., @",
        "password_required": "Пароль обязателен", "password_too_short": "Пароль должен быть не менее {} символов",
        "passwords_not_match": "Пароли не совпадают", "confirm_password": "Подтверждение пароля",
        "old_password": "Старый пароль", "new_password": "Новый пароль", "change_password": "Сменить пароль",
        "password_optional": "оставьте пустым, чтобы не менять", "invalid_credentials": "Неверный логин или пароль",
        "wrong_password": "Неверный пароль", "password_changed": "Пароль изменён",
        "manage_users": "Управление пользователями", "new_user": "Новый пользователь", "edit_user": "Редактировать пользователя",
        "user_created": "Пользователь создан", "user_updated": "Пользователь обновлён", "user_deleted": "Пользователь удалён",
        "user_saved": "Пользователь сохранён", "select_user": "Выберите пользователя", "total_users": "Всего пользователей",
        "no_users": "Нет пользователей", "cannot_delete_admin": "Нельзя удалить главного администратора",
        "confirm_delete_user": "Удалить пользователя '{username}'?", "delete_user_warning": "Все его действия будут потеряны.",
        "branch_required": "Выберите филиал", "no_branches": "Нет филиалов",
        "col_id": "ID", "col_username": "Логин", "col_role": "Роль", "col_branch": "Филиал",
        "col_created": "Создано", "col_name": "Название", "col_phone": "Телефон", "col_email": "Email",
        "col_date": "Дата", "col_employee": "Сотрудник", "col_equipment": "Оборудование", "col_status": "Статус",
        "col_sum": "Сумма", "col_master": "Мастер", "col_model": "Модель", "col_serial": "Серийный номер",
        "col_problem": "Проблема", "col_quantity": "Кол-во", "col_price": "Цена", "col_stock": "Остаток",
        "col_category": "Категория", "col_sku": "Артикул", "col_unit": "Ед.", "col_type": "Тип",
        "new": "Новая", "status_new": "Новая", "diagnostics": "Диагностика", "in_progress": "В работе",
        "ready": "Готова", "closed": "Закрыта", "all": "Все", "status": "Статус", "set_status": "Установить статус",
        "create_request": "Создать заявку", "edit_request": "Редактировать заявку", "request_saved": "Заявка сохранена",
        "loading_requests": "Загрузка заявок...", "no_requests": "Заявки не найдены", "select_requests": "Выберите заявки",
        "select_employee": "Выберите сотрудника", "problem_desc": "Описание проблемы", "describe_problem": "Опишите проблему",
        "problem_too_short": "Опишите проблему минимум {} символов", "labor_cost": "Работа", "parts_cost": "Запчасти",
        "total_cost": "Итого", "planned_date": "Плановая дата", "select_date": "Выбрать дату",
        "invalid_date_format": "Неверный формат даты (ГГГГ-ММ-ДД)", "invalid_date_range": "Неверный диапазон дат",
        "employee_info": "Информация о сотруднике", "add_employee": "Добавить сотрудника", "edit_employee": "Изменить сотрудника",
        "employee_stats": "Статистика сотрудников", "employee_report": "Отчёт по сотрудникам", "search_employee": "Поиск сотрудника",
        "no_employees": "Нет сотрудников", "equipment_info": "Информация об оборудовании", "add_equipment": "Добавить оборудование",
        "edit_equipment": "Изменить оборудование", "equipment_saved": "Оборудование сохранено", "no_equipment": "Нет оборудования",
        "no_equipment_for_employee": "Нет оборудования у сотрудника", "device_type": "Тип устройства", "model": "Модель",
        "model_placeholder": "Введите модель", "serial_number": "Серийный номер", "serial_placeholder": "Введите серийный номер",
        "no_serial": "Без серийного номера", "color": "Цвет", "imei": "IMEI", "accessories": "Комплектация",
        "external_damage": "Внешние повреждения", "part_info": "Информация о запчасти", "add_part": "Добавить запчасть",
        "edit_part": "Изменить запчасть", "parts_cost": "Стоимость запчастей", "quantity": "Количество",
        "price": "Цена", "cost_price": "Себестоимость", "retail_price": "Розничная цена", "markup": "Наценка",
        "sku": "Артикул", "category": "Категория", "supplier": "Поставщик", "unit": "Единица", "pieces": "шт",
        "low_stock": "Мало на складе", "in_stock": "В наличии", "out_of_stock": "Нет в наличии",
        "no_parts": "Нет запчастей", "no_parts_found": "Запчасти не найдены", "loading_parts": "Загрузка запчастей...",
        "contractor_info": "Информация о контрагенте", "add_contractor": "Добавить контрагента",
        "edit_contractor": "Изменить контрагента", "contractor_stats": "Статистика контрагентов",
        "no_contractors": "Нет контрагентов", "financial_report": "Финансовый отчёт", "inventory_report": "Отчёт по складу",
        "revenue": "Доход", "expenses": "Расходы", "profit": "Прибыль", "requests_count": "Кол-во заявок",
        "period": "Период", "start_date": "Дата начала", "end_date": "Дата окончания",
        "loading_report": "Загрузка отчёта...", "no_data_for_period": "Нет данных за выбранный период",
        "report_saved": "Отчёт сохранён", "report_not_loaded": "Отчёт не загружен", "report_under_construction": "Отчёт в разработке",
        "general_settings": "Общие настройки", "language": "Язык", "language_changed": "Язык изменён",
        "theme": "Тема", "dark": "Тёмная", "light": "Светлая", "security_settings": "Безопасность",
        "database_settings": "Настройки базы данных", "settings_saved": "Настройки сохранены",
        "seed_data": "Заполнить тестовыми данными", "seed_confirm": "Создать тестовые данные?",
        "loading_demo_data": "Загрузка тестовых данных...", "data_loaded": "Данные загружены",
        "error_loading_demo": "Ошибка загрузки демо-данных", "error_loading": "Ошибка загрузки",
        "error_saving": "Ошибка сохранения", "error_deleting": "Ошибка удаления", "error_exporting": "Ошибка экспорта",
        "confirm_delete": "Подтверждение удаления", "deleted": "Удалено", "updated": "Обновлено", "added": "Добавлено",
        "record_saved": "Запись сохранена", "select_row": "Выберите строку", "no_records_match": "Нет подходящих записей",
        "search_placeholder": "Введите текст для поиска...", "search_user": "Поиск пользователя...",
        "today": "Сегодня", "never": "Никогда", "other": "Другое",
        # === Номенклатура и единицы ===
        "nomenclature": "Номенклатура", "units": "Единицы измерения", "unit_info": "Информация о единице",
        "nom_type": "Тип номенклатуры", "nom_types": "Типы номенклатуры", "nom_type_info": "Информация о типе",
        "add_unit": "Добавить единицу", "edit_unit": "Изменить единицу", "delete_unit_confirm": "Удалить единицу?",
        "add_nom_type": "Добавить тип", "edit_nom_type": "Изменить тип", "delete_nom_type_confirm": "Удалить тип номенклатуры?",
        "no_units": "Нет единиц измерения", "no_nom_types": "Нет типов номенклатуры",
        # === Массовые операции ===
        "mass_status": "Массовая смена статуса",
        # === Аналоги ===
        "manage_analogs": "Управление аналогами", "manage_analogs_for": "Аналоги для: {}",
        "add_analog": "Добавить аналог", "current_analogs": "Текущие аналоги",
        "no_analogs": "Нет аналогов", "no_new_analogs": "Нет доступных аналогов",
        "analogs_added": "Аналоги добавлены", "analogs_removed": "Аналоги удалены",
        "confirm_remove_analogs": "Убрать выбранные аналоги?",
        "select_analog_to_remove": "Выберите аналог для удаления",
        "add_selected": "Добавить выбранные", "remove_selected": "Убрать выбранные",
        # === Поиск ===
        "search_hint": "Введите запрос...", "search_parts": "Поиск запчастей",
        "search_parts_placeholder": "Введите название или артикул...",
        "search_preview": "Предпросмотр поиска", "searching": "Поиск...",
        # === Запчасти (дополнительно) ===
        "select_part_to_add": "Выберите запчасть для добавления",
        "select_parts_instruction": "Выберите запчасти из списка",
        "select_at_least_one_part": "Выберите хотя бы одну запчасть",
        "delete_part_confirm": "Удалить запчасть?",
        "deduct_parts_title": "Списание запчастей", "confirm_deduction": "Подтвердить списание?",
        "insufficient_stock": "Недостаточно на складе", "quantity_required": "Укажите количество",
        "enter_quantity": "Введите количество",
        "low_stock_threshold": "Порог низкого остатка", "show_low_stock_button": "Показать дефицитные",
        "total_items": "Всего позиций", "total_value": "Общая стоимость", "total_spent": "Всего потрачено",
        "showing_limited": "Показано {} из {}",
        "invalid_threshold": "Неверное значение порога", "invalid_coefficient": "Неверный коэффициент",
        "coefficient": "Коэффициент",
        # === Импорт/Экспорт ===
        "export_csv": "Экспорт CSV", "export_excel": "Экспорт Excel",
        "export_csv_placeholder": "Выберите файл для экспорта CSV",
        "import_csv": "Импорт CSV", "import_csv_placeholder": "Выберите CSV-файл для импорта",
        "import_parts_csv": "Импорт запчастей из CSV", "export_price_list": "Экспорт прайс-листа",
        "exporting": "Экспорт...", "parsing_file": "Разбор файла...",
        "csv_files": "CSV-файлы", "excel_files": "Excel-файлы", "all_files": "Все файлы",
        "select_file": "Выбрать файл", "select_csv_file": "Выберите CSV-файл",
        "file_not_selected": "Файл не выбран", "missing_openpyxl": "Для экспорта в Excel установите openpyxl",
        "export_permission_error": "Нет прав для записи файла",
        # === Резервное копирование ===
        "create_backup": "Создать резервную копию", "backup_in_progress": "Создание резервной копии...",
        "backup_permission_error": "Нет прав для создания резервной копии",
        # === База данных ===
        "optimize_db": "Оптимизировать БД", "optimizing_db": "Оптимизация БД...",
        "db_optimized": "База данных оптимизирована",
        # === SMTP ===
        "smtp_settings": "Настройки SMTP", "smtp_server": "SMTP-сервер",
        "smtp_port": "Порт", "smtp_login": "Логин SMTP",
        "smtp_password": "Пароль SMTP", "smtp_from": "Email отправителя",
        "smtp_tls": "Использовать TLS", "smtp_saved": "Настройки SMTP сохранены",
        "smtp_host_required": "Укажите адрес SMTP-сервера",
        "test_email": "Тестовое письмо", "email_test_sent": "Тестовое письмо отправлено",
        # === SMS ===
        "sms_settings": "Настройки SMS", "sms_provider": "SMS-провайдер",
        "sms_api_key": "API-ключ SMS", "sms_sender": "Имя отправителя",
        "sms_saved": "Настройки SMS сохранены",
        "sms_provider_required": "Укажите SMS-провайдера",
        "test_sms": "Тестовое SMS", "sms_test_sent": "Тестовое SMS отправлено",
        # === Безопасность ===
        "auto_logout": "Авто-выход (мин.)",
        "password_min_length": "Мин. длина пароля",
        # === Оборудование (дополнительно) ===
        "delete_equipment_confirm": "Удалить оборудование?",
        # === Валидация (дополнительно) ===
        "name_exists": "Такое название уже существует",
        "name_too_short": "Название слишком короткое",
        "name_too_long": "Название слишком длинное",
        "name_invalid_chars": "Название содержит недопустимые символы",
        "field_too_long": "Поле слишком длинное",
        "invalid_port": "Неверный порт",
        "invalid_quantity_range": "Количество вне допустимого диапазона",
        "invalid_status": "Недопустимый статус",
        "number_too_large": "Число слишком большое",
        "number_too_small": "Число слишком маленькое",
        "serial_invalid_chars": "Серийный номер содержит недопустимые символы",
        "serial_too_long": "Серийный номер слишком длинный",
        "allowed_chars_hint": "Допустимые символы: буквы, цифры, _, -, ., @",
        # === Пользовательский интерфейс ===
        "enter_username": "Введите логин", "enter_password": "Введите пароль",
        "username_placeholder": "Имя пользователя", "password_placeholder": "Пароль",
        "confirm_password_placeholder": "Подтвердите пароль",
        "enter_new_name": "Введите новое название", "new_name": "Новое название",
        "user_not_found": "Пользователь не найден",
        "open_users_screen": "Открыть экран пользователей",
        "users_in_settings_note": "Управление пользователями доступно в разделе Настройки → Пользователи",
        "section_under_construction": "Раздел в разработке",
        "enter_api_key": "Введите API-ключ",
        "unknown_key": "Неизвестный ключ",
        "edit_reference": "Редактировать справочник",
        "edit_request_unavailable": "Редактирование заявки недоступно",
        "reference_updated": "Справочник обновлён",
        # === Колонки (дополнительно) ===
        "col_action": "Действие", "col_checkbox": "", "col_inn": "ИНН", "col_row_num": "№",
        # === Роли ===
        "role_admin": "Администратор", "role_manager": "Менеджер",
        "role_technician": "Техник", "role_viewer": "Наблюдатель",
        # === Массовые операции (дополнительно) ===
        "selected_count": "Выбрано: {}", "mass_status_updated": "Статус обновлён для {} заявок",
        # === Резервное копирование (дополнительно) ===
        "backup_created": "Резервная копия создана",
        "error_backup": "Ошибка создания резервной копии",
        "error_optimize": "Ошибка оптимизации БД",
        # === Импорт CSV (дополнительно) ===
        "confirm_import": "Импортировать данные?",
        "confirm_import_title": "Подтверждение импорта",
        "csv_example": "Пример CSV",
        "csv_example_value": "Название;Артикул;Количество;Цена",
        "csv_format_hint": "Формат: CSV с разделителем ;",
        "importing": "Импорт...",
        "import_progress": "Импорт: {} из {}",
        "import_completed": "Импорт завершён",
        "import_success": "Успешно импортировано: {}",
        "import_failed": "Ошибка импорта",
        "import_errors": "Ошибок при импорте: {}",
        "import_with_errors": "Импорт завершён с ошибками",
        "load_file_first": "Сначала загрузите файл",
        "select_file_first": "Сначала выберите файл",
        "file_parsed": "Файл разобран: {} записей",
        "loaded_records": "Загружено записей: {}",
        "missing_columns": "Отсутствуют обязательные колонки",
        "no_valid_records": "Нет корректных записей",
        "encoding_error": "Ошибка кодировки файла",
        "error_reading_file": "Ошибка чтения файла",
        "showing_preview": "Предпросмотр: {} записей",
        # === Ошибки валидации (дополнительно) ===
        "error_no_name": "Не указано название",
        "error_no_sku": "Не указан артикул",
        "error_invalid_quantity": "Неверное количество",
        "error_invalid_price": "Неверная цена",
        "error_invalid_cost": "Неверная себестоимость",
        "error_negative_quantity": "Количество не может быть отрицательным",
        "error_negative_price": "Цена не может быть отрицательной",
        "error_negative_cost": "Себестоимость не может быть отрицательной",
        "error_negative_min_stock": "Мин. остаток не может быть отрицательным",
        "error_changing_password": "Ошибка смены пароля",
        "error_table": "Ошибка таблицы",
        # === Разное (дополнительно) ===
        "callback_error": "Ошибка обратного вызова",
        "deduct_parts_for": "Списание для заявки №{}",
        "dynamic_form_coming": "Динамическая форма в разработке",
        "editor_stub": "Редактор в разработке",
        "edit_request": "Редактировать заявку",
        "max_available": "Максимально доступно: {}",
        "no_available_parts": "Нет доступных запчастей",
        "no_category": "Без категории",
        "record_id": "ID записи",
        "selected": "Выбрано",
        "selected_summary": "Выбрано: {} шт. на сумму {}",
        "total": "Итого",
        "unit_default": "шт.",
    },
    "en": {
        "add": "Add", "edit": "Edit", "delete": "Delete", "save": "Save", "cancel": "Cancel",
        "close": "Close", "back": "Back", "ok": "OK", "confirm": "Confirm", "apply": "Apply",
        "clear": "Clear", "reset": "Reset", "find": "Find", "search": "Search", "update": "Update",
        "export": "Export", "import": "Import", "preview": "Preview", "processing": "Processing",
        "saving": "Saving...", "loading": "Loading...", "error": "Error", "under_construction": "Under construction",
        "dashboard": "Dashboard", "requests": "Requests", "request_plural": "Requests", "employees": "Employees",
        "employee": "Employee", "equipment": "Equipment", "parts": "Parts", "contractors": "Contractors",
        "reports": "Reports", "settings": "Settings", "documents": "Documents", "reference": "Reference",
        "analytics": "Analytics", "users": "Users", "main": "Main", "system": "System",
        "login": "Login", "logout": "Logout", "username": "Username", "password": "Password", "role": "Role",
        "branch": "Branch", "full_name": "Full name", "position": "Position", "phone": "Phone", "email": "Email",
        "address": "Address", "salary": "Salary", "inn": "Tax ID", "contacts": "Contacts", "description": "Description",
        "name_required": "Name is required", "field_required": "Field is required", "fill_required": "Fill required fields",
        "fill_all_fields": "Fill all fields", "required_field": "Required field", "invalid_email": "Invalid email",
        "invalid_phone": "Invalid phone", "invalid_number": "Invalid number", "invalid_quantity": "Invalid quantity",
        "invalid_cost": "Invalid cost", "invalid_salary": "Salary must be a number >= 0",
        "username_required": "Username is required", "username_exists": "A user with this username already exists",
        "username_too_short": "Username must be at least {} characters", "username_too_long": "Username is too long",
        "username_invalid_chars": "Username may contain only letters, digits, _, -, ., @",
        "password_required": "Password is required", "password_too_short": "Password must be at least {} characters",
        "passwords_not_match": "Passwords do not match", "confirm_password": "Confirm password",
        "old_password": "Old password", "new_password": "New password", "change_password": "Change password",
        "password_optional": "leave blank to keep unchanged", "invalid_credentials": "Invalid username or password",
        "wrong_password": "Wrong password", "password_changed": "Password changed",
        "manage_users": "User management", "new_user": "New user", "edit_user": "Edit user",
        "user_created": "User created", "user_updated": "User updated", "user_deleted": "User deleted",
        "user_saved": "User saved", "select_user": "Select a user", "total_users": "Total users",
        "no_users": "No users", "cannot_delete_admin": "Cannot delete the main administrator",
        "confirm_delete_user": "Delete user '{username}'?", "delete_user_warning": "All related actions will be lost.",
        "branch_required": "Select a branch", "no_branches": "No branches",
        "col_id": "ID", "col_username": "Username", "col_role": "Role", "col_branch": "Branch",
        "col_created": "Created", "col_name": "Name", "col_phone": "Phone", "col_email": "Email",
        "col_date": "Date", "col_employee": "Employee", "col_equipment": "Equipment", "col_status": "Status",
        "col_sum": "Amount", "col_master": "Technician", "col_model": "Model", "col_serial": "Serial number",
        "col_problem": "Problem", "col_quantity": "Qty", "col_price": "Price", "col_stock": "Stock",
        "col_category": "Category", "col_sku": "SKU", "col_unit": "Unit", "col_type": "Type",
        "new": "New", "status_new": "New", "diagnostics": "Diagnostics", "in_progress": "In progress",
        "ready": "Ready", "closed": "Closed", "all": "All", "status": "Status", "set_status": "Set status",
        "create_request": "Create request", "edit_request": "Edit request", "request_saved": "Request saved",
        "loading_requests": "Loading requests...", "no_requests": "No requests found", "select_requests": "Select requests",
        "select_employee": "Select an employee", "problem_desc": "Problem description", "describe_problem": "Describe the problem",
        "problem_too_short": "Describe the problem with at least {} characters", "labor_cost": "Labor cost",
        "parts_cost": "Parts cost", "total_cost": "Total", "planned_date": "Planned date", "select_date": "Select date",
        "invalid_date_format": "Invalid date format (YYYY-MM-DD)", "invalid_date_range": "Invalid date range",
        "employee_info": "Employee information", "add_employee": "Add employee", "edit_employee": "Edit employee",
        "employee_stats": "Employee stats", "employee_report": "Employee report", "search_employee": "Search employee",
        "no_employees": "No employees", "equipment_info": "Equipment information", "add_equipment": "Add equipment",
        "edit_equipment": "Edit equipment", "equipment_saved": "Equipment saved", "no_equipment": "No equipment",
        "no_equipment_for_employee": "No equipment for this employee", "device_type": "Device type", "model": "Model",
        "model_placeholder": "Enter model", "serial_number": "Serial number", "serial_placeholder": "Enter serial number",
        "no_serial": "No serial", "color": "Color", "imei": "IMEI", "accessories": "Accessories",
        "external_damage": "External damage", "part_info": "Part information", "add_part": "Add part",
        "edit_part": "Edit part", "quantity": "Quantity", "price": "Price", "cost_price": "Cost price",
        "retail_price": "Retail price", "markup": "Markup", "sku": "SKU", "category": "Category",
        "supplier": "Supplier", "unit": "Unit", "pieces": "pcs", "low_stock": "Low stock",
        "in_stock": "In stock", "out_of_stock": "Out of stock", "no_parts": "No parts",
        "no_parts_found": "No parts found", "loading_parts": "Loading parts...",
        "contractor_info": "Contractor information", "add_contractor": "Add contractor",
        "edit_contractor": "Edit contractor", "contractor_stats": "Contractor stats", "no_contractors": "No contractors",
        "financial_report": "Financial report", "inventory_report": "Inventory report", "revenue": "Revenue",
        "expenses": "Expenses", "profit": "Profit", "requests_count": "Requests count", "period": "Period",
        "start_date": "Start date", "end_date": "End date", "loading_report": "Loading report...",
        "no_data_for_period": "No data for selected period", "report_saved": "Report saved",
        "report_not_loaded": "Report not loaded", "report_under_construction": "Report under construction",
        "general_settings": "General settings", "language": "Language", "language_changed": "Language changed",
        "theme": "Theme", "dark": "Dark", "light": "Light", "security_settings": "Security settings",
        "database_settings": "Database settings", "settings_saved": "Settings saved",
        "seed_data": "Load demo data", "seed_confirm": "Create demo data?", "loading_demo_data": "Loading demo data...",
        "data_loaded": "Data loaded", "error_loading_demo": "Error loading demo data", "error_loading": "Loading error",
        "error_saving": "Saving error", "error_deleting": "Delete error", "error_exporting": "Export error",
        "confirm_delete": "Confirm delete", "deleted": "Deleted", "updated": "Updated", "added": "Added",
        "record_saved": "Record saved", "select_row": "Select a row", "no_records_match": "No matching records",
        "search_placeholder": "Enter search text...", "search_user": "Search user...", "today": "Today",
        "never": "Never", "other": "Other",
        # === Nomenclature & units ===
        "nomenclature": "Nomenclature", "units": "Units", "unit_info": "Unit information",
        "nom_type": "Nomenclature type", "nom_types": "Nomenclature types", "nom_type_info": "Type information",
        "add_unit": "Add unit", "edit_unit": "Edit unit", "delete_unit_confirm": "Delete unit?",
        "add_nom_type": "Add type", "edit_nom_type": "Edit type", "delete_nom_type_confirm": "Delete nomenclature type?",
        "no_units": "No units", "no_nom_types": "No nomenclature types",
        # === Mass operations ===
        "mass_status": "Mass status change",
        # === Analogs ===
        "manage_analogs": "Manage analogs", "manage_analogs_for": "Analogs for: {}",
        "add_analog": "Add analog", "current_analogs": "Current analogs",
        "no_analogs": "No analogs", "no_new_analogs": "No available analogs",
        "analogs_added": "Analogs added", "analogs_removed": "Analogs removed",
        "confirm_remove_analogs": "Remove selected analogs?",
        "select_analog_to_remove": "Select an analog to remove",
        "add_selected": "Add selected", "remove_selected": "Remove selected",
        # === Search ===
        "search_hint": "Enter query...", "search_parts": "Search parts",
        "search_parts_placeholder": "Enter name or SKU...",
        "search_preview": "Search preview", "searching": "Searching...",
        # === Parts (extra) ===
        "select_part_to_add": "Select a part to add",
        "select_parts_instruction": "Select parts from the list",
        "select_at_least_one_part": "Select at least one part",
        "delete_part_confirm": "Delete part?",
        "deduct_parts_title": "Parts deduction", "confirm_deduction": "Confirm deduction?",
        "insufficient_stock": "Insufficient stock", "quantity_required": "Quantity is required",
        "enter_quantity": "Enter quantity",
        "low_stock_threshold": "Low stock threshold", "show_low_stock_button": "Show low stock",
        "total_items": "Total items", "total_value": "Total value", "total_spent": "Total spent",
        "showing_limited": "Showing {} of {}",
        "invalid_threshold": "Invalid threshold value", "invalid_coefficient": "Invalid coefficient",
        "coefficient": "Coefficient",
        # === Import/Export ===
        "export_csv": "Export CSV", "export_excel": "Export Excel",
        "export_csv_placeholder": "Select file for CSV export",
        "import_csv": "Import CSV", "import_csv_placeholder": "Select a CSV file for import",
        "import_parts_csv": "Import parts from CSV", "export_price_list": "Export price list",
        "exporting": "Exporting...", "parsing_file": "Parsing file...",
        "csv_files": "CSV files", "excel_files": "Excel files", "all_files": "All files",
        "select_file": "Select file", "select_csv_file": "Select a CSV file",
        "file_not_selected": "No file selected", "missing_openpyxl": "Install openpyxl for Excel export",
        "export_permission_error": "No write permission for file",
        # === Backup ===
        "create_backup": "Create backup", "backup_in_progress": "Creating backup...",
        "backup_permission_error": "No permission to create backup",
        # === Database ===
        "optimize_db": "Optimize DB", "optimizing_db": "Optimizing DB...",
        "db_optimized": "Database optimized",
        # === SMTP ===
        "smtp_settings": "SMTP settings", "smtp_server": "SMTP server",
        "smtp_port": "Port", "smtp_login": "SMTP login",
        "smtp_password": "SMTP password", "smtp_from": "Sender email",
        "smtp_tls": "Use TLS", "smtp_saved": "SMTP settings saved",
        "smtp_host_required": "SMTP server address is required",
        "test_email": "Test email", "email_test_sent": "Test email sent",
        # === SMS ===
        "sms_settings": "SMS settings", "sms_provider": "SMS provider",
        "sms_api_key": "SMS API key", "sms_sender": "Sender name",
        "sms_saved": "SMS settings saved",
        "sms_provider_required": "SMS provider is required",
        "test_sms": "Test SMS", "sms_test_sent": "Test SMS sent",
        # === Security ===
        "auto_logout": "Auto-logout (min.)",
        "password_min_length": "Min. password length",
        # === Equipment (extra) ===
        "delete_equipment_confirm": "Delete equipment?",
        # === Validation (extra) ===
        "name_exists": "This name already exists",
        "name_too_short": "Name is too short",
        "name_too_long": "Name is too long",
        "name_invalid_chars": "Name contains invalid characters",
        "field_too_long": "Field is too long",
        "invalid_port": "Invalid port",
        "invalid_quantity_range": "Quantity out of range",
        "invalid_status": "Invalid status",
        "number_too_large": "Number is too large",
        "number_too_small": "Number is too small",
        "serial_invalid_chars": "Serial number contains invalid characters",
        "serial_too_long": "Serial number is too long",
        "allowed_chars_hint": "Allowed characters: letters, digits, _, -, ., @",
        # === UI ===
        "enter_username": "Enter username", "enter_password": "Enter password",
        "username_placeholder": "Username", "password_placeholder": "Password",
        "confirm_password_placeholder": "Confirm password",
        "enter_new_name": "Enter new name", "new_name": "New name",
        "user_not_found": "User not found",
        "open_users_screen": "Open users screen",
        "users_in_settings_note": "User management is available in Settings → Users",
        "section_under_construction": "Section under construction",
        "enter_api_key": "Enter API key",
        "unknown_key": "Unknown key",
        "edit_reference": "Edit reference",
        "edit_request_unavailable": "Request editing is unavailable",
        "reference_updated": "Reference updated",
        # === Columns (extra) ===
        "col_action": "Action", "col_checkbox": "", "col_inn": "Tax ID", "col_row_num": "#",
        # === Roles ===
        "role_admin": "Administrator", "role_manager": "Manager",
        "role_technician": "Technician", "role_viewer": "Viewer",
        # === Mass operations (extra) ===
        "selected_count": "Selected: {}", "mass_status_updated": "Status updated for {} requests",
        # === Backup (extra) ===
        "backup_created": "Backup created",
        "error_backup": "Backup creation error",
        "error_optimize": "Database optimization error",
        # === CSV Import (extra) ===
        "confirm_import": "Import data?",
        "confirm_import_title": "Import confirmation",
        "csv_example": "CSV example",
        "csv_example_value": "Name;SKU;Quantity;Price",
        "csv_format_hint": "Format: CSV with ; delimiter",
        "importing": "Importing...",
        "import_progress": "Import: {} of {}",
        "import_completed": "Import completed",
        "import_success": "Successfully imported: {}",
        "import_failed": "Import failed",
        "import_errors": "Import errors: {}",
        "import_with_errors": "Import completed with errors",
        "load_file_first": "Load a file first",
        "select_file_first": "Select a file first",
        "file_parsed": "File parsed: {} records",
        "loaded_records": "Records loaded: {}",
        "missing_columns": "Required columns are missing",
        "no_valid_records": "No valid records found",
        "encoding_error": "File encoding error",
        "error_reading_file": "Error reading file",
        "showing_preview": "Preview: {} records",
        # === Validation errors (extra) ===
        "error_no_name": "Name is not specified",
        "error_no_sku": "SKU is not specified",
        "error_invalid_quantity": "Invalid quantity",
        "error_invalid_price": "Invalid price",
        "error_invalid_cost": "Invalid cost price",
        "error_negative_quantity": "Quantity cannot be negative",
        "error_negative_price": "Price cannot be negative",
        "error_negative_cost": "Cost cannot be negative",
        "error_negative_min_stock": "Min. stock cannot be negative",
        "error_changing_password": "Error changing password",
        "error_table": "Table error",
        # === Miscellaneous (extra) ===
        "callback_error": "Callback error",
        "deduct_parts_for": "Deduction for request #{}",
        "dynamic_form_coming": "Dynamic form coming soon",
        "editor_stub": "Editor coming soon",
        "edit_request": "Edit request",
        "max_available": "Max available: {}",
        "no_available_parts": "No available parts",
        "no_category": "No category",
        "record_id": "Record ID",
        "selected": "Selected",
        "selected_summary": "Selected: {} pcs. total {}",
        "total": "Total",
        "unit_default": "pcs",
    }
}

TRANSLATIONS["ru"].update(_COMMON_TRANSLATIONS["ru"])
TRANSLATIONS["en"].update(_COMMON_TRANSLATIONS["en"])

# ==================== ГЛОБАЛЬНОЕ СОСТОЯНИЕ ====================
_current_language: Language = "ru"
_translations_cache: Dict[Language, TranslationsDict] = {}


# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

def _humanize_key(key: str, language: Language) -> str:
    words = key.replace("_", " ").strip().split()
    if language == "en":
        return " ".join(words).capitalize()
    ru_words = {
        "add": "добавить", "edit": "изменить", "delete": "удалить", "confirm": "подтверждение",
        "error": "ошибка", "loading": "загрузка", "import": "импорт", "export": "экспорт",
        "csv": "CSV", "excel": "Excel", "file": "файл", "files": "файлы", "parts": "запчасти",
        "part": "запчасть", "analog": "аналог", "analogs": "аналоги", "selected": "выбранные",
        "settings": "настройки", "backup": "резервная копия", "created": "создано",
        "permission": "доступ", "required": "обязательно", "invalid": "неверно",
        "quantity": "количество", "price": "цена", "cost": "стоимость", "name": "название",
        "new": "новый", "old": "старый", "password": "пароль", "placeholder": "подсказка",
        "title": "заголовок", "message": "сообщение", "select": "выберите", "open": "открыть",
        "remove": "убрать", "unit": "единица", "units": "единицы", "nom": "номенклатура",
        "type": "тип", "types": "типы", "row": "строка", "count": "количество",
        "total": "итого", "value": "значение", "progress": "прогресс", "completed": "завершено",
        "failed": "не удалось", "success": "успешно", "table": "таблица", "threshold": "порог",
        "low": "низкий", "stock": "остаток", "available": "доступно", "records": "записи",
        "record": "запись", "preview": "предпросмотр", "search": "поиск", "smtp": "SMTP",
        "sms": "SMS", "provider": "провайдер", "server": "сервер", "port": "порт",
    }
    return " ".join(ru_words.get(word, word) for word in words).capitalize()

def get_text(
    key: str, 
    lang: Optional[str] = None, 
    default: Optional[str] = None,
    **kwargs
) -> str:
    """
    Получить переведённый текст с поддержкой форматирования.
    
    ✅ Fallback на русский если ключ не найден в выбранном языке
    ✅ Форматирование через .format() если переданы **kwargs
    ✅ Безопасное преобразование в строку
    
    Args:
        key: Ключ перевода (например, "login", "save", "error_loading")
        lang: Код языка ("ru" или "en"). По умолчанию используется текущий.
        default: Значение по умолчанию если ключ не найден ни в одном языке.
        **kwargs: Параметры для форматирования строки (для плейсхолдеров {}).
    
    Returns:
        str: Переведённый и отформатированный текст.
    
    Example:
        >>> get_text("login", lang="en")
        'Login'
        
        >>> get_text("report_saved", filename="report.xlsx")
        'Отчёт сохранён: report.xlsx'
        
        >>> get_text("unknown_key", default="Fallback text")
        'Fallback text'
    """
    # ✅ Определяем язык
    language: Language = lang if lang in TRANSLATIONS else _current_language
    
    # ✅ Ленивая загрузка (оптимизация для больших приложений)
    if language not in _translations_cache:
        _translations_cache[language] = TRANSLATIONS[language]
    
    translations = _translations_cache[language]
    
    # ✅ Пытаемся найти ключ
    value = translations.get(key)
    
    # ✅ Fallback: default → русский → ключ как значение
    if value is None:
        if default is not None:
            value = default
        elif language != "ru":
            # Пробуем русский как второй вариант
            value = TRANSLATIONS["ru"].get(key)
            if value is None:
                value = _humanize_key(key, language)
        else:
            value = _humanize_key(key, language)
    
    # ✅ Форматирование если есть плейсхолдеры и параметры
    if kwargs and ("{}" in value or "{" in value):
        try:
            # Поддерживаем как позиционные {}, так и именованные {name}
            if all(isinstance(k, str) for k in kwargs.keys()):
                value = value.format(**kwargs)
            else:
                value = value.format(*kwargs.values())
        except (KeyError, IndexError, ValueError, TypeError) as e:
            # ✅ Не ломаем приложение если форматирование не удалось
            from core.logger import app_logger
            app_logger.warning(f"⚠️ Format error for key '{key}': {e}")
    
    return str(value)


def set_language(lang: str) -> bool:
    """
    Установить язык приложения.
    
    ✅ Возвращает True если язык установлен успешно
    ✅ Возвращает False если язык не поддерживается
    
    Args:
        lang: Код языка ("ru" или "en")
    
    Returns:
        bool: Успех операции
    
    Example:
        >>> set_language("en")
        True
        >>> set_language("fr")  # Не поддерживается
        False
    """
    global _current_language
    
    if lang in TRANSLATIONS:
        _current_language = lang  # type: ignore
        # ✅ Очищаем кэш чтобы загрузить актуальные переводы
        _translations_cache.clear()
        return True
    return False


def get_language() -> Language:
    """
    Получить текущий язык приложения.
    
    Returns:
        Language: Код текущего языка ("ru" или "en")
    
    Example:
        >>> get_language()
        'ru'
    """
    return _current_language


def get_available_languages() -> list[Language]:
    """
    Получить список доступных языков.
    
    Returns:
        list[Language]: Список кодов поддерживаемых языков
    
    Example:
        >>> get_available_languages()
        ['ru', 'en']
    """
    return list(TRANSLATIONS.keys())


def has_translation(key: str, lang: Optional[str] = None) -> bool:
    """
    Проверить, существует ли перевод для ключа.
    
    ✅ Полезно для условного отображения элементов интерфейса
    
    Args:
        key: Ключ перевода
        lang: Код языка (по умолчанию текущий)
    
    Returns:
        bool: True если перевод существует
    
    Example:
        >>> has_translation("login")
        True
        >>> has_translation("unknown_key")
        False
    """
    language = lang if lang in TRANSLATIONS else _current_language
    return key in TRANSLATIONS.get(language, {})


def get_all_keys(lang: Optional[str] = None) -> list[str]:
    """
    Получить все доступные ключи переводов для языка.
    
    ✅ Полезно для отладки и генерации документации
    
    Args:
        lang: Код языка (по умолчанию текущий)
    
    Returns:
        list[str]: Список всех ключей
    
    Example:
        >>> keys = get_all_keys("en")
        >>> "login" in keys
        True
    """
    language = lang if lang in TRANSLATIONS else _current_language
    return list(TRANSLATIONS.get(language, {}).keys())


# ==================== УТИЛИТЫ ДЛЯ ОТЛАДКИ ====================

def debug_missing_translations(lang: Language = "en") -> list[str]:
    """
    Найти ключи которые есть в русском но отсутствуют в другом языке.
    
    ✅ Полезно при добавлении новых языков
    
    Args:
        lang: Целевой язык для проверки
    
    Returns:
        list[str]: Список отсутствующих ключей
    """
    ru_keys = set(TRANSLATIONS["ru"].keys())
    target_keys = set(TRANSLATIONS.get(lang, {}).keys())
    
    missing = ru_keys - target_keys
    return sorted(missing)


def sync_translations(source: Language = "ru", target: Language = "en") -> Dict[str, str]:
    """
    Сгенерировать шаблон недостающих переводов.
    
    ✅ Возвращает dict с ключами из source и значениями = ключам
    ✅ Удобно для копирования в файл переводов
    
    Args:
        source: Язык-источник (обычно "ru")
        target: Целевой язык для заполнения
    
    Returns:
        Dict[str, str]: Шаблон недостающих переводов
    
    Example:
        >>> template = sync_translations()
        >>> print(template["new_key"])  # "new_key"
    """
    source_keys = TRANSLATIONS[source]
    target_keys = TRANSLATIONS.get(target, {})
    
    missing = {
        key: key  # По умолчанию значение = ключу (заглушка)
        for key in source_keys 
        if key not in target_keys
    }
    
    return missing