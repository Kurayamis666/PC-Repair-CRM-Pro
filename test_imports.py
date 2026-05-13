# test_imports.py
"""Проверка что все импорты работают"""

print("🔍 Проверка импортов...")

try:
    from utils.validators import validate_name, validate_date_format, validate_required
    print("✅ utils.validators: OK")
except ImportError as e:
    print(f"❌ utils.validators: {e}")

try:
    from database.repositories import EmployeeRepository, RequestRepository
    print("✅ database.repositories: OK")
except ImportError as e:
    print(f"❌ database.repositories: {e}")

try:
    from ui.login.login_window import LoginWindow
    print("✅ ui.login: OK")
except ImportError as e:
    print(f"❌ ui.login: {e}")

try:
    from ui.app import App
    print("✅ ui.app: OK")
except ImportError as e:
    print(f"❌ ui.app: {e}")

print("\n🎉 Проверка завершена!")