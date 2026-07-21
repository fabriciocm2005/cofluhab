"""
Verificar o conjunto original na tabela Movimentacao
(antes de remover os zeros à esquerda)
"""

import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=" * 70)
print("VERIFICANDO CONJUNTO NA TABELA MOVIMENTACAO")
print("=" * 70)
print()

# Buscar conjuntos distintos na tabela movimentacao
cursor.execute("""
    SELECT DISTINCT conjunto, COUNT(*) as count
    FROM principal_movimentacao
    WHERE conjunto != ''
    GROUP BY conjunto
    ORDER BY count DESC
    LIMIT 30
""")

print("Valores de conjunto na tabela Movimentacao (original):")
for conj, count in cursor.fetchall():
    print(f"  '{conj}': {count} movimentações")

print()
print("=" * 70)

# Verificar se há movimentações que possam estar relacionadas ao contrato 6000
# O contrato 6000 deve ter um mutuário associado
cursor.execute("""
    SELECT 
        c.codigo as codigo_contrato,
        c.conjunto as conjunto_contrato,
        c.mutuario_principal_id,
        c.cod_imovel
    FROM principal_contrato c
    WHERE c.codigo = '6000'
""")

contrato = cursor.fetchone()
if contrato:
    codigo_contrato, conjunto_contrato, mutuario_id, cod_imovel = contrato
    print(f"Contrato 6000:")
    print(f"  Conjunto atual: '{conjunto_contrato}'")
    print(f"  Mutuário ID: {mutuario_id}")
    print(f"  Cod Imóvel: '{cod_imovel}'")
    print()
    
    if mutuario_id:
        # Buscar código do mutuário
        cursor.execute("""
            SELECT codigo, nome
            FROM principal_mutuario
            WHERE id = ?
        """, (mutuario_id,))
        
        mut = cursor.fetchone()
        if mut:
            cod_mutuario, nome = mut
            print(f"  Mutuário código: {cod_mutuario}")
            print(f"  Nome: {nome}")
            print()
            
            # Buscar movimentações desse mutuário
            cursor.execute("""
                SELECT DISTINCT conjunto
                FROM principal_movimentacao
                WHERE codigo = ?
                ORDER BY conjunto
            """, (cod_mutuario,))
            
            conjuntos_mov = cursor.fetchall()
            if conjuntos_mov:
                print(f"  Conjuntos nas movimentações do mutuário {cod_mutuario}:")
                for (conj,) in conjuntos_mov:
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM principal_movimentacao
                        WHERE codigo = ? AND conjunto = ?
                    """, (cod_mutuario, conj))
                    count = cursor.fetchone()[0]
                    print(f"    '{conj}': {count} movimentações")

print()
print("=" * 70)
print("SOLUÇÃO")
print("=" * 70)
print()
print("Se os conjuntos na tabela Movimentacao estão corretos (com zeros),")
print("podemos restaurar o conjunto do contrato a partir das movimentações!")

conn.close()
