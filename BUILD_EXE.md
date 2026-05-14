# Сборка PC Repair CRM Pro в Windows EXE

## Быстро через GitHub Actions

1. Откройте вкладку **Actions** в GitHub.
2. Запустите workflow **Build Windows EXE** через **Run workflow**.
3. После завершения скачайте artifact **PC-Repair-CRM-Pro-Windows-EXE**.

Workflow собирает настоящий Windows `.exe` на `windows-latest`, потому что PyInstaller не кросс-компилирует Windows EXE из Linux.

## Локальная сборка на Windows

Требования:
- Windows 10/11.
- Python 3.12.

Команда из корня проекта:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_exe.ps1
```

Готовый файл будет здесь:

```text
dist\PC Repair CRM Pro\PC Repair CRM Pro.exe
```

## Что входит в сборку

- `main.py` как entrypoint.
- PyInstaller hook для `customtkinter`.
- Динамические views, которые загружаются через `__import__`.
- `database/schema.sql` и `.env.example` как вспомогательные файлы.

## Что не входит

- Реальные `.env` значения и секреты.
- Локальные runtime-файлы пользователя.

При первом запуске приложение создаст/использует локальную SQLite базу `repair_shop.db` рядом с `.exe` или в writable fallback-директории.

## Почему папка, а не один файл

Сборка использует PyInstaller `onedir`: GitHub artifact содержит папку `PC Repair CRM Pro` с `.exe` и зависимостями. Такой формат надёжнее для Tk/CustomTkinter и проще диагностируется, чем single-file executable.
