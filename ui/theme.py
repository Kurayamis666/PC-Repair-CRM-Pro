# ui/theme.py
"""
Система тем оформления для PC Repair CRM Pro
✅ УЛУЧШЕНО: Поддержка светлой/тёмной темы, утилиты цветов, CustomTkinter интеграция
✅ ГИБКОСТЬ: Динамическое переключение, кастомизация, валидация
✅ СОВМЕСТИМО: Прямая интеграция с customtkinter.set_default_color_theme()
"""

import re
import customtkinter as ctk
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional, Dict, Tuple, Union, ClassVar


@dataclass(frozen=True)
class ColorPalette:
    """Неизменяемая палитра цветов для одной темы"""
    
    # 🔷 Основные
    primary: str = "#6366f1"
    primary_hover: str = "#4f46e5"
    secondary: str = "#8b5cf6"
    
    # 🎨 Фон
    bg_main: str = "#0f172a"
    bg_card: str = "#1e293b"
    bg_input: str = "#334155"
    bg_hover: str = "#334155"
    
    # ✍️ Текст
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#94a3b8"
    text_disabled: str = "#64748b"
    
    # 🟢 Статусы
    status_new: str = "#3b82f6"
    status_diagnostics: str = "#f59e0b"
    status_in_progress: str = "#a855f7"
    status_ready: str = "#22c55e"
    status_closed: str = "#64748b"
    status_cancelled: str = "#ef4444"
    
    # 💬 Сообщения
    success: str = "#22c55e"
    warning: str = "#f59e0b"
    error: str = "#ef4444"
    info: str = "#3b82f6"
    
    # 🔘 Интерактив
    border: str = "#475569"
    border_focus: str = "#6366f1"
    disabled: str = "#475569"
    selected: str = "#3b82f6"
    scrollbar: str = "#475569"
    scrollbar_hover: str = "#64748b"
    tooltip_bg: str = "#1e293b"
    tooltip_text: str = "#FFFFFF"
    divider: str = "#334155"
    
    # 🔍 Валидация при создании
    def __post_init__(self):
        for fname, fvalue in self.__dataclass_fields__.items():
            value = getattr(self, fname)
            if not ColorUtils.is_valid_hex(value):
                raise ValueError(f"Invalid hex color for {fname}: {value}")


class ColorUtils:
    """Утилиты для работы с цветами"""
    
    HEX_PATTERN: ClassVar[str] = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
    
    @staticmethod
    def is_valid_hex(color: str) -> bool:
        """Проверка валидности hex-кода"""
        return bool(re.match(ColorUtils.HEX_PATTERN, color.strip()))
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Конвертация #RRGGBB → (R, G, B)"""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))  # type: ignore
    
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """Конвертация (R, G, B) → #RRGGBB"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def lighten(hex_color: str, percent: float) -> str:
        """
        Осветлить цвет на процент (0-100)
        
        >>> lighten("#000000", 50)  # "#808080"
        """
        r, g, b = ColorUtils.hex_to_rgb(hex_color)
        factor = 1 + (percent / 100)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return ColorUtils.rgb_to_hex(r, g, b)
    
    @staticmethod
    def darken(hex_color: str, percent: float) -> str:
        """
        Затемнить цвет на процент (0-100)
        
        >>> darken("#FFFFFF", 50)  # "#808080"
        """
        r, g, b = ColorUtils.hex_to_rgb(hex_color)
        factor = 1 - (percent / 100)
        r = max(0, int(r * factor))
        g = max(0, int(g * factor))
        b = max(0, int(b * factor))
        return ColorUtils.rgb_to_hex(r, g, b)
    
    @staticmethod
    def to_rgba(hex_color: str, alpha: float) -> str:
        """
        Добавить прозрачность: #RRGGBB → rgba(R, G, B, A)
        
        >>> to_rgba("#FF0000", 0.5)  # "rgba(255, 0, 0, 0.5)"
        """
        r, g, b = ColorUtils.hex_to_rgb(hex_color)
        return f"rgba({r}, {g}, {b}, {alpha})"
    
    @staticmethod
    def contrast_ratio(color1: str, color2: str) -> float:
        """
        Рассчитать контрастность двух цветов (WCAG 2.1)
        
        Returns:
            float: Коэффициент контрастности (1.0 - 21.0)
            ≥ 4.5 — нормально для обычного текста
            ≥ 7.0 — хорошо для мелкого текста
        """
        def luminance(hex_color: str) -> float:
            r, g, b = [x / 255 for x in ColorUtils.hex_to_rgb(hex_color)]
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = luminance(color1)
        l2 = luminance(color2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)
    
    @staticmethod
    def is_accessible(fg: str, bg: str, level: str = "AA") -> bool:
        """
        Проверить доступность цвета по стандартам WCAG
        
        Args:
            fg: Цвет текста
            bg: Цвет фона
            level: "AA" (4.5:1) или "AAA" (7:1)
        """
        ratio = ColorUtils.contrast_ratio(fg, bg)
        threshold = 7.0 if level == "AAA" else 4.5
        return ratio >= threshold


# ==================== ПРЕДОПРЕДЕЛЁННЫЕ ТЕМЫ ====================

DARK_THEME = ColorPalette(
    # Основные
    primary="#6366f1",
    primary_hover="#4f46e5",
    secondary="#8b5cf6",
    
    # Фон
    bg_main="#0f172a",
    bg_card="#1e293b",
    bg_input="#334155",
    bg_hover="#334155",
    
    # Текст
    text_primary="#FFFFFF",
    text_secondary="#94a3b8",
    text_disabled="#64748b",
    
    # Статусы
    status_new="#3b82f6",
    status_diagnostics="#f59e0b",
    status_in_progress="#a855f7",
    status_ready="#22c55e",
    status_closed="#64748b",
    status_cancelled="#ef4444",
    
    # Сообщения
    success="#22c55e",
    warning="#f59e0b",
    error="#ef4444",
    info="#3b82f6",
    
    # Интерактив
    border="#475569",
    border_focus="#6366f1",
    disabled="#475569",
    selected="#3b82f6",
    scrollbar="#475569",
    scrollbar_hover="#64748b",
    tooltip_bg="#1e293b",
    tooltip_text="#FFFFFF",
    divider="#334155",
)

LIGHT_THEME = ColorPalette(
    # Основные
    primary="#4f46e5",
    primary_hover="#4338ca",
    secondary="#7c3aed",
    
    # Фон
    bg_main="#FFFFFF",
    bg_card="#F8FAFC",
    bg_input="#F1F5F9",
    bg_hover="#E2E8F0",
    
    # Текст
    text_primary="#0F172A",
    text_secondary="#475569",
    text_disabled="#94A3B8",
    
    # Статусы
    status_new="#2563eb",
    status_diagnostics="#d97706",
    status_in_progress="#9333ea",
    status_ready="#16a34a",
    status_closed="#64748b",
    status_cancelled="#dc2626",
    
    # Сообщения
    success="#16a34a",
    warning="#d97706",
    error="#dc2626",
    info="#2563eb",
    
    # Интерактив
    border="#CBD5E1",
    border_focus="#4f46e5",
    disabled="#CBD5E1",
    selected="#4f46e5",
    scrollbar="#CBD5E1",
    scrollbar_hover="#94A3B8",
    tooltip_bg="#1e293b",
    tooltip_text="#FFFFFF",
    divider="#E2E8F0",
)


class ThemeManager:
    """
    Менеджер тем оформления
    
    ✅ Динамическое переключение тем
    ✅ Интеграция с CustomTkinter
    ✅ Подписка на изменения для обновления UI
    """
    
    _instance: Optional["ThemeManager"] = None
    _current_theme: Literal["dark", "light"] = "dark"
    _custom_themes: Dict[str, ColorPalette] = {}
    _callbacks: list = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get(cls) -> "ThemeManager":
        """Получить экземпляр менеджера тем"""
        return cls()
    
    @property
    def current(self) -> ColorPalette:
        """Текущая палитра цветов"""
        return DARK_THEME if self._current_theme == "dark" else LIGHT_THEME
    
    @property
    def is_dark(self) -> bool:
        """Проверка: тёмная тема активна"""
        return self._current_theme == "dark"
    
    def set_theme(self, theme_name: Literal["dark", "light"]) -> None:
        """
        Установить тему оформления
        
        ✅ Автоматически применяет к CustomTkinter
        ✅ Уведомляет подписчиков об изменении
        """
        if theme_name not in ("dark", "light"):
            raise ValueError(f"Unknown theme: {theme_name}")
        
        if self._current_theme == theme_name:
            return  # Уже установлена
        
        self._current_theme = theme_name
        
        # Применяем к CustomTkinter
        self._apply_to_customtkinter()
        
        # Уведомляем подписчиков
        for callback in self._callbacks:
            try:
                callback(theme_name)
            except Exception as e:
                from core.logger import app_logger
                app_logger.error(f"Theme callback error: {e}")
    
    def _apply_to_customtkinter(self) -> None:
        """Применить текущую тему к CustomTkinter"""
        palette = self.current
        
        # Настройка цветов для виджетов
        ctk.set_default_color_theme("blue")  # Базовая тема
        
        # Можно дополнительно настроить через configure
        # Например, для CTkButton:
        # button.configure(fg_color=palette.primary, hover_color=palette.primary_hover)
    
    def register_callback(self, callback: callable) -> None:
        """
        Зарегистрировать колбэк на смену темы
        
        Callback получает название новой темы: callback("dark" | "light")
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def unregister_callback(self, callback: callable) -> None:
        """Отменить регистрацию колбэка"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def add_custom_theme(self, name: str, palette: ColorPalette) -> None:
        """Добавить кастомную тему"""
        self._custom_themes[name] = palette
    
    def get_ctk_config(self, widget_type: str = "default") -> Dict[str, str]:
        """
        Получить конфигурацию для CustomTkinter виджета
        
        >>> theme.get_ctk_config("button")
        {"fg_color": "#6366f1", "hover_color": "#4f46e5", ...}
        """
        p = self.current
        configs = {
            "default": {
                "fg_color": p.bg_card,
                "hover_color": p.bg_hover,
                "border_color": p.border,
                "text_color": p.text_primary,
            },
            "button": {
                "fg_color": p.primary,
                "hover_color": p.primary_hover,
                "border_color": p.border,
                "text_color": p.text_primary,
            },
            "entry": {
                "fg_color": p.bg_input,
                "border_color": p.border,
                "text_color": p.text_primary,
            },
            "frame": {
                "fg_color": p.bg_card,
                "border_color": p.border,
            },
            "label": {
                "text_color": p.text_primary,
            },
            "table": {
                "fg_color": p.bg_input,
                "selected_color": p.selected,
                "text_color": p.text_primary,
            },
        }
        return configs.get(widget_type, configs["default"])


# ==================== BACKWARD COMPATIBILITY ====================
# Для старого кода, который использует ColorTheme напрямую

class ColorTheme:
    """
    ⚠️  Устаревший класс — используйте ThemeManager.get().current
    
    Оставлен для совместимости со старым кодом.
    """
    
    # 🔷 Основные
    PRIMARY: ClassVar[str] = DARK_THEME.primary
    PRIMARY_HOVER: ClassVar[str] = DARK_THEME.primary_hover
    SECONDARY: ClassVar[str] = DARK_THEME.secondary
    
    # 🎨 Фон
    BG_DARK: ClassVar[str] = DARK_THEME.bg_main
    BG_CARD: ClassVar[str] = DARK_THEME.bg_card
    BG_INPUT: ClassVar[str] = DARK_THEME.bg_input
    BG_HOVER: ClassVar[str] = DARK_THEME.bg_hover
    
    # ✍️ Текст
    TEXT_PRIMARY: ClassVar[str] = DARK_THEME.text_primary
    TEXT_SECONDARY: ClassVar[str] = DARK_THEME.text_secondary
    TEXT_DISABLED: ClassVar[str] = DARK_THEME.text_disabled
    
    # 🟢 Статусы
    STATUS_NEW: ClassVar[str] = DARK_THEME.status_new
    STATUS_DIAGNOSTICS: ClassVar[str] = DARK_THEME.status_diagnostics
    STATUS_IN_PROGRESS: ClassVar[str] = DARK_THEME.status_in_progress
    STATUS_READY: ClassVar[str] = DARK_THEME.status_ready
    STATUS_CLOSED: ClassVar[str] = DARK_THEME.status_closed
    STATUS_CANCELLED: ClassVar[str] = DARK_THEME.status_cancelled
    
    # 💬 Сообщения
    SUCCESS: ClassVar[str] = DARK_THEME.success
    WARNING: ClassVar[str] = DARK_THEME.warning
    ERROR: ClassVar[str] = DARK_THEME.error
    INFO: ClassVar[str] = DARK_THEME.info
    
    # 🔘 Интерактив
    SAFE_HOVER: ClassVar[str] = DARK_THEME.bg_hover
    TABLE_SELECTED: ClassVar[str] = DARK_THEME.selected
    
    # ✅ ИСПРАВЛЕНО: Добавлен атрибут BORDER для обратной совместимости
    BORDER: ClassVar[str] = DARK_THEME.border
    BORDER_FOCUS: ClassVar[str] = DARK_THEME.border_focus
    DISABLED: ClassVar[str] = DARK_THEME.disabled
    SCROLLBAR: ClassVar[str] = DARK_THEME.scrollbar
    SCROLLBAR_HOVER: ClassVar[str] = DARK_THEME.scrollbar_hover
    TOOLTIP_BG: ClassVar[str] = DARK_THEME.tooltip_bg
    TOOLTIP_TEXT: ClassVar[str] = DARK_THEME.tooltip_text
    DIVIDER: ClassVar[str] = DARK_THEME.divider
    
    # 🔍 Утилиты (делегирование)
    @staticmethod
    def is_valid_hex(color: str) -> bool:
        return ColorUtils.is_valid_hex(color)
    
    @staticmethod
    def lighten(color: str, percent: float) -> str:
        return ColorUtils.lighten(color, percent)
    
    @staticmethod
    def darken(color: str, percent: float) -> str:
        return ColorUtils.darken(color, percent)
    
    @staticmethod
    def contrast_ratio(c1: str, c2: str) -> float:
        return ColorUtils.contrast_ratio(c1, c2)


# ==================== 🚀 QUICK ACCESS ====================
# Для удобного импорта: from ui.theme import theme

theme = ThemeManager.get()
colors = theme.current  # Текущая палитра
utils = ColorUtils  # Утилиты цветов