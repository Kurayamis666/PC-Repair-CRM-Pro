# ui/login/login_window.py
"""
Окно входа для PC Repair CRM Pro

✅ ИСПРАВЛЕНО: Кастомные kwargs извлекаются ДО super().__init__()
✅ ИСПРАВЛЕНО: Окно закрывается через after() для избежания гонок событий
✅ СОВМЕСТИМО: Работа с CustomTkinter без ошибок аргументов
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any

from core.logger import app_logger
from core.config import config as app_config
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from database.connection import DatabaseConnection
from database.repositories.user_repo import UserRepository
from ui.widgets.toast import ToastNotification


class LoginWindow(ctk.CTkToplevel):
    """
    Модальное окно входа в систему
    
    ✅ Кастомные callback'и извлекаются до инициализации родителя
    ✅ Валидация ввода, обработка ошибок, логирование
    ✅ Поддержка тем и локализации
    ✅ Корректное закрытие через after() для избежания гонок событий
    """
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        on_success: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        lang: Optional[str] = None,
        **kwargs
    ):
        # ✅ Извлекаем кастомные аргументы ПЕРЕД super().__init__()
        self._on_success = on_success
        self._on_close = on_close
        self.lang = lang or (app_config.language if hasattr(app_config, 'language') else 'ru')
        
        # ✅ Только валидные аргументы передаём в родительский класс
        valid_kwargs = {k: v for k, v in kwargs.items() 
                       if k not in ('on_success', 'on_close', 'lang')}
        
        # ✅ Инициализация родительского класса с ТОЛЬКО валидными аргументами
        super().__init__(parent, **valid_kwargs)
        
        # 🎨 Настройка окна
        self.title(get_text("login", self.lang) or "Вход в систему")
        self.geometry("400x500")
        self.minsize(350, 450)
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        # 🔐 Репозиторий пользователей
        self.db = DatabaseConnection()
        self.user_repo = UserRepository(self.db)
        
        # 🧱 Построение интерфейса
        self._build_ui()
        
        # 🎯 Центрирование относительно родителя
        self._center_relative_to(parent)
        
        # 🔐 Обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        app_logger.debug("🔐 LoginWindow initialized")
    
    def _build_ui(self) -> None:
        """Построение интерфейса окна входа"""
        # Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, 
            text=get_text("login", self.lang),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=20)
        
        # Форма входа
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Поле логина
        ctk.CTkLabel(
            form_frame, 
            text=get_text("username", self.lang),
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=get_text("enter_username", self.lang),
            height=40
        )
        self.username_entry.pack(fill="x", pady=5)
        self.username_entry.bind("<Return>", lambda e: self._login())
        
        # Поле пароля
        ctk.CTkLabel(
            form_frame, 
            text=get_text("password", self.lang),
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=get_text("enter_password", self.lang),
            show="*",
            height=40
        )
        self.password_entry.pack(fill="x", pady=5)
        self.password_entry.bind("<Return>", lambda e: self._login())
        
        # Кнопка входа
        login_btn = ctk.CTkButton(
            form_frame,
            text=get_text("login", self.lang),
            command=self._login,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10)
        )
        login_btn.pack(fill="x", pady=30)
        
        # Ссылка на смену языка
        lang_btn = ctk.CTkButton(
            self,
            text=f"🌍 {self.lang.upper()}",
            command=self._toggle_language,
            width=80,
            height=30,
            fg_color="transparent",
            border_width=1,
            border_color=ColorTheme.BORDER,
            text_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorTheme.BG_HOVER
        )
        lang_btn.pack(side="bottom", pady=10)
        
        # Фокус на поле логина
        self.after(100, lambda: self.username_entry.focus_set())
    
    def _center_relative_to(self, parent: ctk.CTkBaseClass) -> None:
        """Центрировать окно относительно родителя"""
        self.update_idletasks()
        
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        self_w = self.winfo_width()
        self_h = self.winfo_height()
        
        x = parent_x + (parent_w - self_w) // 2
        y = parent_y + (parent_h - self_h) // 2
        
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
    
    def _toggle_language(self) -> None:
        """Переключение языка интерфейса с перестроением UI"""
        new_lang = "en" if self.lang == "ru" else "ru"
        self.lang = new_lang
        self.title(get_text("login", self.lang))
        app_logger.info(f"🌍 Language toggled to: {self.lang}")
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
    
    def _login(self) -> None:
        """Обработка входа в систему"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            ToastNotification(
                self, 
                get_text("fill_all_fields", self.lang) or "Заполните все поля",
                "warning"
            )
            return
        
        app_logger.debug(f"🔐 Login attempt: {username}")
        
        try:
            user = self.user_repo.authenticate(username, password)
            
            if user:
                app_logger.info(f"✅ User {username} authenticated")
                
                # Вызываем callback успеха
                if self._on_success:
                    try:
                        self._on_success({
                            "id": user.id,
                            "username": user.username,
                            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                            "lang": self.lang
                        })
                    except Exception as cb_error:
                        app_logger.error(f"❌ Error in on_success callback: {cb_error}")
                
                # ✅ ИСПРАВЛЕНО: Закрываем окно через after() для избежания гонок событий
                # Это даёт Tkinter время обработать callback перед уничтожением окна
                self.after(10, self.destroy)
                
            else:
                app_logger.warning(f"⚠️ Failed login attempt for: {username}")
                ToastNotification(
                    self,
                    get_text("invalid_credentials", self.lang) or "Неверный логин или пароль",
                    "error"
                )
                self.password_entry.delete(0, 'end')
                self.password_entry.focus_set()
                
        except Exception as e:
            app_logger.exception(f"❌ Login error: {e}")
            ToastNotification(
                self,
                f"{get_text('error', self.lang)}: {e}",
                "error"
            )
    
    def _on_window_close(self) -> None:
        """Обработчик закрытия окна (крестик)"""
        app_logger.debug("🔐 LoginWindow closed via X button")
        
        if self._on_close:
            try:
                self._on_close()
            except Exception as e:
                app_logger.error(f"❌ Error in on_close callback: {e}")
        
        # ✅ Защита: проверяем существование окна перед уничтожением
        try:
            if self.winfo_exists():
                self.destroy()
        except Exception:
            pass
    
    def focus_login_field(self) -> None:
        """Установить фокус на поле логина"""
        if hasattr(self, 'username_entry') and self.username_entry.winfo_exists():
            self.username_entry.focus_set()