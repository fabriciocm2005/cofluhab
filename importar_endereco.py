import os
import django
from dbfread import DBF

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Endereco

DBF_PATH = os.path.join(os.path.dirname(__file__), 'dados_antigos', 'CADEND.DBF')

def safe_text(value):
    if value is None:
        return ''
    if isinstance(value, bytes):
        return value.decode('latin-1', errors='ignore').strip()
    return str(value).strip()

def importar_endereco():
    registros = DBF(DBF_PATH, raw=True)
    for registro in registros:
        try:
            endereco = safe_text(registro.get('ENDERECO'))
            numero = safe_text(registro.get('NUMERO'))
            compl = safe_text(registro.get('COMPL'))
            bairro = safe_text(registro.get('BAIRRO'))
            cidade = safe_text(registro.get('CIDADE'))
            cep = safe_text(registro.get('CEP'))
            uf = safe_text(registro.get('UF'))

            Endereco.objects.update_or_create(
                endereco=endereco,
                numero=numero,
                defaults={
                    'compl': compl,
                    'bairro': bairro,
                    'cidade': cidade,
                    'cep': cep,
                    'uf': uf
                }
            )
        except Exception as e:
            print('Aviso: falha ao importar um registro de endereço:', e)
            continue
    print('Importação de endereços concluída.')

if __name__ == '__main__':
    importar_endereco()
