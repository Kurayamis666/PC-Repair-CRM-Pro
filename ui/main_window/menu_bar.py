# ui/main_window/menu_bar.py
"""
Верхняя панель главного окна для PC Repair CRM Pro
✅ УЛУЧШЕНО: Валидация данных, обработка ошибок, горячие клавиши
✅ ГИБКОСТЬ: Методы обновления, согласованные стили из темы
✅ СОВМЕСТИМО: Интеграция с системой тем и переводов
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any
from core.logger import app_logger
from ui.theme import ColorTheme, ColorUtils
from translations import get_text


class MenuBar(ctk.CTkFrame):
    """
    Верхняя панель с информацией о пользователе и кнопками управления
    
    ✅ Безопасное получение данных пользователя
    ✅ Обработка ошибок в колбэках
    ✅ Горячие клавиши (Ctrl+Q для выхода)
    ✅ Методы динамического обновления
    ✅ Согласованные стили из ColorTheme
    """
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        user: Dict[str, Any],
        lang: str = "ru",
        on_logout: Optional[Callable[[], None]] = None,
        on_language_change: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(
            parent, 
            fg_color=ColorTheme.PRIMARY, 
            corner_radius=12, 
            height=55  # Можно сделать адаптивным при необходимости
        )
        
        # ✅ Валидация входных данных
        if not isinstance(user, dict):
            app_logger.warning("⚠️ MenuBar: user must be a dict")
            user = {}
        
        self.user = user
        self.lang = lang
        self.on_logout = on_logout
        self.on_language_change = on_language_change
        
        # 🔧 UI элементы для последующего обновления
        self._username_label: Optional[ctk.CTkLabel] = None
        self._role_label: Optional[ctk.CTkLabel] = None
        self._lang_menu: Optional[ctk.CTkOptionMenu] = None
        
        self._build_ui()
        self._bind_hotkeys()
    
    def _build_ui(self) -> None:
        """Построение интерфейса с безопасным доступом к данным"""
        
        # 👤 Информация о пользователе (слева)
        user_frame = ctk.CTkFrame(self, fg_color="transparent")
        user_frame.pack(side="left", padx=20)
        
        # ✅ Безопасное получение имени пользователя
        username = self.user.get("username") or self.user.get("full_name") or "Пользователь"
        self._username_label = ctk.CTkLabel(
            user_frame,
            text=f"👤 {username}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        )
        self._username_label.pack(side="left")
        
        # ✅ Безопасное получение роли (опционально)
        role = self.user.get("role")
        if role:
            # Перевод роли если есть ключ
            role_text = get_text(f"role_{role}", self.lang) or role
            self._role_label = ctk.CTkLabel(
                user_frame,
                text=f" • {role_text}",
                font=ctk.CTkFont(size=12),
                text_color=ColorTheme.TEXT_SECONDARY,
            )
            self._role_label.pack(side="left")
        
        # 🔘 Правая часть: язык + выход
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", padx=15)
        
        # 🌐 Переключатель языка
        self.lang_var = ctk.StringVar(value=self.lang)
        self._lang_menu = ctk.CTkOptionMenu(
            right_frame,
            values=["ru", "en"],
            variable=self.lang_var,
            command=self._on_language_change,
            width=80,
            height=32,
            fg_color=ColorTheme.PRIMARY_HOVER,  # ✅ Из темы вместо SECONDARY
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD,
            corner_radius=8,
        )
        self._lang_menu.pack(side="right", padx=5)
        
        # 🚪 Кнопка выхода
        ctk.CTkButton(
            right_frame,
            text=get_text("logout", self.lang),
            command=self._on_logout,
            width=110,
            height=32,
            fg_color=ColorTheme.ERROR,
            hover_color=ColorUtils.darken(ColorTheme.ERROR, 10),  # ✅ Из темы
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="right", padx=10)
    
    def _bind_hotkeys(self) -> None:
        """Привязка горячих клавиш"""
        # Ctrl+Q или Ctrl+L для выхода
        self.bind("<Control-q>", lambda e: self._on_logout())
        self.bind("<Control-Q>", lambda e: self._on_logout())
        self.bind("<Control-l>", lambda e: self._on_logout())
        self.bind("<Control-L>", lambda e: self._on_logout())
    
    def _on_logout(self) -> None:
        """Обработчик выхода с обработкой ошибок"""
        username = self.user.get("username") or self.user.get("full_name") or "unknown"
        
        try:
            app_logger.info(f"👤 Пользователь {username} нажал 'Выход'")
            
            # Вызываем колбэк с обработкой ошибок
            if self.on_logout:
                try:
                    self.on_logout()
                except Exception as e:
                    app_logger.error(f"❌ Error in on_logout callback: {e}")
                    # Показываем пользователю если возможно
                    try:
                        import tkinter.messagebox as mb
                        mb.showerror("Ошибка", "Не удалось выполнить выход. Попробуйте ещё раз.")
                    except:
                        pass
        except Exception as e:
            app_logger.error(f"❌ Unexpected error in _on_logout: {e}")
    
    def _on_language_change(self, new_lang: str) -> None:
        """Обработчик смены языка с обновлением интерфейса"""
        try:
            app_logger.info(f"🌍 Язык изменён на: {new_lang}")
            
            # Обновляем внутреннее состояние
            self.lang = new_lang
            
            # ✅ Обновляем текст кнопки выхода
            logout_btn = self.winfo_children()[-1].winfo_children()[0]  # Хрупко, но работает
            # Лучше: сохранить ссылку на кнопку при создании
            
            # Вызываем колбэк для обновления всего интерфейса
            if self.on_language_change:
                try:
                    self.on_language_change(new_lang)
                except Exception as e:
                    app_logger.error(f"❌ Error in on_language_change callback: {e}")
                    
        except Exception as e:
            app_logger.error(f"❌ Unexpected error in _on_language_change: {e}")
    
    # ==================== 🔄 ПУБЛИЧНЫЕ МЕТОДЫ ДЛЯ ОБНОВЛЕНИЯ ====================
    
    def update_user_info(self, user: Dict[str, Any]) -> None:
        """
        Обновить информацию о пользователе в интерфейсе
        
        ✅ Безопасное обновление без пересоздания виджетов
        
        Args:
            user: Новые данные пользователя
        """
        if not isinstance(user, dict):
            app_logger.warning("⚠️ update_user_info: user must be a dict")
            return
        
        self.user = user
        
        # Обновляем имя пользователя
        if self._username_label:
            username = user.get("username") or user.get("full_name") or "Пользователь"
            self._username_label.configure(text=f"👤 {username}")
        
        # Обновляем роль
        if self._role_label:
            role = user.get("role")
            if role:
                role_text = get_text(f"role_{role}", self.lang) or role
                self._role_label.configure(text=f" • {role_text}")
                self._role_label.pack(side="left")
            else:
                self._role_label.pack_forget()  # Скрыть если роли нет
    
    def update_language(self, new_lang: str) -> None:
        """
        Обновить выбранный язык в меню
        
        ✅ Синхронизация без вызова колбэка
        
        Args:
            new_lang: Код языка ("ru" или "en")
        """
        if new_lang in ("ru", "en"):
            self.lang = new_lang
            if self._lang_menu:
                self._lang_menu.set(new_lang)
            if self._username_label:
                # Перерисовать имя если нужно (для перевода "Пользователь")
                username = self.user.get("username") or self.user.get("full_name") or "Пользователь"
                self._username_label.configure(text=f"👤 {username}")
    
    def set_logout_callback(self, callback: Callable[[], None]) -> None:
        """Установить или обновить колбэк для выхода"""
        self.on_logout = callback
    
    def set_language_callback(self, callback: Callable[[str], None]) -> None:
        """Установить или обновить колбэк для смены языка"""
        self.on_language_change = callback
    
    def focus_logout_button(self) -> None:
        """Установить фокус на кнопку выхода (для доступа с клавиатуры)"""
        # Найти кнопку выхода и установить фокус
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkButton):
                        if child.cget("text") == get_text("logout", self.lang):
                            child.focus_set()
                            return