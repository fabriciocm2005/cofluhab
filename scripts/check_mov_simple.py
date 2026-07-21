import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Total
cur.execute('SELECT COUNT(*) FROM principal_movimentacao')
total = cur.fetchone()[0]
print(f"Total movimentações: {total}")

# Com valor diferente de 0
cur.execute("SELECT COUNT(*) FROM principal_movimentacao WHERE CAST(valor AS REAL) != 0.0")
com_valor = cur.fetchone()[0]
print(f"Com valor != 0: {com_valor}")

# Amostras com valor
print("\nAmostras de movimentações:")
cur.execute("SELECT codigo, valor, data, tipo FROM principal_movimentacao LIMIT 10")
for row in cur.fetchall():
    print(f"  Codigo={row[0]}, Valor={row[1]}, Data={row[2]}, Tipo={row[3]}")

print("\nAmostras com valor != 0:")
cur.execute("SELECT codigo, valor, data, tipo FROM principal_movimentacao WHERE CAST(valor AS REAL) != 0.0 LIMIT 10")
for row in cur.fetchall():
    print(f"  Codigo={row[0]}, Valor={row[1]}, Data={row[2]}, Tipo={row[3]}")

conn.close()
