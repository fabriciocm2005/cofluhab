import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

print("=" * 80)
print("VERIFICANDO CAMPO CONJUNTO NOS CONTRATOS")
print("=" * 80)

# Distribuição por conjunto
cur.execute("""
    SELECT conjunto, COUNT(*) as qtd
    FROM principal_contrato
    GROUP BY conjunto
    ORDER BY conjunto
""")

print("\nDistribuição de contratos por conjunto:")
total = 0
for row in cur.fetchall():
    conjunto = row[0] if row[0] else '(vazio)'
    qtd = row[1]
    print(f"  {conjunto:15s}: {qtd:5d} contratos")
    total += qtd

print(f"\nTotal: {total} contratos")

# Verificar conjunto 010 especificamente
cur.execute("SELECT COUNT(*) FROM principal_contrato WHERE conjunto = '010'")
print(f"\nConjunto '010': {cur.fetchone()[0]} contratos")

conn.close()
