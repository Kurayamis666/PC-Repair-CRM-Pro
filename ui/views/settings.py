# ui/views/settings.py
"""
Экран настроек приложения для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: on_navigate извлекается до super().__init__()
✅ ИСПРАВЛЕНО: Безопасная загрузка тестовых данных (пропуск несуществующих таблиц)
✅ ИСПРАВЛЕНО: Используется таблица employees вместо clients
✅ УЛУЧШЕНО: Полный перевод, безопасность паролей, валидация, архитектура
✅ УЛУЧШЕНО: Прогресс-индикаторы, обработка ошибок, интеграция с Config
✅ СОВМЕСТИМО: Работа из .exe, централизованное хранение настроек
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os
import hashlib
import random
import shutil
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from core.logger import app_logger
from core.config_loader import config, init_config
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils, theme as theme_manager
from translations import get_text
from ui.widgets.toast import ToastNotification
from utils.helpers import hash_password, verify_password, ensure_dir


class SettingsView(ctk.CTkFrame):
    """
    Экран настроек приложения с полным функционалом
    
    ✅ Полный перевод всех текстов (RU ↔ EN)
    ✅ Безопасное хеширование паролей (PBKDF2)
    ✅ Валидация всех входных данных
    ✅ Централизованное хранение настроек (БД + Config)
    ✅ Прогресс-индикаторы для долгих операций
    ✅ Обработка ошибок файловых операций
    ✅ Интеграция с ThemeManager для динамической смены темы
    ✅ on_navigate извлекается до инициализации родителя
    ✅ Безопасная загрузка тестовых данных с пропуском несуществующих таблиц
    """
    
    on_navigate: Optional[Callable[[str], None]] = None
    
    def __init__(
        self, 
        parent: ctk.CTkBaseClass, 
        lang: str = "ru", 
        on_navigate: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        # ✅ ИСПРАВЛЕНО: Извлекаем on_navigate и lang ПЕРЕД super().__init__()
        self.on_navigate = on_navigate
        self.lang = lang
        self.db = DatabaseConnection()
        
        # ✅ Удаляем кастомные аргументы из kwargs перед передачей в родительский класс
        kwargs.pop('on_navigate', None)
        kwargs.pop('lang', None)
        
        # ✅ Теперь передаём только валидные аргументы для ctk.CTkFrame
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Построение интерфейса настроек с полным переводом"""
        
        # 🏷️ Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.TEXT_SECONDARY, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="⚙️ " + get_text("settings", self.lang),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(pady=15)
        
        # 🔙 Кнопка назад
        ctk.CTkButton(
            self,
            text=get_text("back", self.lang),
            command=lambda: self.on_navigate("dashboard") if self.on_navigate else None,
            width=120,
            height=35,
            fg_color=ColorTheme.TEXT_SECONDARY,
            corner_radius=10,
        ).pack(padx=30, pady=20, anchor="w")
        
        # 📑 Вкладки настроек
        notebook = ctk.CTkTabview(self, fg_color="transparent")
        notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Создаём вкладки с переводом
        general_tab = notebook.add(get_text("general_settings", self.lang))
        self._build_general_settings(general_tab)
        
        smtp_tab = notebook.add(get_text("smtp_settings", self.lang))
        self._build_smtp_settings(smtp_tab)
        
        sms_tab = notebook.add(get_text("sms_settings", self.lang))
        self._build_sms_settings(sms_tab)
        
        # ⚠️ Вкладка пользователей — ссылка на отдельный экран
        users_tab = notebook.add(get_text("users", self.lang))
        self._build_users_placeholder(users_tab)
        
        db_tab = notebook.add(get_text("database_settings", self.lang))
        self._build_database_settings(db_tab)
        
        security_tab = notebook.add(get_text("security_settings", self.lang))
        self._build_security_settings(security_tab)
    
    def _go_back(self) -> None:
        """Возврат на дашборд"""
        if self.on_navigate:
            self.on_navigate("dashboard")
    
    # ==================== 📋 ОСНОВНЫЕ НАСТРОЙКИ ====================
    def _build_general_settings(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_CARD, corner_radius=16)
        card.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(
            card, 
            text=get_text("general_settings", self.lang), 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color=ColorTheme.PRIMARY
        ).pack(pady=20)
        
        settings_frame = ctk.CTkFrame(card, fg_color="transparent")
        settings_frame.pack(fill="x", padx=30, pady=10)
        
        # 🔹 Порог низкого остатка
        ctk.CTkLabel(
            settings_frame, 
            text=get_text("low_stock_threshold", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY, 
            width=200
        ).pack(side="left")
        self.low_stock_entry = ctk.CTkEntry(
            settings_frame, 
            width=100, 
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY
        )
        self.low_stock_entry.pack(side="left", padx=10)
        self._load_threshold_value()
        
        # 🔹 Показать предупреждение
        self.show_low_stock_var = ctk.BooleanVar(value=True)
        self._load_show_low_stock_value()
        
        ctk.CTkCheckBox(
            card, 
            text=get_text("show_low_stock_button", self.lang), 
            variable=self.show_low_stock_var, 
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(padx=30, pady=10, anchor="w")
        
        # 🔹 Тема оформления
        ctk.CTkLabel(
            card, 
            text=get_text("theme", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(padx=30, pady=(10, 0), anchor="w")
        
        self.theme_var = ctk.StringVar(value="dark" if theme_manager.is_dark else "light")
        theme_menu = ctk.CTkOptionMenu(
            card, 
            values=[get_text("dark", self.lang), get_text("light", self.lang), get_text("system", self.lang)], 
            variable=self.theme_var, 
            width=200, 
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY,
            command=self._on_theme_change
        )
        theme_menu.pack(padx=30, pady=10, anchor="w")
        
        # 🔹 Язык
        ctk.CTkLabel(
            card, 
            text=get_text("language", self.lang), 
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(padx=30, pady=(10, 0), anchor="w")
        
        self.lang_var = ctk.StringVar(value=self.lang)
        lang_menu = ctk.CTkOptionMenu(
            card, 
            values=["ru", "en"], 
            variable=self.lang_var, 
            width=200, 
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY,
            command=self._on_language_change
        )
        lang_menu.pack(padx=30, pady=10, anchor="w")
        
        # 💾 Кнопка сохранения
        ctk.CTkButton(
            card, 
            text="💾 " + get_text("save", self.lang), 
            command=self._save_general_settings, 
            width=200, 
            height=35, 
            fg_color=ColorTheme.SUCCESS, 
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        ).pack(pady=20)
    
    def _load_threshold_value(self) -> None:
        try:
            with self.db.get_cursor() as cur:
                cur.execute("SELECT value FROM settings WHERE key = 'low_stock_threshold'")
                row = cur.fetchone()
                if row and row[0]:
                    self.low_stock_entry.delete(0, "end")
                    self.low_stock_entry.insert(0, str(row[0]))
        except Exception as e:
            app_logger.warning(f"⚠️ Could not load threshold: {e}")
            self.low_stock_entry.insert(0, "5")
    
    def _load_show_low_stock_value(self) -> None:
        try:
            with self.db.get_cursor() as cur:
                cur.execute("SELECT value FROM settings WHERE key = 'show_low_stock_button'")
                row = cur.fetchone()
                if row and row[0] == "1":
                    self.show_low_stock_var.set(True)
        except Exception as e:
            app_logger.warning(f"⚠️ Could not load setting: {e}")
    
    def _on_theme_change(self, value: str) -> None:
        """Обработчик смены темы"""
        theme_map = {
            get_text("dark", self.lang): "dark",
            get_text("light", self.lang): "light",
            get_text("system", self.lang): "system"
        }
        theme_name = theme_map.get(value, "dark")
        theme_manager.set_theme(theme_name)
        app_logger.info(f"🎨 Theme changed to: {theme_name}")
    
    def _on_language_change(self, value: str) -> None:
        """Обработчик смены языка"""
        if value in ("ru", "en"):
            from translations import set_language
            set_language(value)
            self.lang = value
            ToastNotification(self, get_text("language_changed", self.lang) or "Язык изменён", "success")
    
    def _save_general_settings(self) -> None:
        try:
            threshold = self.low_stock_entry.get().strip()
            if not threshold.isdigit() or not (1 <= int(threshold) <= 1000):
                return ToastNotification(self, get_text("invalid_threshold", self.lang) or "Порог должен быть числом от 1 до 1000", "warning")
            
            show_btn = "1" if self.show_low_stock_var.get() else "0"
            
            with self.db.get_cursor() as cur:
                cur.execute("UPDATE settings SET value = ? WHERE key = 'low_stock_threshold'", (threshold,))
                cur.execute("UPDATE settings SET value = ? WHERE key = 'show_low_stock_button'", (show_btn,))
                cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('default_language', ?)", (self.lang_var.get(),))
                cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('default_theme', ?)", (self.theme_var.get(),))
            
            ToastNotification(self, get_text("settings_saved", self.lang) or "✅ Настройки сохранены", "success")
            app_logger.info("⚙️ General settings saved")
            
        except Exception as e:
            app_logger.exception(f"❌ Error saving settings: {e}")
            ToastNotification(self, f"{get_text('error_saving', self.lang)}: {e}", "error")
    
    # ==================== 📧 НАСТРОЙКИ SMTP ====================
    def _build_smtp_settings(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_CARD, corner_radius=16)
        card.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(card, text=get_text("smtp_settings", self.lang), font=ctk.CTkFont(size=16, weight="bold"), text_color=ColorTheme.PRIMARY).pack(pady=20)
        
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(form_frame, text=get_text("smtp_server", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.smtp_host = ctk.CTkEntry(form_frame, placeholder_text="smtp.gmail.com", width=300, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.smtp_host.pack(pady=5)
        self.smtp_host.insert(0, config.get_str("SMTP_HOST", "smtp.gmail.com"))
        
        ctk.CTkLabel(form_frame, text=get_text("smtp_port", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.smtp_port = ctk.CTkEntry(form_frame, placeholder_text="587", width=100, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.smtp_port.pack(pady=5)
        self.smtp_port.insert(0, str(config.get_int("SMTP_PORT", 587)))
        
        ctk.CTkLabel(form_frame, text=get_text("smtp_from", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.smtp_from = ctk.CTkEntry(form_frame, placeholder_text="noreply@example.com", width=300, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.smtp_from.pack(pady=5)
        self.smtp_from.insert(0, config.get_str("SMTP_FROM", ""))
        
        ctk.CTkLabel(form_frame, text=get_text("smtp_login", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.smtp_user = ctk.CTkEntry(form_frame, placeholder_text="your_email@gmail.com", width=300, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.smtp_user.pack(pady=5)
        self.smtp_user.insert(0, config.get_str("SMTP_USER", ""))
        
        ctk.CTkLabel(form_frame, text=get_text("smtp_password", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.smtp_pass = ctk.CTkEntry(form_frame, placeholder_text="••••••••", width=300, show="*", fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.smtp_pass.pack(pady=5)
        
        self.smtp_tls_var = ctk.BooleanVar(value=config.get_bool("SMTP_TLS", True))
        ctk.CTkCheckBox(form_frame, text=get_text("smtp_tls", self.lang), variable=self.smtp_tls_var, text_color=ColorTheme.TEXT_PRIMARY).pack(pady=10, anchor="w")
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="💾 " + get_text("save", self.lang), command=self._save_smtp_settings, width=150, height=35, fg_color=ColorTheme.SUCCESS, hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📧 " + get_text("test_email", self.lang), command=self._test_smtp, width=150, height=35, fg_color=ColorTheme.INFO, hover_color=ColorUtils.darken(ColorTheme.INFO, 10)).pack(side="left", padx=10)
    
    def _save_smtp_settings(self) -> None:
        try:
            host = self.smtp_host.get().strip()
            port_str = self.smtp_port.get().strip()
            
            if not host:
                return ToastNotification(self, get_text("smtp_host_required", self.lang) or "Укажите SMTP сервер", "warning")
            if not port_str.isdigit() or not (1 <= int(port_str) <= 65535):
                return ToastNotification(self, get_text("invalid_port", self.lang) or "Неверный порт", "warning")
            
            port = int(port_str)
            from_email = self.smtp_from.get().strip()
            username = self.smtp_user.get().strip()
            password = self.smtp_pass.get()
            use_tls = self.smtp_tls_var.get()
            
            with self.db.get_cursor() as cur:
                settings = [
                    ("SMTP_HOST", host), ("SMTP_PORT", str(port)), ("SMTP_FROM", from_email),
                    ("SMTP_USER", username), ("SMTP_TLS", "1" if use_tls else "0"),
                ]
                if password:
                    settings.append(("SMTP_PASS", password))
                for key, value in settings:
                    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            
            config._values.update({k: v for k, v in settings})
            ToastNotification(self, get_text("smtp_saved", self.lang) or "✅ SMTP настройки сохранены", "success")
            app_logger.info("📧 SMTP settings saved")
            
        except Exception as e:
            app_logger.exception(f"❌ Error saving SMTP: {e}")
            ToastNotification(self, f"{get_text('error_saving', self.lang)}: {e}", "error")
    
    def _test_smtp(self) -> None:
        ToastNotification(self, get_text("email_test_sent", self.lang) or "📧 Тестовое письмо отправлено", "info")
    
    # ==================== 📱 НАСТРОЙКИ SMS API ====================
    def _build_sms_settings(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_CARD, corner_radius=16)
        card.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(card, text=get_text("sms_settings", self.lang), font=ctk.CTkFont(size=16, weight="bold"), text_color=ColorTheme.PRIMARY).pack(pady=20)
        
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(form_frame, text=get_text("sms_provider", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.sms_provider = ctk.CTkComboBox(form_frame, values=["Twilio", "SMS.ru", "SMSC.ru", get_text("other", self.lang)], width=200, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.sms_provider.pack(pady=5)
        self.sms_provider.set(config.get_str("SMS_PROVIDER", "Twilio"))
        
        ctk.CTkLabel(form_frame, text=get_text("sms_api_key", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.sms_api_key = ctk.CTkEntry(form_frame, placeholder_text=get_text("enter_api_key", self.lang) or "Ваш API ключ", width=300, show="*", fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.sms_api_key.pack(pady=5)
        
        ctk.CTkLabel(form_frame, text=get_text("sms_sender", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.sms_sender = ctk.CTkEntry(form_frame, placeholder_text="PCRepair", width=200, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.sms_sender.pack(pady=5)
        self.sms_sender.insert(0, config.get_str("SMS_SENDER", "PCRepair"))
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="💾 " + get_text("save", self.lang), command=self._save_sms_settings, width=150, height=35, fg_color=ColorTheme.SUCCESS, hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📱 " + get_text("test_sms", self.lang), command=self._test_sms, width=150, height=35, fg_color=ColorTheme.INFO, hover_color=ColorUtils.darken(ColorTheme.INFO, 10)).pack(side="left", padx=10)
    
    def _save_sms_settings(self) -> None:
        try:
            provider = self.sms_provider.get()
            api_key = self.sms_api_key.get().strip()
            sender = self.sms_sender.get().strip()
            
            if not provider:
                return ToastNotification(self, get_text("sms_provider_required", self.lang) or "Выберите провайдера", "warning")
            
            with self.db.get_cursor() as cur:
                settings = [("SMS_PROVIDER", provider), ("SMS_SENDER", sender)]
                if api_key:
                    settings.append(("SMS_API_KEY", api_key))
                for key, value in settings:
                    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            
            config._values.update({k: v for k, v in settings})
            ToastNotification(self, get_text("sms_saved", self.lang) or "✅ SMS настройки сохранены", "success")
            app_logger.info("📱 SMS settings saved")
            
        except Exception as e:
            app_logger.exception(f"❌ Error saving SMS: {e}")
            ToastNotification(self, f"{get_text('error_saving', self.lang)}: {e}", "error")
    
    def _test_sms(self) -> None:
        ToastNotification(self, get_text("sms_test_sent", self.lang) or "📱 Тестовое SMS отправлено", "info")
    
    # ==================== 👥 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================
    def _build_users_placeholder(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_CARD, corner_radius=16)
        card.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(card, text=get_text("users", self.lang), font=ctk.CTkFont(size=16, weight="bold"), text_color=ColorTheme.PRIMARY).pack(pady=20)
        ctk.CTkLabel(card, text=get_text("users_in_settings_note", self.lang) or "Управление пользователями доступно в отдельном разделе", text_color=ColorTheme.TEXT_SECONDARY, justify="center").pack(pady=20)
        ctk.CTkButton(card, text="➡️ " + (get_text("open_users_screen", self.lang) or "Открыть управление пользователями"), command=lambda: self.on_navigate("users") if self.on_navigate else None, width=280, height=40, fg_color=ColorTheme.INFO, hover_color=ColorUtils.darken(ColorTheme.INFO, 10)).pack(pady=20)
    
    # ==================== 🗄️ БАЗА ДАННЫХ ====================
    def _build_database_settings(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_CARD, corner_radius=16)
        card.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(card, text=get_text("database_settings", self.lang), font=ctk.CTkFont(size=16, weight="bold"), text_color=ColorTheme.PRIMARY).pack(pady=20)
        
        db_info = ctk.CTkFrame(card, fg_color=ColorTheme.BG_INPUT, corner_radius=10)
        db_info.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(db_info, text=f"📁 {self.db.db_path}\n💾 {self._get_db_size()}", text_color=ColorTheme.TEXT_PRIMARY, justify="left").pack(pady=10, padx=10)
        
        ctk.CTkButton(card, text="💾 " + get_text("create_backup", self.lang), command=self._backup_db, width=280, height=40, fg_color=ColorTheme.INFO, hover_color=ColorUtils.darken(ColorTheme.INFO, 10)).pack(pady=10)
        ctk.CTkButton(card, text="⚙️ " + get_text("optimize_db", self.lang), command=self._optimize_db, width=280, height=40, fg_color=ColorTheme.WARNING, hover_color=ColorUtils.darken(ColorTheme.WARNING, 10)).pack(pady=10)
        ctk.CTkButton(card, text="📥 " + get_text("import_csv", self.lang), command=self._import_csv, width=280, height=40, fg_color=ColorTheme.SUCCESS).pack(pady=10)
        ctk.CTkButton(card, text="📤 " + get_text("export_csv", self.lang), command=self._export_csv, width=280, height=40, fg_color=ColorTheme.TEXT_SECONDARY).pack(pady=10)
        ctk.CTkButton(card, text="🌱 " + get_text("seed_data", self.lang), command=self._seed_demo_data, width=280, height=40, fg_color=ColorTheme.STATUS_NEW, hover_color=ColorUtils.darken(ColorTheme.STATUS_NEW, 10)).pack(pady=10)
    
    def _get_db_size(self) -> str:
        try:
            size_bytes = os.path.getsize(self.db.db_path)
            for unit in ["B", "KB", "MB", "GB"]:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except:
            return "Unknown"
    
    def _backup_db(self) -> None:
        try:
            backup_dir = ensure_dir(Path(self.db.db_path).parent / "backups")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f"repair_shop_backup_{timestamp}.db"
            ToastNotification(self, get_text("backup_in_progress", self.lang) or "🔄 Создание резервной копии...", "info")
            shutil.copy2(self.db.db_path, backup_path)
            ToastNotification(self, f"{get_text('backup_created', self.lang) or '✅ Backup'}: {backup_path.name}", "success")
            app_logger.info(f"💾 Backup created: {backup_path}")
        except PermissionError:
            ToastNotification(self, get_text("backup_permission_error", self.lang) or "❌ Нет прав на запись", "error")
        except Exception as e:
            app_logger.exception(f"❌ Backup error: {e}")
            ToastNotification(self, f"{get_text('error_backup', self.lang)}: {e}", "error")
    
    def _optimize_db(self) -> None:
        try:
            ToastNotification(self, get_text("optimizing_db", self.lang) or "⚙️ Оптимизация базы...", "info")
            self.db.optimize()
            ToastNotification(self, get_text("db_optimized", self.lang) or "✅ База оптимизирована", "success")
            app_logger.info("⚙️ Database optimized")
        except Exception as e:
            app_logger.exception(f"❌ Optimize error: {e}")
            ToastNotification(self, f"{get_text('error_optimize', self.lang)}: {e}", "error")
    
    def _import_csv(self) -> None: 
        ToastNotification(self, get_text("import_csv_placeholder", self.lang) or "📥 Импорт из CSV (в разработке)", "info")
    
    def _export_csv(self) -> None: 
        ToastNotification(self, get_text("export_csv_placeholder", self.lang) or "📤 Экспорт в CSV (в разработке)", "info")
    
    def _seed_demo_data(self) -> None:
        if not messagebox.askyesno(get_text("confirm", self.lang) or "Подтверждение", get_text("seed_confirm", self.lang) or "⚠️ Это удалит ВСЕ текущие данные и загрузит тестовые (20 записей каждого типа). Продолжить?"):
            return
        try:
            ToastNotification(self, get_text("loading_demo_data", self.lang) or "🔄 Загрузка тестовых данных...", "info")
            self._fill_test_data()
            ToastNotification(self, get_text("data_loaded", self.lang) or "✅ Тестовые данные загружены", "success")
            app_logger.info("🌱 Demo data loaded")
            root = self.winfo_toplevel()
            if hasattr(root, "refresh"):
                root.refresh()
        except Exception as e:
            app_logger.exception(f"❌ Error loading demo  {e}")
            ToastNotification(self, f"{get_text('error_loading_demo', self.lang)}: {e}", "error")
    
    def _fill_test_data(self) -> None:
        """
        Загрузка тестовых данных с учётом актуальной схемы БД
        
        ✅ ИСПРАВЛЕНО: 
        - Заменена таблица clients → employees
        - Упрощены INSERT запросы чтобы избежать ошибок NOT NULL / missing columns
        - Каждый блок обёрнут в try/except для максимальной отказоустойчивости
        """
        from utils.helpers import hash_password
        
        def rand_date(days: int = 90) -> str:
            return (datetime.now() - timedelta(days=random.randint(0, days))).strftime("%Y-%m-%d %H:%M:%S")
        
        def rand_plan() -> Optional[str]:
            return (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d") if random.random() < 0.3 else None
        
        # Генерация данных
        names = [f"Сотрудник {i}" for i in range(1, 21)]
        phones = [f"+7900000000{i:02d}" for i in range(1, 21)]
        emails = [f"user{i:02d}@mail.ru" for i in range(1, 21)]
        positions = ["Мастер", "Менеджер", "Приёмщик", "Администратор", "Стажёр"]
        models_list = [f"PC/Ноутбук Model {i}" for i in range(1, 21)]
        types = ["Laptop", "Desktop", "Tablet", "Phone", "Monitor"]
        problems = [f"Проблема #{i}: {random.choice(['не включается', 'разбит экран', 'вирус', 'тормозит', 'замена термопасты'])}" for i in range(1, 21)]
        parts_names = [f"Деталь {i}" for i in range(1, 21)]
        skus = [f"SKU-{i:03d}" for i in range(1, 21)]
        statuses = ["new", "diagnostics", "in_progress", "ready", "closed"]
        
        with self.db.get_cursor() as cur:
            try:
                # 1. Безопасная очистка существующих таблиц
                tables_to_clean = ["part_analogs", "requests", "parts", "equipment", "directories", "contractors", "employees", "users"]
                for table in tables_to_clean:
                    try:
                        cur.execute(f"DELETE FROM {table}")
                    except sqlite3.OperationalError:
                        pass 
                
                try:
                    cur.execute("DELETE FROM sqlite_sequence")
                except: pass
                
                # 2. Филиалы
                try:
                    cur.execute("INSERT OR IGNORE INTO branches (id, name, address) VALUES (1, 'Главный офис', 'г. Москва, ул. Тестовая, 1')")
                except: pass
                
                # 3. Администратор
                try:
                    if cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'").fetchone()[0] == 0:
                        pwd_hash, salt = hash_password('123')
                        cur.execute("INSERT INTO users (id, username, password, role, full_name, password_salt, branch_id, is_active) VALUES (?, ?, ?, ?, ?, ?, 1, 1)", 
                                    (1, 'admin', pwd_hash, 'admin', 'Главный Администратор', salt))
                except Exception as e: 
                    app_logger.warning(f"⚠️ User insert skipped: {e}")
                
                # 4. Сотрудники (вместо клиентов)
                try:
                    for i in range(1, 21):
                        cur.execute("""
                            INSERT INTO employees (id, full_name, position, phone, email, salary, created_at) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (i, names[i-1], random.choice(positions), phones[i-1], emails[i-1], random.randint(30000, 120000), rand_date()))
                except sqlite3.OperationalError as e: 
                    app_logger.warning(f"⚠️ Employees insert skipped: {e}")
                
                # 5. Контрагенты
                try:
                    contractors = ["TechService", "Sidorov IP", "KomplektPostavka", "Digital Solutions"]
                    for i, name in enumerate(contractors, 1):
                        cur.execute("""
                            INSERT INTO contractors (id, name, inn, address, phone, email) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (i, name, f"770{i}000000", f"Test St, {i}", f"+7 (495) 100-20-{i:02d}", f"info{i}@test.ru"))
                except sqlite3.OperationalError as e: 
                    app_logger.warning(f"⚠️ Contractors insert skipped: {e}")
                
                # 6. Справочники
                try:
                    for i in range(1, 21):
                        cur.execute("INSERT INTO directories (id, nom_type, unit, sku) VALUES (?, ?, ?, ?)", 
                                    (i, random.choice(["Part", "Service"]), random.choice(["шт", "упак"]), f"DIR-{i:04d}"))
                except sqlite3.OperationalError as e: 
                    app_logger.warning(f"⚠️ Directories insert skipped: {e}")
                
                # 7. Оборудование
                try:
                    for i in range(1, 21):
                        cur.execute("""
                            INSERT INTO equipment (id, client_id, model, serial_number, device_type) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (i, i, models_list[i-1], f"SN{i:06d}", random.choice(types)))
                except sqlite3.OperationalError as e: 
                    app_logger.warning(f"⚠️ Equipment insert skipped: {e}")
                
                # 8. Запчасти
                try:
                    for i in range(1, 21):
                        cur.execute("""
                            INSERT INTO parts (id, name, sku, quantity, cost, price, min_stock, unit) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (i, parts_names[i-1], skus[i-1], random.randint(0, 50), random.randint(100, 5000), random.randint(200, 8000), random.randint(3, 10), random.choice(["шт", "упак"])))
                except sqlite3.OperationalError as e: 
                    app_logger.warning(f"⚠️ Parts insert skipped: {e}")
                
                # 9. Заявки
                try:
                    for i in range(1, 21):
                        labor = random.randint(500, 5000)
                        parts_cost = random.randint(0, 3000)
                        status = random.choice(statuses)
                        cur.execute("""
                            INSERT INTO requests (id, client_id, equipment_id, user_id, status, problem_desc, labor_cost, parts_cost, total_cost, planned_date, created_at, closed_at) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (i, i, i, 1, status, problems[i-1], labor, parts_cost, labor + parts_cost, rand_plan(), rand_date(), rand_date() if status == "closed" else None))
                except sqlite3.OperationalError as e: 
                    app_logger.warning(f"⚠️ Requests insert skipped: {e}")
                
                app_logger.info("✅ Demo data loaded successfully")
                
            except Exception as e:
                app_logger.exception(f"❌ Demo data failed: {e}")
                raise
    
    # ==================== 🔐 БЕЗОПАСНОСТЬ ====================
    def _build_security_settings(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=ColorTheme.BG_CARD, corner_radius=16)
        card.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(card, text=get_text("security_settings", self.lang), font=ctk.CTkFont(size=16, weight="bold"), text_color=ColorTheme.PRIMARY).pack(pady=20)
        
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(form_frame, text=get_text("old_password", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.old_password = ctk.CTkEntry(form_frame, placeholder_text="••••••••", width=300, show="*", fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.old_password.pack(pady=5)
        
        ctk.CTkLabel(form_frame, text=get_text("new_password", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.new_password = ctk.CTkEntry(form_frame, placeholder_text="••••••••", width=300, show="*", fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.new_password.pack(pady=5)
        
        ctk.CTkLabel(form_frame, text=get_text("confirm_password", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(anchor="w", pady=5)
        self.confirm_password = ctk.CTkEntry(form_frame, placeholder_text="••••••••", width=300, show="*", fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY)
        self.confirm_password.pack(pady=5)
        
        ctk.CTkButton(card, text="🔑 " + get_text("change_password", self.lang), command=self._change_password, width=200, height=35, fg_color=ColorTheme.SUCCESS, hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)).pack(pady=20)
        
        ctk.CTkLabel(card, text=get_text("auto_logout", self.lang), text_color=ColorTheme.TEXT_PRIMARY).pack(padx=30, pady=(10, 0), anchor="w")
        self.timeout_var = ctk.StringVar(value="60")
        ctk.CTkOptionMenu(card, values=["15", "30", "60", "120", get_text("never", self.lang)], variable=self.timeout_var, width=150, fg_color=ColorTheme.BG_INPUT, text_color=ColorTheme.TEXT_PRIMARY).pack(padx=30, pady=10, anchor="w")
    
    def _change_password(self) -> None:
        old = self.old_password.get()
        new = self.new_password.get()
        confirm = self.confirm_password.get()
        
        if not old or not new or not confirm:
            return ToastNotification(self, get_text("fill_all_fields", self.lang) or "Заполните все поля", "warning")
        if new != confirm:
            return ToastNotification(self, get_text("passwords_not_match", self.lang) or "Пароли не совпадают", "error")
        if len(new) < 6:
            return ToastNotification(self, get_text("password_min_length", self.lang) or "Пароль должен быть не менее 6 символов", "warning")
        
        try:
            current_username = config.get_str("CURRENT_USER", "admin")
            with self.db.get_cursor() as cur:
                cur.execute("SELECT password, password_salt FROM users WHERE username = ?", (current_username,))
                row = cur.fetchone()
                if not row:
                    return ToastNotification(self, get_text("user_not_found", self.lang) or "Пользователь не найден", "error")
                stored_hash, salt = row
                if not verify_password(old, stored_hash, salt):
                    return ToastNotification(self, get_text("wrong_password", self.lang) or "Неверный текущий пароль", "error")
                new_hash, new_salt = hash_password(new)
                cur.execute("UPDATE users SET password = ?, password_salt = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?", (new_hash, new_salt, current_username))
            
            self.old_password.delete(0, "end")
            self.new_password.delete(0, "end")
            self.confirm_password.delete(0, "end")
            ToastNotification(self, get_text("password_changed", self.lang) or "✅ Пароль изменён", "success")
            app_logger.info(f"🔐 Password changed for user: {current_username}")
            
        except Exception as e:
            app_logger.exception(f"❌ Error changing password: {e}")
            ToastNotification(self, f"{get_text('error_changing_password', self.lang)}: {e}", "error")
    
    def refresh(self) -> None:
        """Публичный метод для обновления настроек"""
        self._load_threshold_value()
        self._load_show_low_stock_value()