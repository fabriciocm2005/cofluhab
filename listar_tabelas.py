import sqlite3

conn = sqlite3.connect(r'C:\Users\fabri\cofluhab\cofluhab\db.sqlite3')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tabelas = [row[0] for row in cur.fetchall()]

print("Tabelas no banco:")
for t in tabelas:
    if 'mutuario' in t.lower() or 'contrato' in t.lower():
        print(f"  - {t}")

conn.close()
