import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

cursor.execute("SELECT codigo, cod_imovel, conjunto FROM principal_contrato WHERE codigo = '6000'")
print('Contrato 6000:', cursor.fetchone())

cursor.execute("SELECT codigo, codimovel, conjunto, nome FROM principal_mutuario WHERE codigo = '6000'")
result = cursor.fetchone()
if result:
    print(f'Mutuario 6000: codigo={result[0]}, codimovel={result[1]}, conjunto={result[2]}, nome={result[3]}')
else:
    print('Mutuario 6000: Não encontrado')

conn.close()
