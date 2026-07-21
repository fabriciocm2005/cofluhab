import sqlite3
conn=sqlite3.connect('db.sqlite3')
cur=conn.cursor()
cur.execute('SELECT count(*) FROM contrato_mutuario_map')
print('mapping_table_count=', cur.fetchone()[0])
cur.execute('SELECT contrato_id,mutuario_id,score,method FROM contrato_mutuario_map ORDER BY contrato_id LIMIT 10')
rows=cur.fetchall()
print('sample rows:')
for r in rows:
    print(r)
conn.close()
