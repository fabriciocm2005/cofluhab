import django, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
from django.db.models import Max, Min

codigos = ['4012','4046','4060','4064','4078','4086','4155','5014','5019','5054']

print(f"{'Contrato':<10} {'Ocorr':<8} {'Prazo':<6} {'Data contrato':<15} {'Max nmens':<10} {'Max venc':<12} {'Max pgto':<12}")
print("-" * 85)
for cod in codigos:
    try:
        c = Contrato.objects.get(codigo=cod)
        p = ParcelaContrato.objects.filter(contrato=c).aggregate(
            max_n=Max('nmens'),
            max_venc=Max('dtvenc'),
            max_pgto=Max('dtpgto'),
        )
        print(f"{cod:<10} {str(c.ocorrencia):<8} {str(c.prazo):<6} {str(c.data_contrato):<15} {str(p['max_n']):<10} {str(p['max_venc']):<12} {str(p['max_pgto']):<12}")
    except Contrato.DoesNotExist:
        print(f"{cod:<10} NAO ENCONTRADO NO BANCO")
    except Exception as e:
        print(f"{cod:<10} ERRO: {e}")
