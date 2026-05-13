# ui/dialogs/confirm.py
"""
Универсальный диалог подтверждения для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Адаптивный размер, горячие клавиши, управление фокусом
✅ УЛУЧШЕНО: Визуальные индикаторы, надёжное центрирование, типизация
✅ СОВМЕСТИМО: Интеграция с системой тем и переводов
"""

import customtkinter as ctk
from typing import Callable, Optional, Union
from ui.theme import ColorTheme, ColorUtils
from translations import get_text


class ConfirmDialog(ctk.CTkToplevel):
    """
    Универсальный модальный диалог подтверждения действия
    
    ✅ Адаптивный размер под длину сообщения
    ✅ Горячие клавиши: Enter = подтвердить, Esc = отменить
    ✅ Управление фокусом: фокус на нужной кнопке
    ✅ Визуальный индикатор для опасных действий (⚠️)
    ✅ Надёжное центрирование относительно родителя или экрана
    """
    
    # ⚙️ Конфигурация
    MIN_WIDTH: int = 350
    MAX_WIDTH: int = 500
    MIN_HEIGHT: int = 180
    PADDING_X: int = 20
    PADDING_Y: int = 20
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        on_cancel: Optional[Callable[[], None]] = None,
        confirm_text: Optional[str] = None,
        cancel_text: Optional[str] = None,
        lang: str = "ru",
        danger: bool = False,
        focus_confirm: Optional[bool] = None,  # None = авто (danger → confirm, else → cancel)
    ):
        super().__init__(parent)
        
        self.parent = parent
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.lang = lang
        self.danger = danger
        
        # 🔧 UI элементы (для доступа из обработчиков)
        self._confirm_btn: Optional[ctk.CTkButton] = None
        self._cancel_btn: Optional[ctk.CTkButton] = None
        
        # ✅ Переведённые тексты кнопок по умолчанию
        self._confirm_text = confirm_text or (get_text("delete", lang) if danger else get_text("confirm", lang))
        self._cancel_text = cancel_text or get_text("cancel", lang)
        
        # ✅ Адаптивный заголовок
        self.title(title)
        
        # ✅ Расчёт размера под сообщение
        width = self._calculate_width(message)
        height = self._calculate_height(message)
        
        self.geometry(f"{width}x{height}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.transient(parent)
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        
        self._build_ui(message, danger)
        self._setup_focus(focus_confirm)
        
        # Центрирование и модальность — после построения UI
        self._center_window(parent)
        self.grab_set()
        
        # ⌨️ Горячие клавиши
        self._bind_hotkeys()
    
    def _calculate_width(self, message: str) -> int:
        """Расчёт ширины окна под длину сообщения"""
        # Примерно 8 пикселей на символ для шрифта размера 14
        estimated = len(message) * 8 + self.PADDING_X * 2
        return max(self.MIN_WIDTH, min(estimated, self.MAX_WIDTH))
    
    def _calculate_height(self, message: str) -> int:
        """Расчёт высоты окна под количество строк"""
        # Примерно 20 пикселей на строку + отступы
        lines = (len(message) // 40) + 1  # ~40 символов на строку
        base_height = self.MIN_HEIGHT
        extra = max(0, (lines - 2) * 25)  # Дополнительные строки сверх 2
        return base_height + extra
    
    def _center_window(self, parent: ctk.CTkBaseClass) -> None:
        """Надёжное центрирование окна"""
        self.update_idletasks()
        
        # Пробуем центрировать относительно родителя
        if hasattr(parent, "winfo_x") and hasattr(parent, "winfo_width"):
            try:
                parent_x = parent.winfo_x()
                parent_y = parent.winfo_y()
                parent_w = parent.winfo_width()
                parent_h = parent.winfo_height()
                
                win_w = self.winfo_width()
                win_h = self.winfo_height()
                
                x = parent_x + (parent_w - win_w) // 2
                y = parent_y + (parent_h - win_h) // 2
                
                self.geometry(f"+{max(0, x)}+{max(0, y)}")
                return
            except Exception:
                pass  # Fallback на центрирование по экрану
        
        # ✅ Fallback: центрирование по экрану
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = self.winfo_width()
        win_h = self.winfo_height()
        
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
    
    def _build_ui(self, message: str, danger: bool) -> None:
        """Построение интерфейса с адаптивным сообщением"""
        
        # ⚠️ Визуальный индикатор для опасных действий
        display_message = message
        if danger:
            display_message = f"⚠️ {message}"
        
        # ✅ Центрирование для коротких сообщений
        justify = "center" if len(message) < 80 else "left"
        wraplength = min(320, self.winfo_width() - self.PADDING_X * 2) if self.winfo_width() > 0 else 320
        
        # 📝 Сообщение
        ctk.CTkLabel(
            self,
            text=display_message,
            font=ctk.CTkFont(size=14),
            text_color=ColorTheme.TEXT_PRIMARY,
            justify=justify,
            wraplength=wraplength,
        ).pack(pady=25, padx=self.PADDING_X, fill="x")
        
        # 🔘 Кнопки
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(pady=15)
        
        # Кнопка отмены
        self._cancel_btn = ctk.CTkButton(
            buttons_frame,
            text=self._cancel_text,
            command=self._cancel,
            width=120,
            height=35,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            corner_radius=10,
            text_color=ColorTheme.TEXT_PRIMARY,
        )
        self._cancel_btn.pack(side="left", padx=10)
        
        # Кнопка подтверждения
        confirm_color = ColorTheme.ERROR if danger else ColorTheme.SUCCESS
        confirm_hover = ColorUtils.darken(confirm_color, 10)
        
        self._confirm_btn = ctk.CTkButton(
            buttons_frame,
            text=self._confirm_text,
            command=self._confirm,
            width=120,
            height=35,
            fg_color=confirm_color,
            hover_color=confirm_hover,
            corner_radius=10,
            text_color=ColorTheme.TEXT_PRIMARY,
            font=ctk.CTkFont(weight="bold") if danger else None,
        )
        self._confirm_btn.pack(side="left", padx=10)
    
    def _setup_focus(self, focus_confirm: Optional[bool]) -> None:
        """Установка фокуса на нужную кнопку"""
        # Авто-выбор: для опасных действий фокус на "Отмена" (безопаснее), иначе на "Подтвердить"
        if focus_confirm is None:
            focus_confirm = not self.danger
        
        self.after(100, lambda: (
            self._confirm_btn.focus_set() if focus_confirm and self._confirm_btn else
            self._cancel_btn.focus_set() if self._cancel_btn else None
        ))
    
    def _bind_hotkeys(self) -> None:
        """Привязка горячих клавиш"""
        # Enter → подтвердить
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<KP_Enter>", lambda e: self._confirm())
        
        # Esc → отменить
        self.bind("<Escape>", lambda e: self._cancel())
    
    def _confirm(self) -> None:
        """Обработчик подтверждения"""
        try:
            if self.on_confirm:
                self.on_confirm()
        except Exception as e:
            from core.logger import app_logger
            app_logger.error(f"❌ Error in on_confirm callback: {e}")
        finally:
            # ✅ Безопасное закрытие
            try:
                self.destroy()
            except Exception:
                pass
    
    def _cancel(self) -> None:
        """Обработчик отмены (включая закрытие крестиком)"""
        try:
            if self.on_cancel:
                self.on_cancel()
        except Exception as e:
            from core.logger import app_logger
            app_logger.error(f"❌ Error in on_cancel callback: {e}")
        finally:
            # ✅ Безопасное закрытие
            try:
                self.destroy()
            except Exception:
                pass
    
    def destroy(self) -> None:
        """Корректное уничтожение диалога"""
        # Отменяем любые отложенные задачи
        try:
            pass  # Можно добавить очистку таймеров если есть
        except:
            pass
        super().destroy()


def ask_confirm(
    parent: ctk.CTkBaseClass,
    message: str,
    on_confirm: Callable[[], None],
    title: str = "Подтверждение",
    on_cancel: Optional[Callable[[], None]] = None,
    confirm_text: Optional[str] = None,
    cancel_text: Optional[str] = None,
    lang: str = "ru",
    danger: bool = False,
) -> ConfirmDialog:
    """
    Удобная функция для показа модального диалога подтверждения
    
    ✅ Диалог блокирует родительское окно до закрытия
    ✅ Возвращает экземпляр диалога для дальнейшего управления (опционально)
    
    Args:
        parent: Родительское окно
        message: Текст сообщения для подтверждения
        on_confirm: Callback при подтверждении
        title: Заголовок окна (по умолчанию: "Подтверждение")
        on_cancel: Callback при отмене (опционально)
        confirm_text: Текст кнопки подтверждения (по умолчанию: "Подтвердить" / "Удалить")
        cancel_text: Текст кнопки отмены (по умолчанию: "Отмена")
        lang: Язык интерфейса
        danger: Если True — красный стиль для опасных действий
        
    Returns:
        ConfirmDialog: Созданный экземпляр диалога
        
    Example:
        >>> ask_confirm(
        ...     parent=self,
        ...     message="Удалить пользователя 'admin'?",
        ...     on_confirm=lambda: delete_user("admin"),
        ...     danger=True,
        ...     confirm_text="Удалить"
        ... )
    """
    dialog = ConfirmDialog(
        parent=parent,
        title=title,
        message=message,
        on_confirm=on_confirm,
        on_cancel=on_cancel,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
        lang=lang,
        danger=danger,
    )
    # ✅ Диалог уже модальный благодаря grab_set() в __init__
    return dialog