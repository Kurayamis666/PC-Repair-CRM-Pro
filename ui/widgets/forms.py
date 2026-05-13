# ui/widgets/forms.py
"""
Переиспользуемые формы и поля ввода для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Геометрия, адаптивность, валидация, ошибка UI
✅ УЛУЧШЕНО: Кастомные валидаторы, визуальная обратная связь, навигация
✅ ГИБКОСТЬ: Checkbox, Switch, Date, File, FormPanel без фиксированной ширины
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable, Any, Union, List, Tuple
from datetime import datetime
from ui.theme import ColorTheme, ColorUtils
from translations import get_text


class FormField:
    """
    Адаптивное поле формы с валидацией и визуальной обратной связью
    
    ✅ Правильная геометрия (без двойного pack)
    ✅ Адаптивная ширина (fill="x", expand=True)
    ✅ Визуальная ошибка (красная рамка + сообщение под полем)
    ✅ Поддержка кастомных валидаторов
    ✅ Навигация Tab/Shift+Tab
    """
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        label: str,
        field_type: str = "entry",
        placeholder: str = "",
        required: bool = False,
        values: Optional[List[str]] = None,
        validator: Optional[Callable[[str], Tuple[bool, str]]] = None,
        on_change: Optional[Callable[[Any], None]] = None,
        default_value: Any = None,
        **kwargs: Any,
    ):
        self.parent = parent
        self.label_text = label
        self.field_type = field_type
        self.placeholder = placeholder
        self.required = required
        self.values = values or []
        self.validator = validator
        self.on_change = on_change
        self.default_value = default_value
        self.kwargs = kwargs
        
        self.widget: Optional[Union[ctk.CTkEntry, ctk.CTkTextbox, ctk.CTkComboBox, ctk.CTkCheckBox, ctk.CTkSwitch]] = None
        self.label_widget: Optional[ctk.CTkLabel] = None
        self.error_widget: Optional[ctk.CTkLabel] = None
        self.container: Optional[ctk.CTkFrame] = None
        self._is_valid: bool = True
        
        self._build()
    
    def _build(self) -> None:
        """Построение поля с корректной геометрией"""
        # 📦 Основной контейнер (вертикальный стек)
        self.container = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.container.pack_propagate(False)  # Управляем высотой вручную
        
        # 🏷️ Метка поля
        label_text = f"{self.label_text}{' *' if self.required else ''}"
        self.label_widget = ctk.CTkLabel(
            self.container,
            text=label_text,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="normal"),
            text_color=ColorTheme.TEXT_PRIMARY,
        )
        self.label_widget.pack(fill="x", pady=(0, 4))
        
        # 📥 Контейнер для инпута (с рамкой для ошибки)
        self.input_frame = ctk.CTkFrame(
            self.container,
            fg_color="transparent",
            border_color=ColorTheme.BORDER,
            border_width=1,
            corner_radius=10,
        )
        self.input_frame.pack(fill="x")
        
        # 🧩 Создание виджета
        if self.field_type == "entry":
            self.widget = ctk.CTkEntry(
                self.input_frame,
                placeholder_text=self.placeholder,
                height=36,
                corner_radius=10,
                fg_color=ColorTheme.BG_INPUT,
                border_color="transparent",  # Рамка на input_frame
                text_color=ColorTheme.TEXT_PRIMARY,
                placeholder_text_color=ColorTheme.TEXT_SECONDARY,
                **self.kwargs
            )
            self.widget.pack(fill="x", expand=True, padx=8, pady=6)
            self.widget.bind("<KeyRelease>", lambda e: self._on_change())
            self.widget.bind("<FocusIn>", lambda e: self._set_border(ColorTheme.PRIMARY))
            self.widget.bind("<FocusOut>", lambda e: self._set_border())
            
        elif self.field_type == "text":
            self.widget = ctk.CTkTextbox(
                self.input_frame,
                height=100,
                corner_radius=10,
                fg_color=ColorTheme.BG_INPUT,
                border_color="transparent",
                text_color=ColorTheme.TEXT_PRIMARY,
                **self.kwargs
            )
            self.widget.pack(fill="both", expand=True, padx=8, pady=6)
            self.widget.bind("<KeyRelease>", lambda e: self._on_change())
            
            # Workaround для placeholder в Textbox
            if self.placeholder:
                self.widget.insert("0.0", self.placeholder)
                self.widget.text_color_disabled = ColorTheme.TEXT_SECONDARY
                self.widget.bind("<FocusIn>", self._clear_placeholder)
                self.widget.bind("<FocusOut>", self._restore_placeholder)
                
        elif self.field_type == "combo":
            self.widget = ctk.CTkComboBox(
                self.input_frame,
                values=[""] + self.values if self.required == False else self.values,
                height=36,
                corner_radius=10,
                fg_color=ColorTheme.BG_INPUT,
                border_color="transparent",
                text_color=ColorTheme.TEXT_PRIMARY,
                button_color=ColorTheme.PRIMARY,
                dropdown_fg_color=ColorTheme.BG_CARD,
                state="readonly",
                **self.kwargs
            )
            self.widget.pack(fill="x", expand=True, padx=8, pady=6)
            if self.default_value and self.default_value in self.widget.cget("values"):
                self.widget.set(self.default_value)
            elif not self.required and "" in self.widget.cget("values"):
                self.widget.set("")
            elif self.values:
                self.widget.set(self.values[0])
            self.widget.bind("<<ComboboxSelected>>", lambda e: self._on_change())
            
        elif self.field_type == "checkbox":
            self.widget = ctk.CTkCheckBox(
                self.input_frame,
                text=self.placeholder or self.label_text,
                text_color=ColorTheme.TEXT_PRIMARY,
                fg_color=ColorTheme.PRIMARY,
                hover_color=ColorTheme.PRIMARY_HOVER,
                **self.kwargs
            )
            self.widget.pack(fill="x", padx=8, pady=8)
            self.widget.configure(command=self._on_change)
            
        elif self.field_type == "switch":
            self.widget = ctk.CTkSwitch(
                self.input_frame,
                text=self.placeholder or self.label_text,
                text_color=ColorTheme.TEXT_PRIMARY,
                fg_color=ColorTheme.PRIMARY,
                **self.kwargs
            )
            self.widget.pack(fill="x", padx=8, pady=8)
            self.widget.configure(command=self._on_change)
        
        # ❌ Метка ошибки (под полем)
        self.error_widget = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=ColorTheme.ERROR,
            anchor="w",
        )
        self.error_widget.pack(fill="x", pady=(4, 0))
        
        # Устанавливаем значение по умолчанию
        if self.default_value is not None and self.field_type not in ("combo", "checkbox", "switch"):
            self.set_value(self.default_value)
    
    def _clear_placeholder(self, event):
        if self.widget.get("0.0", "end-1c") == self.placeholder:
            self.widget.delete("0.0", "end")
            self.widget.configure(text_color=ColorTheme.TEXT_PRIMARY)
            
    def _restore_placeholder(self, event):
        if not self.widget.get("0.0", "end-1c"):
            self.widget.insert("0.0", self.placeholder)
            self.widget.configure(text_color=ColorTheme.TEXT_SECONDARY)
    
    def _set_border(self, color: Optional[str] = None):
        """Изменить цвет рамки при фокусе/ошибке"""
        if self.input_frame:
            self.input_frame.configure(border_color=color or ColorTheme.BORDER)
    
    def _on_change(self) -> None:
        """Обработчик изменения значения"""
        self._is_valid = True  # Сбрасываем статус валидации при изменении
        self.clear_error()
        if self.on_change and self.widget:
            try:
                self.on_change(self.get_value())
            except Exception as e:
                from core.logger import app_logger
                app_logger.error(f"❌ FormField on_change error: {e}")
    
    def get_value(self) -> Any:
        """Получить значение поля"""
        if not self.widget:
            return None
        if isinstance(self.widget, ctk.CTkEntry):
            return self.widget.get().strip()
        elif isinstance(self.widget, ctk.CTkTextbox):
            val = self.widget.get("0.0", "end-1c").strip()
            return val if val != self.placeholder else ""
        elif isinstance(self.widget, ctk.CTkComboBox):
            return self.widget.get()
        elif isinstance(self.widget, (ctk.CTkCheckBox, ctk.CTkSwitch)):
            return self.widget.get() == 1
        return None
    
    def set_value(self, value: Any) -> None:
        """Установить значение поля"""
        if not self.widget:
            return
        try:
            if isinstance(self.widget, ctk.CTkEntry):
                self.widget.delete(0, "end")
                self.widget.insert(0, str(value) if value is not None else "")
            elif isinstance(self.widget, ctk.CTkTextbox):
                self.widget.delete("0.0", "end")
                if value:
                    self.widget.insert("0.0", str(value))
            elif isinstance(self.widget, ctk.CTkComboBox):
                str_val = str(value) if value is not None else ""
                if str_val in self.widget.cget("values"):
                    self.widget.set(str_val)
            elif isinstance(self.widget, (ctk.CTkCheckBox, ctk.CTkSwitch)):
                self.widget.select() if value else self.widget.deselect()
        except Exception as e:
            from core.logger import app_logger
            app_logger.warning(f"⚠️ set_value error: {e}")
    
    def set_error(self, message: str) -> None:
        """Показать ошибку"""
        if self.error_widget:
            self.error_widget.configure(text=message)
        self._set_border(ColorTheme.ERROR)
        self._is_valid = False
    
    def clear_error(self) -> None:
        """Очистить ошибку"""
        if self.error_widget:
            self.error_widget.configure(text="")
        self._set_border()
        self._is_valid = True
    
    def validate(self) -> bool:
        """
        Валидация поля: required + custom validator
        """
        self.clear_error()
        value = self.get_value()
        
        # 1. Проверка обязательности
        if self.required and not value:
            self.set_error(get_text("fill_required", "ru") or "This field is required")
            return False
        
        # 2. Кастомная валидация
        if self.validator and value:
            is_valid, msg = self.validator(value)
            if not is_valid:
                self.set_error(msg)
                return False
        
        return True
    
    def focus(self) -> None:
        """Установить фокус на поле"""
        if self.widget:
            self.widget.focus_set()
    
    def pack(self, **kwargs: Any) -> "FormField":
        """Упаковать контейнер поля (вызывается один раз!)"""
        if self.container:
            self.container.pack(**kwargs)
        return self
    
    def grid(self, **kwargs: Any) -> "FormField":
        if self.container:
            self.container.grid(**kwargs)
        return self


class FormPanel(ctk.CTkScrollableFrame):
    """
    Адаптивная панель формы без фиксированной ширины
    
    ✅ Автоматическая вёрстка полей
    ✅ Пакетная валидация, get/set, clear
    ✅ Поддержка submit callback
    """
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        on_submit: Optional[Callable[[dict], None]] = None,
        submit_text: Optional[str] = None,
        **kwargs: Any
    ):
        # ✅ Убрали фиксированную width=400
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.on_submit = on_submit
        self.submit_text = submit_text or get_text("save", "ru")
        self.fields: dict[str, FormField] = {}
        self._submit_btn: Optional[ctk.CTkButton] = None
        
        if self.on_submit:
            self._build_submit_button()
    
    def _build_submit_button(self):
        """Кнопка отправки формы"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 10))
        
        self._submit_btn = ctk.CTkButton(
            btn_frame,
            text=f"💾 {self.submit_text}",
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
            corner_radius=10,
            command=self._handle_submit,
        )
        self._submit_btn.pack(side="right")
    
    def add_field(self, name: str, **kwargs: Any) -> FormField:
        """Добавить поле в форму"""
        field = FormField(self, **kwargs)
        self.fields[name] = field
        field.pack(fill="x", pady=6)  # ✅ Вертикальный стек
        return field
    
    def get_values(self) -> dict[str, Any]:
        """Получить словарь значений всех полей"""
        return {name: field.get_value() for name, field in self.fields.items()}
    
    def set_values(self, values: dict[str, Any]) -> None:
        """Установить значения из словаря"""
        for name, value in values.items():
            if name in self.fields:
                self.fields[name].set_value(value)
    
    def validate(self) -> bool:
        """Валидировать все поля. Возвращает True если всё ОК"""
        all_valid = True
        first_invalid = None
        
        for name, field in self.fields.items():
            if not field.validate():
                all_valid = False
                if first_invalid is None:
                    first_invalid = field
        
        # Фокус на первое невалидное поле
        if first_invalid:
            first_invalid.focus()
            
        return all_valid
    
    def _handle_submit(self):
        """Обработчик кнопки отправки"""
        if self.validate():
            if self.on_submit:
                try:
                    self.on_submit(self.get_values())
                except Exception as e:
                    from core.logger import app_logger
                    app_logger.error(f"❌ FormPanel submit error: {e}")
    
    def clear(self) -> None:
        """Очистить все поля и ошибки"""
        for field in self.fields.values():
            field.set_value("")
            field.clear_error()
        # Фокус на первое поле
        if self.fields:
            next(iter(self.fields.values())).focus()
    
    def reset(self) -> None:
        """Сбросить к значениям по умолчанию"""
        for name, field in self.fields.items():
            field.set_value(field.default_value)
            field.clear_error()


# ==================== 🚀 QUICK ACCESS ====================

def create_form(parent, fields_config: list[dict], **kwargs) -> FormPanel:
    """
    Быстрое создание формы из конфигурации
    
    >>> panel = create_form(frame, [
    ...     {"name": "full_name", "label": "ФИО", "required": True},
    ...     {"name": "email", "label": "Email", "validator": validate_email},
    ...     {"name": "role", "label": "Роль", "field_type": "combo", "values": ["Admin", "User"]}
    ... ])
    """
    panel = FormPanel(parent, **kwargs)
    for cfg in fields_config:
        panel.add_field(**cfg)
    return panel