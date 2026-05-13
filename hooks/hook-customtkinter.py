# hooks/hook-customtkinter.py
"""
PyInstaller hook для customtkinter

✅ Гарантирует включение всех динамических импортов (hiddenimports)
✅ Гарантирует включение ресурсов: шрифтов (Roboto), тем (JSON), изображений
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 1. Сбор всех подмодулей (скрытых импортов)
# Это необходимо, так как CustomTkinter может импортировать части библиотеки динамически.
hiddenimports = collect_submodules("customtkinter")

# 2. Сбор всех файлов данных (assets)
# CustomTkinter хранит шрифты и конфигурации тем в папке assets.
# Если их не включить, приложение упадёт при старте.
# include_py_files=False по умолчанию, что корректно, т.к. модули уже собраны выше.
datas = collect_data_files("customtkinter")