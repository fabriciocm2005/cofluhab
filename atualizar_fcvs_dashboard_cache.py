import os
import json
from datetime import datetime

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.views import calcular_fcvs_residual_global


CACHE_PATH = os.path.join(os.path.dirname(__file__), 'fcvs_dashboard_cache.json')


def main():
    contratos_payload = []
    total_fcvs_geral = 0.0
    contratos_com_fcvs_geral = 0

    qs = Contrato.objects.all().only('id', 'codigo', 'conjunto')
    total = qs.count()

    for idx, contrato in enumerate(qs.iterator(), start=1):
        try:
            evolucao, anomalias, fcvs_residual = calcular_fcvs_residual_global(contrato.id)
            fcvs_residual = float(fcvs_residual)
            saldo_atual = evolucao[-1]['saldo_novo'] if evolucao else 0

            if fcvs_residual > 100:
                total_fcvs_geral += fcvs_residual
                contratos_com_fcvs_geral += 1

            contratos_payload.append({
                'id': contrato.id,
                'codigo': str(contrato.codigo),
                'conjunto': str(contrato.conjunto),
                'fcvs_residual': fcvs_residual,
                'anomalias': int(anomalias),
                'saldo_atual': float(saldo_atual),
            })

            if idx % 250 == 0:
                print(f'Processados: {idx}/{total}')
        except Exception as e:
            print(f'Erro contrato {contrato.id}: {e}')

    payload = {
        'gerado_em': datetime.now().isoformat(),
        'total_fcvs_geral': total_fcvs_geral,
        'contratos_com_fcvs_geral': contratos_com_fcvs_geral,
        'contratos': contratos_payload,
    }

    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)

    print('CACHE_OK')
    print(f'total_fcvs_geral={total_fcvs_geral:.2f}')
    print(f'contratos_com_fcvs_geral={contratos_com_fcvs_geral}')
    print(f'arquivo={CACHE_PATH}')


if __name__ == '__main__':
    main()
