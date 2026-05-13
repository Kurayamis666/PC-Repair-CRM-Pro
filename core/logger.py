# core/logger.py
"""
Модуль логирования для PC Repair CRM Pro

✅ БЕЗОПАСНОСТЬ: Корректная обработка extra-полей
✅ ГИБКОСТЬ: Настройка уровня логирования из конфига
✅ ПРОДАКШЕН: Отключение консоли в .exe, JSON-режим опционально
✅ ОТЛАДКА: Расширенный формат с именем файла и строкой
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Any

from core.config import Config  # ✅ Для чтения уровня логирования из конфига


class AppLogger:
    """
    Кастомный логгер для приложения
    
    ✅ Безопасная работа с extra-полями (без KeyError)
    ✅ Защита от дублирования хендлеров (Singleton)
    ✅ Автоматическое отключение консоли в скомпилированном .exe
    ✅ Расширенный формат для отладки (файл:строка)
    """
    
    _instance: Optional["AppLogger"] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton паттерн: один экземпляр на всё приложение"""
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(
        self, 
        name: str = "pc_repair", 
        log_dir: str = "logs",
        console_output: Optional[bool] = None,
    ):
        # ✅ Инициализация только один раз
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.logger = logging.getLogger(name)
        
        # ✅ Чтение уровня логирования из конфига (или дефолт)
        log_level_str = getattr(Config, 'LOG_LEVEL', 'DEBUG').upper()
        log_level = getattr(logging, log_level_str, logging.DEBUG)
        self.logger.setLevel(log_level)
        
        # ✅ Создаем директорию для логов
        os.makedirs(log_dir, exist_ok=True)
        
        # ✅ Расширенный формат с файлом и строкой для отладки
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # ✅ Файловый обработчик (ротация)
        log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m')}.log")
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8',
            delay=True  # ✅ Не создавать файл пока не будет первого лога
        )
        file_handler.setLevel(logging.DEBUG)  # В файл пишем всё
        file_handler.setFormatter(formatter)
        
        # ✅ Консольный обработчик (только если не .exe или явно включено)
        if console_output is None:
            # Авто-определение: в .exe консоли нет
            console_output = not getattr(sys, 'frozen', False)
        
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)  # В консоль только важное
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # ✅ Добавляем хендлеры (только если ещё не добавлены)
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            if console_output and console_handler:
                self.logger.addHandler(console_handler)
        
        # ✅ Запрещаем прокидывание логов в корневой логгер (избегаем дублей)
        self.logger.propagate = False
        
        self._initialized = True
    
    def _prepare_extra(self, **kwargs) -> dict:
        """
        Безопасная подготовка extra-полей
        
        ✅ Фильтрует зарезервированные ключи, которые могут вызвать ошибку
        ✅ Возвращает только безопасные для логгера данные
        """
        # Ключи, которые нельзя передавать в extra (вызовут ошибку или конфликт)
        reserved = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'exc_info', 'exc_text',
            'stack_info', 'message', 'module'  # module — частая ошибка!
        }
        return {k: v for k, v in kwargs.items() if k not in reserved}
    
    def _log(self, level: int, message: str, **kwargs):
        """Внутренний метод для безопасного логирования"""
        extra = self._prepare_extra(**kwargs)
        # ✅ Передаём extra только если есть данные
        self.logger.log(level, message, extra=extra if extra else {})
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """
        Логирование исключения с полным traceback
        
        ✅ Всегда включает exc_info=True
        ✅ Безопасно фильтрует extra-поля
        """
        extra = self._prepare_extra(**kwargs)
        # ✅ Явно передаём exc_info=True для записи стека вызовов
        self.logger.exception(message, exc_info=True, extra=extra if extra else {})
    
    def set_level(self, level: str):
        """
        Динамическая смена уровня логирования (для отладки)
        
        Args:
            level: Строка уровня ('DEBUG', 'INFO', 'WARNING', etc.)
        """
        log_level = getattr(logging, level.upper(), logging.DEBUG)
        self.logger.setLevel(log_level)
        self.info(f"🔧 Log level changed to: {level.upper()}")


# ✅ Глобальный экземпляр (Singleton)
app_logger = AppLogger()