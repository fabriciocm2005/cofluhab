import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("Verificando diferentes valores de conjunto na tabela Contrato\n")

# Get distribution of conjunto values
cursor.execute("""
    SELECT conjunto, COUNT(*) as count
    FROM principal_contrato
    WHERE conjunto != ''
    GROUP BY conjunto
    ORDER BY count DESC
    LIMIT 20
""")

print("Top 20 valores de conjunto:")
for conj, count in cursor.fetchall():
    print(f"  '{conj}': {count} contratos")

print("\n" + "=" * 60)
print("Verificando contrato 6000 especificamente:")
print("=" * 60)

cursor.execute("""
    SELECT codigo, conjunto, ocorrencia, cod_imovel
    FROM principal_contrato
    WHERE codigo = '6000'
""")

result = cursor.fetchone()
if result:
    codigo, conjunto, ocorrencia, cod_imovel = result
    print(f"Código: {codigo}")
    print(f"Conjunto atual: '{conjunto}'")
    print(f"Ocorrência: '{ocorrencia}'")
    print(f"Cod Imóvel: '{cod_imovel}'")

print("\n" + "=" * 60)
print("Verificando dados originais no arquivo MOVMUT.DBF")
print("=" * 60)

# Try to read from imported movimentacoes
cursor.execute("""
    SELECT DISTINCT conjunto
    FROM principal_movimentacao
    WHERE codigo = '6000'
    LIMIT 5
""")

conjuntos_mov = cursor.fetchall()
if conjuntos_mov:
    print(f"Valores de conjunto nas movimentações do código 6000:")
    for (conj,) in conjuntos_mov:
        print(f"  '{conj}'")
else:
    print("Nenhuma movimentação encontrada para código 6000")

conn.close()
