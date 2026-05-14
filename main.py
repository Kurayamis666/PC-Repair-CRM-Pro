# main.py
"""
Точка входа в приложение PC Repair CRM Pro
✅ СОВМЕСТИМО: Запуск из .exe через PyInstaller
✅ УЛУЧШЕНО: Обработка ошибок, ресурсы, иконка, логирование
"""

import sys
import os
import traceback
from datetime import datetime

# 🔧 Критично для PyInstaller: путь к ресурсам
if getattr(sys, 'frozen', False):
    # Запуск из .exe
    application_path = os.path.dirname(sys.executable)
    # Для доступа к встроенным ресурсам в .exe
    internal_path = os.path.join(application_path, "_internal")
    if os.path.isdir(internal_path):
        sys._MEIPASS = internal_path
    else:
        sys._MEIPASS = application_path
else:
    # Запуск из скрипта
    application_path = os.path.dirname(os.path.abspath(__file__))

# Добавляем путь к проекту в sys.path для импортов
import_paths = [application_path]
if getattr(sys, 'frozen', False):
    import_paths.append(os.path.join(application_path, "_internal"))
    import_paths.append(getattr(sys, "_MEIPASS", application_path))

for import_path in import_paths:
    if import_path not in sys.path:
        sys.path.insert(0, import_path)


def resource_path(relative_path: str) -> str:
    """
    Получить абсолютный путь к ресурсу.
    Работает как в режиме скрипта, так и в упакованном .exe.
    
    Пример:
        icon = resource_path("ui/assets/app_icon.ico")
        config = resource_path("data/config.json")
    """
    try:
        # PyInstaller создает временную папку _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Запуск из скрипта
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def setup_error_handling():
    """
    Настройка глобальной обработки ошибок.
    Логирует исключения в файл crash.log для отладки .exe.
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        # Игнорируем KeyboardInterrupt (Ctrl+C)
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Формируем сообщение об ошибке
        error_msg = f"""
═══════════════════════════════════════
🚨 CRASH REPORT — PC Repair CRM Pro
═══════════════════════════════════════
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python: {sys.version}
Platform: {sys.platform}
Frozen: {getattr(sys, 'frozen', False)}
Path: {application_path}

Exception Type: {exc_type.__name__}
Exception Value: {exc_value}

Traceback:
{''.join(traceback.format_tb(exc_traceback))}
═══════════════════════════════════════
"""
        # Пишем в лог-файл
        log_path = os.path.join(application_path, "crash.log")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(error_msg)
        except Exception as e:
            print(f"Failed to write crash log: {e}", file=sys.stderr)
        
        # Если есть интерфейс — показываем сообщение (может не сработать в --windowed)
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "🚨 Критическая ошибка",
                f"Приложение завершилось с ошибкой:\n\n{exc_type.__name__}: {exc_value}\n\n"
                f"Подробности в файле:\n{log_path}"
            )
        except:
            pass
        
        # Вызываем стандартный обработчик
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    # Устанавливаем глобальный обработчик
    sys.excepthook = exception_handler


# ✅ Настраиваем обработку ошибок ДО импорта приложения
setup_error_handling()


# ✅ Импортируем класс App (согласовано с ui/app.py)
from ui.app import App


def main():
    """Главная функция запуска приложения"""
    try:
        # Создаем экземпляр приложения
        app = App()
        
        # 🔧 Устанавливаем иконку (если файл существует)
        icon_path = resource_path(os.path.join("ui", "assets", "app_icon.ico"))
        if os.path.exists(icon_path):
            try:
                app.iconbitmap(icon_path)  # Windows
            except Exception:
                # Для macOS/Linux можно использовать другие методы
                pass
        
        # 🔧 Устанавливаем заголовок окна (дублирование на всякий случай)
        app.title("PC Repair CRM Pro")
        
        # Запускаем главный цикл tkinter
        app.mainloop()
        
    except Exception as e:
        # Эта обработка сработает, если ошибка произойдет ДО установки sys.excepthook
        error_log = os.path.join(application_path, "crash.log")
        with open(error_log, "w", encoding="utf-8") as f:
            f.write(f"CRASH at {datetime.now()}\n")
            f.write(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()