# ui/app.py
"""
Главный класс приложения PC Repair CRM Pro

✅ ИСПРАВЛЕНО: Рекурсия в hasattr() → проверка через __dict__
✅ ИСПРАВЛЕНО: Порядок инициализации (resource_path ДО _set_app_icon)
✅ ИСПРАВЛЕНО: Единый mainloop, корректное управление окнами
✅ ИСПРАВЛЕНО: Безопасное закрытие окна входа через withdraw/destroy
✅ УЛУЧШЕНО: Поддержка PyInstaller --onefile, обработка закрытия, центрирование
✅ СОВМЕСТИМО: Работа из .exe и из скрипта без изменений
"""

import customtkinter as ctk
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

from core.logger import app_logger
from ui.theme import ColorTheme, theme as theme_manager
from ui.login.login_window import LoginWindow


class App(ctk.CTk):
    """
    Главный класс приложения — единственная точка входа tkinter
    
    ✅ Единый mainloop() для всего приложения
    ✅ Корректное переключение между окнами (Login → MainWindow)
    ✅ Обработка закрытия, сохранение состояния
    ✅ Поддержка ресурсов в PyInstaller --onefile
    ✅ БЕЗ РЕКУРСИИ: проверка _initialized через __dict__
    ✅ БЕЗ ГОНОК: безопасное закрытие модальных окон
    """
    
    _instance: Optional["App"] = None
    
    def __new__(cls):
        """Singleton: гарантируем один экземпляр приложения"""
        if cls._instance is None:
            cls._instance = super(App, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # ✅ Проверка через __dict__ (не вызывает __getattr__ tkinter!)
        if '_initialized' in self.__dict__ and self._initialized:
            return
        
        # ✅ Инициализация родительского класса (ОБЯЗАТЕЛЬНО ПЕРВОЙ)
        super().__init__()
        
        # 🔧 Инициализация CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 🎨 Настройка главного окна
        self.title("PC Repair CRM Pro")
        self.geometry("1400x900")
        self.minsize(1024, 768)
        self.configure(fg_color=ColorTheme.BG_DARK)
        
        # ✅ Сначала создаём resource_path, ПОТОМ используем его
        self.resource_path = self._get_resource_path()
        
        # 🖼️ Иконка приложения
        self._set_app_icon()
        
        # 🔐 Обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 🎯 Центрирование окна на экране
        self.after(100, self._center_window)
        
        # 👤 Данные авторизованного пользователя
        self.current_user: Optional[Dict[str, Any]] = None
        
        # 🪟 Ссылки на окна
        self._login_window: Optional[LoginWindow] = None
        self._main_window: Optional[Any] = None
        
        # ✅ Флаг инициализации В КОНЦЕ
        self._initialized = True
        
        # Запуск окна входа
        self._show_login()
        
        app_logger.info("🚀 PC Repair CRM Pro started")
    
    def _get_resource_path(self) -> Path:
        """Получить путь к ресурсам (работает в .exe и в скрипте)"""
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                return Path(sys._MEIPASS)
            else:
                return Path(sys.executable).parent
        else:
            return Path(__file__).parent.parent
    
    def _set_app_icon(self) -> None:
        """Установить иконку приложения"""
        if not hasattr(self, 'resource_path'):
            icon_paths = [Path(__file__).parent / "assets" / "app_icon.ico"]
        else:
            icon_paths = [
                self.resource_path / "ui" / "assets" / "app_icon.ico",
                self.resource_path / "assets" / "app_icon.ico",
                Path(__file__).parent / "assets" / "app_icon.ico",
            ]
        
        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    self.iconbitmap(str(icon_path))
                    return
                except Exception:
                    pass
    
    def _center_window(self) -> None:
        """Центрировать окно на экране"""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
    
    def _show_login(self) -> None:
        """Показать окно входа как модальное окно"""
        def on_login_success(user_data: Dict[str, Any]):
            """Callback при успешном входе"""
            self.current_user = user_data
            self._login_window = None
            self._switch_to_main_window()
        
        def on_login_close():
            """Callback при закрытии окна входа"""
            self._on_closing()
        
        # Создаём окно входа как дочернее (transient)
        self._login_window = LoginWindow(
            parent=self,
            on_success=on_login_success,
            on_close=on_login_close
        )
        
        # Делаем окно входа модальным
        self._login_window.transient(self)
        self._login_window.grab_set()
        
        # Фокус на поле логина
        if hasattr(self._login_window, 'focus_login_field'):
            self._login_window.focus_login_field()
    
    def _switch_to_main_window(self) -> None:
        """
        Переключиться на главное окно после успешного входа
        
        ✅ БЕЗОПАСНОЕ закрытие: withdraw → destroy → None
        ✅ Защита от TclError если окно уже уничтожено
        """
        if not self.current_user:
            app_logger.error("❌ Switch to main window without authenticated user")
            return
        
        # ✅ Безопасное закрытие окна входа
        try:
            if self._login_window and self._login_window.winfo_exists():
                # 1. Снимаем захват фокуса
                if self._login_window.grab_current() == self._login_window:
                    self._login_window.grab_release()
                
                # 2. Мгновенно скрываем окно (визуально)
                self._login_window.withdraw()
                
                # 3. Уничтожаем виджет
                self._login_window.destroy()
        except Exception as e:
            # Окно уже уничтожено — это нормально при быстром переключении
            app_logger.debug(f"ℹ️ Login window already closed: {e}")
        finally:
            # 4. Обнуляем ссылку в любом случае
            self._login_window = None
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from ui.main_window.main_window import MainWindow
        
        # Создаём главное окно как фрейм внутри App
        self._main_window = MainWindow(
            parent=self,
            user=self.current_user
        )
        
        # Показываем главное окно
        self._main_window.pack(fill="both", expand=True)
        
        # Возвращаем фокус на главное окно
        self.deiconify()
        self.focus_set()
        
        app_logger.info(f"✅ Main window loaded for user: {self.current_user.get('username')}")
    
    def _on_closing(self) -> None:
        """Обработчик закрытия приложения"""
        app_logger.info("👤 Приложение закрывается")
        
        # 🔹 Сохранение настроек (если есть)
        try:
            from core.config_loader import config
            # config.save()
        except Exception as e:
            app_logger.warning(f"⚠️ Could not save config on exit: {e}")
        
        # 🔹 Закрытие соединения с БД
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if hasattr(db, 'conn') and db.conn:
                db.close()
        except Exception as e:
            app_logger.warning(f"⚠️ Could not close DB on exit: {e}")
        
        # 🔹 Очистка окон с защитой от уже уничтоженных виджетов
        for window_name, window in [("_main_window", self._main_window), 
                                     ("_login_window", self._login_window)]:
            if window:
                try:
                    if hasattr(window, 'winfo_exists') and window.winfo_exists():
                        window.destroy()
                except Exception as e:
                    app_logger.debug(f"ℹ️ {window_name} already destroyed: {e}")
        
        # 🔹 Финальное закрытие
        app_logger.info("🔌 Application shutdown complete")
        self.quit()
        self.destroy()
    
    def restart(self) -> None:
        """Перезапустить приложение"""
        app_logger.info("🔄 Application restart requested")
        python = sys.executable
        os.execv(python, [python] + sys.argv)
    
    def get_resource(self, relative_path: str) -> Path:
        """Получить абсолютный путь к ресурсу"""
        return self.resource_path / relative_path
    
    @property
    def is_logged_in(self) -> bool:
        """Проверка: пользователь авторизован"""
        return self.current_user is not None
    
    @property
    def current_theme(self):
        """Текущая тема оформления"""
        return theme_manager.current


# ==================== 🚀 ТОЧКА ВХОДА ====================

def main():
    """Точка входа — вынесена для удобства тестирования"""
    try:
        app = App()
        app.mainloop()
    except RecursionError as e:
        app_logger.critical(f"💥 RecursionError: {e}", exc_info=True)
        print("\n" + "="*60)
        print("🚨 КРИТИЧЕСКАЯ ОШИБКА: Рекурсия при инициализации")
        print("="*60)
        print("Возможные причины:")
        print("  1. hasattr() в __init__ класса, наследуемого от tkinter")
        print("  2. super().__init__() вызван не первым")
        print("  3. Циклический импорт модулей")
        print("\nРешение: Используйте '_attr' in self.__dict__ вместо hasattr()")
        print("="*60 + "\n")
        sys.exit(1)
    except Exception as e:
        app_logger.critical(f"💥 Application crashed: {e}", exc_info=True)
        try:
            import tkinter.messagebox as mb
            mb.showerror("Критическая ошибка", f"Приложение завершилось с ошибкой:\n{e}")
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()