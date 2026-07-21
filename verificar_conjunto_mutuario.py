import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=" * 70)
print("VERIFICANDO CAMPO CONJUNTO NA TABELA MUTUARIO")
print("=" * 70)
print()

# Ver se tem conjunto na tabela mutuario
cursor.execute("""
    SELECT conjunto, COUNT(*) as count
    FROM principal_mutuario
    WHERE conjunto != ''
    GROUP BY conjunto
    ORDER BY count DESC
    LIMIT 30
""")

print("Distribuição de conjunto na tabela Mutuario:")
for conj, count in cursor.fetchall():
    print(f"  '{conj}': {count} mutuários")

print()
print("=" * 70)
print("Verificando mutuário do contrato 6000")
print("=" * 70)
print()

# Pegar mutuário do contrato 6000
cursor.execute("""
    SELECT 
        c.codigo as codigo_contrato,
        c.conjunto as conjunto_contrato,
        m.codigo as codigo_mutuario,
        m.conjunto as conjunto_mutuario,
        m.nome
    FROM principal_contrato c
    LEFT JOIN principal_mutuario m ON c.mutuario_principal_id = m.id
    WHERE c.codigo = '6000'
""")

row = cursor.fetchone()
if row:
    cod_contrato, conj_contrato, cod_mutuario, conj_mutuario, nome = row
    print(f"Contrato {cod_contrato}:")
    print(f"  Conjunto no contrato: '{conj_contrato}'")
    print(f"  Mutuário: {cod_mutuario} - {nome}")
    print(f"  Conjunto no mutuário: '{conj_mutuario}'")
    print()
    if conj_mutuario and conj_mutuario != conj_contrato:
        print(f"✓ ENCONTRADO! O conjunto correto é '{conj_mutuario}'!")

conn.close()
