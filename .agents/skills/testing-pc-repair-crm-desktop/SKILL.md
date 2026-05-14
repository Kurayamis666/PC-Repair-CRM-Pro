---
name: testing-pc-repair-crm-desktop
description: Test the PC Repair CRM Pro Tk/CustomTkinter desktop app end-to-end. Use when verifying UI flows, table rendering, navigation, or visual regressions in the local desktop app.
---

# PC Repair CRM Pro desktop testing

## Devin Secrets Needed

- None for local desktop smoke/E2E testing. The local database seeds a demo admin user.
- If future tests cover SMTP/SMS integrations, request provider credentials separately and store them as named Devin secrets before testing those integrations.

## Runtime

- Repo path: `/home/ubuntu/repos/PC-Repair-CRM-Pro`
- Tk-capable Python environment: `/home/ubuntu/.venvs/pc-repair-system`
- Launch command:
  ```bash
  DISPLAY=:0 /home/ubuntu/.venvs/pc-repair-system/bin/python /home/ubuntu/repos/PC-Repair-CRM-Pro/main.py
  ```
- The project venv may not have `_tkinter`; if GUI launch fails there, use the Tk-capable environment above.
- Before recording desktop tests, maximize the app window. `wmctrl` may be available; if not, install it in the environment or use window controls.

## Local login

- Default seeded login: `admin`
- Default seeded password: `123`
- The seed is defined in `database/connection.py` and may also be present in `database/init_db.py`.

## Visual table testing flow

1. Start the app and log in as the seeded admin user.
2. Dashboard opens by default. Verify the requests table headers and rows are visible and readable.
3. Use Dashboard navigation buttons for:
   - `📄 Документы` to test the documents/requests table.
   - `👥 Справочники`, then `Открыть` under contacts, to test reference/contact tables.
   - `⚙️ Настройки`, then the `Пользователи` tab and `Открыть экран пользователей`, to test the users table.
4. For table-spacing or table-rendering changes, collect a full-screen screenshot for each table state and a screen recording with structured annotations.

## Assertions to use

- Login succeeds and Dashboard table loads.
- Adjacent column text has visible horizontal separation.
- Headers remain readable after spacing changes.
- Search widgets and scrollbars remain visible and do not overlap table cells.
- Selection colors/alternating row colors still make rows readable.

## Notes

- The app uses a local SQLite DB (`repair_shop.db`) that can be modified by runtime testing. Do not commit DB changes.
- Full repo lint/type/test suites might fail because of broader project debt; for UI verification, report those separately from runtime visual results.
