# check_schema.py
from database.connection import DatabaseConnection

db = DatabaseConnection()
with db.get_cursor() as cur:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]
    print("📋 Таблицы в БД:")
    for t in tables:
        print(f"  - {t}")