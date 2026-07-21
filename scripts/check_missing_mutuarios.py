import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Pegar os códigos dos contratos sem mapeamento
cur.execute("""
    SELECT c.codigo, c.conjunto 
    FROM principal_contrato c
    LEFT JOIN contrato_mutuario_map m ON c.id = m.contrato_id
    WHERE m.contrato_id IS NULL
    ORDER BY c.codigo
    LIMIT 20
""")
contratos_sem_map = cur.fetchall()

print("=== Verificando se mutuários existem ===\n")
for codigo, conjunto in contratos_sem_map:
    # Verificar se existe mutuário com esse código
    cur.execute("SELECT id, codigo, nome FROM principal_mutuario WHERE codigo=?", (codigo,))
    mutuario = cur.fetchone()
    
    if mutuario:
        print(f"✓ Contrato {codigo}/{conjunto} → Mutuário EXISTE: {mutuario[2]}")
    else:
        print(f"✗ Contrato {codigo}/{conjunto} → Mutuário NÃO EXISTE no banco")

# Ver range de códigos
print("\n=== Range de códigos ===")
cur.execute("SELECT MIN(codigo), MAX(codigo) FROM principal_contrato")
print(f"Contratos: {cur.fetchone()}")

cur.execute("SELECT MIN(codigo), MAX(codigo) FROM principal_mutuario")
print(f"Mutuários: {cur.fetchone()}")

conn.close()
