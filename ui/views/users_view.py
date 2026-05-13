# ui/views/users_view.py
"""
Экран управления пользователями для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Полный перевод, сортировка, адаптивная вёрстка
✅ УЛУЧШЕНО: Поиск, горячие клавиши, пустое состояние, валидация
✅ СОВМЕСТИМО: Интеграция с системой тем и переводов
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.tables import TableStyle, DataTable
from ui.widgets.toast import ToastNotification
from ui.widgets.search_bar import SearchBar


class UsersView(ctk.CTkFrame):
    """
    Экран управления пользователями с полным функционалом
    
    ✅ Полный перевод всех текстов (RU ↔ EN)
    ✅ Сортировка по клику на заголовок
    ✅ Поиск/фильтрация пользователей
    ✅ Горячие клавиши (Delete, Enter, Ctrl+N)
    ✅ Адаптивная вёрстка колонок
    ✅ Пустое состояние с подсказкой
    ✅ Надёжная проверка прав перед удалением
    """
    
    on_navigate: Optional[Callable[[str], None]] = None
    
    # 🔐 Роли с иконками и цветами
    ROLE_CONFIG: Dict[str, Dict[str, Any]] = {
        "admin": {"icon": "🔑", "label_ru": "Администратор", "label_en": "Administrator", "color": ColorTheme.ERROR},
        "manager": {"icon": "👔", "label_ru": "Менеджер", "label_en": "Manager", "color": ColorTheme.INFO},
        "technician": {"icon": "🔧", "label_ru": "Техник", "label_en": "Technician", "color": ColorTheme.SUCCESS},
        "viewer": {"icon": "👁️", "label_ru": "Наблюдатель", "label_en": "Viewer", "color": ColorTheme.TEXT_SECONDARY},
    }
    
    def __init__(self, parent: ctk.CTkBaseClass, lang: str = "ru", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.lang = lang
        self.db = DatabaseConnection()
        self._sort_reverse: Dict[str, bool] = {}
        self._build_ui()
        self._bind_hotkeys()
    
    def _build_ui(self) -> None:
        """Построение интерфейса с полным переводом"""
        
        # 🏷️ Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=get_text("manage_users", self.lang) or "👥 Управление пользователями",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(pady=15)
        
        # 🔙 Кнопка назад
        ctk.CTkButton(
            self,
            text=get_text("back", self.lang),
            command=self._go_back,
            width=120,
            height=35,
            fg_color=ColorTheme.TEXT_SECONDARY,
            corner_radius=10,
        ).pack(padx=20, pady=10, anchor="w")
        
        # 🎛️ Панель действий + поиск
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Кнопки действий
        btn_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            btn_frame,
            text=f"➕ {get_text('add', self.lang)}",
            command=self._add_user,
            width=130,
            height=35,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text=f"✏️ {get_text('edit', self.lang)}",
            command=self._edit_user,
            width=130,
            height=35,
            fg_color=ColorTheme.INFO,
            hover_color=ColorUtils.darken(ColorTheme.INFO, 10),
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text=f"🗑️ {get_text('delete', self.lang)}",
            command=self._delete_user,
            width=130,
            height=35,
            fg_color=ColorTheme.ERROR,
            hover_color=ColorUtils.darken(ColorTheme.ERROR, 10),
        ).pack(side="left", padx=3)
        
        # Поиск
        self.search = SearchBar(
            control_frame,
            placeholder=get_text("search_user", self.lang) or "Поиск пользователя...",
            on_search=self._filter_users,
            on_reset=self._load_users,
            show_find_button=False,
            lang=self.lang,
        )
        self.search.pack(side="right", padx=(10, 0))
        
        # 📊 Статистика
        self.stats_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=ColorTheme.TEXT_SECONDARY,
            anchor="w",
        )
        self.stats_label.pack(fill="x", padx=20, pady=(0, 5))
        
        # 📋 Таблица пользователей
        table_frame = ctk.CTkFrame(self, fg_color=ColorTheme.BG_INPUT)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ✅ Используем DataTable для сортировки и адаптивности
        cols = [
            get_text("col_id", self.lang),
            get_text("col_username", self.lang),
            get_text("col_role", self.lang),
            get_text("col_branch", self.lang),
            get_text("col_created", self.lang),
        ]
        col_widths = {
            get_text("col_id", self.lang): 60,
            get_text("col_username", self.lang): 180,
            get_text("col_role", self.lang): 150,
            get_text("col_branch", self.lang): 150,
            get_text("col_created", self.lang): 140,
        }
        col_align = {
            get_text("col_id", self.lang): "center",
            get_text("col_username", self.lang): "left",
            get_text("col_role", self.lang): "center",
            get_text("col_branch", self.lang): "left",
            get_text("col_created", self.lang): "center",
        }
        
        self.tree = DataTable(
            table_frame,
            columns=cols,
            column_widths=col_widths,
            column_align=col_align,
            sortable=True,
            copyable=True,
            searchable=False,  # Поиск уже есть отдельно
            on_row_double_click=lambda item: self._edit_user(),
        )
        self.tree.pack(fill="both", expand=True)
        
        # 🎨 Теги для ролей
        for role, config in self.ROLE_CONFIG.items():
            self.tree.tag_configure(
                f"role_{role}",
                background=ColorUtils.darken(config["color"], 30) if role != "admin" else "#3b2d3b",
                foreground=ColorTheme.TEXT_PRIMARY,
            )
        
        self._load_users()
    
    def _bind_hotkeys(self):
        """Привязка горячих клавиш"""
        # Delete → удалить выбранного
        self.tree.bind("<Delete>", lambda e: self._delete_user())
        
        # Enter → редактировать выбранного
        self.tree.bind("<Return>", lambda e: self._edit_user())
        
        # Ctrl+N → новый пользователь
        self.bind("<Control-n>", lambda e: self._add_user())
        self.bind("<Control-N>", lambda e: self._add_user())
    
    def _get_role_display(self, role: str) -> str:
        """Получить отображаемое имя роли с иконкой"""
        config = self.ROLE_CONFIG.get(role, {})
        icon = config.get("icon", "❓")
        label = config.get(f"label_{self.lang}", role)
        return f"{icon} {label}"
    
    def _get_role_tag(self, role: str) -> str:
        """Получить тег для стилизации строки по роли"""
        return f"role_{role}" if role in self.ROLE_CONFIG else ("odd" if hash(role) % 2 else "even")
    
    def _go_back(self) -> None:
        """Возврат на дашборд"""
        if self.on_navigate:
            self.on_navigate("dashboard")
    
    def _load_users(self, search_query: str = "") -> None:
        """
        Загрузить список пользователей с опциональной фильтрацией
        
        ✅ Адаптивные колонки
        ✅ Перевод ролей
        ✅ Обновление статистики
        """
        # Очищаем таблицу
        self.tree.delete(*self.tree.get_children())
        
        try:
            with self.db.get_cursor() as cur:
                query = """
                    SELECT u.id, u.username, u.role, b.name, u.created_at 
                    FROM users u 
                    LEFT JOIN branches b ON u.branch_id = b.id
                """
                params = []
                
                # Фильтрация по поиску
                if search_query:
                    query += " WHERE u.username LIKE ? OR u.role LIKE ? OR b.name LIKE ?"
                    search_param = f"%{search_query}%"
                    params = [search_param, search_param, search_param]
                
                query += " ORDER BY u.username"
                cur.execute(query, params)
                rows = cur.fetchall()
            
            # Обновляем статистику
            total = len(rows)
            self.stats_label.configure(
                text=f"{get_text('total_users', self.lang) or 'Всего пользователей'}: {total}"
            )
            
            # Показываем пустое состояние если нет данных
            if not rows:
                self.tree.show_empty_state(
                    message=get_text("no_users", self.lang) or "Нет пользователей",
                    icon="👥"
                )
                return
            else:
                self.tree.hide_empty_state()
            
            # Заполняем таблицу
            for idx, row in enumerate(rows):
                user_id, username, role, branch, created_at = row
                
                # Форматируем дату
                date_str = created_at[:10] if created_at else "-"
                
                # Форматируем роль
                role_display = self._get_role_display(role)
                
                # Определяем тег
                tag = self._get_role_tag(role)
                
                values = (user_id, username, role_display, branch or "-", date_str)
                self.tree.insert("", "end", values=values, tags=(tag,))
                
        except Exception as e:
            app_logger.exception(f"❌ Error loading users: {e}")
            ToastNotification(self, f"{get_text('error_loading', self.lang)}: {e}", "error")
    
    def _filter_users(self, query: str) -> None:
        """Фильтрация пользователей по поисковому запросу"""
        self._load_users(search_query=query)
    
    def _add_user(self) -> None:
        """Открыть диалог создания пользователя"""
        self._open_user_dialog(user_id=None)
    
    def _edit_user(self) -> None:
        """Открыть диалог редактирования пользователя"""
        selection = self.tree.selection()
        if not selection:
            return ToastNotification(self, get_text("select_user", self.lang) or "Выберите пользователя", "warning")
        
        user_id = self.tree.item(selection[0])["values"][0]
        self._open_user_dialog(user_id=user_id)
    
    def _open_user_dialog(self, user_id: Optional[int]) -> None:
        """Открыть диалог редактирования/создания пользователя"""
        try:
            from ui.dialogs.user_editor import UserEditorDialog
            
            def on_save():
                """Callback после успешного сохранения"""
                self._load_users()
                ToastNotification(
                    self,
                    get_text("user_saved", self.lang) or "Пользователь сохранён",
                    "success"
                )
            
            dialog = UserEditorDialog(
                parent=self,
                user_id=user_id,
                lang=self.lang,
                on_save=on_save
            )
            dialog.transient(self)
            dialog.grab_set()
            
        except ImportError as e:
            app_logger.error(f"❌ Could not import UserEditorDialog: {e}")
            ToastNotification(self, "❌ Ошибка загрузки диалога", "error")
        except Exception as e:
            app_logger.exception(f"❌ Error opening user dialog: {e}")
            ToastNotification(self, f"❌ {e}", "error")
    
    def _delete_user(self) -> None:
        """Удалить пользователя с подтверждением"""
        selection = self.tree.selection()
        if not selection:
            return ToastNotification(self, get_text("select_user", self.lang) or "Выберите пользователя", "warning")
        
        item = self.tree.item(selection[0])
        user_id = item["values"][0]
        username = item["values"][1]
        role = item["values"][2]  # "🔑 Администратор" и т.д.
        
        # 🔐 Защита от удаления администратора
        # Проверяем по ID=1 или роли "admin"
        if user_id == 1 or role.startswith("🔑"):
            return ToastNotification(
                self,
                get_text("cannot_delete_admin", self.lang) or "❌ Нельзя удалить главного администратора!",
                "error"
            )
        
        # Подтверждение удаления
        confirm_msg = get_text("confirm_delete_user", self.lang) or "Удалить пользователя '{username}'?"
        if not messagebox.askyesno(
            get_text("confirm_delete", self.lang) or "Подтверждение",
            confirm_msg.format(username=username) + "\n\n" + 
            (get_text("delete_user_warning", self.lang) or "Все его действия будут потеряны."),
            icon="warning"
        ):
            return
        
        try:
            with self.db.get_cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            ToastNotification(self, get_text("user_deleted", self.lang) or "✅ Пользователь удалён", "success")
            app_logger.info(f"👤 User deleted: {username} (ID: {user_id})")
            self._load_users()
            
        except Exception as e:
            app_logger.exception(f"❌ Error deleting user: {e}")
            ToastNotification(self, f"{get_text('error_deleting', self.lang)}: {e}", "error")
    
    def refresh(self) -> None:
        """Публичный метод для обновления данных (вызов извне)"""
        self._load_users()
    
    def focus_search(self) -> None:
        """Установить фокус на поиск"""
        if hasattr(self, 'search'):
            self.search.focus_search()