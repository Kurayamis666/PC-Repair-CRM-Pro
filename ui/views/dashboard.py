# ui/views/dashboard.py
"""
Главный экран заявок (Дашборд) для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: on_navigate извлекается до super().__init__()
✅ ИСПРАВЛЕНО: Запросы к таблице employees (не clients)
✅ УЛУЧШЕНО: Пустое состояние, сортировка, форматирование цен
✅ СОВМЕСТИМО: Интеграция с системой тем, переводов и виджетов
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.tables import DataTable
from ui.widgets.toast import ToastNotification
from utils.helpers import format_currency


class DashboardView(ctk.CTkFrame):
    """Главный экран управления заявками с полным функционалом"""
    
    on_navigate: Optional[Callable[[str], None]] = None
    
    # 📊 Конфигурация статусов заявок
    STATUS_CONFIG: Dict[str, Dict[str, Any]] = {
        "new": {"icon": "🆕", "label_ru": "Новая", "label_en": "New", "color": ColorTheme.STATUS_NEW},
        "diagnostics": {"icon": "🔍", "label_ru": "Диагностика", "label_en": "Diagnostics", "color": ColorTheme.STATUS_DIAGNOSTICS},
        "in_progress": {"icon": "🔧", "label_ru": "В работе", "label_en": "In Progress", "color": ColorTheme.STATUS_IN_PROGRESS},
        "ready": {"icon": "✅", "label_ru": "Готово", "label_en": "Ready", "color": ColorTheme.STATUS_READY},
        "closed": {"icon": "🏁", "label_ru": "Закрыто", "label_en": "Closed", "color": ColorTheme.STATUS_CLOSED},
        "cancelled": {"icon": "❌", "label_ru": "Отменено", "label_en": "Cancelled", "color": ColorTheme.ERROR},
    }
    
    ALLOWED_STATUSES = ["new", "diagnostics", "in_progress", "ready", "closed", "cancelled"]

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
        self.current_filter = "all"
        self._stat_labels: Dict[str, ctk.CTkLabel] = {}
        
        # ✅ Удаляем кастомные аргументы из kwargs перед передачей в родительский класс
        kwargs.pop('on_navigate', None)
        kwargs.pop('lang', None)
        
        # ✅ Теперь передаём только валидные аргументы для ctk.CTkFrame
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Построение интерфейса дашборда с полным переводом"""
        
        # 1. Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.INFO, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=get_text("dashboard", self.lang),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY
        ).pack(pady=10)

        # 2. Навигационное меню
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        nav_items = [
            ("📋 " + get_text("main", self.lang), "dashboard", ColorTheme.PRIMARY),
            ("👥 " + get_text("reference", self.lang), "reference", ColorTheme.BG_INPUT),
            ("📄 " + get_text("documents", self.lang), "documents", ColorTheme.BG_INPUT),
            ("📊 " + get_text("reports", self.lang), "reports", ColorTheme.BG_INPUT),
            ("⚙️ " + get_text("settings", self.lang), "settings", ColorTheme.BG_INPUT)
        ]
        
        for text, view, color in nav_items:
            ctk.CTkButton(
                nav_frame, text=text,
                command=lambda v=view: self.on_navigate(v) if self.on_navigate else None,
                width=140, height=35, corner_radius=8,
                fg_color=color, text_color=ColorTheme.TEXT_PRIMARY,
                hover_color=ColorUtils.darken(color, 10) if color != ColorTheme.PRIMARY else ColorTheme.PRIMARY_HOVER
            ).pack(side="left", padx=5)

        # 3. Панель действий
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            top_frame, text="⚡ " + get_text("mass_status", self.lang),
            command=self._open_mass_status_dialog,
            width=180, height=35,
            fg_color=ColorTheme.WARNING,
            hover_color=ColorUtils.darken(ColorTheme.WARNING, 10),
            corner_radius=10
        ).pack(side="right", padx=10)

        # 4. Статистика с правильными ссылками на label
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        self._stat_labels = {}
        stats_config = [
            ("all", "📊 " + get_text("all", self.lang), ColorTheme.PRIMARY),
            ("new", "🆕 " + get_text("new", self.lang), ColorTheme.STATUS_NEW),
            ("in_progress", "🔧 " + get_text("in_progress", self.lang), ColorTheme.STATUS_IN_PROGRESS),
            ("ready", "✅ " + get_text("ready", self.lang), ColorTheme.STATUS_READY),
            ("closed", "🏁 " + get_text("closed", self.lang), ColorTheme.STATUS_CLOSED),
        ]
        
        for key, title, color in stats_config:
            card = ctk.CTkFrame(stats_frame, fg_color=ColorTheme.BG_CARD, corner_radius=12)
            card.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color=ColorTheme.TEXT_SECONDARY).pack(pady=(10, 0))
            lbl = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
            lbl.pack(pady=(5, 10))
            self._stat_labels[key] = lbl  # ✅ Сохраняем ссылку

        # 5. Фильтры
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=5)
        
        filters = [
            (" " + get_text("all", self.lang), "all", ColorTheme.BG_INPUT),
            ("🆕 " + get_text("new", self.lang), "new", ColorTheme.STATUS_NEW),
            ("🔍 " + get_text("diagnostics", self.lang), "diagnostics", ColorTheme.STATUS_DIAGNOSTICS),
            ("🔧 " + get_text("in_progress", self.lang), "in_progress", ColorTheme.STATUS_IN_PROGRESS),
            ("✅ " + get_text("ready", self.lang), "ready", ColorTheme.STATUS_READY),
            ("🏁 " + get_text("closed", self.lang), "closed", ColorTheme.STATUS_CLOSED)
        ]
        
        self.filter_vars: Dict[str, ctk.CTkButton] = {}
        for i, (text, status, color) in enumerate(filters):
            btn = ctk.CTkButton(
                filter_frame, text=text, command=lambda s=status: self._filter_requests(s),
                width=120, height=30, corner_radius=8,
                fg_color=color if status != "all" else ColorTheme.PRIMARY,
                hover_color=ColorUtils.darken(color, 10) if status != "all" else ColorUtils.darken(ColorTheme.BG_INPUT, 10),
                text_color=ColorTheme.TEXT_PRIMARY
            )
            btn.pack(side="left", padx=5)
            self.filter_vars[status] = btn

        # 6. Таблица заявок с DataTable для сортировки
        table_container = ctk.CTkFrame(self, fg_color=ColorTheme.BG_INPUT)
        table_container.pack(fill="both", expand=True, padx=20, pady=10)

        cols = [
            get_text("col_id", self.lang),
            get_text("col_date", self.lang),
            get_text("col_employee", self.lang),  # ✅ employees вместо clients
            get_text("col_equipment", self.lang),
            get_text("col_status", self.lang),
            get_text("col_sum", self.lang),
            get_text("col_master", self.lang)
        ]
        col_widths = {
            get_text("col_id", self.lang): 50,
            get_text("col_date", self.lang): 100,
            get_text("col_employee", self.lang): 150,
            get_text("col_equipment", self.lang): 150,
            get_text("col_status", self.lang): 120,
            get_text("col_sum", self.lang): 100,
            get_text("col_master", self.lang): 120
        }
        col_align = {
            get_text("col_id", self.lang): "center",
            get_text("col_date", self.lang): "center",
            get_text("col_employee", self.lang): "left",
            get_text("col_equipment", self.lang): "left",
            get_text("col_status", self.lang): "center",
            get_text("col_sum", self.lang): "right",
            get_text("col_master", self.lang): "left"
        }
        
        self.tree = DataTable(
            table_container,
            columns=cols,
            column_widths=col_widths,
            column_align=col_align,
            sortable=True,
            copyable=True,
            on_row_double_click=lambda item: self._edit_request()
        )
        self.tree.pack(fill="both", expand=True)
        
        # ✅ Теги для статусов с цветами из темы
        for status, config in self.STATUS_CONFIG.items():
            self.tree.tag_configure(
                status,
                background=ColorUtils.darken(config["color"], 30),
                foreground=ColorTheme.TEXT_PRIMARY
            )

        # 7. Нижняя панель
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(bottom_frame, text="🗑️ " + get_text("delete", self.lang), command=self._delete_request, width=120, height=30, fg_color=ColorTheme.ERROR, hover_color=ColorUtils.darken(ColorTheme.ERROR, 10)).pack(side="left", padx=10)
        ctk.CTkButton(bottom_frame, text="🔄 " + get_text("update", self.lang), command=self._load_requests, width=120, height=30, fg_color=ColorTheme.INFO, hover_color=ColorUtils.darken(ColorTheme.INFO, 10)).pack(side="right", padx=10)

        # ⌨️ Горячие клавиши
        self._bind_hotkeys()
        
        self._load_requests()
    
    def _bind_hotkeys(self):
        """Привязка горячих клавиш"""
        # Delete → удалить выбранные
        self.tree.bind("<Delete>", lambda e: self._delete_request())
        
        # Ctrl+E → редактировать выбранное
        self.tree.bind("<Control-e>", lambda e: self._edit_request())
        self.tree.bind("<Control-E>", lambda e: self._edit_request())
        
        # Ctrl+R → обновить
        self.bind("<Control-r>", lambda e: self._load_requests())
        self.bind("<Control-R>", lambda e: self._load_requests())
    
    def _get_status_display(self, status: str) -> str:
        """Получить отображаемый статус с иконкой"""
        config = self.STATUS_CONFIG.get(status, {})
        icon = config.get("icon", "❓")
        label = config.get(f"label_{self.lang}", status)
        return f"{icon} {label}"
    
    def _load_requests(self) -> None:
        """Загрузка заявок из БД с пустым состоянием"""
        # Показываем индикатор загрузки
        ToastNotification(self, get_text("loading_requests", self.lang) or "🔄 Загрузка заявок...", "info")
        
        # Очищаем таблицу
        self.tree.delete(*self.tree.get_children())
            
        try:
            with self.db.get_cursor() as cur:
                # ✅ ИСПРАВЛЕНО: employees вместо clients
                query = """
                    SELECT r.id, r.created_at, emp.full_name, e.model, r.status, r.total_cost, u.username
                    FROM requests r
                    JOIN employees emp ON r.client_id = emp.id
                    LEFT JOIN equipment e ON r.equipment_id = e.id
                    LEFT JOIN users u ON r.user_id = u.id
                    ORDER BY r.created_at DESC
                """
                cur.execute(query)
                rows = cur.fetchall()

            counts = {s: 0 for s in ["all"] + self.ALLOWED_STATUSES}
            
            # Пустое состояние
            if not rows:
                self.tree.show_empty_state(
                    message=get_text("no_requests", self.lang) or "Заявки не найдены",
                    icon="📋"
                )
                # Обновляем статистику нулями
                for key in self._stat_labels:
                    self._stat_labels[key].configure(text="0")
                return
            else:
                self.tree.hide_empty_state()

            for idx, row in enumerate(rows):
                r_id, date, employee, equip, status, cost, master = row
                
                # Считаем статистику
                counts["all"] += 1
                if status in counts:
                    counts[status] += 1

                # Фильтрация
                if self.current_filter != "all" and status != self.current_filter:
                    continue

                # Определяем тег
                tag = status if status in self.STATUS_CONFIG else ("odd" if idx % 2 else "even")
                
                # ✅ Форматируем сумму через format_currency
                values = (
                    r_id, 
                    (date or "")[:10], 
                    employee or "—", 
                    equip or "—", 
                    self._get_status_display(status), 
                    format_currency(cost, "RUB", self.lang), 
                    master or "—"
                )
                self.tree.insert("", "end", values=values, tags=(tag,))

            # ✅ Обновляем статистику через сохранённые ссылки
            stat_mapping = {
                "all": "all",
                "new": "new",
                "in_progress": "in_progress",
                "ready": "ready",
                "closed": "closed"
            }
            for db_key, ui_key in stat_mapping.items():
                if ui_key in self._stat_labels:
                    self._stat_labels[ui_key].configure(text=str(counts.get(db_key, 0)))

        except Exception as e:
            app_logger.exception(f"❌ Error loading requests: {e}")
            ToastNotification(self, f"{get_text('error_loading', self.lang)}: {e}", "error")
        finally:
            # Скрываем индикатор загрузки (если нужно)
            pass

    def _filter_requests(self, status: str) -> None:
        """Фильтрация заявок по статусу"""
        if status not in ["all"] + self.ALLOWED_STATUSES:
            return  # Защита от недопустимых статусов
        
        self.current_filter = status
        for s, btn in self.filter_vars.items():
            btn.configure(
                fg_color=ColorTheme.PRIMARY if s == status else ColorTheme.BG_INPUT,
                hover_color=ColorTheme.PRIMARY_HOVER if s == status else ColorUtils.darken(ColorTheme.BG_INPUT, 10)
            )
        self._load_requests()

    def _edit_request(self) -> None:
        """Открытие диалога редактирования заявки"""
        sel = self.tree.selection()
        if not sel:
            return ToastNotification(self, get_text("select_row", self.lang), "warning")
        
        request_id = self.tree.item(sel[0])['values'][0]
        try:
            from ui.dialogs.request_editor import RequestEditorDialog
            RequestEditorDialog(
                self, request_id=request_id, lang=self.lang,
                on_save=self._load_requests
            )
        except ImportError as e:
            app_logger.warning(f"⚠️ Could not import RequestEditorDialog: {e}")
            ToastNotification(self, "⚠️ " + get_text("edit_request_unavailable", self.lang) or "Редактирование доступно в разделе Документы", "warning")
        except Exception as e:
            app_logger.error(f"❌ Error opening request editor: {e}")
            ToastNotification(self, f"❌ {e}", "error")

    def _delete_request(self) -> None:
        """Удаление выбранных заявок"""
        sel = self.tree.selection()
        if not sel:
            return ToastNotification(self, get_text("select_row", self.lang), "warning")
            
        ids = [self.tree.item(item)['values'][0] for item in sel]
        count = len(ids)
        
        if messagebox.askyesno(
            get_text("confirm_delete", self.lang), 
            f"{get_text('delete', self.lang)} {count} {get_text('request_plural', self.lang, count)}?"
        ):
            try:
                with self.db.get_cursor() as cur:
                    cur.executemany("DELETE FROM requests WHERE id = ?", [(rid,) for rid in ids])
                ToastNotification(self, f"✅ {get_text('deleted', self.lang)}: {count}", "success")
                self._load_requests()
            except Exception as e:
                ToastNotification(self, f"❌ {get_text('error', self.lang)}: {e}", "error")

    def _open_mass_status_dialog(self) -> None:
        """Открывает диалог для массового изменения статуса"""
        selected_items = self.tree.selection()
        
        if not selected_items:
            ToastNotification(self, get_text("select_requests", self.lang) or "Выберите заявки для изменения статуса", "warning")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(get_text("mass_status", self.lang))
        dialog.geometry("350x220")
        dialog.transient(self)
        dialog.configure(fg_color=ColorTheme.BG_CARD)

        ctk.CTkLabel(
            dialog, 
            text=f"{get_text('selected_count', self.lang).format(len(selected_items))}\n{get_text('set_status', self.lang)}", 
            text_color=ColorTheme.TEXT_PRIMARY,
            justify="center",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=15)

        # ✅ Только разрешённые статусы
        status_values = [
            self._get_status_display(s) for s in ["diagnostics", "in_progress", "ready", "closed"]
        ]
        status_map = dict(zip(status_values, ["diagnostics", "in_progress", "ready", "closed"]))
        
        status_combo = ctk.CTkComboBox(
            dialog, 
            values=status_values,
            width=220,
            fg_color=ColorTheme.BG_INPUT,
            text_color=ColorTheme.TEXT_PRIMARY,
            dropdown_fg_color=ColorTheme.BG_CARD
        )
        status_combo.pack(pady=10)
        status_combo.set(status_values[2])  # "ready" по умолчанию

        def apply_mass_change():
            display_status = status_combo.get()
            new_status = status_map.get(display_status)
            if new_status and new_status in self.ALLOWED_STATUSES:
                self._execute_mass_status_update(selected_items, new_status)
            else:
                ToastNotification(self, get_text("invalid_status", self.lang) or "Недопустимый статус", "error")
            dialog.destroy()

        ctk.CTkButton(
            dialog, 
            text=get_text("apply", self.lang), 
            command=apply_mass_change, 
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            width=200,
            height=35
        ).pack(pady=10)

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 350) // 2
        y = (dialog.winfo_screenheight() - 220) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.grab_set()

    def _execute_mass_status_update(self, items, new_status: str) -> None:
        """Выполняет SQL запрос на обновление статусов выбранных заявок"""
        # ✅ Валидация статуса
        if new_status not in self.ALLOWED_STATUSES:
            ToastNotification(self, get_text("invalid_status", self.lang) or "Недопустимый статус", "error")
            return
            
        try:
            request_ids = [self.tree.item(item)['values'][0] for item in items]
            
            with self.db.get_cursor() as cur:
                cur.executemany(
                    "UPDATE requests SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    [(new_status, rid) for rid in request_ids]
                )
            
            self._load_requests()
            ToastNotification(self, f"✅ {get_text('mass_status_updated', self.lang).format(len(request_ids))}", "success")
            app_logger.info(f"⚡ Mass status updated to {new_status} for {len(request_ids)} requests")
            
        except Exception as e:
            app_logger.exception(f"❌ Mass update error: {e}")
            ToastNotification(self, f"{get_text('error', self.lang)}: {e}", "error")
    
    def refresh(self) -> None:
        """Публичный метод для обновления данных (вызов извне)"""
        self._load_requests()
    
    def focus_search(self) -> None:
        """Заглушка для совместимости с другими видами"""
        # Можно добавить поиск по заявкам в будущем
        pass