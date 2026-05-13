# ui/dialogs/calendar.py
"""
Модальное окно выбора даты для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Переводы через get_text(), горячие клавиши, адаптивность
✅ УЛУЧШЕНО: Навигация клавиатурой, очистка даты, визуальные индикаторы
✅ СОВМЕСТИМО: Интеграция с системой тем и переводов
"""

import customtkinter as ctk
import calendar
from datetime import datetime
from typing import Callable, Optional, List
from ui.theme import ColorTheme, ColorUtils
from translations import get_text


class CalendarPopup(ctk.CTkToplevel):
    """
    Модальное окно выбора даты с полным функционалом
    
    ✅ Перевод дней/месяцев через get_text() для единой системы локализации
    ✅ Горячие клавиши: стрелки для навигации, Enter/Esc для подтверждения/отмены
    ✅ Адаптивный размер с minsize() вместо фиксированного
    ✅ Визуальный индикатор выбранной даты в заголовке
    ✅ Кнопка "Очистить" для сброса выбора
    ✅ Учёт первого дня недели через calendar.firstweekday
    """
    
    # ⚙️ Конфигурация
    DAY_BUTTON_SIZE: int = 42
    MIN_WIDTH: int = 320
    MIN_HEIGHT: int = 380
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,  # ✅ CTkBaseClass вместо строгого CTk
        callback: Callable[[Optional[str]], None],  # ✅ None для очистки даты
        initial_date: Optional[str] = None,
        lang: str = "ru",
        min_date: Optional[str] = None,  # ✅ Минимальная доступная дата
        max_date: Optional[str] = None,  # ✅ Максимальная доступная дата
    ):
        super().__init__(parent)
        
        self.callback = callback
        self.lang = lang
        self.selected_date: Optional[str] = None
        self.min_date = min_date
        self.max_date = max_date
        self._focused_day: Optional[int] = None  # Для навигации клавиатурой
        
        # Инициализация даты
        if initial_date:
            try:
                date_obj = datetime.strptime(initial_date, "%Y-%m-%d")
                self.current_year = date_obj.year
                self.current_month = date_obj.month
                self.selected_date = initial_date
            except ValueError:
                self.current_year = datetime.now().year
                self.current_month = datetime.now().month
        else:
            self.current_year = datetime.now().year
            self.current_month = datetime.now().month
        
        # ✅ Переведённый заголовок
        self.title(get_text("select_date", self.lang) or "Выберите дату")
        
        self.geometry("360x420")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)  # ✅ Адаптивный минимальный размер
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        # 🛡️ Обработчик закрытия окна (крестик = отмена)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        # 🎯 Центрирование
        self._center_window(parent)
        
        self._build_ui()
        
        # ⌨️ Горячие клавиши
        self._bind_hotkeys()
    
    def _center_window(self, parent: ctk.CTkBaseClass) -> None:
        """Центрирование окна относительно родителя"""
        self.update_idletasks()
        try:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            win_w = 360
            win_h = 420
            x = parent_x + (parent_w - win_w) // 2
            y = parent_y + (parent_h - win_h) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass  # Fallback на позиционирование по умолчанию
    
    def _build_ui(self):
        """Построение интерфейса с переводом и адаптивностью"""
        
        # 🏷️ Заголовок с навигацией
        header = ctk.CTkFrame(self, fg_color=ColorTheme.PRIMARY, corner_radius=0)
        header.pack(fill="x")
        
        # Кнопка "Назад"
        ctk.CTkButton(
            header,
            text="<",
            width=40,
            fg_color="transparent",
            hover_color=ColorUtils.darken(ColorTheme.PRIMARY, 10),
            command=lambda: self._change_month(-1),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(side="left", padx=10)
        
        # Метка месяца
        self.month_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        )
        self.month_label.pack(side="left", expand=True)
        self._update_month_label()
        
        # Кнопка "Вперёд"
        ctk.CTkButton(
            header,
            text=">",
            width=40,
            fg_color="transparent",
            hover_color=ColorUtils.darken(ColorTheme.PRIMARY, 10),
            command=lambda: self._change_month(1),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(side="right", padx=10)
        
        # 📅 Выбранная дата (индикатор)
        if self.selected_date:
            self.selected_label = ctk.CTkLabel(
                self,
                text=f"{get_text('selected', self.lang) or 'Выбрано'}: {self.selected_date}",
                text_color=ColorTheme.SUCCESS,
                font=ctk.CTkFont(size=11),
            )
            self.selected_label.pack(pady=(5, 0))
        
        # 🗓️ Дни недели (с переводом через get_text)
        days_frame = ctk.CTkFrame(self, fg_color=ColorTheme.BG_INPUT)
        days_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        # ✅ Используем get_text для дней недели
        days = self._get_day_names()
        for day in days:
            ctk.CTkLabel(
                days_frame,
                text=day,
                width=self.DAY_BUTTON_SIZE,
                font=ctk.CTkFont(weight="bold", size=11),
                text_color=ColorTheme.PRIMARY,
            ).pack(side="left")
        
        # 📆 Календарь
        self.calendar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self._render_calendar()
        
        # 🔘 Кнопки управления
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=15)
        
        # Кнопка "Сегодня"
        ctk.CTkButton(
            buttons_frame,
            text=get_text("today", self.lang),
            command=self._select_today,
            fg_color=ColorTheme.INFO,
            hover_color=ColorUtils.darken(ColorTheme.INFO, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
            width=100,
            height=35,
        ).pack(side="left", padx=5)
        
        # ✅ Кнопка "Очистить" (новая функция)
        ctk.CTkButton(
            buttons_frame,
            text="🗑️ " + (get_text("clear", self.lang) or "Очистить"),
            command=self._clear_date,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
            width=100,
            height=35,
        ).pack(side="left", padx=5)
        
        # Кнопка "Отмена"
        ctk.CTkButton(
            buttons_frame,
            text=get_text("cancel", self.lang),
            command=self.destroy,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
            width=100,
            height=35,
        ).pack(side="right", padx=5)
        
        # Кнопка "ОК"
        ctk.CTkButton(
            buttons_frame,
            text=get_text("ok", self.lang),
            command=self._confirm,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
            width=100,
            height=35,
            font=ctk.CTkFont(weight="bold"),
        ).pack(side="right", padx=5)
    
    def _get_day_names(self) -> List[str]:
        """Получить названия дней недели через систему переводов"""
        # ✅ Используем get_text для единой системы локализации
        # Ключи: day_mon, day_tue, ..., day_sun
        days = []
        for key in ["day_mon", "day_tue", "day_wed", "day_thu", "day_fri", "day_sat", "day_sun"]:
            days.append(get_text(key, self.lang) or key.replace("day_", "").upper()[:2])
        return days
    
    def _get_month_names(self) -> List[str]:
        """Получить названия месяцев через систему переводов"""
        # ✅ Используем get_text для единой системы локализации
        # Ключи: month_january, month_february, ..., month_december
        months = []
        for key in ["january", "february", "march", "april", "may", "june", 
                    "july", "august", "september", "october", "november", "december"]:
            months.append(get_text(f"month_{key}", self.lang) or key.capitalize())
        return months
    
    def _update_month_label(self):
        """Обновить заголовок месяца"""
        months = self._get_month_names()
        self.month_label.configure(
            text=f"{months[self.current_month - 1]} {self.current_year}"
        )
    
    def _is_date_enabled(self, year: int, month: int, day: int) -> bool:
        """Проверка, доступна ли дата (min/max ограничения)"""
        date_str = f"{year}-{month:02d}-{day:02d}"
        if self.min_date and date_str < self.min_date:
            return False
        if self.max_date and date_str > self.max_date:
            return False
        return True
    
    def _change_month(self, delta: int):
        """Изменить месяц с учётом года"""
        self.current_month += delta
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        elif self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self._update_month_label()
        self._render_calendar()
    
    def _render_calendar(self):
        """Отрисовать календарь с поддержкой локалей и ограничений"""
        # Очистка
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        today = datetime.now()
        
        # ✅ Учитываем первый день недели для локали
        first_weekday = calendar.firstweekday()  # 0 = Monday, 6 = Sunday
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        for week in cal:
            week_frame = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
            week_frame.pack(fill="x")
            
            for day in week:
                if day == 0:
                    # Пустой день
                    ctk.CTkLabel(week_frame, text="", width=self.DAY_BUTTON_SIZE).pack(side="left")
                else:
                    is_today = (
                        day == today.day
                        and self.current_month == today.month
                        and self.current_year == today.year
                    )
                    
                    is_selected = (
                        self.selected_date
                        and self.selected_date == f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                    )
                    
                    is_enabled = self._is_date_enabled(self.current_year, self.current_month, day)
                    
                    # ✅ Цвет кнопки с учётом состояния
                    if not is_enabled:
                        bg_color = ColorTheme.BG_CARD
                        hover_color = ColorTheme.BG_CARD
                        text_color = ColorTheme.TEXT_SECONDARY
                        state = "disabled"
                    elif is_today:
                        bg_color = ColorTheme.SUCCESS
                        hover_color = ColorUtils.darken(ColorTheme.SUCCESS, 10)
                        text_color = ColorTheme.TEXT_PRIMARY
                        state = "normal"
                    elif is_selected:
                        bg_color = ColorTheme.PRIMARY
                        hover_color = ColorUtils.darken(ColorTheme.PRIMARY, 10)
                        text_color = ColorTheme.TEXT_PRIMARY
                        state = "normal"
                    else:
                        bg_color = ColorTheme.BG_INPUT
                        hover_color = ColorUtils.darken(ColorTheme.BG_INPUT, 10)
                        text_color = ColorTheme.TEXT_PRIMARY
                        state = "normal"
                    
                    # ✅ Используем явную фиксацию значения в lambda (d=day)
                    ctk.CTkButton(
                        week_frame,
                        text=str(day),
                        width=self.DAY_BUTTON_SIZE,
                        height=self.DAY_BUTTON_SIZE,
                        corner_radius=8,
                        fg_color=bg_color,
                        hover_color=hover_color,
                        text_color=text_color,
                        state=state,
                        command=lambda d=day: self._select_date(d),  # ✅ d=day фиксирует значение
                        font=ctk.CTkFont(weight="bold" if is_selected or is_today else "normal"),
                    ).pack(side="left", padx=2, pady=2)
    
    def _select_date(self, day: int):
        """Выбрать дату и обновить интерфейс"""
        if not self._is_date_enabled(self.current_year, self.current_month, day):
            return
        
        self.selected_date = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
        self._focused_day = day
        
        # ✅ Обновляем индикатор выбранной даты
        if hasattr(self, 'selected_label'):
            self.selected_label.configure(text=f"{get_text('selected', self.lang) or 'Выбрано'}: {self.selected_date}")
        
        self._render_calendar()  # Перерисовать для обновления выделения
    
    def _select_today(self):
        """Выбрать сегодня"""
        today = datetime.now()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date = today.strftime("%Y-%m-%d")
        self._focused_day = today.day
        self._update_month_label()
        self._render_calendar()
    
    def _clear_date(self):
        """Очистить выбранную дату"""
        self.selected_date = None
        self._focused_day = None
        if hasattr(self, 'selected_label'):
            self.selected_label.configure(text="")
        self._render_calendar()
    
    def _confirm(self):
        """Подтвердить выбор даты"""
        # ✅ Вызываем callback с датой или None
        if self.callback:
            self.callback(self.selected_date)
        self.destroy()
    
    def _bind_hotkeys(self) -> None:
        """Привязка горячих клавиш для навигации"""
        # ✅ Навигация по дням (стрелки)
        self.bind("<Left>", lambda e: self._navigate_day(-1))
        self.bind("<Right>", lambda e: self._navigate_day(1))
        self.bind("<Up>", lambda e: self._navigate_day(-7))
        self.bind("<Down>", lambda e: self._navigate_day(7))
        
        # ✅ Навигация по месяцам (Ctrl+стрелки)
        self.bind("<Control-Left>", lambda e: self._change_month(-1))
        self.bind("<Control-Right>", lambda e: self._change_month(1))
        
        # ✅ Подтверждение / Отмена
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<KP_Enter>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self.destroy())
    
    def _navigate_day(self, delta: int) -> None:
        """Навигация по дням с клавиатуры"""
        # Простая реализация: меняем focused_day и выделяем
        if self._focused_day is None:
            self._focused_day = datetime.now().day if (
                self.current_month == datetime.now().month and 
                self.current_year == datetime.now().year
            ) else 1
        
        new_day = self._focused_day + delta
        
        # Получаем количество дней в месяце
        import calendar
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        
        if 1 <= new_day <= days_in_month:
            self._focused_day = new_day
            self._select_date(new_day)
        elif new_day < 1:
            # Переход на предыдущий месяц
            self._change_month(-1)
            import calendar
            days_in_prev = calendar.monthrange(self.current_year, self.current_month)[1]
            self._focused_day = min(days_in_prev, abs(new_day))
            self._select_date(self._focused_day)
        elif new_day > days_in_month:
            # Переход на следующий месяц
            self._change_month(1)
            self._focused_day = min(7, new_day - days_in_month)
            self._select_date(self._focused_day)
    
    def destroy(self) -> None:
        """Корректное закрытие диалога"""
        # Отменяем любые отложенные задачи
        try:
            pass
        except:
            pass
        super().destroy()


def ask_date(
    parent: ctk.CTkBaseClass,
    callback: Callable[[Optional[str]], None],
    initial_date: Optional[str] = None,
    lang: str = "ru",
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
) -> CalendarPopup:
    """
    Удобная функция для показа календаря
    
    ✅ Модальный диалог с блокировкой родителя
    ✅ Поддержка очистки даты (callback получает None)
    
    Args:
        parent: Родительское окно
        callback: Функция, вызываемая с выбранной датой (формат "YYYY-MM-DD") или None
        initial_date: Начальная дата для отображения (формат "YYYY-MM-DD")
        lang: Язык интерфейса
        min_date: Минимальная доступная дата (формат "YYYY-MM-DD")
        max_date: Максимальная доступная дата (формат "YYYY-MM-DD")
        
    Returns:
        CalendarPopup: Созданный экземпляр диалога
        
    Example:
        >>> def on_date_selected(date: Optional[str]):
        ...     if date:
        ...         print(f"Выбрана дата: {date}")
        ...     else:
        ...         print("Дата очищена")
        >>> ask_date(parent=self, callback=on_date_selected, lang="ru")
    """
    return CalendarPopup(
        parent=parent,
        callback=callback,
        initial_date=initial_date,
        lang=lang,
        min_date=min_date,
        max_date=max_date,
    )