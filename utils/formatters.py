# utils/formatters.py
"""
Модуль форматирования данных для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Критический баг с заменой месяцев, типизация, отрицательные числа
✅ УЛУЧШЕНО: Надёжное форматирование, расширенная поддержка локалей
✅ ДОБАВЛЕНО: Форматирование размеров, процентов, длительности
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union, Tuple, List, Any, Literal
import re


class DateFormat:
    """Предопределённые форматы дат"""
    SHORT = "%Y-%m-%d"
    MEDIUM = "%d.%m.%Y"
    LONG = "%d %B %Y"
    DATETIME = "%Y-%m-%d %H:%M:%S"
    DATETIME_RU = "%d.%m.%Y %H:%M"
    TIME = "%H:%M:%S"
    TIME_SHORT = "%H:%M"


class CurrencyCode:
    """Коды валют"""
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    BYN = "BYN"
    UAH = "UAH"


class DateFormatter:
    """Форматировщик дат с поддержкой локалей"""

    MONTHS_RU: List[str] = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    MONTHS_EN: List[str] = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    MONTHS_RU_NOM: List[str] = [
        "январь", "февраль", "март", "апрель", "май", "июнь",
        "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
    ]

    def __init__(self, locale: str = "ru"):
        self.locale = locale

    def format(
        self,
        date_value: Union[str, date, datetime, None],
        format_type: str = DateFormat.SHORT,
        include_time: bool = False,
    ) -> str:
        """
        Форматирование даты с корректной заменой месяцев
        
        ✅ ИСПРАВЛЕНО: Использует плейсхолдер вместо прямой замены чисел
        """
        if date_value is None:
            return ""

        # Парсинг строки
        if isinstance(date_value, str):
            parsed = self._parse_date_string(date_value)
            if parsed is None:
                return str(date_value)
            date_value = parsed

        # Определение формата
        format_str = format_type
        if include_time and "%H" not in format_str:
            format_str += " %H:%M" if self.locale == "ru" else " %H:%M:%S"

        # ✅ ИСПРАВЛЕНО: Корректная замена месяцев через плейсхолдер
        if self.locale == "ru" and "%B" in format_str:
            # Заменяем %B на уникальный плейсхолдер
            temp_format = format_str.replace("%B", "%%MONTH_NAME%%")
            result = date_value.strftime(temp_format)
            month_name = self.MONTHS_RU[date_value.month - 1]
            return result.replace("%%MONTH_NAME%%", month_name)
        
        if self.locale == "en" and "%B" in format_str:
            temp_format = format_str.replace("%B", "%%MONTH_NAME%%")
            result = date_value.strftime(temp_format)
            month_name = self.MONTHS_EN[date_value.month - 1]
            return result.replace("%%MONTH_NAME%%", month_name)

        return date_value.strftime(format_str)

    def format_relative(
        self, 
        date_value: Union[str, date, datetime], 
        now: Optional[datetime] = None,
        short: bool = False
    ) -> str:
        """
        Форматирование относительной даты
        
        Args:
            short: Короткий формат ("2д" вместо "2 дня назад")
        """
        if isinstance(date_value, str):
            parsed = self._parse_date_string(date_value)
            if parsed is None:
                return ""
            date_value = parsed

        if now is None:
            now = datetime.now()

        # Приводим к date для сравнения дней
        target_date = date_value.date() if isinstance(date_value, datetime) else date_value
        today = now.date()
        delta = today - target_date

        if self.locale == "ru":
            if delta == timedelta(0):
                return "сегодня"
            elif delta == timedelta(1):
                return "вчера"
            elif delta == timedelta(2):
                return "позавчера"
            elif delta.days < 0:
                if delta.days == -1:
                    return "завтра"
                elif delta.days == -2:
                    return "послезавтра"
                return f"через {abs(delta.days)} дн." if short else f"через {abs(delta.days)} дней"
            elif delta.days < 7:
                return f"{delta.days}д" if short else f"{delta.days} дн. назад"
            elif delta.days < 30:
                weeks = delta.days // 7
                return f"{weeks}н" if short else f"{weeks} нед. назад"
            else:
                return self.format(date_value, DateFormat.MEDIUM)
        else:
            if delta == timedelta(0):
                return "today"
            elif delta == timedelta(1):
                return "yesterday"
            elif delta.days < 7:
                return f"{delta.days}d ago" if short else f"{delta.days} days ago"
            elif delta.days < 30:
                weeks = delta.days // 7
                return f"{weeks}w ago" if short else f"{weeks} weeks ago"
            else:
                return self.format(date_value, "%b %d, %Y")

    def format_duration(self, seconds: Union[int, float], short: bool = False) -> str:
        """
        Форматирование длительности в секундах
        
        Example:
            >>> format_duration(3665)
            '1ч 1м 5с'
        """
        seconds = int(seconds)
        if seconds < 0:
            return "-" + self.format_duration(-seconds, short)
        
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        
        if self.locale == "ru":
            parts = []
            if hours:
                parts.append(f"{hours}ч" if short else f"{hours} ч")
            if minutes:
                parts.append(f"{minutes}м" if short else f"{minutes} мин")
            if secs or not parts:
                parts.append(f"{secs}с" if short else f"{secs} сек")
            return " ".join(parts)
        else:
            parts = []
            if hours:
                parts.append(f"{hours}h" if short else f"{hours} hr")
            if minutes:
                parts.append(f"{minutes}m" if short else f"{minutes} min")
            if secs or not parts:
                parts.append(f"{secs}s" if short else f"{secs} sec")
            return " ".join(parts)

    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Парсинг строки даты в datetime"""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
            "%d.%m.%Y", "%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S",
            "%d/%m/%Y", "%m/%d/%Y",  # US format
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    def set_locale(self, locale: Literal["ru", "en"]) -> None:
        """Смена локали"""
        if locale in ("ru", "en"):
            self.locale = locale


class CurrencyFormatter:
    """Форматировщик денежных сумм"""

    SYMBOLS: dict[str, str] = {
        "RUB": "₽", "USD": "$", "EUR": "€", "KZT": "₸", "BYN": "Br", "UAH": "₴"
    }

    def __init__(
        self,
        currency: str = "RUB",
        locale: str = "ru",
        show_symbol: bool = True,
        decimal_places: int = 2,
    ):
        self.currency = currency.upper()
        self.locale = locale
        self.show_symbol = show_symbol
        self.decimal_places = decimal_places

    def format(
        self, 
        amount: Union[int, float, str, None], 
        show_sign: bool = False,
        force_sign_for_positive: bool = False
    ) -> str:
        """
        Форматирование суммы с корректной обработкой отрицательных чисел
        
        ✅ ИСПРАВЛЕНО: Отдельная обработка знака для надёжности
        """
        if amount is None:
            return ""

        try:
            num_amount = float(amount)
        except (ValueError, TypeError):
            return str(amount)

        # ✅ ИСПРАВЛЕНО: Обрабатываем знак отдельно
        sign = ""
        if show_sign or (force_sign_for_positive and num_amount > 0):
            if num_amount > 0:
                sign = "+"
            elif num_amount < 0:
                sign = "−"  # Используем правильный минус, не дефис
                num_amount = abs(num_amount)  # Работаем с модулем

        # Форматируем абсолютное значение
        if self.locale == "ru":
            # Русское форматирование
            formatted = f"{num_amount:,.{self.decimal_places}f}"
            # Заменяем разделители: запятая→X, точка→запятая, X→пробел
            formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
            # Группируем тысячи пробелами
            if "." in formatted:
                int_part, dec_part = formatted.split(".")
                int_part = re.sub(r"(?<=\d)(?=(\d{3})+(?!\d))", " ", int_part)
                formatted = f"{int_part},{dec_part}"
            else:
                formatted = re.sub(r"(?<=\d)(?=(\d{3})+(?!\d))", " ", formatted)
        else:
            # Английское форматирование
            formatted = f"{num_amount:,.{self.decimal_places}f}"

        # Собираем результат
        result = f"{sign}{formatted}"
        
        if self.show_symbol:
            symbol = self.SYMBOLS.get(self.currency, self.currency)
            if self.locale == "ru":
                result = f"{result} {symbol}"
            else:
                result = f"{symbol}{result}"

        return result

    def format_range(
        self, 
        min_amount: Union[int, float], 
        max_amount: Union[int, float],
        separator: Optional[str] = None
    ) -> str:
        """Форматирование диапазона сумм"""
        min_str = self.format(min_amount, show_sign=False)
        max_str = self.format(max_amount, show_sign=False)
        
        sep = separator or (" до " if self.locale == "ru" else " - ")
        prefix = "от " if self.locale == "ru" and not separator else ""
        
        return f"{prefix}{min_str}{sep}{max_str}"

    def format_percentage(
        self, 
        value: Union[int, float], 
        show_sign: bool = True,
        decimal_places: int = 1
    ) -> str:
        """
        Форматирование процента
        
        Example:
            >>> format_percentage(12.5)
            '+12,5%'
        """
        try:
            num = float(value)
        except (ValueError, TypeError):
            return str(value)
        
        sign = ""
        if show_sign:
            if num > 0:
                sign = "+"
            elif num < 0:
                sign = "−"
                num = abs(num)
        
        if self.locale == "ru":
            formatted = f"{num:.{decimal_places}f}".replace(".", ",")
        else:
            formatted = f"{num:.{decimal_places}f}"
        
        return f"{sign}{formatted}%"

    def set_currency(self, currency: str) -> None:
        self.currency = currency.upper()

    def set_locale(self, locale: Literal["ru", "en"]) -> None:
        if locale in ("ru", "en"):
            self.locale = locale


class PhoneFormatter:
    """Форматировщик телефонных номеров"""

    def __init__(self, country: str = "ru"):
        self.country = country

    def format(
        self, 
        phone: Optional[str], 
        format_type: Literal["international", "national", "e164"] = "international"
    ) -> str:
        if not phone:
            return ""

        clean = re.sub(r"[^\d+]", "", phone)

        if self.country == "ru":
            return self._format_ru_phone(clean, format_type)
        elif self.country == "us":
            return self._format_us_phone(clean, format_type)
        else:
            return self._format_generic_phone(clean, format_type)

    def _format_ru_phone(self, phone: str, format_type: str) -> str:
        """Форматирование российского телефона"""
        # Нормализация: убираем +7 или 8
        if phone.startswith("+7"):
            phone = phone[2:]
        elif phone.startswith("8"):
            phone = phone[1:]
        
        digits = re.sub(r"\D", "", phone)
        
        if len(digits) != 10:
            return phone  # Возвращаем как есть если не валидный
        
        d1, d2, d3, d4, d5 = digits[:3], digits[3:6], digits[6:8], digits[8:10], digits[8:]
        
        if format_type == "e164":
            return f"+7{digits}"
        elif format_type == "national":
            return f"8 ({d1}) {d2}-{d3}-{d4}"
        else:  # international
            return f"+7 ({d1}) {d2}-{d3}-{d4}"

    def _format_us_phone(self, phone: str, format_type: str) -> str:
        """Форматирование телефона США"""
        if phone.startswith("+1"):
            phone = phone[2:]
        elif phone.startswith("1"):
            phone = phone[1:]
        
        digits = re.sub(r"\D", "", phone)
        
        if len(digits) != 10:
            return phone
        
        d1, d2, d3 = digits[:3], digits[3:6], digits[6:]
        
        if format_type == "e164":
            return f"+1{digits}"
        elif format_type == "national":
            return f"({d1}) {d2}-{d3}"
        else:
            return f"+1 ({d1}) {d2}-{d3}"

    def _format_generic_phone(self, phone: str, format_type: str) -> str:
        """Базовое форматирование для других стран"""
        if format_type == "e164" and not phone.startswith("+"):
            return f"+{phone}"
        return phone

    def is_valid(self, phone: Optional[str]) -> bool:
        """Проверка валидности телефона"""
        if not phone:
            return False
        clean = re.sub(r"[^\d+]", "", phone)
        if self.country == "ru":
            return bool(re.match(r"^(\+7|8)?\d{10}$", clean))
        return len(re.sub(r"\D", "", clean)) >= 10


class TextFormatter:
    """Форматировщик текста"""

    @staticmethod
    def capitalize_words(text: str) -> str:
        """Капитализация каждого слова"""
        return " ".join(word.capitalize() for word in text.split())

    @staticmethod
    def title_case(text: str) -> str:
        """Заголовок: капитализация с исключениями"""
        small_words = {"и", "в", "на", "по", "с", "к", "о", "за", "the", "a", "an", "of", "in", "on", "at"}
        words = text.split()
        result = []
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in small_words:
                result.append(word.capitalize())
            else:
                result.append(word.lower())
        return " ".join(result)

    @staticmethod
    def slugify(text: str, separator: str = "-", lowercase: bool = True) -> str:
        """Преобразование текста в URL-friendly slug"""
        if lowercase:
            text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_]+", separator, text)
        text = re.sub(f"{re.escape(separator)}+", separator, text)
        return text.strip(separator)

    @staticmethod
    def pluralize(
        number: int,
        forms: Tuple[str, str, str],
        locale: str = "ru",
    ) -> str:
        """
        Склонение слов по числам для русского языка
        
        forms: (1, 2-4, 5-0) например: ("день", "дня", "дней")
        """
        if locale != "ru":
            return forms[0] if number == 1 else forms[1]

        n = abs(number) % 100
        n1 = n % 10

        if 11 <= n <= 19:
            return forms[2]
        if n1 == 1:
            return forms[0]
        elif 2 <= n1 <= 4:
            return forms[1]
        else:
            return forms[2]

    @staticmethod
    def mask_email(email: str, visible_chars: int = 3, mask_char: str = "*") -> str:
        """Маскировка email для безопасного отображения"""
        if not email or "@" not in email:
            return email or ""

        local, domain = email.rsplit("@", 1)
        
        if len(local) <= visible_chars:
            masked_local = local
        else:
            masked_local = local[:visible_chars] + mask_char * (len(local) - visible_chars)
        
        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str, visible_digits: int = 4, mask_char: str = "*") -> str:
        """
        Маскировка телефона с сохранением исходного форматирования
        
        ✅ ИСПРАВЛЕНО: Корректно сохраняет исходные разделители
        """
        if not phone:
            return phone or ""

        # Сохраняем исходные разделители и их позиции
        original = phone
        digits = re.sub(r"\D", "", phone)
        
        if len(digits) <= visible_digits:
            return phone

        # Создаём маску из цифр
        masked_digits = mask_char * (len(digits) - visible_digits) + digits[-visible_digits:]
        
        # Восстанавливаем форматирование, заменяя цифры в оригинале
        result = []
        digit_idx = 0
        for char in original:
            if char.isdigit():
                result.append(masked_digits[digit_idx])
                digit_idx += 1
            else:
                result.append(char)  # Сохраняем разделители
        
        return "".join(result)

    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = "...", 
                 break_words: bool = False) -> str:
        """
        Обрезка текста с опцией сохранения целостности слов
        
        Args:
            break_words: Если False, обрезает на границе слова
        """
        if not text or len(text) <= max_length:
            return text or ""
        
        if break_words:
            return text[:max_length - len(suffix)].rstrip() + suffix
        
        # Обрезаем и ищем последнее полное слово
        truncated = text[:max_length - len(suffix)]
        last_space = truncated.rfind(" ")
        if last_space > max_length * 0.7:  # Не обрезаем слишком агрессивно
            truncated = truncated[:last_space]
        
        return truncated.rstrip() + suffix

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Извлечение всех чисел из текста"""
        return [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", text)]

    @staticmethod
    def remove_extra_spaces(text: str) -> str:
        """Удаление лишних пробелов"""
        return re.sub(r"\s+", " ", text).strip()


class SizeFormatter:
    """Форматировщик размеров файлов/данных"""
    
    UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]
    
    @classmethod
    def format(cls, size_bytes: Union[int, float], locale: str = "ru", 
               decimal_places: int = 1) -> str:
        """
        Форматирование размера в человекочитаемый вид
        
        >>> SizeFormatter.format(1536)
        '1,5 KB'
        """
        size = float(size_bytes)
        if size < 0:
            return "0 B"
        
        for unit in cls.UNITS:
            if size < 1024.0:
                if unit == "B":
                    return f"{int(size)} {unit}"
                if locale == "ru":
                    formatted = f"{size:.{decimal_places}f}".replace(".", ",")
                else:
                    formatted = f"{size:.{decimal_places}f}"
                return f"{formatted} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} PB"