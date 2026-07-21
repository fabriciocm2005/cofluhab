import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Check if table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contrato_mutuario_map'")
result = cur.fetchone()
print('Tabela existe:', result is not None)

if result:
    cur.execute('SELECT COUNT(*) FROM contrato_mutuario_map')
    print('Total registros:', cur.fetchone()[0])
    
    cur.execute('SELECT * FROM contrato_mutuario_map LIMIT 5')
    for row in cur.fetchall():
        print(f'  Contrato {row[0]} -> Mutuario {row[1]} (score={row[2]}, method={row[3]})')
    
    # Check for mutuario ID 1 (codigo 000327)
    cur.execute('SELECT * FROM contrato_mutuario_map WHERE mutuario_id=1')
    maps = cur.fetchall()
    print(f'\nMapeamentos para mutuario_id=1: {len(maps)}')
    for row in maps[:3]:
        print(f'  Contrato {row[0]} -> Mutuario {row[1]} (score={row[2]}, method={row[3]})')
else:
    print('TABELA NÃO EXISTE - precisa executar apply_mapping_v2.py novamente')

conn.close()
