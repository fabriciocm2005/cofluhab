import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.views import calcular_fcvs_residual_global


def somar_fcvs(qs):
    total = 0.0
    qtd = 0
    for cid in qs.values_list('id', flat=True):
        try:
            _, _, fcvs = calcular_fcvs_residual_global(cid)
            if fcvs > 100:
                total += fcvs
                qtd += 1
        except Exception:
            pass
    return total, qtd

if __name__ == '__main__':
    filtro = Contrato.objects.filter(conjunto__icontains='10')
    total_filtro, qtd_filtro = somar_fcvs(filtro)
    total_geral, qtd_geral = somar_fcvs(Contrato.objects.all())
    print(f'FCVS_FILTRO_CONJ10: {total_filtro:.2f}')
    print(f'QTD_FILTRO_CONJ10: {qtd_filtro}')
    print(f'FCVS_GERAL: {total_geral:.2f}')
    print(f'QTD_GERAL: {qtd_geral}')
