# utils/validators.py
"""
Модуль валидации данных для PC Repair CRM Pro
✅ УЛУЧШЕНО: Валидация ИНН, паролей, дат, имён, юзернеймов, поддержка стран
✅ СОВМЕСТИМО: Использует app_logger без module= параметра
"""

import re
import logging
from typing import Optional, Union, List, Tuple
from datetime import datetime
from pathlib import Path
from core.logger import app_logger

logger = logging.getLogger(__name__)


# ==================== БАЗОВЫЕ ВАЛИДАТОРЫ ====================

def validate_required(
    value: Optional[str], field_name: str = "Field"
) -> Tuple[bool, str]:
    """Проверка: поле не пустое"""
    if value is None or str(value).strip() == "":
        msg = f"{field_name} is required"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg
    return True, ""


def validate_optional(value: Optional[str]) -> Tuple[bool, str]:
    """Проверка: поле может быть пустым"""
    return True, ""


def validate_email(email: str, required: bool = False) -> Tuple[bool, str]:
    """Проверка формата email"""
    if not email or not email.strip():
        if required:
            msg = "Email is required"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        return True, ""

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email.strip()):
        msg = "Invalid email format"
        app_logger.warning(f"⚠️ Validation failed: {msg} for '{email}'")
        return False, msg

    return True, ""


def validate_phone(phone: str, country: str = "ru", required: bool = False) -> Tuple[bool, str]:
    """Проверка формата телефона с поддержкой стран"""
    if not phone or not phone.strip():
        if required:
            msg = "Phone number is required"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        return True, ""

    phone_clean = re.sub(r"[^\d+]", "", phone)
    phone_stripped = phone.strip()

    patterns = {
        'ru': [
            r"^(\+7|8)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$",
            r"^\+?7?\d{10}$",
        ],
        'us': [
            r"^\+?1?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}$",
            r"^\+?1?\d{10}$",
        ],
        'kz': [
            r"^\+?7?\d{10}$",
            r"^8?\d{10}$",
        ],
        'generic': [
            r"^[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,}$",
        ]
    }

    country_patterns = patterns.get(country, patterns['generic'])
    
    for pattern in country_patterns:
        if re.match(pattern, phone_stripped):
            return True, ""
    
    digits_only = re.sub(r"\D", "", phone_clean)
    if len(digits_only) >= 10 and len(digits_only) <= 15:
        return True, ""

    msg = f"Invalid phone format for {country.upper()}"
    app_logger.warning(f"⚠️ Validation failed: {msg} for '{phone}'")
    return False, msg


def validate_number(
    value: Union[str, int, float],
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    field_name: str = "Number",
    allow_decimal: bool = True,
) -> Tuple[bool, str]:
    """Проверка числового значения"""
    try:
        num_value = float(value)
        if not allow_decimal and num_value != int(num_value):
            msg = f"{field_name} must be an integer"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
    except (ValueError, TypeError):
        msg = f"{field_name} must be a number"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg

    if min_val is not None and num_value < min_val:
        msg = f"{field_name} must be >= {min_val}"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg

    if max_val is not None and num_value > max_val:
        msg = f"{field_name} must be <= {max_val}"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg

    return True, ""


def validate_currency(
    value: Union[str, int, float],
    min_val: float = 0,
    max_val: Optional[float] = None,
    currency: str = "RUB",
    field_name: str = "Amount",
) -> Tuple[bool, str]:
    """Проверка денежной суммы"""
    valid, msg = validate_number(value, min_val, max_val, field_name)
    if not valid:
        return False, msg
    
    num_value = float(value)
    
    if num_value < 0:
        msg = f"{field_name} cannot be negative"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg
    
    if num_value > 1_000_000_000:
        msg = f"{field_name} seems too large"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg
    
    return True, ""


def validate_date(
    date_str: str,
    date_format: str = "%Y-%m-%d",
    field_name: str = "Date",
    allow_past: bool = True,
    allow_future: bool = True,
) -> Tuple[bool, str]:
    """Проверка формата и логики даты"""
    if not date_str or not date_str.strip():
        return True, ""

    try:
        parsed_date = datetime.strptime(date_str.strip(), date_format)
        today = datetime.now().date()
        parsed = parsed_date.date()

        if not allow_past and parsed < today:
            msg = f"{field_name} cannot be in the past"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg

        if not allow_future and parsed > today:
            msg = f"{field_name} cannot be in the future"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg

        return True, ""

    except ValueError as e:
        msg = f"{field_name} has invalid format (expected: {date_format})"
        app_logger.warning(f"⚠️ Validation failed: {msg} - {e}")
        return False, msg


def validate_date_format(
    date_str: str,
    date_format: str = "%Y-%m-%d",
    field_name: str = "Date"
) -> Tuple[bool, str]:
    """Проверка формата даты (только формат, без логики дат)"""
    if not date_str or not date_str.strip():
        return True, ""
    
    try:
        datetime.strptime(date_str.strip(), date_format)
        return True, "OK"
    except ValueError as e:
        msg = f"{field_name} has invalid format (expected: {date_format})"
        app_logger.warning(f"⚠️ Validation failed: {msg} - {e}")
        return False, msg


def validate_date_range(
    start_date: str,
    end_date: str,
    date_format: str = "%Y-%m-%d",
    field_name: str = "Date range",
) -> Tuple[bool, str]:
    """Проверка диапазона дат: start <= end"""
    if not start_date or not end_date:
        return True, ""
    
    valid_start, msg_start = validate_date(start_date, date_format, "Start date")
    if not valid_start:
        return False, msg_start
    
    valid_end, msg_end = validate_date(end_date, date_format, "End date")
    if not valid_end:
        return False, msg_end
    
    start = datetime.strptime(start_date.strip(), date_format).date()
    end = datetime.strptime(end_date.strip(), date_format).date()
    
    if start > end:
        msg = "Start date cannot be after end date"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg
    
    return True, ""


def validate_string_length(
    value: str, min_length: int = 0, max_length: int = 255, field_name: str = "Text"
) -> Tuple[bool, str]:
    """Проверка длины строки"""
    if not value:
        if min_length > 0:
            msg = f"{field_name} is required"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        return True, ""

    if len(value) < min_length:
        msg = f"{field_name} must be at least {min_length} characters"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg

    if len(value) > max_length:
        msg = f"{field_name} must not exceed {max_length} characters"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg

    return True, ""


# ==================== 👤 ВАЛИДАЦИЯ ИМЕНИ/ФАМИЛИИ ====================

def validate_name(
    value: str, 
    min_len: int = 2, 
    max_len: int = 100,
    allow_spaces: bool = True,
    allow_hyphens: bool = True,
    field_name: str = "name"
) -> Tuple[bool, str]:
    """Валидация имени, фамилии или полного имени"""
    if not value or not value.strip():
        return False, f"{field_name} cannot be empty"
    
    cleaned = value.strip()
    
    if len(cleaned) < min_len:
        return False, f"{field_name} too short (min {min_len} characters)"
    
    if len(cleaned) > max_len:
        return False, f"{field_name} too long (max {max_len} characters)"
    
    allowed_pattern = r"^[\w\s\-']+$" if allow_spaces and allow_hyphens else r"^[\w']+$"
    
    if not re.match(allowed_pattern, cleaned, re.UNICODE):
        return False, f"{field_name} contains invalid characters (use letters, spaces, hyphens only)"
    
    if any(c.isdigit() for c in cleaned):
        return False, f"{field_name} should not contain numbers"
    
    return True, "OK"


# ==================== 👤 ВАЛИДАЦИЯ ЮЗЕРНЕЙМА ====================

def validate_username(
    username: str,
    min_len: int = 3,
    max_len: int = 50,
    allow_underscore: bool = True,
    allow_dot: bool = False,
    field_name: str = "Username"
) -> Tuple[bool, str]:
    """
    Валидация имени пользователя (логина)
    
    ✅ Только латиница, цифры, _ и . (опционально)
    ✅ Без пробелов и спецсимволов
    ✅ Проверка длины
    
    Args:
        username: Проверяемый юзернейм
        min_len: Минимальная длина (по умолчанию 3)
        max_len: Максимальная длина (по умолчанию 50)
        allow_underscore: Разрешить подчёркивания (по умолчанию True)
        allow_dot: Разрешить точки (по умолчанию False)
        field_name: Название поля для сообщения об ошибке
        
    Returns:
        Tuple[bool, str]: (валидно, сообщение)
    """
    if not username or not username.strip():
        return False, f"{field_name} cannot be empty"
    
    cleaned = username.strip()
    
    # Проверка длины
    if len(cleaned) < min_len:
        return False, f"{field_name} too short (min {min_len} characters)"
    
    if len(cleaned) > max_len:
        return False, f"{field_name} too long (max {max_len} characters)"
    
    # Разрешённые символы: латиница, цифры, _ и . (опционально)
    allowed_chars = r"a-zA-Z0-9"
    if allow_underscore:
        allowed_chars += r"_"
    if allow_dot:
        allowed_chars += r"\."
    
    pattern = f"^[{allowed_chars}]+$"
    
    if not re.match(pattern, cleaned):
        return False, f"{field_name} contains invalid characters (use letters, numbers, {'_' if allow_underscore else ''}{'.' if allow_dot else ''} only)"
    
    # Юзернейм не должен начинаться/заканчиваться на _ или .
    if cleaned.startswith(('_', '.')) or cleaned.endswith(('_', '.')):
        return False, f"{field_name} cannot start or end with '_' or '.'"
    
    # Не должен содержать последовательные _ или .
    if '__' in cleaned or '..' in cleaned:
        return False, f"{field_name} cannot contain consecutive '_' or '.'"
    
    return True, "OK"


# ==================== СПЕЦИАЛИЗИРОВАННЫЕ ВАЛИДАТОРЫ ====================

def validate_sku(sku: str, required: bool = False) -> Tuple[bool, str]:
    """Проверка формата артикула (SKU)"""
    if not sku or not sku.strip():
        if required:
            msg = "SKU is required"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        return True, ""

    pattern = r"^[A-Za-z0-9\-_]{3,50}$"
    if not re.match(pattern, sku.strip()):
        msg = "Invalid SKU format (3-50 chars, letters/numbers/-/_)"
        app_logger.warning(f"⚠️ Validation failed: {msg} for '{sku}'")
        return False, msg

    return True, ""


def validate_inn(inn: str, entity_type: str = "legal", required: bool = False) -> Tuple[bool, str]:
    """Проверка ИНН РФ с контрольной суммой"""
    if not inn or not inn.strip():
        if required:
            msg = "INN is required"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        return True, ""

    inn_clean = re.sub(r"[^\d]", "", inn)
    
    expected_len = 10 if entity_type == "legal" else 12
    if len(inn_clean) != expected_len:
        msg = f"INN must be {expected_len} digits for {entity_type}"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg

    if not _validate_inn_checksum(inn_clean, entity_type):
        msg = "Invalid INN checksum"
        app_logger.warning(f"⚠️ Validation failed: {msg} for '{inn}'")
        return False, msg

    return True, ""


def _validate_inn_checksum(inn: str, entity_type: str) -> bool:
    """Внутренняя функция: проверка контрольной суммы ИНН РФ"""
    try:
        digits = [int(d) for d in inn]
        
        if entity_type == "legal" and len(digits) == 10:
            weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum = sum(d * w for d, w in zip(digits[:9], weights)) % 11 % 10
            return checksum == digits[9]
            
        elif entity_type == "individual" and len(digits) == 12:
            weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum1 = sum(d * w for d, w in zip(digits[:10], weights1)) % 11 % 10
            if checksum1 != digits[10]:
                return False
            weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum2 = sum(d * w for d, w in zip(digits[:11], weights2)) % 11 % 10
            return checksum2 == digits[11]
            
        return True
    except Exception:
        return False


def validate_password(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = False,
) -> Tuple[bool, str]:
    """Проверка сложности пароля"""
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    
    if require_uppercase and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if require_lowercase and not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if require_digit and not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character"
    
    weak_passwords = ['password', '123456', 'qwerty', 'admin', '111111']
    if password.lower() in weak_passwords:
        return False, "Password is too common, please choose a stronger one"
    
    return True, ""


def validate_url(url: str, required: bool = False, allowed_schemes: List[str] = None) -> Tuple[bool, str]:
    """Проверка формата URL"""
    if not url or not url.strip():
        if required:
            msg = "URL is required"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        return True, ""
    
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    pattern = r"^(?:{}):\/\/[^\s/$.?#].[^\s]*$".format('|'.join(allowed_schemes))
    if not re.match(pattern, url.strip(), re.IGNORECASE):
        msg = f"Invalid URL format (allowed: {', '.join(allowed_schemes)}://...)"
        app_logger.warning(f"⚠️ Validation failed: {msg} for '{url}'")
        return False, msg
    
    return True, ""


def validate_file_path(
    path: str,
    must_exist: bool = False,
    must_be_file: bool = False,
    must_be_dir: bool = False,
    allowed_extensions: List[str] = None,
    field_name: str = "File path",
) -> Tuple[bool, str]:
    """Проверка пути к файлу/директории"""
    if not path or not path.strip():
        return True, ""
    
    try:
        p = Path(path.strip())
        
        if ".." in str(p) and not p.is_absolute():
            msg = f"{field_name} contains invalid path traversal"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        
        if must_exist and not p.exists():
            msg = f"{field_name} does not exist"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        
        if must_be_file and not p.is_file():
            msg = f"{field_name} must be a file"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        
        if must_be_dir and not p.is_dir():
            msg = f"{field_name} must be a directory"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        
        if allowed_extensions and p.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
            msg = f"{field_name} has invalid extension (allowed: {', '.join(allowed_extensions)})"
            app_logger.warning(f"⚠️ Validation failed: {msg}")
            return False, msg
        
        return True, ""
        
    except Exception as e:
        msg = f"{field_name} validation error: {e}"
        app_logger.warning(f"⚠️ Validation failed: {msg}")
        return False, msg


# ==================== УТИЛИТЫ ====================

class ValidationError(Exception):
    """Исключение для ошибок валидации с поддержкой поля"""

    def __init__(self, field: str, message: str, value: any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")

    def __str__(self):
        value_info = f" (got: {self.value!r})" if self.value is not None else ""
        return f"ValidationError({self.field}): {self.message}{value_info}"


def raise_if_invalid(valid: bool, message: str, field: str = "", value: any = None):
    """Выбросить ValidationError если валидация не прошла"""
    if not valid:
        app_logger.error(f"❌ Validation error in field '{field}': {message}")
        raise ValidationError(field, message, value)


def validate_multiple(
    *validations: Tuple[bool, str, str]
) -> Tuple[bool, List[str]]:
    """Выполнить несколько валидаций и собрать все ошибки"""
    errors = []
    for is_valid, message, field in validations:
        if not is_valid and message:
            errors.append(f"{field}: {message}" if field else message)
    
    return len(errors) == 0, errors


# ==================== ПРЕДЗАПОЛНЕННЫЕ НАБОРЫ ====================

def validate_employee_data(
    full_name: str,
    position: str = "",
    phone: str = "",
    email: str = "",
    salary: Union[str, float] = None,
) -> Tuple[bool, List[str]]:
    """Комплексная валидация данных сотрудника"""
    validations = [
        (validate_required(full_name, "Full name")[0], 
         validate_required(full_name, "Full name")[1], 
         "full_name"),
        (validate_string_length(full_name, max_length=100, field_name="Full name")[0],
         validate_string_length(full_name, max_length=100, field_name="Full name")[1],
         "full_name"),
        (validate_phone(phone, required=False)[0],
         validate_phone(phone, required=False)[1],
         "phone"),
        (validate_email(email, required=False)[0],
         validate_email(email, required=False)[1],
         "email"),
    ]
    
    if salary is not None:
        validations.append(
            (validate_currency(salary, min_val=0, field_name="Salary")[0],
             validate_currency(salary, min_val=0, field_name="Salary")[1],
             "salary")
        )
    
    return validate_multiple(*validations)


def validate_part_data(
    name: str,
    sku: str = "",
    quantity: Union[str, int] = None,
    price: Union[str, float] = None,
    cost: Union[str, float] = None,
) -> Tuple[bool, List[str]]:
    """Комплексная валидация данных запчасти"""
    validations = [
        (validate_required(name, "Part name")[0],
         validate_required(name, "Part name")[1],
         "name"),
        (validate_string_length(name, max_length=200, field_name="Part name")[0],
         validate_string_length(name, max_length=200, field_name="Part name")[1],
         "name"),
        (validate_sku(sku, required=False)[0],
         validate_sku(sku, required=False)[1],
         "sku"),
    ]
    
    if quantity is not None:
        validations.append(
            (validate_number(quantity, min_val=0, field_name="Quantity", allow_decimal=False)[0],
             validate_number(quantity, min_val=0, field_name="Quantity", allow_decimal=False)[1],
             "quantity")
        )
    
    if price is not None:
        validations.append(
            (validate_currency(price, min_val=0, field_name="Price")[0],
             validate_currency(price, min_val=0, field_name="Price")[1],
             "price")
        )
    
    if cost is not None:
        validations.append(
            (validate_currency(cost, min_val=0, field_name="Cost")[0],
             validate_currency(cost, min_val=0, field_name="Cost")[1],
             "cost")
        )
        if price is not None and cost is not None:
            try:
                if float(price) < float(cost):
                    validations.append((False, "Price cannot be less than cost", "price"))
            except (ValueError, TypeError):
                pass
    
    return validate_multiple(*validations)