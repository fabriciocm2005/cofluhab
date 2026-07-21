from dbfread import DBF
import os

DBF_PATH = os.path.join(os.path.dirname(__file__), 'dados_antigos', 'CADMUT.DBF')

def listar_campos_e_registros():
    table = DBF(DBF_PATH, encoding='latin-1')
    print('Campos disponíveis:')
    print(table.field_names)
    print('\nPrimeiros registros:')
    for i, record in enumerate(table):
        print(record)
        if i >= 4:
            break

if __name__ == '__main__':
    listar_campos_e_registros()
