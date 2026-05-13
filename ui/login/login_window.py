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
        self.geometry("440x560")
        self.minsize(400, 520)
        self.configure(fg_color=ColorTheme.BG_DARK)
        
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
        # Верхняя декоративная полоска
        top_accent = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, height=4, corner_radius=0)
        top_accent.pack(fill="x")
        
        # Лого и заголовок в красивой карточке
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        
        # Иконка в круглом бейдже
        icon_badge = ctk.CTkFrame(header, fg_color=ColorTheme.PRIMARY_HOVER, width=64, height=64, corner_radius=32)
        icon_badge.pack(pady=(24, 8))
        icon_badge.pack_propagate(False)
        ctk.CTkLabel(
            icon_badge,
            text="🛠️",
            font=ctk.CTkFont(size=28)
        ).pack(expand=True)
        
        ctk.CTkLabel(
            header,
            text="PC Repair CRM Pro",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=(0, 2))
        ctk.CTkLabel(
            header,
            text=get_text("login", self.lang),
            font=ctk.CTkFont(size=12),
            text_color=ColorTheme.TEXT_SECONDARY
        ).pack(pady=(0, 20))
        
        # Форма входа в карточке
        form_card = ctk.CTkFrame(self, fg_color=ColorTheme.BG_CARD, corner_radius=16, border_width=1, border_color=ColorTheme.BORDER)
        form_card.pack(fill="both", expand=True, padx=28, pady=(20, 12))
        
        form_inner = ctk.CTkFrame(form_card, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Поле логина с иконкой
        ctk.CTkLabel(
            form_inner, 
            text="👤  " + get_text("username", self.lang),
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(fill="x", pady=(8, 6))
        self.username_entry = ctk.CTkEntry(
            form_inner,
            placeholder_text=get_text("enter_username", self.lang),
            height=44,
            corner_radius=12,
            border_width=2,
            border_color=ColorTheme.BORDER,
            fg_color=ColorTheme.BG_INPUT,
            font=ctk.CTkFont(size=14)
        )
        self.username_entry.pack(fill="x", pady=(0, 4))
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.username_entry.bind("<FocusIn>", lambda e: self.username_entry.configure(border_color=ColorTheme.PRIMARY))
        self.username_entry.bind("<FocusOut>", lambda e: self.username_entry.configure(border_color=ColorTheme.BORDER))
        
        # Поле пароля с иконкой
        ctk.CTkLabel(
            form_inner, 
            text="🔒  " + get_text("password", self.lang),
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(fill="x", pady=(12, 6))
        self.password_entry = ctk.CTkEntry(
            form_inner,
            placeholder_text=get_text("enter_password", self.lang),
            show="●",
            height=44,
            corner_radius=12,
            border_width=2,
            border_color=ColorTheme.BORDER,
            fg_color=ColorTheme.BG_INPUT,
            font=ctk.CTkFont(size=14)
        )
        self.password_entry.pack(fill="x", pady=(0, 4))
        self.password_entry.bind("<Return>", lambda e: self._login())
        self.password_entry.bind("<FocusIn>", lambda e: self.password_entry.configure(border_color=ColorTheme.PRIMARY))
        self.password_entry.bind("<FocusOut>", lambda e: self.password_entry.configure(border_color=ColorTheme.BORDER))
        
        # Кнопка входа — крупная, с анимацией
        login_btn = ctk.CTkButton(
            form_inner,
            text="→  " + (get_text("login", self.lang) or "Войти"),
            command=self._login,
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ColorTheme.PRIMARY,
            hover_color=ColorTheme.PRIMARY_HOVER,
            corner_radius=12
        )
        login_btn.pack(fill="x", pady=(20, 0))
        
        # Нижняя панель — язык
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=28, pady=(0, 12))
        
        lang_btn = ctk.CTkButton(
            bottom_frame,
            text=f"🌐  {self.lang.upper()}",
            command=self._toggle_language,
            width=90,
            height=32,
            fg_color=ColorTheme.BG_CARD,
            border_width=1,
            border_color=ColorTheme.BORDER,
            text_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorTheme.BG_HOVER,
            corner_radius=10,
            font=ctk.CTkFont(size=12)
        )
        lang_btn.pack(pady=4)
        
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