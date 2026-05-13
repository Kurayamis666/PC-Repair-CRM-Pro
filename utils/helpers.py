# utils/helpers.py (исправленные импорты)
"""
Вспомогательные функции общего назначения для PC Repair CRM Pro
✅ УЛУЧШЕНО: Исправлены measure_time, format_date, safe_get
✅ ДОБАВЛЕНО: validate_url, debounce, cache, json helpers
✅ СОВМЕСТИМО: Использует app_logger без module= параметра
"""

# ✅ ИМПОРТЫ
import os
import re
import uuid
import json
import hashlib
import secrets
import time
import threading  # ← ДОБАВЛЕНО: Для debounce декоратора
from datetime import datetime, timedelta, date
from typing import (
    Optional,
    Union,
    List,
    Dict,
    Any,
    Callable,
    Tuple,
    TypeVar,
    cast,
    Type,
)
from pathlib import Path
from functools import wraps, lru_cache
from collections import defaultdict

from core.logger import app_logger

T = TypeVar("T")


# ==================== ИДЕНТИФИКАТОРЫ И ТОКЕНЫ ====================

def generate_id(prefix: str = "") -> str:
    """
    Генерация уникального идентификатора
    
    Returns:
        str: Уникальный ID (12 hex символов) с опциональным префиксом
        
    Example:
        >>> generate_id("USR_")
        'USR_A1B2C3D4E5F6'
    """
    unique_part = uuid.uuid4().hex[:12].upper()
    return f"{prefix}{unique_part}" if prefix else unique_part


def generate_secure_token(length: int = 32) -> str:
    """
    Генерация криптографически безопасного токена
    
    Args:
        length: Длина токена в байтах (по умолчанию 32)
        
    Returns:
        str: URL-safe base64 encoded token
    """
    return secrets.token_urlsafe(length)


# ==================== ПАРОЛИ И БЕЗОПАСНОСТЬ ====================

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Хеширование пароля с солью используя PBKDF2-HMAC-SHA256
    
    Args:
        password: Пароль в открытом виде
        salt: Соль (если None, будет сгенерирована)
        
    Returns:
        Tuple[str, str]: (хеш, соль)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256", 
        password.encode("utf-8"), 
        salt.encode("utf-8"), 
        100_000  # Итерации для стойкости к брутфорсу
    ).hex()

    return password_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Проверка пароля против хеша (timing-safe сравнение)
    
    Args:
        password: Введённый пароль
        password_hash: Сохранённый хеш
        salt: Соль, использованная при хешировании
        
    Returns:
        bool: True если пароль верный
    """
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(test_hash, password_hash)


# ==================== ФОРМАТИРОВАНИЕ ====================

def format_currency(
    amount: Union[int, float, str, None], 
    currency: str = "RUB", 
    locale: str = "ru",
    show_symbol: bool = True,
) -> str:
    """
    Форматирование денежной суммы с учётом локали
    
    Args:
        amount: Сумма (число или строка)
        currency: Код валюты (RUB, USD, EUR)
        locale: Язык форматирования (ru, en)
        show_symbol: Показывать ли символ валюты
        
    Returns:
        str: Отформатированная сумма
        
    Examples:
        >>> format_currency(1234.5, "RUB", "ru")
        '1 234,50 ₽'
        >>> format_currency(1234.5, "USD", "en")
        '$1,234.50'
    """
    if amount is None:
        return ""

    try:
        num_amount = float(amount)
    except (ValueError, TypeError):
        return str(amount)

    # Словарь символов валют
    symbols = {"RUB": "₽", "USD": "$", "EUR": "€", "KZT": "₸", "BYN": "Br"}
    symbol = symbols.get(currency, f"{currency} ") if show_symbol else ""
    
    if locale == "ru":
        # Русское форматирование: пробел как разделитель тысяч, запятая для десятичных
        formatted = f"{abs(num_amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        # Группировка тысяч пробелами
        if "." in formatted:
            int_part, dec_part = formatted.split(".")
            int_part = re.sub(r"(?<=\d)(?=(\d{3})+(?!\d))", " ", int_part)
            formatted = f"{int_part},{dec_part}"
        else:
            formatted = re.sub(r"(?<=\d)(?=(\d{3})+(?!\d))", " ", formatted)
        
        # Добавляем знак минус для отрицательных чисел
        if num_amount < 0:
            formatted = f"-{formatted}"
            
        return f"{formatted} {symbol}".strip() if symbol else formatted
    else:
        # Английское форматирование: запятая для тысяч, точка для десятичных
        formatted = f"{num_amount:,.2f}"
        return f"{symbol}{formatted}" if symbol and show_symbol else formatted


def format_date(
    date_value: Union[str, datetime, date, None],
    format_str: str = "%Y-%m-%d",
    locale: str = "ru",
) -> str:
    """
    Форматирование даты с поддержкой русских месяцев
    
    Args:
        date_value: Дата (строка, datetime или date)
        format_str: Формат strftime
        locale: Язык ('ru' для русских месяцев)
        
    Returns:
        str: Отформатированная дата
        
    Examples:
        >>> format_date("2026-05-11", "%d %B %Y", "ru")
        '11 мая 2026'
    """
    if date_value is None:
        return ""

    parsed_dt: Optional[datetime] = None

    if isinstance(date_value, str):
        # Пробуем несколько распространённых форматов
        for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y", "%d/%m/%Y"]:
            try:
                parsed_dt = datetime.strptime(date_value.strip(), fmt)
                break
            except ValueError:
                continue
        if parsed_dt is None:
            return str(date_value)
        date_value = parsed_dt

    if isinstance(date_value, (datetime, date)):
        # Обработка русских месяцев (%B)
        if locale == "ru" and "%B" in format_str:
            months_ru = [
                "января", "февраля", "марта", "апреля", "мая", "июня",
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            # Заменяем %B на плейсхолдер, форматируем, потом заменяем плейсхолдер
            temp_format = format_str.replace("%B", "%%MONTH%%")
            result = date_value.strftime(temp_format)
            month_name = months_ru[date_value.month - 1]
            return result.replace("%%MONTH%%", month_name)
        
        return date_value.strftime(format_str)

    return str(date_value)


def format_datetime(
    dt: Union[str, datetime, None], 
    include_time: bool = True, 
    locale: str = "ru"
) -> str:
    """
    Форматирование даты и времени
    
    Args:
        dt: Дата/время (строка ISO или datetime)
        include_time: Включать ли время в вывод
        locale: Язык форматирования
        
    Returns:
        str: Отформатированная дата и время
    """
    if dt is None:
        return ""

    if isinstance(dt, str):
        try:
            # Поддержка ISO формата с 'Z' для UTC
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            # Если не распарсили — возвращаем как есть
            return dt

    if isinstance(dt, datetime):
        if locale == "ru":
            fmt = "%d.%m.%Y %H:%M" if include_time else "%d.%m.%Y"
        else:
            fmt = "%Y-%m-%d %H:%M" if include_time else "%Y-%m-%d"
        return dt.strftime(fmt)

    return str(dt)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезка текста до заданной длины с суффиксом
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина результата (включая суффикс)
        suffix: Суффикс для обрезанного текста
        
    Returns:
        str: Обрезанный текст
    """
    if not text or len(text) <= max_length:
        return text or ""
    
    # Учитываем длину суффикса при обрезке
    cut_length = max_length - len(suffix)
    if cut_length <= 0:
        return suffix[:max_length]
    
    return text[:cut_length].rstrip() + suffix


# ==================== РАБОТА С ДАННЫМИ ====================

def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Безопасное получение вложенного значения из словаря
    
    ⚠️  Возвращает default ТОЛЬКО если ключ отсутствует, 
        а не если значение равно None!
    
    Args:
        data: Исходный словарь
        *keys: Цепочка ключей для вложенного доступа
        default: Значение по умолчанию если ключ не найден
        
    Returns:
        Any: Найденное значение или default
        
    Example:
        >>> data = {'user': {'profile': {'name': 'Alice'}}}
        >>> safe_get(data, 'user', 'profile', 'name')
        'Alice'
        >>> safe_get(data, 'user', 'email', default='N/A')
        'N/A'
    """
    result: Any = data
    for key in keys:
        if not isinstance(result, dict):
            return default
        # Проверяем наличие ключа явно, чтобы отличать None от отсутствия
        if key not in result:
            return default
        result = result[key]
    return result


def safe_set(data: Dict[str, Any], *keys: str, value: Any) -> Dict[str, Any]:
    """
    Безопасная установка вложенного значения в словарь
    
    Создаёт промежуточные словари если нужно.
    
    Args:
        data: Целевой словарь (будет изменён)
        *keys: Цепочка ключей
        value: Значение для установки
        
    Returns:
        Dict[str, Any]: Изменённый словарь (для цепочки вызовов)
        
    Example:
        >>> data = {}
        >>> safe_set(data, 'user', 'profile', 'name', value='Alice')
        >>> data
        {'user': {'profile': {'name': 'Alice'}}}
    """
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    if keys:
        current[keys[-1]] = value
    return data


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """
    Разбиение списка на части заданного размера
    
    Args:
        lst: Исходный список
        chunk_size: Размер каждой части
        
    Returns:
        List[List[T]]: Список списков
        
    Example:
        >>> chunk_list([1,2,3,4,5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if chunk_size <= 0:
        return [lst] if lst else []
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested: List[Any]) -> List[Any]:
    """
    Рекурсивное «выпрямление» вложенного списка
    
    Args:
        nested: Список с возможными вложениями
        
    Returns:
        List[Any]: Плоский список
        
    Example:
        >>> flatten_list([1, [2, [3, 4]], 5])
        [1, 2, 3, 4, 5]
    """
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def merge_dicts(*dicts: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
    """
    Слияние нескольких словарей
    
    Args:
        *dicts: Словари для слияния (последние переопределяют первые)
        deep: Рекурсивно сливать вложенные словари
        
    Returns:
        Dict[str, Any]: Объединённый словарь
    """
    result: Dict[str, Any] = {}
    
    for d in dicts:
        if not d:
            continue
        for key, value in d.items():
            if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value, deep=True)
            else:
                result[key] = value
    
    return result


# ==================== ДЕКОРАТОРЫ ====================

def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable:
    """
    Декоратор для повторных попыток при ошибке с экспоненциальной задержкой
    
    Args:
        max_attempts: Максимальное количество попыток
        delay: Начальная задержка в секундах
        backoff: Множитель задержки после каждой попытки
        exceptions: Кортеж исключений для перехвата
        on_retry: Callback(attempt, exception) вызывается перед повтором
        
    Example:
        @retry_on_error(max_attempts=5, delay=0.5, exceptions=(ConnectionError,))
        def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    app_logger.warning(
                        f"⚠️ Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}"
                    )
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as cb_error:
                            app_logger.error(f"Error in on_retry callback: {cb_error}")
                    
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        break

            app_logger.error(
                f"❌ All {max_attempts} attempts failed for {func.__name__}",
                exc_info=last_exception,
            )
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unknown error after {max_attempts} retries")

        return wrapper
    return decorator


def measure_time(func: Callable[..., T]) -> Callable[..., T]:
    """
    Декоратор для замера времени выполнения функции
    
    Логирует время выполнения в секундах с миллисекундной точностью.
    
    ✅ ИСПРАВЛЕНО: Теперь корректно возвращает результат функции
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.perf_counter()  # Более точный таймер
        try:
            result: T = func(*args, **kwargs)  # ✅ Сохраняем результат
            return result
        finally:
            duration = time.perf_counter() - start
            app_logger.info(f"⏱️ {func.__name__} executed in {duration:.3f}s")
    
    return wrapper


def debounce(wait: float) -> Callable:
    """
    Декоратор для «задержки» вызова функции (debounce)
    
    Полезно для обработки ввода пользователя, чтобы не выполнять
    тяжёлые операции на каждое нажатие клавиши.
    
    Args:
        wait: Время ожидания в секундах после последнего вызова
        
    Example:
        @debounce(0.5)
        def on_search(text):
            # Будет вызвана только через 0.5с после остановки ввода
            search_api(text)
    """
    timers: Dict[Callable, Optional[threading.Timer]] = {}
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            import threading
            
            def call_func():
                func(*args, **kwargs)
                timers[func] = None
            
            # Отменяем предыдущий таймер если есть
            if timers.get(func):
                timers[func].cancel()
            
            # Создаём новый таймер
            timer = threading.Timer(wait, call_func)
            timer.daemon = True
            timer.start()
            timers[func] = timer
        
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 300, max_size: int = 128) -> Callable:
    """
    Декоратор для кэширования результатов функции
    
    ⚠️  Работает только для функций с хешируемыми аргументами!
    
    Args:
        ttl_seconds: Время жизни кеша в секундах
        max_size: Максимальное количество записей в кеше
        
    Example:
        @cache_result(ttl_seconds=60)
        def get_exchange_rate(currency: str) -> float:
            # Результат будет закэширован на 60 секунд
            return fetch_from_api(currency)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: Dict[str, Tuple[T, float]] = {}
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            import hashlib
            
            # Создаём ключ кеша из аргументов
            key_parts = [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            now = time.time()
            
            # Проверяем кеш
            if cache_key in cache:
                value, timestamp = cache[cache_key]
                if now - timestamp < ttl_seconds:
                    return value  # Возвращаем закэшированное значение
                else:
                    del cache[cache_key]  # Срок истёк — удаляем
            
            # Вызываем функцию и кэшируем результат
            result: T = func(*args, **kwargs)
            cache[cache_key] = (result, now)
            
            # Ограничиваем размер кеша (LRU)
            if len(cache) > max_size:
                # Удаляем самый старый элемент
                oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                del cache[oldest_key]
            
            return result
        
        # Добавляем метод для очистки кеша
        wrapper.clear_cache = lambda: cache.clear()  # type: ignore
        wrapper.cache_info = lambda: len(cache)  # type: ignore
        
        return wrapper
    return decorator


# ==================== РАБОТА С ФАЙЛАМИ И ПУТЯМИ ====================

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Гарантировать существование директории
    
    Создаёт директорию и все родительские если нужно.
    
    Args:
        path: Путь к директории
        
    Returns:
        Path: Объект пути к созданной/существующей директории
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Получить размер файла в байтах
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        int: Размер в байтах, 0 если файл не найден
    """
    try:
        return Path(file_path).stat().st_size
    except (FileNotFoundError, OSError):
        return 0


def format_file_size(size_bytes: Union[int, float]) -> str:
    """
    Форматирование размера файла в человекочитаемый вид
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        str: Форматированный размер (например, "1.5 MB")
        
    Example:
        >>> format_file_size(1536)
        '1.5 KB'
    """
    size: float = float(size_bytes)
    if size < 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    for unit in units:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Очистка имени файла от недопустимых символов
    
    Безопасно для использования в пути на Windows/Linux/macOS.
    
    Args:
        filename: Исходное имя файла
        replacement: Символ для замены недопустимых
        
    Returns:
        str: Безопасное имя файла (макс. 255 символов)
    """
    # Запрещённые символы в путях (Windows + универсальные)
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Убираем пробелы в начале/конце и ограничиваем длину
    sanitized = sanitized.strip()[:255]
    
    # Защита от зарезервированных имён в Windows
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'LPT1', 'LPT2'}
    name_without_ext = Path(sanitized).stem.upper()
    if name_without_ext in reserved:
        sanitized = f"{replacement}{sanitized}"
    
    return sanitized or "unnamed"


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Проверка формата URL
    
    Args:
        url: URL для проверки
        allowed_schemes: Разрешённые протоколы (по умолчанию ['http', 'https'])
        
    Returns:
        Tuple[bool, str]: (валидно, сообщение об ошибке)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"
    
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    # Простая, но надёжная проверка
    pattern = r"^(?:{}):\/\/[^\s/$.?#].[^\s]*$".format('|'.join(re.escape(s) for s in allowed_schemes))
    
    if not re.match(pattern, url.strip(), re.IGNORECASE):
        return False, f"Invalid URL format (allowed: {', '.join(allowed_schemes)}://...)"
    
    return True, ""


# ==================== JSON И СЕРИАЛИЗАЦИЯ ====================

def to_json_safe(obj: Any) -> Any:
    """
    Преобразование объекта в JSON-совместимый формат
    
    Обрабатывает datetime, Path, sets и другие не-сериализуемые типы.
    
    Args:
        obj: Произвольный объект
        
    Returns:
        Any: JSON-совместимое представление
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    if isinstance(obj, Path):
        return str(obj)
    
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple)):
        return [to_json_safe(item) for item in obj]
    
    if hasattr(obj, '__dict__'):
        return to_json_safe(obj.__dict__)
    
    return str(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    Безопасная сериализация в JSON
    
    Автоматически обрабатывает не-сериализуемые типы через to_json_safe.
    
    Args:
        obj: Объект для сериализации
        **kwargs: Дополнительные аргументы для json.dumps
        
    Returns:
        str: JSON строка
    """
    safe_obj = to_json_safe(obj)
    return json.dumps(safe_obj, ensure_ascii=False, **kwargs)


# ==================== УТИЛИТЫ ====================

class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass


def raise_if(condition: bool, message: str, exc_type: Type[Exception] = ValueError):
    """
    Выбросить исключение если условие истинно
    
    Удобная короткая запись для валидаций.
    
    Args:
        condition: Условие для проверки
        message: Сообщение об ошибке
        exc_type: Тип исключения для выброса
        
    Raises:
        exc_type: Если condition == True
        
    Example:
        >>> raise_if(not user, "User not found", NotFoundError)
    """
    if condition:
        raise exc_type(message)


def batch_process(
    items: List[T],
    processor: Callable[[T], Any],
    batch_size: int = 100,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> List[Any]:
    """
    Пакетная обработка списка с прогрессом
    
    Args:
        items: Список элементов для обработки
        processor: Функция обработки одного элемента
        batch_size: Размер пакета
        on_progress: Callback(current, total) для обновления прогресса
        
    Returns:
        List[Any]: Результаты обработки
    """
    results = []
    total = len(items)
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        for item in batch:
            results.append(processor(item))
        
        if on_progress:
            on_progress(min(i + batch_size, total), total)
    
    return results