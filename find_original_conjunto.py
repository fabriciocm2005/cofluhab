import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=" * 70)
print("Verificando conjunto na tabela Movimentacao (dados originais)")
print("=" * 70)
print()

# Check if movimentacao table exists and has conjunto
cursor.execute("""
    SELECT sql FROM sqlite_master 
    WHERE type='table' AND name='principal_movimentacao'
""")

schema = cursor.fetchone()
if schema:
    print("Schema da tabela principal_movimentacao:")
    print(schema[0])
    print()
    
    # Check if conjunto column exists
    if 'conjunto' in schema[0].lower():
        # Get distinct conjunto values for codigo 6000
        cursor.execute("""
            SELECT DISTINCT conjunto
            FROM principal_movimentacao
            WHERE codigo = '6000'
            ORDER BY conjunto
        """)
        
        conjuntos = cursor.fetchall()
        print("Valores de conjunto nas movimentações do código 6000:")
        for (conj,) in conjuntos:
            # Count how many records
            cursor.execute("""
                SELECT COUNT(*)
                FROM principal_movimentacao
                WHERE codigo = '6000' AND conjunto = ?
            """, (conj,))
            count = cursor.fetchone()[0]
            print(f"  '{conj}': {count} movimentações")
        
        if not conjuntos:
            print("  (nenhuma movimentação encontrada)")
    else:
        print("A tabela movimentacao não tem coluna 'conjunto'")
else:
    print("Tabela principal_movimentacao não existe")

print("\n" + "=" * 70)
print("Tentando descobrir conjunto através de dados relacionados")
print("=" * 70)
print()

# Check the mutuario associated with contract 6000
cursor.execute("""
    SELECT 
        c.codigo,
        c.conjunto,
        c.ocorrencia,
        c.cod_imovel,
        m.nome,
        m.endereco
    FROM principal_contrato c
    LEFT JOIN principal_mutuario m ON c.mutuario_id = m.id
    WHERE c.codigo = '6000'
""")

result = cursor.fetchone()
if result:
    codigo, conjunto, ocorrencia, cod_imovel, nome, endereco = result
    print(f"Contrato 6000:")
    print(f"  Conjunto atual: '{conjunto}'")
    print(f"  Ocorrência: '{ocorrencia}'")
    print(f"  Cod Imóvel: '{cod_imovel}'")
    print(f"  Mutuário: {nome}")
    print(f"  Endereço: {endereco}")

conn.close()
