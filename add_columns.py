import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE principal_validacaoai ADD COLUMN correcao_automatica BOOLEAN DEFAULT 0')
    print('✅ Campo correcao_automatica adicionado')
except Exception as e:
    print(f'Campo correcao_automatica: {e}')

try:
    cursor.execute('ALTER TABLE principal_validacaoai ADD COLUMN correcoes_aplicadas TEXT DEFAULT ""')
    print('✅ Campo correcoes_aplicadas adicionado')
except Exception as e:
    print(f'Campo correcoes_aplicadas: {e}')

conn.commit()
conn.close()
print('\n✅ Processo concluído!')
