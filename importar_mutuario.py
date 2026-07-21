import os
import django
from dbfread import DBF

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario

DBF_PATH = os.path.join(os.path.dirname(__file__), 'dados_antigos', 'CADBAK.DBF')

def importar_mutuario():
    registros = DBF(DBF_PATH, encoding='latin-1')
    for registro in registros:
        Mutuario.objects.update_or_create(
            codigo=registro.get('CODIGO', ''),
            defaults={
                'codimovel': registro.get('CODIMOVEL', ''),
                'conjunto': registro.get('CONJUNTO', ''),
                'conjseg': registro.get('CONJSEG', ''),
                'nome': registro.get('NOME', ''),
                'ident': registro.get('IDENT', ''),
                'orgao': registro.get('ORGAO', ''),
                'dtnasc': registro.get('DTNASC', None),
                'cpf': registro.get('CPF', ''),
                'renda': registro.get('RENDA', 0),
                'crenda': registro.get('CRENDA', 0),
                'endereco': registro.get('ENDERECO', ''),
                'numero': registro.get('NUMERO', ''),
                'compl': registro.get('COMPL', ''),
                'tipoimovel': registro.get('TIPOIMOVEL', ''),
                'bairro': registro.get('BAIRRO', ''),
                'cidade': registro.get('CIDADE', ''),
                'cep': registro.get('CEP', ''),
                'uf': registro.get('UF', '')
            }
        )
    print('Importação de mutuários concluída.')

if __name__ == '__main__':
    importar_mutuario()
