# ui/main_window/main_window.py
"""
Главное окно приложения после авторизации для PC Repair CRM Pro

✅ ИСПРАВЛЕНО: Единый mainloop, корректное управление окнами, обработка ошибок
✅ УЛУЧШЕНО: Валидация, центрирование, минимальные размеры, обработка закрытия
✅ СОВМЕСТИМО: Работа как фрейм внутри App, не как отдельное окно
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from core.logger import app_logger
from ui.theme import ColorTheme, theme as theme_manager
from translations import get_text, set_language

# ✅ ИМПОРТЫ ВИДЖЕТОВ И КОМПОНЕНТОВ
from ui.main_window.menu_bar import MenuBar  # ← ДОБАВЛЕНО: Меню приложения


class MainWindow(ctk.CTkFrame):
    """
    Главное окно приложения — работает как фрейм внутри App
    
    ✅ НЕ создаёт новый mainloop() — использует цикл событий родительского App
    ✅ Корректное переключение между видами без пересоздания окна
    ✅ Обработка закрытия, сохранение состояния
    ✅ Динамическая загрузка видов с обработкой ошибок
    """
    
    # Карта доступных видов для валидации
    AVAILABLE_VIEWS: Dict[str, Callable] = {
        "dashboard": "ui.views.dashboard.DashboardView",
        "reference": "ui.views.reference.ReferenceView",
        "documents": "ui.views.documents.DocumentsView",
        "settings": "ui.views.settings.SettingsView",
        "users": "ui.views.users_view.UsersView",
        "reports": "ui.views.reports_view.ReportsView",
    }
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,  # ✅ Родитель — App, а не новый CTk
        user: Dict[str, Any],
        on_logout: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        # ✅ Валидация входных данных
        if not isinstance(user, dict):
            app_logger.warning("⚠️ MainWindow: user must be a dict")
            user = {"username": "unknown", "role": "user", "lang": "ru"}
        
        self.user = user
        self.lang = user.get("lang", "ru") or "ru"
        self.on_logout_callback = on_logout
        
        # Текущий вид
        self.current_view: Optional[str] = None
        self.current_view_instance: Optional[ctk.CTkFrame] = None
        
        # 🔧 Настройка интерфейса
        self._setup_window()
        self._build_interface()
        
        app_logger.info(f"🖥️ MainWindow loaded for user: {user.get('username')}")
    
    def _setup_window(self) -> None:
        """Настройка параметров окна (если родитель — CTk)"""
        # Если родитель — CTk (главное окно), настраиваем его
        if isinstance(self.master, ctk.CTk):
            root = self.master
            root.title("PC Repair CRM Pro")
            root.geometry("1400x900")
            root.minsize(1024, 768)  # ✅ Минимальный размер
            root.configure(fg_color=ColorTheme.BG_DARK)
            
            # 🖼️ Иконка приложения
            self._set_app_icon(root)
            
            # 🔐 Обработчик закрытия окна
            root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # 🎯 Центрирование окна
            root.after(100, self._center_window)
    
    def _set_app_icon(self, root: ctk.CTk) -> None:
        """Установить иконку приложения"""
        icon_paths = [
            Path(__file__).parent.parent / "assets" / "app_icon.ico",
            Path(__file__).parent / "assets" / "app_icon.ico",
        ]
        
        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    root.iconbitmap(str(icon_path))  # Windows
                    return
                except Exception:
                    pass  # macOS/Linux используют другие методы
    
    def _center_window(self) -> None:
        """Центрировать окно на экране"""
        if not isinstance(self.master, ctk.CTk):
            return
            
        root = self.master
        root.update_idletasks()
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        window_width = root.winfo_width()
        window_height = root.winfo_height()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        root.geometry(f"+{x}+{y}")
    
    def _build_interface(self) -> None:
        """Построение интерфейса"""
        # Очищаем контент
        for widget in self.winfo_children():
            widget.destroy()
        
        # Верхняя панель
        self.menu_bar = MenuBar(
            self,
            self.user,
            self.lang,
            on_logout=self.logout,
            on_language_change=self.on_language_change,
        )
        self.menu_bar.pack(fill="x", padx=15, pady=(15, 0))
        
        # Основная область
        self.content_frame = ctk.CTkFrame(
            self, fg_color=ColorTheme.BG_CARD, corner_radius=16
        )
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Показываем дашборд по умолчанию
        self.show_view("dashboard")
    
    def show_view(self, view_name: str) -> None:
        """
        Показать указанный вид с валидацией и обработкой ошибок
        
        ✅ Динамический импорт с кэшированием
        ✅ Обработка ошибок импорта
        ✅ Очистка предыдущего вида
        """
        # ✅ Валидация имени вида
        if view_name not in self.AVAILABLE_VIEWS:
            app_logger.warning(f"⚠️ Unknown view: {view_name}")
            # Показываем заглушку
            self._show_unknown_view(view_name)
            return
        
        # ✅ Очищаем предыдущий вид
        if self.current_view_instance and self.current_view_instance.winfo_exists():
            try:
                self.current_view_instance.destroy()
            except Exception as e:
                app_logger.warning(f"⚠️ Error destroying previous view: {e}")
        
        # ✅ Динамический импорт вида
        try:
            module_path, class_name = self.AVAILABLE_VIEWS[view_name].rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            ViewClass = getattr(module, class_name)
            
            # Создаём вид
            view = ViewClass(
                parent=self.content_frame,
                lang=self.lang,
                on_navigate=self.show_view
            )
            view.pack(fill="both", expand=True)
            
            self.current_view = view_name
            self.current_view_instance = view
            
            app_logger.info(f"📄 Showing view: {view_name}")
            
        except ImportError as e:
            app_logger.error(f"❌ Could not import view {view_name}: {e}")
            self._show_import_error(view_name, str(e))
        except AttributeError as e:
            app_logger.error(f"❌ View class not found in {view_name}: {e}")
            self._show_import_error(view_name, str(e))
        except Exception as e:
            app_logger.exception(f"❌ Error loading view {view_name}: {e}")
            self._show_error_view(str(e))
    
    def _show_unknown_view(self, view_name: str) -> None:
        """Показать заглушку для неизвестного вида"""
        ctk.CTkLabel(
            self.content_frame,
            text=f"❌ Вид '{view_name}' не найден",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.ERROR
        ).pack(expand=True, pady=50)
        
        ctk.CTkButton(
            self.content_frame,
            text="⬅ Вернуться на главную",
            command=lambda: self.show_view("dashboard"),
            fg_color=ColorTheme.PRIMARY,
            width=200
        ).pack(pady=10)
    
    def _show_import_error(self, view_name: str, error: str) -> None:
        """Показать ошибку импорта вида"""
        ctk.CTkLabel(
            self.content_frame,
            text=f"❌ Ошибка загрузки '{view_name}'",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ColorTheme.ERROR
        ).pack(expand=True, pady=20)
        
        ctk.CTkLabel(
            self.content_frame,
            text=error,
            text_color=ColorTheme.TEXT_SECONDARY,
            justify="center"
        ).pack(pady=10)
        
        ctk.CTkButton(
            self.content_frame,
            text="🔄 Попробовать ещё раз",
            command=lambda: self.show_view(view_name),
            fg_color=ColorTheme.INFO,
            width=200
        ).pack(pady=10)
        
        ctk.CTkButton(
            self.content_frame,
            text="⬅ На главную",
            command=lambda: self.show_view("dashboard"),
            fg_color=ColorTheme.PRIMARY,
            width=200
        ).pack(pady=10)
    
    def _show_error_view(self, error: str) -> None:
        """Показать общий экран ошибки"""
        ctk.CTkLabel(
            self.content_frame,
            text="❌ Произошла ошибка",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ColorTheme.ERROR
        ).pack(expand=True, pady=20)
        
        ctk.CTkLabel(
            self.content_frame,
            text=error,
            text_color=ColorTheme.TEXT_SECONDARY,
            justify="center",
            wraplength=400
        ).pack(pady=10)
        
        ctk.CTkButton(
            self.content_frame,
            text="🔄 Обновить",
            command=lambda: self.show_view(self.current_view or "dashboard"),
            fg_color=ColorTheme.INFO,
            width=200
        ).pack(pady=10)
    
    def on_language_change(self, new_lang: str) -> None:
        """
        Смена языка интерфейса
        
        ✅ Обновляет язык и перестраивает интерфейс
        ✅ Сохраняет текущий вид
        ✅ Обновляет MenuBar
        """
        if new_lang not in ("ru", "en"):
            app_logger.warning(f"⚠️ Unsupported language: {new_lang}")
            return
        
        # ✅ Сохраняем текущий вид для восстановления
        previous_view = self.current_view
        
        # ✅ Обновляем язык в системе переводов
        set_language(new_lang)
        self.lang = new_lang
        
        app_logger.info(f"🌍 Language changed to: {self.lang}")
        
        # ✅ Обновляем MenuBar
        if hasattr(self, "menu_bar") and self.menu_bar.winfo_exists():
            self.menu_bar.update_language(new_lang)
        
        # ✅ Перестраиваем интерфейс (можно оптимизировать в будущем)
        # Для сейчас — простое пересоздание надёжнее
        self._build_interface()
        
        # ✅ Восстанавливаем вид если возможно
        if previous_view and previous_view in self.AVAILABLE_VIEWS:
            self.after(50, lambda: self.show_view(previous_view))
    
    def logout(self) -> None:
        """
        Выход из системы
        
        ✅ Логирует выход
        ✅ Вызывает колбэк для возврата к экрану входа
        ✅ Не уничтожает окно — это делает родительский App
        """
        username = self.user.get("username") or "unknown"
        app_logger.info(f"👤 Пользователь {username} нажал 'Выход'")
        
        # ✅ Вызываем колбэк (если есть)
        if self.on_logout_callback:
            try:
                self.on_logout_callback()
            except Exception as e:
                app_logger.error(f"❌ Error in logout callback: {e}")
                # Продолжаем выход даже если колбэк упал
        
        # ✅ Не уничтожаем окно здесь — это делает App
        # Мы просто сигнализируем о желании выйти
    
    def _on_closing(self) -> None:
        """
        Обработчик закрытия окна (крестик)
        
        ✅ Логирует закрытие
        ✅ Вызывает logout() для корректного завершения
        """
        app_logger.info("🔐 MainWindow closing requested")
        self.logout()
        # Дальнейшее закрытие обрабатывается в App._on_closing()
    
    def refresh(self) -> None:
        """
        Обновить текущий вид
        
        ✅ Полезно после изменений данных в другом месте
        ✅ Перезагружает текущий вид без смены языка
        """
        if self.current_view:
            current_lang = self.lang
            self.show_view(self.current_view)
            # Язык восстановится в show_view через параметры вида
    
    def update_user_info(self, user: Dict[str, Any]) -> None:
        """
        Обновить информацию о пользователе
        
        ✅ Обновляет MenuBar
        ✅ Сохраняет новый user dict
        """
        if not isinstance(user, dict):
            return
        
        self.user = user
        
        if hasattr(self, "menu_bar") and self.menu_bar.winfo_exists():
            self.menu_bar.update_user_info(user)
    
    def get_current_view(self) -> Optional[str]:
        """Получить имя текущего вида"""
        return self.current_view
    
    def destroy(self) -> None:
        """Корректное уничтожение окна"""
        # ✅ Уничтожаем текущий вид
        if self.current_view_instance and self.current_view_instance.winfo_exists():
            try:
                self.current_view_instance.destroy()
            except Exception:
                pass
        
        # ✅ Уничтожаем menu_bar
        if hasattr(self, "menu_bar") and self.menu_bar.winfo_exists():
            try:
                self.menu_bar.destroy()
            except Exception:
                pass
        
        # ✅ Стандартное уничтожение
        super().destroy()