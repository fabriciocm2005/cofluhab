import os
import django
from dbfread import DBF

# configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import ConjuntoHabitacional

# Caminho do arquivo CONJUNTO.DBF
DBF_PATH = os.path.join(os.path.dirname(__file__), 'dados_antigos', 'CONJUNTO.DBF')

def importar_conjunto():
    registros = DBF(DBF_PATH, encoding='latin-1')
    for registro in registros:
        ConjuntoHabitacional.objects.update_or_create(
            conj=registro.get('CONJ', ''),
            defaults={
                'conjunto': registro.get('CONJUNTO', ''),
                'contrato': registro.get('CONTRATO', ''),
                'conjseg': registro.get('CONJSEG', ''),
                'nome': registro.get('NOME', ''),
                'nomeseg': registro.get('NOMESEG', ''),
                'qtd_mut': registro.get('QTD_MUT', 0)
            }
        )
    print('Importação de conjuntos concluída.')

if __name__ == '__main__':
    importar_conjunto()
