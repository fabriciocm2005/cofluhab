import os
import json
from datetime import datetime

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.views import calcular_fcvs_residual_global

BASE_DIR = os.path.dirname(__file__)
CACHE_GERAL = os.path.join(BASE_DIR, 'fcvs_total_cache.json')
CACHE_FILTROS = os.path.join(BASE_DIR, 'fcvs_filtros_cache.json')


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
            continue
    return total, qtd


def main():
    total_geral, qtd_geral = somar_fcvs(Contrato.objects.all())
    payload_geral = {
        'total_fcvs_geral': float(total_geral),
        'contratos_com_fcvs_geral': int(qtd_geral),
        'atualizado_em': datetime.now().isoformat(),
    }
    with open(CACHE_GERAL, 'w', encoding='utf-8') as f:
        json.dump(payload_geral, f, ensure_ascii=False, indent=2)

    payload_filtro = {}
    key_010 = 'conjunto=010|contrato='
    total_010, qtd_010 = somar_fcvs(Contrato.objects.filter(conjunto__icontains='010'))
    payload_filtro[key_010] = {
        'total_fcvs_filtro': float(total_010),
        'contratos_com_fcvs_filtro': int(qtd_010),
        'atualizado_em': datetime.now().isoformat(),
    }

    with open(CACHE_FILTROS, 'w', encoding='utf-8') as f:
        json.dump(payload_filtro, f, ensure_ascii=False, indent=2)

    print('CACHE_GERAL_OK', payload_geral)
    print('CACHE_FILTRO_010_OK', payload_filtro[key_010])


if __name__ == '__main__':
    main()
