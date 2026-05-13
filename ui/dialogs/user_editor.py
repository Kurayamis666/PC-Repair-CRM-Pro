# ui/dialogs/user_editor.py
"""
Диалог редактирования/создания пользователя для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Хеширование паролей через utils.helpers (PBKDF2)
✅ УЛУЧШЕНО: Полный перевод, валидация, обработка ошибок
✅ СОВМЕСТИМО: Интеграция с системой тем, переводов и утилит
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Callable, Dict, Any, List
import re

from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.toast import ToastNotification
from utils.helpers import hash_password, verify_password
from utils.validators import validate_required, validate_string_length


class UserEditorDialog(ctk.CTkToplevel):
    """
    Диалог редактирования/создания пользователя с безопасным хешированием
    
    ✅ Использует hash_password() из utils.helpers (PBKDF2)
    ✅ Полный перевод всех текстов через get_text()
    ✅ Валидация логина, пароля, уникальности
    ✅ Безопасный парсинг branch_id через маппинг
    ✅ Индикатор загрузки при сохранении
    """
    
    # ⚙️ Конфигурация валидации
    MIN_USERNAME_LENGTH: int = 3
    MAX_USERNAME_LENGTH: int = 50
    MIN_PASSWORD_LENGTH: int = 8
    ALLOWED_USERNAME_CHARS: str = r"^[a-zA-Z0-9_\-.@]+$"  # Разрешённые символы
    
    # 🗂️ Роли с переводом
    ROLES: List[Dict[str, str]] = [
        {"value": "admin", "ru": "🔑 Администратор", "en": "🔑 Administrator"},
        {"value": "manager", "ru": "👔 Менеджер", "en": "👔 Manager"},
        {"value": "technician", "ru": "🔧 Техник", "en": "🔧 Technician"},
        {"value": "viewer", "ru": "👁️ Наблюдатель", "en": "👁️ Viewer"},
    ]
    
    def __init__(
        self,
        parent,
        user_id: Optional[int] = None,
        lang: str = "ru",
        on_save: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        
        self.user_id = user_id
        self.lang = lang
        self.on_save = on_save
        self.db = DatabaseConnection()
        
        # 🔧 UI элементы (для обновления)
        self._username_entry: Optional[ctk.CTkEntry] = None
        self._password_entry: Optional[ctk.CTkEntry] = None
        self._confirm_entry: Optional[ctk.CTkEntry] = None
        self._role_menu: Optional[ctk.CTkOptionMenu] = None
        self._branch_menu: Optional[ctk.CTkOptionMenu] = None
        self._save_btn: Optional[ctk.CTkButton] = None
        self._branch_mapping: Dict[str, int] = {}  # "1 - Главный" → 1
        
        # ✅ Переведённый заголовок
        title_key = "edit_user" if user_id else "new_user"
        self.title(get_text(title_key, self.lang) or ("Редактирование пользователя" if user_id else "Новый пользователь"))
        
        self.geometry("450x650")
        self.minsize(400, 600)
        self.transient(parent)
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        self._original_username: str = ""
        
        self._build_ui()
        
        # 🎯 Фокус на поле логина
        self.after(100, lambda: self._username_entry.focus_set() if self._username_entry else None)
        
        if user_id:
            self._load_user_data()
        
        # Центрирование и модальность — после построения UI
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 650) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.grab_set()
    
    def _build_ui(self) -> None:
        """Построение интерфейса с полным переводом"""
        
        # 🏷️ Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        
        title_key = "edit_user" if self.user_id else "new_user"
        title_text = get_text(title_key, self.lang) or ("✏️ Редактирование" if self.user_id else "➕ Новый пользователь")
        
        ctk.CTkLabel(
            header,
            text=title_text,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(pady=15)
        
        # 📋 Форма
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 👤 Логин
        ctk.CTkLabel(
            form, 
            text=get_text("username", self.lang) + " *",  # ✅ Переведено + обязательное поле
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(10, 5))
        
        self._username_entry = ctk.CTkEntry(
            form, 
            placeholder_text=get_text("username_placeholder", self.lang) or "admin",
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY,
            height=40,
        )
        self._username_entry.pack(fill="x", pady=5)
        self._username_entry.bind("<KeyRelease>", lambda e: self._clear_error())
        
        # 🔐 Пароль
        password_label = get_text("password", self.lang)
        if self.user_id:
            password_label += f" ({get_text('password_optional', self.lang) or 'оставьте пустым чтобы не менять'})"
        
        ctk.CTkLabel(
            form,
            text=password_label,
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(10, 5))
        
        self._password_entry = ctk.CTkEntry(
            form,
            placeholder_text=get_text("password_placeholder", self.lang) or "••••••",
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            show="*",
            height=40,
        )
        self._password_entry.pack(fill="x", pady=5)
        self._password_entry.bind("<KeyRelease>", lambda e: self._clear_error())
        
        # 🔐 Подтверждение пароля
        ctk.CTkLabel(
            form, 
            text=get_text("confirm_password", self.lang) + ":", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(10, 5))
        
        self._confirm_entry = ctk.CTkEntry(
            form,
            placeholder_text=get_text("confirm_password_placeholder", self.lang) or "••••••",
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            show="*",
            height=40,
        )
        self._confirm_entry.pack(fill="x", pady=5)
        self._confirm_entry.bind("<KeyRelease>", lambda e: self._clear_error())
        
        # 🎭 Роль (с переводом)
        ctk.CTkLabel(
            form, 
            text=get_text("role", self.lang) + ":", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(10, 5))
        
        # ✅ Создаём маппинг: отображаемое значение → значение для БД
        role_values = [role[self.lang] if self.lang in role else role["ru"] for role in self.ROLES]
        self._role_mapping = {role[self.lang] if self.lang in role else role["ru"]: role["value"] for role in self.ROLES}
        
        self._role_var = ctk.StringVar(value=self.ROLES[1][self.lang] if self.lang in self.ROLES[1] else self.ROLES[1]["ru"])  # manager по умолчанию
        self._role_menu = ctk.CTkOptionMenu(
            form,
            values=role_values,
            variable=self._role_var,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD,
            height=40,
        )
        self._role_menu.pack(fill="x", pady=5)
        
        # 🏢 Филиал (с безопасным маппингом)
        ctk.CTkLabel(
            form, 
            text=get_text("branch", self.lang) + ":", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=(10, 5))
        
        self._branch_var = ctk.StringVar(value="")
        self._branch_menu = ctk.CTkOptionMenu(
            form,
            values=[get_text("loading", self.lang) or "Загрузка..."],
            variable=self._branch_var,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD,
            height=40,
            state="disabled" if not self.user_id else "normal",  # Отключён для новых пользователей пока не загрузятся филиалы
        )
        self._branch_menu.pack(fill="x", pady=5)
        
        # Загружаем филиалы асинхронно
        self.after(10, self._load_branches)
        
        # 🔘 Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text=get_text("cancel", self.lang),
            command=self.destroy,
            width=150,
            height=35,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(side="left", padx=10)
        
        self._save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 " + get_text("save", self.lang),
            command=self._save,
            width=150,
            height=35,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
        )
        self._save_btn.pack(side="right", padx=10)
        
        # ⏳ Индикатор загрузки (скрыт по умолчанию)
        self._loading_label = ctk.CTkLabel(
            btn_frame,
            text="",
            text_color=ColorTheme.INFO,
            font=ctk.CTkFont(size=11)
        )
        self._loading_label.pack(side="right", padx=10)
    
    def _clear_error(self) -> None:
        """Очистить сообщение об ошибке при вводе"""
        # Можно добавить inline error labels в будущем
        pass
    
    def _set_loading(self, loading: bool) -> None:
        """Показать/скрыть индикатор загрузки"""
        if loading:
            if self._loading_label:
                self._loading_label.configure(text="🔄 " + (get_text("saving", self.lang) or "Сохранение..."))
            if self._save_btn:
                self._save_btn.configure(state="disabled")
            # Блокируем поля
            for entry in [self._username_entry, self._password_entry, self._confirm_entry]:
                if entry:
                    entry.configure(state="disabled")
        else:
            if self._loading_label:
                self._loading_label.configure(text="")
            if self._save_btn:
                self._save_btn.configure(state="normal")
            for entry in [self._username_entry, self._password_entry, self._confirm_entry]:
                if entry:
                    entry.configure(state="normal")
    
    def _load_branches(self) -> None:
        """Загрузить список филиалов с безопасным маппингом"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("SELECT id, name FROM branches ORDER BY name")
                branches = cur.fetchall()
                
                if branches:
                    # ✅ Создаём безопасный маппинг: "1 - Главный" → 1
                    self._branch_mapping = {}
                    display_values = []
                    
                    for b_id, b_name in branches:
                        display = f"{b_id} - {b_name}"
                        display_values.append(display)
                        self._branch_mapping[display] = b_id
                    
                    self._branch_menu.configure(values=display_values, state="normal")
                    
                    # Если редактируем — устанавливаем текущий филиал
                    if self.user_id and hasattr(self, '_current_branch_id'):
                        for display, b_id in self._branch_mapping.items():
                            if b_id == self._current_branch_id:
                                self._branch_var.set(display)
                                break
                    elif display_values:
                        self._branch_var.set(display_values[0])  # Первый по умолчанию
                else:
                    self._branch_menu.configure(values=[get_text("no_branches", self.lang) or "Нет филиалов"], state="disabled")
                    
        except Exception as e:
            app_logger.error(f"Error loading branches: {e}")
            self._branch_menu.configure(values=[get_text("error_loading", self.lang) or "Ошибка"], state="disabled")
    
    def _load_user_data(self) -> None:
        """Загрузить данные пользователя"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute(
                    "SELECT username, role, branch_id FROM users WHERE id = ?",
                    (self.user_id,),
                )
                row = cur.fetchone()
                
                if row:
                    username, role, branch_id = row
                    self._original_username = username
                    
                    # Устанавливаем логин
                    if self._username_entry:
                        self._username_entry.delete(0, "end")
                        self._username_entry.insert(0, username)
                    
                    # Устанавливаем роль
                    if self._role_menu:
                        for role_config in self.ROLES:
                            if role_config["value"] == role:
                                display = role_config[self.lang] if self.lang in role_config else role_config["ru"]
                                self._role_var.set(display)
                                break
                    
                    # Сохраняем branch_id для установки после загрузки филиалов
                    self._current_branch_id = branch_id
                    
                    # Если филиалы уже загружены — устанавливаем сразу
                    if self._branch_mapping and branch_id in self._branch_mapping.values():
                        for display, b_id in self._branch_mapping.items():
                            if b_id == branch_id:
                                self._branch_var.set(display)
                                break
                                
        except Exception as e:
            app_logger.error(f"Error loading user: {e}")
            ToastNotification(self, f"{get_text('error_loading', self.lang)}: {e}", "error")
    
    def _validate_username(self, username: str) -> tuple[bool, str]:
        """Валидация логина"""
        if not username:
            return False, get_text("username_required", self.lang) or "Логин обязателен"
        
        if len(username) < self.MIN_USERNAME_LENGTH:
            return False, get_text("username_too_short", self.lang).format(self.MIN_USERNAME_LENGTH) or f"Логин должен быть не менее {self.MIN_USERNAME_LENGTH} символов"
        
        if len(username) > self.MAX_USERNAME_LENGTH:
            return False, get_text("username_too_long", self.lang).format(self.MAX_USERNAME_LENGTH) or f"Логин не может превышать {self.MAX_USERNAME_LENGTH} символов"
        
        if not re.match(self.ALLOWED_USERNAME_CHARS, username):
            return False, get_text("username_invalid_chars", self.lang) or "Логин может содержать только буквы, цифры, _, -, ., @"
        
        # Проверка на уникальность (если создаём нового или меняем логин)
        if not self.user_id or (self._username_entry and self._username_entry.get().strip() != self._original_username):
            try:
                with self.db.get_cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
                    if cur.fetchone():
                        return False, get_text("username_exists", self.lang) or "Пользователь с таким логином уже существует"
            except Exception as e:
                app_logger.warning(f"⚠️ Could not check username uniqueness: {e}")
        
        return True, ""
    
    def _validate_password(self, password: str, is_new_user: bool) -> tuple[bool, str]:
        """Валидация пароля"""
        if is_new_user and not password:
            return False, get_text("password_required", self.lang) or "Пароль обязателен для нового пользователя"
        
        if password:  # Если пароль указан (для редактирования — опционально)
            if len(password) < self.MIN_PASSWORD_LENGTH:
                return False, get_text("password_too_short", self.lang).format(self.MIN_PASSWORD_LENGTH) or f"Пароль должен быть не менее {self.MIN_PASSWORD_LENGTH} символов"
        
        return True, ""
    
    def _save(self) -> None:
        """Сохранить пользователя с безопасным хешированием"""
        # ✅ Получаем и валидируем данные
        username = self._username_entry.get().strip() if self._username_entry else ""
        password = self._password_entry.get() if self._password_entry else ""
        confirm = self._confirm_entry.get() if self._confirm_entry else ""
        
        # ✅ Валидация логина
        valid, error = self._validate_username(username)
        if not valid:
            ToastNotification(self, error, "warning")
            if self._username_entry:
                self._username_entry.focus_set()
            return
        
        # ✅ Валидация пароля
        is_new_user = not self.user_id
        valid, error = self._validate_password(password, is_new_user)
        if not valid:
            ToastNotification(self, error, "warning")
            if self._password_entry:
                self._password_entry.focus_set()
            return
        
        # ✅ Проверка совпадения паролей (если пароль указан)
        if password and password != confirm:
            ToastNotification(self, get_text("passwords_not_match", self.lang) or "Пароли не совпадают", "error")
            if self._confirm_entry:
                self._confirm_entry.focus_set()
            return
        
        # ✅ Получение роли и филиала через безопасный маппинг
        role_display = self._role_var.get() if self._role_var else ""
        role = self._role_mapping.get(role_display, "manager")  # fallback к manager
        
        branch_display = self._branch_var.get() if self._branch_var else ""
        branch_id = self._branch_mapping.get(branch_display)
        
        if branch_id is None:
            # Если филиал не выбран или ошибка маппинга — берём первый доступный
            if self._branch_mapping:
                branch_id = next(iter(self._branch_mapping.values()))
            else:
                ToastNotification(self, get_text("branch_required", self.lang) or "Выберите филиал", "warning")
                return
        
        # ✅ Показываем индикатор загрузки
        self._set_loading(True)
        
        try:
            if self.user_id:
                # 🔁 Обновление существующего пользователя
                if password:
                    # ✅ ИСПОЛЬЗУЕМ hash_password() из utils.helpers (PBKDF2)
                    password_hash, salt = hash_password(password)
                    with self.db.get_cursor() as cur:
                        cur.execute(
                            """UPDATE users SET username=?, password=?, password_salt=?, role=?, branch_id=?, updated_at=CURRENT_TIMESTAMP 
                               WHERE id=?""",
                            (username, password_hash, salt, role, branch_id, self.user_id),
                        )
                else:
                    # Пароль не меняем
                    with self.db.get_cursor() as cur:
                        cur.execute(
                            """UPDATE users SET username=?, role=?, branch_id=?, updated_at=CURRENT_TIMESTAMP 
                               WHERE id=?""",
                            (username, role, branch_id, self.user_id),
                        )
                
                ToastNotification(self, get_text("user_updated", self.lang) or "✅ Пользователь обновлён", "success")
                app_logger.info(f"👤 User updated: {username} (ID: {self.user_id})")
                
            else:
                # ➕ Создание нового пользователя
                # ✅ ИСПОЛЬЗУЕМ hash_password() из utils.helpers (PBKDF2)
                password_hash, salt = hash_password(password)
                with self.db.get_cursor() as cur:
                    cur.execute(
                        """INSERT INTO users (username, password, password_salt, role, branch_id, created_at) 
                           VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                        (username, password_hash, salt, role, branch_id),
                    )
                
                ToastNotification(self, get_text("user_created", self.lang) or "✅ Пользователь создан", "success")
                app_logger.info(f"👤 User created: {username} (ID: {cur.lastrowid})")
            
            # ✅ Вызываем колбэк обновления
            if self.on_save:
                try:
                    self.on_save()
                except Exception as e:
                    app_logger.warning(f"⚠️ on_save callback error: {e}")
            
            # ✅ Закрываем диалог
            self.destroy()
            
        except Exception as e:
            app_logger.exception(f"❌ Error saving user: {e}")
            ToastNotification(self, f"{get_text('error_saving', self.lang)}: {e}", "error")
        finally:
            # ✅ Скрываем индикатор загрузки
            self._set_loading(False)
    
    def destroy(self) -> None:
        """Корректное закрытие диалога"""
        # Отменяем любые отложенные задачи
        try:
            self.after_cancel(self._load_branches)  # type: ignore
        except:
            pass
        super().destroy()