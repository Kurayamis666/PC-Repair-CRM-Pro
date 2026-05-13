# core/unit_converter.py
"""
Конвертер единиц измерения для PC Repair CRM Pro

✅ ТОЧНОСТЬ: Использование Decimal для избежания ошибок float
✅ НАДЕЖНОСТЬ: Нормализация ввода (регистр, пробелы, алиасы)
✅ ГИБКОСТЬ: Расширенный список единиц и категорий
✅ ТИПИЗАЦИЯ: Полная аннотация типов
"""

from typing import Dict, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import logging

logger = logging.getLogger(__name__)

# ==================== 📦 КОНФИГУРАЦИЯ ЕДИНИЦ ====================

# Коэффициенты конвертации (относительно базовой единицы категории)
# Базовые единицы: вес=kg, длина=m, объем=l, количество=pcs
CONVERSION_RATES: Dict[str, Dict[str, Decimal]] = {
    "weight": {  # Вес (Base: kg)
        "kg": Decimal("1.0"),
        "g": Decimal("0.001"),
        "mg": Decimal("0.000001"),
        "t": Decimal("1000.0"),
        "lb": Decimal("0.453592"),  # Фунт
        "oz": Decimal("0.0283495"),  # Унция
    },
    "length": {  # Длина (Base: m)
        "m": Decimal("1.0"),
        "cm": Decimal("0.01"),
        "mm": Decimal("0.001"),
        "km": Decimal("1000.0"),
        "in": Decimal("0.0254"),  # Дюйм
        "ft": Decimal("0.3048"),   # Фут
    },
    "volume": {  # Объем (Base: l)
        "l": Decimal("1.0"),
        "ml": Decimal("0.001"),
        "m3": Decimal("1000.0"),
        "gal": Decimal("3.78541"), # Галлон
    },
    "quantity": {  # Количество (Base: pcs)
        "pcs": Decimal("1.0"),
        "pack": Decimal("10.0"),   # Упаковка = 10 шт
        "box": Decimal("50.0"),    # Коробка = 50 шт
        "doz": Decimal("12.0"),    # Дюжина
        "set": Decimal("1.0"),     # Комплект (как 1 шт)
    }
}

# Алиасы (синонимы) для нормализации ввода
UNIT_ALIASES: Dict[str, str] = {
    # Вес
    "кг": "kg", "килограмм": "kg", "килограмм": "kg",
    "г": "g", "грамм": "g", "грамма": "g",
    "мг": "mg", "миллиграмм": "mg",
    "т": "t", "тонна": "t", "тонны": "t",
    "фунт": "lb", "унция": "oz",
    # Длина
    "м": "m", "метр": "m", "метра": "m", "метров": "m",
    "см": "cm", "сантиметр": "cm",
    "мм": "mm", "миллиметр": "mm",
    "км": "km", "километр": "km",
    "дюйм": "in", "фут": "ft",
    # Объем
    "л": "l", "литр": "l", "литра": "l", "литров": "l",
    "мл": "ml", "миллилитр": "ml",
    "м3": "m3", "куб": "m3",
    # Количество
    "шт": "pcs", "штука": "pcs", "штук": "pcs", "штуки": "pcs",
    "упак": "pack", "упаковка": "pack",
    "кор": "box", "коробка": "box",
    "дюжина": "doz", "пара": "pcs", "пара": "pcs", # Пара часто считается как 1 единица товара в CRM
    "комплект": "set", "набор": "set",
    "piece": "pcs", "pieces": "pcs",
}

# Переводы для отображения (Внутренний код -> RU / EN)
UNIT_DISPLAY_NAMES: Dict[str, Dict[str, str]] = {
    "ru": {
        "kg": "кг", "g": "г", "mg": "мг", "t": "т",
        "m": "м", "cm": "см", "mm": "мм", "km": "км",
        "l": "л", "ml": "мл", "m3": "м³",
        "pcs": "шт", "pack": "уп.", "box": "кор.", "set": "компл.",
        "lb": "фунт", "oz": "унция", "in": "дюйм", "ft": "фут",
    },
    "en": {
        "kg": "kg", "g": "g", "mg": "mg", "t": "t",
        "m": "m", "cm": "cm", "mm": "mm", "km": "km",
        "l": "L", "ml": "mL", "m3": "m³",
        "pcs": "pcs", "pack": "pack", "box": "box", "set": "set",
        "lb": "lb", "oz": "oz", "in": "in", "ft": "ft",
    }
}


class UnitConverter:
    """
    Класс для конвертации единиц измерения
    
    ✅ Использует Decimal для точных вычислений
    ✅ Поддерживает алиасы и нормализацию
    """

    @classmethod
    def normalize_unit(cls, unit: str) -> Optional[str]:
        """
        Нормализация единицы: удаление пробелов, нижний регистр, поиск алиасов
        
        Args:
            unit: Исходная строка (например, " Кг ", "штук")
            
        Returns:
            str: Нормализованный код (например, "kg") или None
        """
        if not unit:
            return None
            
        # Очистка: пробелы, точки в конце, нижний регистр
        clean = unit.strip().rstrip(".").lower()
        
        # 1. Проверка на точное совпадение в Rate
        for category in CONVERSION_RATES.values():
            if clean in category:
                return clean
        
        # 2. Проверка по алиасам
        if clean in UNIT_ALIASES:
            return UNIT_ALIASES[clean]
            
        return None

    @classmethod
    def get_unit_category(cls, unit: str) -> Optional[str]:
        """Определить категорию единицы измерения"""
        code = cls.normalize_unit(unit)
        if not code:
            return None
            
        for category, units in CONVERSION_RATES.items():
            if code in units:
                return category
        return None

    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """
        Конвертировать значение из одной единицы в другую
        
        ✅ Использует Decimal для избежания ошибок float
        
        Args:
            value: Значение для конвертации
            from_unit: Исходная единица
            to_unit: Целевая единица
            
        Returns:
            float: Конвертированное значение или None
        """
        from_code = cls.normalize_unit(from_unit)
        to_code = cls.normalize_unit(to_unit)
        
        if not from_code or not to_code:
            logger.warning(f"Unknown units: {from_unit} -> {to_unit}")
            return None
            
        if from_code == to_code:
            return value
            
        # Определяем категорию
        category = cls.get_unit_category(from_code)
        if not category:
            return None
            
        # Проверяем совместимость категорий
        if to_code not in CONVERSION_RATES.get(category, {}):
            logger.warning(f"Incompatible units: {from_code} ({category}) -> {to_code}")
            return None
            
        try:
            from_rate = CONVERSION_RATES[category][from_code]
            to_rate = CONVERSION_RATES[category][to_code]
            
            if to_rate == 0:
                logger.error(f"Zero division error for unit: {to_code}")
                return None

            # Расчет через Decimal
            decimal_val = Decimal(str(value))
            # value * from_rate = base_amount
            # base_amount / to_rate = result
            result = (decimal_val * from_rate) / to_rate
            
            # Округляем до 6 знаков и возвращаем float
            return float(result.quantize(Decimal('1.000000'), rounding=ROUND_HALF_UP))
            
        except (InvalidOperation, ZeroDivisionError) as e:
            logger.error(f"Conversion error: {e}")
            return None

    @classmethod
    def translate_unit(cls, unit: str, lang: str = "ru") -> str:
        """
        Перевести название единицы измерения
        
        Args:
            unit: Единица (код или алиас)
            lang: Язык ('ru' или 'en')
            
        Returns:
            str: Переведенное название
        """
        code = cls.normalize_unit(unit)
        if not code:
            return unit  # Возвращаем как есть если не нашли
            
        lang_dict = UNIT_DISPLAY_NAMES.get(lang, UNIT_DISPLAY_NAMES["en"])
        return lang_dict.get(code, code)

    @classmethod
    def format_value(cls, value: float, unit: str, lang: str = "ru") -> str:
        """
        Отформатировать значение с единицей измерения
        
        Примеры:
            1.0 кг -> "1 кг"
            1.500 кг -> "1.5 кг"
            
        Args:
            value: Числовое значение
            unit: Единица измерения
            lang: Язык
            
        Returns:
            str: Отформатированная строка
        """
        translated = cls.translate_unit(unit, lang)
        
        # Умное форматирование: убираем лишние нули
        if value == int(value):
            num_str = str(int(value))
        else:
            num_str = f"{value:.4f}".rstrip('0').rstrip('.')
            
        return f"{num_str} {translated}"

    @classmethod
    def get_available_units(cls, category: Optional[str] = None, lang: str = "ru") -> Dict[str, str]:
        """
        Получить список доступных единиц для выпадающего списка
        
        Args:
            category: Фильтр по категории (None = все)
            lang: Язык отображения
            
        Returns:
            Dict[str, str]: {code: display_name}
        """
        result = {}
        target_cats = [category] if category else CONVERSION_RATES.keys()
        
        for cat in target_cats:
            if cat in CONVERSION_RATES:
                for code in CONVERSION_RATES[cat]:
                    result[code] = cls.translate_unit(code, lang)
        return result


# ==================== 🧪 ТЕСТЫ ====================
if __name__ == "__main__":
    # 1. Конвертация
    print("=== Конвертация ===")
    print(f"1 кг в г: {UnitConverter.convert(1, 'kg', 'g')}")          # 1000.0
    print(f"1000 г в кг: {UnitConverter.convert(1000, 'g', 'kg')}")    # 1.0
    print(f"1 упак в шт: {UnitConverter.convert(1, 'упак', 'шт')}")    # 10.0
    print(f"1 дюжина в шт: {UnitConverter.convert(1, 'doz', 'pcs')}")  # 12.0
    
    # 2. Нормализация (грязный ввод)
    print("\n=== Нормализация ===")
    print(f"' Кг ' -> {UnitConverter.normalize_unit(' Кг ')}")         # kg
    print(f"'штука' -> {UnitConverter.normalize_unit('штука')}")       # pcs
    
    # 3. Перевод
    print("\n=== Перевод ===")
    print(f"pcs (RU): {UnitConverter.translate_unit('pcs', 'ru')}")    # шт
    print(f"pcs (EN): {UnitConverter.translate_unit('pcs', 'en')}")    # pcs
    print(f"кг (EN): {UnitConverter.translate_unit('кг', 'en')}")      # kg
    
    # 4. Форматирование
    print("\n=== Форматирование ===")
    print(UnitConverter.format_value(1.0, 'kg', 'ru'))                # 1 кг
    print(UnitConverter.format_value(1.500, 'kg', 'ru'))              # 1.5 кг
    print(UnitConverter.format_value(0.123456, 'g', 'en'))            # 0.1235 g
    
    # 5. Ошибки
    print("\n=== Ошибки ===")
    print(f"кг в м: {UnitConverter.convert(1, 'kg', 'm')}")           # None (разные категории)
    print(f"кг в попугай: {UnitConverter.convert(1, 'kg', 'parrot')}")# None (нет такой единицы)