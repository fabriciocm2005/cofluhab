"""
Verificar conjunto no backup pós-normalização (antes de popular_conjunto_correto.py)
"""

import sqlite3

# Backup mais recente
backup_path = 'db.sqlite3.bak-pos-normalizacao-20251127-233115'

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

print("Distribuição de conjunto nos contratos (BACKUP PÓS-NORMALIZAÇÃO):")
for conj, count in cursor.fetchall():
    print(f"  '{conj}': {count} contratos")

print()
print("=" * 70)

# Verificar contrato 6000
cursor.execute("""
    SELECT codigo, conjunto, ocorrencia, cod_imovel, chave
    FROM principal_contrato
    WHERE codigo = '6000'
""")

row = cursor.fetchone()
if row:
    print("Contrato 6000 no backup:")
    print(f"  Código: {row[0]}")
    print(f"  Conjunto: '{row[1]}'")
    print(f"  Ocorrência: '{row[2]}'")
    print(f"  CodImovel: '{row[3]}'")
    print(f"  Chave: '{row[4]}'")
else:
    print("Contrato 6000 não encontrado no backup")

print()
print("=" * 70)
print("Se o conjunto no backup também está errado,")
print("significa que o erro veio da importação original")
print("=" * 70)

conn.close()
