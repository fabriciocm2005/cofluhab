import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Testar com o código que está aparecendo na tela
codigo = '006000'  # Com zeros à esquerda como aparece na tela

# Buscar contrato
cur.execute('SELECT id, codigo FROM principal_contrato WHERE codigo = ?', (codigo,))
contrato = cur.fetchone()
print(f"Contrato com '006000': id={contrato[0]}, codigo={contrato[1]}" if contrato else "Contrato '006000' não encontrado")

# Tentar sem zeros à esquerda
codigo2 = '6000'
cur.execute('SELECT id, codigo FROM principal_contrato WHERE codigo = ?', (codigo2,))
contrato2 = cur.fetchone()
print(f"Contrato com '6000': id={contrato2[0]}, codigo={contrato2[1]}" if contrato2 else "Contrato '6000' não encontrado")

# Buscar mutuário
cur.execute('SELECT id, codigo, nome FROM principal_mutuario WHERE codigo = ?', (codigo2,))
mutuario = cur.fetchone()
print(f"Mutuário: id={mutuario[0]}, codigo={mutuario[1]}, nome={mutuario[2]}" if mutuario else "Mutuário não encontrado")

# Buscar relacionamento para ambos
if contrato:
    cur.execute('SELECT * FROM contrato_mutuario_map WHERE contrato_id = ?', (contrato[0],))
    rel = cur.fetchone()
    print(f"Relacionamento '006000': {rel}" if rel else "SEM RELACIONAMENTO para '006000'!")

if contrato2:
    cur.execute('SELECT * FROM contrato_mutuario_map WHERE contrato_id = ?', (contrato2[0],))
    rel2 = cur.fetchone()
    print(f"Relacionamento '6000': {rel2}" if rel2 else "SEM RELACIONAMENTO para '6000'!")

# Ver todos os contratos com código começando com 6000
cur.execute('SELECT id, codigo FROM principal_contrato WHERE codigo LIKE ?', ('6000%',))
todos = cur.fetchall()
print(f"\nTodos contratos começando com '6000': {len(todos)} encontrados")
for t in todos:
    cur.execute('SELECT mutuario_id FROM contrato_mutuario_map WHERE contrato_id = ?', (t[0],))
    has_rel = cur.fetchone()
    print(f"  - id={t[0]}, codigo={t[1]}, tem_relacionamento={bool(has_rel)}")

conn.close()
