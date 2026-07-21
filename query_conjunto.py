import sqlite3

# Connect to database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=" * 60)
print("Verificando conjunto nas parcelas do contrato 6000")
print("=" * 60)
print()

# First, get the contract ID
cursor.execute("SELECT id, codigo, conjunto, ocorrencia FROM principal_contrato WHERE codigo = '6000'")
contrato = cursor.fetchone()

if contrato:
    contrato_id, codigo, conjunto_atual, ocorrencia = contrato
    print(f"Contrato encontrado:")
    print(f"  ID: {contrato_id}")
    print(f"  Código: {codigo}")
    print(f"  Conjunto atual: '{conjunto_atual}'")
    print(f"  Ocorrência: '{ocorrencia}'")
    print()
    
    # Count parcelas
    cursor.execute("SELECT COUNT(*) FROM principal_parcelacontrato WHERE contrato_id = ?", (contrato_id,))
    total_parcelas = cursor.fetchone()[0]
    print(f"Total de parcelas: {total_parcelas}")
    print()
    
    # Get distinct conjunto values
    cursor.execute("""
        SELECT conjunto, COUNT(*) as count 
        FROM principal_parcelacontrato 
        WHERE contrato_id = ? 
        GROUP BY conjunto
        ORDER BY conjunto
    """, (contrato_id,))
    
    conjuntos = cursor.fetchall()
    print("Valores de conjunto nas parcelas:")
    for conj, count in conjuntos:
        print(f"  '{conj}': {count} parcelas")
    
    print()
    
    # Show first 5 parcelas
    cursor.execute("""
        SELECT numero_parcela, conjunto, lote, chave
        FROM principal_parcelacontrato
        WHERE contrato_id = ?
        ORDER BY numero_parcela
        LIMIT 5
    """, (contrato_id,))
    
    print("Primeiras 5 parcelas:")
    for parcela in cursor.fetchall():
        numero, conj, lote, chave = parcela
        print(f"  Parcela {numero}: conjunto='{conj}', lote='{lote}', chave='{chave}'")
    
else:
    print("Contrato 6000 não encontrado")

conn.close()
