
import sqlite3

db = sqlite3.connect("db.sqlite3")
cursor = db.cursor()

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
""")

tables = cursor.fetchall()

print("\n--- OLD SQLITE DATABASE RECORDS ---\n")

for (table,) in tables:
    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
    count = cursor.fetchone()[0]
    print(f"{table}: {count} records")

db.close()
