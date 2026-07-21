import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Verificar contrato 000102
cur.execute("SELECT id, codigo, conjunto FROM principal_contrato WHERE codigo='000102'")
contrato = cur.fetchone()
print(f"Contrato 000102: {contrato}")

if contrato:
    # Verificar se tem mapeamento
    cur.execute("SELECT mutuario_id, score, method FROM contrato_mutuario_map WHERE contrato_id=?", (contrato[0],))
    mapeamento = cur.fetchone()
    print(f"Mapeamento: {mapeamento}")
    
    # Verificar se existe mutuário com o mesmo código
    cur.execute("SELECT id, codigo, nome, conjunto FROM principal_mutuario WHERE codigo='000102'")
    mutuario = cur.fetchone()
    print(f"Mutuário 000102: {mutuario}")

# Estatísticas gerais
cur.execute("SELECT COUNT(*) FROM principal_contrato")
total_contratos = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM contrato_mutuario_map")
total_mapeamentos = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM principal_mutuario")
total_mutuarios = cur.fetchone()[0]

print(f"\n=== Estatísticas ===")
print(f"Total Contratos: {total_contratos:,}")
print(f"Total Mapeamentos: {total_mapeamentos:,}")
print(f"Total Mutuários: {total_mutuarios:,}")
print(f"Contratos sem mapeamento: {total_contratos - total_mapeamentos:,}")

# Ver alguns contratos sem mapeamento
print(f"\n=== Primeiros 10 contratos sem mapeamento ===")
cur.execute("""
    SELECT c.id, c.codigo, c.conjunto 
    FROM principal_contrato c
    LEFT JOIN contrato_mutuario_map m ON c.id = m.contrato_id
    WHERE m.contrato_id IS NULL
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  Contrato ID={row[0]}, Codigo={row[1]}, Conjunto={row[2]}")

conn.close()
