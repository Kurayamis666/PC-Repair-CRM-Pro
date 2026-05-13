# services/barcode_service.py
"""
Сервис генерации штрих-кодов и этикеток для PC Repair CRM Pro

✅ Генерация QR-кодов с валидацией данных
✅ Создание этикеток для оборудования и запчастей
✅ Поддержка пакетной генерации с прогрессом
✅ Кэширование для избежания дубликатов
✅ Гибкая настройка размеров и шрифтов
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import io
import hashlib
from typing import Optional, List, Dict, Union, TypedDict, Callable
from pathlib import Path

from core.logger import app_logger
from utils.helpers import format_currency


# ==================== 🎯 ТИПЫ ДАННЫХ ====================

class EquipmentLabelData(TypedDict):
    """Данные для этикетки оборудования"""
    equipment_id: int
    model: str
    serial_number: str
    client_name: str


class PartLabelData(TypedDict):
    """Данные для этикетки запчасти"""
    part_id: int
    name: str
    sku: str
    price: float


# ==================== ⚙️ КОНФИГУРАЦИЯ ====================

class BarcodeServiceConfig:
    """Конфигурация сервиса генерации кодов"""
    
    # Размеры по умолчанию (в пикселях при 96 DPI)
    EQUIPMENT_LABEL_SIZE = (400, 250)  # ~10x6 см
    PART_LABEL_SIZE = (300, 200)        # ~7.5x5 см
    QR_CODE_SIZE = 120
    
    # Шрифты (с фоллбэком)
    FONT_PATHS = [
        "arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
    ]
    
    # QR-код настройки
    QR_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_L
    QR_BOX_SIZE = 10
    QR_BORDER = 2
    
    # Обрезка текста
    MAX_MODEL_LENGTH = 25
    MAX_CLIENT_LENGTH = 20
    MAX_PART_NAME_LENGTH = 25


class BarcodeService:
    """
    Сервис генерации штрих-кодов и этикеток
    
    ✅ Генерация QR-кодов с валидацией и кэшированием
    ✅ Создание этикеток с адаптивной обрезкой текста
    ✅ Поддержка пакетной генерации с обработкой ошибок
    ✅ Гибкая конфигурация размеров и шрифтов
    ✅ Возврат данных в памяти (BytesIO) для веб-отправки
    
    Пример использования:
        >>> service = BarcodeService()
        >>> # Генерация одной этикетки
        >>> path = service.generate_equipment_label(123, "MacBook Pro", "SN12345", "Иван Петров")
        >>> 
        >>> # Пакетная генерация
        >>> items = [{"equipment_id": 1, "model": "iPhone 14", ...}, ...]
        >>> paths = service.generate_batch_labels(items, label_type="equipment")
    """
    
    def __init__(
        self, 
        output_dir: str = "reports/barcodes",
        config: Optional[BarcodeServiceConfig] = None,
    ):
        """
        Инициализация сервиса
        
        Args:
            output_dir: Директория для сохранения файлов
            config: Конфигурация сервиса (по умолчанию стандартная)
        """
        self.output_dir = output_dir
        self.config = config or BarcodeServiceConfig()
        
        # ✅ Создаём директорию если не существует
        os.makedirs(output_dir, exist_ok=True)
        
        # ✅ Кэш хешей для избежания дубликатов: {hash: filepath}
        self._generated_cache: Dict[str, str] = {}
        
        # ✅ Загружаем шрифты один раз при инициализации
        self._fonts = self._load_fonts()
        
        app_logger.info(f"🔲 BarcodeService initialized (output: {output_dir})")
    
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """
        Загрузка шрифтов с фоллбэком на системные
        
        Returns:
            Dict[str, ImageFont]: Словарь {size: font_object}
        """
        fonts = {}
        
        # Пробуем загрузить из списка путей
        for font_path in self.config.FONT_PATHS:
            try:
                if os.path.exists(font_path):
                    # Загружаем разные размеры
                    for size in [10, 12, 14, 16]:
                        fonts[size] = ImageFont.truetype(font_path, size)
                    break
            except Exception:
                continue
        else:
            # ✅ Fallback на default шрифт (мелкий, но работает везде)
            app_logger.warning("⚠️ Custom fonts not found, using default font")
            default_font = ImageFont.load_default()
            for size in [10, 12, 14, 16]:
                fonts[size] = default_font
        
        return fonts
    
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Получить шрифт нужного размера с фоллбэком"""
        return self._fonts.get(size, self._fonts.get(12, ImageFont.load_default()))
    
    def _sanitize_text(self, text: str, max_length: int) -> str:
        """
        Санитизация и обрезка текста для этикетки
        
        ✅ Убирает опасные символы, обрезает до макс. длины, добавляет "..."
        """
        if not text:
            return ""
        
        # ✅ Убираем переносы строк и лишние пробелы
        cleaned = " ".join(str(text).split())
        
        # ✅ Обрезаем если слишком длинный
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length - 3] + "..."
        
        # ✅ Экранируем спецсимволы для безопасности (хотя PIL не исполняет код)
        cleaned = cleaned.replace("<", "&lt;").replace(">", "&gt;")
        
        return cleaned
    
    def _get_data_hash(self, data: Dict) -> str:
        """Получить хеш данных для кэширования"""
        # ✅ Сортируем ключи для консистентного хеша
        data_str = str(sorted(data.items()))
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def generate_qr_code(
        self, 
        data: str, 
        filename: str, 
        size: Optional[int] = None,
        border: Optional[int] = None,
        return_bytes: bool = False,
    ) -> Union[str, bytes]:
        """
        Генерация QR-кода с кэшированием
        
        ✅ Кэширование по хешу данных для избежания дубликатов
        ✅ Поддержка возврата bytes для веб-отправки
        ✅ Валидация входных данных
        
        Args:
            data: Данные для кодирования (будут обрезаны до 1000 символов)
            filename: Имя файла (без расширения)
            size: Размер изображения (по умолчанию из конфига)
            border: Ширина границы (по умолчанию из конфига)
            return_bytes: Если True — вернуть bytes вместо сохранения файла
            
        Returns:
            str или bytes: Путь к файлу или байты изображения
        """
        # ✅ Валидация и подготовка данных
        if not data:
            app_logger.error("❌ QR code data cannot be empty")
            return b"" if return_bytes else ""
        
        # ✅ Обрезаем очень длинные данные (ограничение QR-кода)
        if len(data) > 1000:
            app_logger.warning(f"⚠️ QR data truncated from {len(data)} to 1000 chars")
            data = data[:1000]
        
        # ✅ Проверяем кэш
        cache_key = f"qr:{data}:{size or self.config.QR_CODE_SIZE}"
        if cache_key in self._generated_cache and not return_bytes:
            cached_path = self._generated_cache[cache_key]
            if os.path.exists(cached_path):
                app_logger.debug(f"♻️ Using cached QR code: {cached_path}")
                return cached_path
        
        try:
            # ✅ Создание QR-кода
            qr = qrcode.QRCode(
                version=1,
                error_correction=self.config.QR_ERROR_CORRECTION,
                box_size=self.config.QR_BOX_SIZE,
                border=border or self.config.QR_BORDER,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # ✅ Ресайз если нужно
            target_size = size or self.config.QR_CODE_SIZE
            if img.size[0] != target_size:
                img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            
            if return_bytes:
                # ✅ Возврат в памяти для веб-отправки
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                return buf.getvalue()
            else:
                # ✅ Сохранение в файл
                output_path = os.path.join(self.output_dir, f"{filename}.png")
                img.save(output_path)
                
                # ✅ Сохраняем в кэш
                self._generated_cache[cache_key] = output_path
                
                app_logger.info(f"📱 QR code generated: {output_path}")
                return output_path
                
        except Exception as e:
            app_logger.exception(f"❌ QR code error: {e}")
            return b"" if return_bytes else ""
    
    def generate_equipment_label(
        self,
        equipment_id: int,
        model: str,
        serial_number: str,
        client_name: str,
        return_bytes: bool = False,
    ) -> Union[str, bytes]:
        """
        Генерация этикетки для оборудования
        
        ✅ Адаптивная обрезка текста
        ✅ Проверка существования файлов перед вставкой
        ✅ Поддержка возврата bytes
        
        Args:
            equipment_id: ID оборудования
            model: Модель устройства
            serial_number: Серийный номер
            client_name: Имя клиента
            return_bytes: Если True — вернуть bytes вместо файла
            
        Returns:
            str или bytes: Путь к файлу или байты изображения
        """
        try:
            # ✅ Подготовка данных с санитизацией
            model_clean = self._sanitize_text(model, self.config.MAX_MODEL_LENGTH)
            serial_clean = self._sanitize_text(serial_number, 30)
            client_clean = self._sanitize_text(client_name, self.config.MAX_CLIENT_LENGTH)
            
            # ✅ Проверка кэша
            cache_data = {
                "type": "equipment",
                "id": equipment_id,
                "model": model_clean,
                "serial": serial_clean,
                "client": client_clean,
            }
            cache_key = self._get_data_hash(cache_data)
            
            if cache_key in self._generated_cache and not return_bytes:
                cached_path = self._generated_cache[cache_key]
                if os.path.exists(cached_path):
                    return cached_path
            
            # ✅ Создание изображения
            width, height = self.config.EQUIPMENT_LABEL_SIZE
            img = Image.new("RGB", (width, height), color="white")
            draw = ImageDraw.Draw(img)
            
            # ✅ Шрифты
            font_title = self._get_font(16)
            font_body = self._get_font(12)
            font_small = self._get_font(10)
            
            # ✅ Текст этикетки
            y_offset = 15
            draw.text((20, y_offset), f"ID: {equipment_id}", fill="black", font=font_title)
            y_offset += 25
            draw.text((20, y_offset), f"Модель: {model_clean}", fill="black", font=font_body)
            y_offset += 25
            draw.text((20, y_offset), f"Сер. номер: {serial_clean}", fill="black", font=font_body)
            y_offset += 25
            draw.text((20, y_offset), f"Клиент: {client_clean}", fill="black", font=font_body)
            
            # ✅ QR-код с ссылкой на оборудование
            qr_data = f"EQUIPMENT:{equipment_id}:{serial_number}"
            qr_result = self.generate_qr_code(
                qr_data, 
                f"eq_{equipment_id}", 
                size=self.config.QR_CODE_SIZE,
                return_bytes=False  # Всегда сохраняем временный файл для вставки
            )
            
            # ✅ Вставка QR-кода если успешно сгенерирован
            if qr_result and isinstance(qr_result, str) and os.path.exists(qr_result):
                try:
                    qr_img = Image.open(qr_result)
                    # ✅ Позиция в правом верхнем углу
                    img.paste(qr_img, (width - self.config.QR_CODE_SIZE - 20, 15))
                    qr_img.close()  # ✅ Закрываем файл после использования
                except Exception as e:
                    app_logger.warning(f"⚠️ Could not paste QR code: {e}")
            
            # ✅ Футер
            draw.text(
                (20, height - 25), 
                "PC Repair CRM Pro", 
                fill="gray", 
                font=font_small
            )
            
            if return_bytes:
                # ✅ Возврат в памяти
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                result = buf.getvalue()
            else:
                # ✅ Сохранение в файл
                output_path = os.path.join(self.output_dir, f"label_eq_{equipment_id}.png")
                img.save(output_path)
                
                # ✅ Кэшируем путь
                self._generated_cache[cache_key] = output_path
                result = output_path
            
            app_logger.info(f"🏷️ Equipment label generated: {result if isinstance(result, str) else '<bytes>'}")
            return result
            
        except Exception as e:
            app_logger.exception(f"❌ Equipment label generation error: {e}")
            return b"" if return_bytes else ""
    
    def generate_part_label(
        self,
        part_id: int,
        name: str,
        sku: str,
        price: float,
        return_bytes: bool = False,
    ) -> Union[str, bytes]:
        """
        Генерация этикетки для запчасти
        
        ✅ Форматирование цены через format_currency()
        ✅ Адаптивная обрезка названия
        
        Args:
            part_id: ID запчасти
            name: Название запчасти
            sku: Артикул
            price: Цена
            return_bytes: Если True — вернуть bytes вместо файла
            
        Returns:
            str или bytes: Путь к файлу или байты изображения
        """
        try:
            # ✅ Подготовка данных
            name_clean = self._sanitize_text(name, self.config.MAX_PART_NAME_LENGTH)
            sku_clean = self._sanitize_text(sku, 20)
            price_formatted = format_currency(price, "RUB", "ru")  # ✅ Используем утилиту
            
            # ✅ Проверка кэша
            cache_data = {
                "type": "part",
                "id": part_id,
                "name": name_clean,
                "sku": sku_clean,
                "price": price,
            }
            cache_key = self._get_data_hash(cache_data)
            
            if cache_key in self._generated_cache and not return_bytes:
                cached_path = self._generated_cache[cache_key]
                if os.path.exists(cached_path):
                    return cached_path
            
            # ✅ Создание изображения
            width, height = self.config.PART_LABEL_SIZE
            img = Image.new("RGB", (width, height), color="white")
            draw = ImageDraw.Draw(img)
            
            # ✅ Шрифты
            font_title = self._get_font(14)
            font_body = self._get_font(12)
            font_price = self._get_font(16)
            
            # ✅ Текст этикетки
            y_offset = 15
            draw.text((15, y_offset), name_clean, fill="black", font=font_title)
            y_offset += 25
            draw.text((15, y_offset), f"SKU: {sku_clean}", fill="black", font=font_body)
            y_offset += 25
            draw.text((15, y_offset), f"Цена: {price_formatted}", fill="black", font=font_price)
            
            # ✅ QR-код
            qr_data = f"PART:{part_id}:{sku}"
            qr_result = self.generate_qr_code(
                qr_data,
                f"part_{part_id}",
                size=100,
                return_bytes=False
            )
            
            # ✅ Вставка QR-кода
            if qr_result and isinstance(qr_result, str) and os.path.exists(qr_result):
                try:
                    qr_img = Image.open(qr_result)
                    img.paste(qr_img, (width - 100 - 20, 15))
                    qr_img.close()
                except Exception as e:
                    app_logger.warning(f"⚠️ Could not paste QR code: {e}")
            
            if return_bytes:
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                result = buf.getvalue()
            else:
                output_path = os.path.join(self.output_dir, f"label_part_{part_id}.png")
                img.save(output_path)
                self._generated_cache[cache_key] = output_path
                result = output_path
            
            return result
            
        except Exception as e:
            app_logger.exception(f"❌ Part label error: {e}")
            return b"" if return_bytes else ""
    
    def generate_batch_labels(
        self, 
        items: List[Union[EquipmentLabelData, PartLabelData]], 
        label_type: str = "equipment",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[str]:
        """
        Генерация пакета этикеток с обработкой ошибок
        
        ✅ Продолжает генерацию даже если одна этикетка упала
        ✅ Опциональный callback для отображения прогресса
        
        Args:
            items: Список словарей с данными для этикеток
            label_type: "equipment" или "part"
            progress_callback: Функция callback(current, total) для прогресс-бара
            
        Returns:
            List[str]: Список путей к успешно сгенерированным файлам
        """
        paths: List[str] = []
        total = len(items)
        
        for idx, item in enumerate(items):
            try:
                if label_type == "equipment":
                    # ✅ Типизированный доступ к полям
                    path = self.generate_equipment_label(
                        equipment_id=item["equipment_id"],
                        model=item["model"],
                        serial_number=item["serial_number"],
                        client_name=item["client_name"],
                    )
                elif label_type == "part":
                    path = self.generate_part_label(
                        part_id=item["part_id"],
                        name=item["name"],
                        sku=item["sku"],
                        price=item["price"],
                    )
                else:
                    app_logger.warning(f"⚠️ Unknown label type: {label_type}")
                    path = ""
                
                if path and isinstance(path, str):
                    paths.append(path)
                    
            except Exception as e:
                app_logger.error(f"❌ Failed to generate label #{idx + 1}: {e}")
                # ✅ Продолжаем генерацию остальных
            
            # ✅ Вызов callback для прогресса
            if progress_callback:
                try:
                    progress_callback(idx + 1, total)
                except Exception:
                    pass  # Не ломаем генерацию если callback упал
        
        app_logger.info(f"✅ Batch generation complete: {len(paths)}/{total} labels created")
        return paths
    
    def clear_cache(self) -> int:
        """
        Очистка кэша сгенерированных файлов
        
        ⚠️ Удаляет файлы из output_dir!
        
        Returns:
            int: Количество удалённых файлов
        """
        removed = 0
        for filepath in self._generated_cache.values():
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    removed += 1
            except Exception as e:
                app_logger.warning(f"⚠️ Could not remove cached file {filepath}: {e}")
        
        self._generated_cache.clear()
        app_logger.info(f"🧹 Cleared {removed} cached barcode files")
        return removed