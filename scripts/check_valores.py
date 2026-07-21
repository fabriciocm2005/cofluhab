import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM principal_movimentacao WHERE CAST(valor AS REAL) != 0')
com_valor = cur.fetchone()[0]
print(f'Movimentações com valor != 0: {com_valor}')

cur.execute('SELECT COUNT(*) FROM principal_movimentacao')
total = cur.fetchone()[0]
print(f'Total de movimentações: {total}')

if com_valor > 0:
    print('\nExemplos com valor != 0:')
    cur.execute('SELECT codigo, tipo, valor, data, descricao FROM principal_movimentacao WHERE CAST(valor AS REAL) != 0 LIMIT 10')
    for r in cur.fetchall():
        print(f'  {r[0]} - {r[1]} - {r[2]} - {r[3]} - {r[4][:40] if r[4] else ""}')

conn.close()
