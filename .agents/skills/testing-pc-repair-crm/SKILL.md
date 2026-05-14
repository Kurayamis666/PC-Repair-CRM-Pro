---
name: testing-pc-repair-crm
description: End-to-end GUI testing of PC Repair CRM Pro. Use when verifying UI changes, dialog fixes, CRUD operations, or login flows.
---

# Testing PC Repair CRM Pro

## Prerequisites
- Python 3.12+ with dependencies from requirements.txt
- X11 display available (DISPLAY=:0)
- No external services required (SQLite local DB)

## Launching the App
```bash
cd /home/ubuntu/repos/PC-Repair-CRM-Pro
DISPLAY=:0 python3 main.py &
```
Wait ~3 seconds for the login window to appear.

## Default Credentials
- Username: `admin`, Password: `123`
- This creates a PBKDF2-HMAC-SHA256 hashed password (not plain SHA-256)

## Loading Demo Data
1. Log in as admin
2. Navigate: Settings (Настройки) → Database tab (Настройки базы данных)
3. Click "Заполнить тестовыми данными" → Confirm "Yes"
4. This seeds 20 employees, 20 equipment records, 20 requests, branches, etc.

## Navigation Structure
- **Dashboard (Главная)**: Request list with status filters, mass status change button
- **Reference (Справочники)**: Employees, Contractors, Nomenclature, Units
- **Documents (Документы)**: Requests tab, Equipment tab
- **Reports (Отчёты)**: Report generation
- **Settings (Настройки)**: General, SMTP, SMS, Users, Database, Security tabs

## Key Test Paths

### User Management
1. Settings → Пользователи tab → "Открыть экран пользователей"
2. Click "Добавить" to open User Editor dialog
3. Fill: username, password (≥8 chars), confirm password, role, branch
4. Save and verify user appears in table

### Mass Status Change
1. Dashboard → click a row to select it
2. Click orange "Массовая смена статуса" button (top right)
3. Dialog should show: selected count label, status ComboBox, Apply button

### CRUD Dialogs (Requests, Equipment, Employees, Contractors)
1. Navigate to relevant section
2. Click add/edit button
3. Verify dialog renders with all form fields (not black/empty)
4. Fill fields and save

## Common Bug Patterns

### grab_set() Timing
CustomTkinter dialogs using `CTkToplevel` may render black/empty if `grab_set()` is called before UI elements are built. The correct pattern:
```python
dialog = ctk.CTkToplevel(parent)
dialog.title("...")
dialog.geometry("WxH")
dialog.transient(parent)
# Build ALL UI elements first
ctk.CTkLabel(dialog, text="...").pack()
# ... more widgets ...
# THEN grab_set
dialog.update_idletasks()
dialog.grab_set()
```

### Dialog Sizing
If form fields are cut off or validation toasts are invisible, the dialog height may be too small. Check `geometry()` and `minsize()` values.

### CTkComboBox
`CTkComboBox` does NOT support `placeholder_text` parameter. Remove it if present to avoid warnings.

### on_navigate Parameter
Views that receive `on_navigate` must extract it from kwargs BEFORE calling `super().__init__()`, since CTkFrame doesn't accept it.

## Logout Note
The "Выход" (logout) button might not respond to automated GUI clicks. Use app restart (`pkill -f "python3 main.py"` then relaunch) as an alternative to test login flows.

## Language Toggle
The app supports RU and EN. Toggle via the language dropdown in the top-right corner of the main window, or via the login screen's language button.

## Devin Secrets Needed
None — the app uses local SQLite and default admin credentials.
