"""
Verificar conjunto em backup antes da normalização
"""

import sqlite3

# Vamos verificar o backup de antes da normalização
backup_path = 'db.sqlite3.bak-20251124-011853'

conn = sqlite3.connect(backup_path)
cursor = conn.cursor()

print("=" * 70)
print(f"VERIFICANDO BACKUP: {backup_path}")
print("=" * 70)
print()

# Ver distribuição de conjuntos
cursor.execute("""
    SELECT conjunto, COUNT(*) as count
    FROM principal_contrato
    WHERE conjunto != ''
    GROUP BY conjunto
    ORDER BY count DESC
    LIMIT 30
""")

print("Distribuição de conjunto nos contratos (BACKUP):")
for conj, count in cursor.fetchall():
    print(f"  '{conj}': {count} contratos")

print()
print("=" * 70)

# Verificar contrato 6000 especificamente
cursor.execute("""
    SELECT codigo, conjunto, chave, cod_imovel
    FROM principal_contrato
    WHERE codigo IN ('6000', '006000', '0006000')
    ORDER BY codigo
""")

print("Contratos com código 6000 (ou variações):")
for row in cursor.fetchall():
    print(f"  Código: {row[0]}, Conjunto: '{row[1]}', Chave: '{row[2]}', CodImovel: '{row[3]}'")

conn.close()
