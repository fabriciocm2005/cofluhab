import os
import json
from datetime import datetime

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.views import calcular_fcvs_residual_global

CACHE_PATH = os.path.join(os.path.dirname(__file__), 'fcvs_dashboard_cache.json')
STATE_PATH = os.path.join(os.path.dirname(__file__), 'fcvs_dashboard_cache_state.json')


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'last_id': 0,
        'total_fcvs_geral': 0.0,
        'contratos_com_fcvs_geral': 0,
        'contratos': [],
        'processados': 0,
        'total_contratos': Contrato.objects.count(),
        'iniciado_em': datetime.now().isoformat(),
    }


def save_state(state):
    state['atualizado_em'] = datetime.now().isoformat()
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False)


def finalize(state):
    payload = {
        'gerado_em': datetime.now().isoformat(),
        'total_fcvs_geral': state['total_fcvs_geral'],
        'contratos_com_fcvs_geral': state['contratos_com_fcvs_geral'],
        'contratos': state['contratos'],
    }
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)


def run_chunk(chunk_size=300):
    state = load_state()

    qs = (
        Contrato.objects
        .filter(id__gt=state['last_id'])
        .order_by('id')
        .only('id', 'codigo', 'conjunto')[:chunk_size]
    )

    batch = list(qs)
    if not batch:
        finalize(state)
        if os.path.exists(STATE_PATH):
            os.remove(STATE_PATH)
        print('CACHE_FINALIZADO')
        print(f"TOTAL_FCVS_GERAL={state['total_fcvs_geral']:.2f}")
        print(f"CONTRATOS_COM_FCVS={state['contratos_com_fcvs_geral']}")
        return

    for contrato in batch:
        try:
            evolucao, anomalias, fcvs_residual = calcular_fcvs_residual_global(contrato.id)
            fcvs_residual = float(fcvs_residual)
            saldo_atual = evolucao[-1]['saldo_novo'] if evolucao else 0

            if fcvs_residual > 100:
                state['total_fcvs_geral'] += fcvs_residual
                state['contratos_com_fcvs_geral'] += 1

            state['contratos'].append({
                'id': contrato.id,
                'codigo': str(contrato.codigo),
                'conjunto': str(contrato.conjunto),
                'fcvs_residual': fcvs_residual,
                'anomalias': int(anomalias),
                'saldo_atual': float(saldo_atual),
            })

            state['last_id'] = contrato.id
            state['processados'] += 1
        except Exception as e:
            print(f'ERRO_CONTRATO_{contrato.id}={e}')
            state['last_id'] = contrato.id
            state['processados'] += 1
            continue

    save_state(state)
    print(f"CHUNK_OK processados={state['processados']}/{state['total_contratos']} last_id={state['last_id']}")


if __name__ == '__main__':
    run_chunk(chunk_size=300)
