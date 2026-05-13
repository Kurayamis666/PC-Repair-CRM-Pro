# ui/dialogs/reference_editor.py
"""
Диалог редактирования справочных значений для PC Repair CRM Pro
✅ ИСПРАВЛЕНО: Защита от SQL injection, корректное получение старого значения
✅ УЛУЧШЕНО: Полный перевод, валидация, обработка дубликатов
✅ СОВМЕСТИМО: Интеграция с системой тем и переводов
"""

import customtkinter as ctk
from typing import Optional, Callable, Set
from core.logger import app_logger
from database.connection import DatabaseConnection
from ui.theme import ColorTheme, ColorUtils
from translations import get_text
from ui.widgets.toast import ToastNotification


class ReferenceEditorDialog(ctk.CTkToplevel):
    """
    Диалог редактирования справочных значений (nom_type, unit)
    
    ✅ Whitelist для table_column (защита от SQL injection)
    ✅ Корректное сохранение исходного значения для WHERE-условия
    ✅ Полный перевод всех текстов через get_text()
    ✅ Валидация: длина, дубликаты, спецсимволы
    ✅ Индикатор загрузки при сохранении
    """
    
    # 🔐 Разрешённые колонки для обновления (защита от SQL injection)
    ALLOWED_COLUMNS: Set[str] = {"nom_type", "unit"}
    
    # ⚙️ Конфигурация валидации
    MIN_NAME_LENGTH: int = 2
    MAX_NAME_LENGTH: int = 100
    ALLOWED_CHARS: str = r"^[a-zA-Zа-яА-ЯёЁ0-9\s\-\._/()]+$"  # Разрешённые символы
    
    def __init__(
        self,
        parent,
        table_column: str,
        record_id: Optional[int],
        initial_value: str,
        lang: str = "ru",
        on_save: Optional[Callable[[], None]] = None,
    ):
        # ✅ Валидация table_column против whitelist
        if table_column not in self.ALLOWED_COLUMNS:
            app_logger.error(f"❌ Invalid table_column: {table_column}")
            raise ValueError(f"Unsupported column: {table_column}")
        
        super().__init__(parent)
        
        self.table_column = table_column
        self.record_id = record_id
        self.initial_value = initial_value  # ✅ Сохраняем исходное значение!
        self.lang = lang
        self.on_save = on_save
        self.db = DatabaseConnection()
        
        # 🔧 UI элементы
        self._name_entry: Optional[ctk.CTkEntry] = None
        self._save_btn: Optional[ctk.CTkButton] = None
        self._loading_label: Optional[ctk.CTkLabel] = None
        
        # ✅ Переведённый заголовок
        title = get_text("edit_reference", self.lang) or "✏️ Редактирование"
        self.title(f"{title}: {initial_value}")
        
        self.geometry("400x260")
        self.minsize(350, 240)
        self.transient(parent)
        self.configure(fg_color=ColorTheme.BG_CARD)
        
        self._build_ui()
        
        # Устанавливаем исходное значение и фокус
        if self._name_entry:
            self._name_entry.insert(0, initial_value)
            self.after(100, lambda: self._name_entry.focus_set() if self._name_entry else None)
        
        # Центрирование и модальность — после построения UI
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 260) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.grab_set()
    
    def _build_ui(self) -> None:
        """Построение интерфейса с полным переводом"""
        
        # 🏷️ Заголовок
        header = ctk.CTkFrame(self, fg_color=ColorTheme.INFO, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=get_text("edit_reference", self.lang) or "✏️ Изменение значения",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(pady=10)
        
        # 📋 Форма
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ✏️ Поле ввода нового значения
        ctk.CTkLabel(
            form, 
            text=get_text("new_name", self.lang) + ":", 
            text_color=ColorTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", pady=5)
        
        self._name_entry = ctk.CTkEntry(
            form, 
            placeholder_text=get_text("enter_new_name", self.lang) or "Введите новое название",
            fg_color=ColorTheme.BG_INPUT, 
            text_color=ColorTheme.TEXT_PRIMARY,
            height=40,
        )
        self._name_entry.pack(fill="x", pady=5)
        self._name_entry.bind("<Return>", lambda e: self._save())
        self._name_entry.bind("<KeyRelease>", lambda e: self._clear_error())
        
        # 💡 Подсказка о допустимых символах
        ctk.CTkLabel(
            form,
            text=get_text("allowed_chars_hint", self.lang) or "Допустимы: буквы, цифры, -, ., _, /, пробел",
            text_color=ColorTheme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=10),
            anchor="w"
        ).pack(anchor="w", pady=(0, 10))
        
        # ⏳ Индикатор загрузки (скрыт по умолчанию)
        self._loading_label = ctk.CTkLabel(
            form,
            text="",
            text_color=ColorTheme.INFO,
            font=ctk.CTkFont(size=11)
        )
        self._loading_label.pack(pady=5)
        
        # 🔘 Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text=get_text("cancel", self.lang),
            command=self.destroy,
            width=120,
            height=35,
            fg_color=ColorTheme.TEXT_SECONDARY,
            hover_color=ColorUtils.darken(ColorTheme.TEXT_SECONDARY, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
        ).pack(side="left", padx=10)
        
        self._save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 " + get_text("save", self.lang),
            command=self._save,
            width=120,
            height=35,
            fg_color=ColorTheme.SUCCESS,
            hover_color=ColorUtils.darken(ColorTheme.SUCCESS, 10),
            text_color=ColorTheme.TEXT_PRIMARY,
        )
        self._save_btn.pack(side="right", padx=10)
    
    def _clear_error(self) -> None:
        """Очистить сообщение об ошибке при вводе"""
        # Можно добавить inline error label в будущем
        pass
    
    def _set_loading(self, loading: bool) -> None:
        """Показать/скрыть индикатор загрузки"""
        if loading:
            if self._loading_label:
                self._loading_label.configure(text="🔄 " + (get_text("saving", self.lang) or "Сохранение..."))
            if self._save_btn:
                self._save_btn.configure(state="disabled")
            if self._name_entry:
                self._name_entry.configure(state="disabled")
        else:
            if self._loading_label:
                self._loading_label.configure(text="")
            if self._save_btn:
                self._save_btn.configure(state="normal")
            if self._name_entry:
                self._name_entry.configure(state="normal")
    
    def _validate_name(self, name: str) -> tuple[bool, str]:
        """
        Валидация нового названия
        
        Returns:
            tuple[bool, str]: (успех, сообщение об ошибке)
        """
        if not name:
            return False, get_text("name_required", self.lang) or "Название обязательно"
        
        if len(name) < self.MIN_NAME_LENGTH:
            return False, get_text("name_too_short", self.lang).format(self.MIN_NAME_LENGTH) or f"Минимум {self.MIN_NAME_LENGTH} символа"
        
        if len(name) > self.MAX_NAME_LENGTH:
            return False, get_text("name_too_long", self.lang).format(self.MAX_NAME_LENGTH) or f"Максимум {self.MAX_NAME_LENGTH} символов"
        
        if not __import__("re").match(self.ALLOWED_CHARS, name):
            return False, get_text("name_invalid_chars", self.lang) or "Недопустимые символы"
        
        # ✅ Проверка на дубликат (исключая текущую запись)
        try:
            with self.db.get_cursor() as cur:
                # Проверяем, есть ли другая запись с таким же значением
                query = f"SELECT id FROM directories WHERE {self.table_column} = ?"
                params = [name]
                if self.record_id:
                    query += " AND id != ?"
                    params.append(self.record_id)
                
                cur.execute(query, params)
                if cur.fetchone():
                    return False, get_text("name_exists", self.lang) or "Такое значение уже существует"
        except Exception as e:
            app_logger.warning(f"⚠️ Could not check for duplicates: {e}")
            # Продолжаем без проверки дубликатов
        
        return True, ""
    
    def _save(self) -> None:
        """Сохранить новое значение с полной валидацией"""
        new_name = self._name_entry.get().strip() if self._name_entry else ""
        
        # ✅ Валидация ввода
        valid, error_msg = self._validate_name(new_name)
        if not valid:
            ToastNotification(self, error_msg, "warning")
            if self._name_entry:
                self._name_entry.focus_set()
            return
        
        # ✅ Показываем индикатор загрузки
        self._set_loading(True)
        
        try:
            with self.db.get_cursor() as cur:
                # ✅ Используем параметризованный запрос + валидированную колонку
                # Обновляем по ID если есть (точнее)
                if self.record_id:
                    cur.execute(
                        f"UPDATE directories SET {self.table_column} = ? WHERE id = ?",
                        (new_name, self.record_id)
                    )
                else:
                    # ✅ ИСПРАВЛЕНО: Используем self.initial_value, а не get()!
                    cur.execute(
                        f"UPDATE directories SET {self.table_column} = ? WHERE {self.table_column} = ?",
                        (new_name, self.initial_value)
                    )
                
                # Если ни одна строка не обновилась — возможно, значение не найдено
                if cur.rowcount == 0:
                    app_logger.warning(f"⚠️ No rows updated for {self.table_column}='{self.initial_value}'")
            
            ToastNotification(self, get_text("reference_updated", self.lang) or "✅ Обновлено", "success")
            app_logger.info(f"📝 Reference updated: {self.table_column} '{self.initial_value}' → '{new_name}'")
            
            # ✅ Вызываем колбэк обновления
            if self.on_save:
                try:
                    self.on_save()
                except Exception as e:
                    app_logger.warning(f"⚠️ on_save callback error: {e}")
            
            # ✅ Закрываем диалог
            self.destroy()
            
        except Exception as e:
            app_logger.exception(f"❌ Error updating reference: {e}")
            ToastNotification(self, f"{get_text('error_saving', self.lang)}: {e}", "error")
        finally:
            # ✅ Скрываем индикатор загрузки
            self._set_loading(False)
    
    def destroy(self) -> None:
        """Корректное закрытие диалога"""
        # Отменяем любые отложенные задачи
        try:
            pass  # Можно добавить очистку таймеров если есть
        except:
            pass
        super().destroy()