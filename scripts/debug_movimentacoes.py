import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

print("=== Verificação de Movimentações ===\n")

# Total
cur.execute('SELECT COUNT(*) FROM principal_movimentacao')
total = cur.fetchone()[0]
print(f"Total de registros: {total}")

# Primeiros 5
print("\nPrimeiros 5 registros:")
cur.execute('SELECT id, codigo, data, tipo, valor, descricao FROM principal_movimentacao LIMIT 5')
for row in cur.fetchall():
    print(f"  ID={row[0]}, Codigo={row[1]}, Data={row[2]}, Tipo={row[3]}, Valor={row[4]}, Desc={row[5][:30] if row[5] else None}")

# Verificar campos
print("\nEstrutura da tabela:")
cur.execute('PRAGMA table_info(principal_movimentacao)')
for row in cur.fetchall():
    print(f"  {row[1]} ({row[2]})")

conn.close()
