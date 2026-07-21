import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Buscar o mutuário 000327
cur.execute("SELECT id, codigo, nome FROM principal_mutuario WHERE codigo = '000327'")
mutuario = cur.fetchone()

if mutuario:
    print(f"Mutuário encontrado: ID={mutuario[0]}, Codigo={mutuario[1]}, Nome={mutuario[2]}")
    
    # Verificar se existe mapeamento
    cur.execute("SELECT COUNT(*) FROM contrato_mutuario_map WHERE mutuario_id = ?", (mutuario[0],))
    count = cur.fetchone()[0]
    print(f"Contratos mapeados: {count}")
    
    if count > 0:
        cur.execute("""
            SELECT cm.contrato_id, c.codigo, cm.score 
            FROM contrato_mutuario_map cm
            JOIN principal_contrato c ON c.id = cm.contrato_id
            WHERE cm.mutuario_id = ?
        """, (mutuario[0],))
        for row in cur.fetchall():
            print(f"  Contrato ID={row[0]}, Codigo={row[1]}, Score={row[2]}")
    
    # Verificar se existe contrato com o mesmo código
    cur.execute("SELECT id, codigo, conjunto FROM principal_contrato WHERE codigo = '000327'")
    contrato = cur.fetchone()
    if contrato:
        print(f"\nContrato com mesmo código: ID={contrato[0]}, Codigo={contrato[1]}, Conjunto={contrato[2]}")
    else:
        print("\nNenhum contrato encontrado com código '000327'")
else:
    print("Mutuário 000327 não encontrado")

# Verificar total de mapeamentos
cur.execute("SELECT COUNT(*) FROM contrato_mutuario_map")
total = cur.fetchone()[0]
print(f"\nTotal de mapeamentos na tabela: {total}")

conn.close()
