"""Rotina operacional para resíduos do FH1.

Foco:
- identificar contratos ignorados/pendentes na geração FH1;
- separar duplicatas não canônicas de pendências financeiras reais;
- gerar relatório acionável para saneamento manual do resíduo restante.
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime

import django

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.ficha_generators import gerar_lote_fh1_separado


def run():
    contratos = list(Contrato.objects.order_by('id'))
    lote = gerar_lote_fh1_separado(contratos, matricula='00044', numero_lote='001')

    detalhes = lote.get('detalhes', [])
    residuos = [d for d in detalhes if str(d.get('status', '')).startswith('ignorado') or d.get('status') == 'pendente_financeiro']
    por_status = Counter(d.get('status', 'desconhecido') for d in residuos)
    contratos_residuo = [str(d.get('contrato', '')) for d in residuos if d.get('contrato')]
    contratos_db = list(Contrato.objects.filter(codigo__in=contratos_residuo).values('id', 'codigo', 'conjunto', 'ocorrencia', 'cod_imovel', 'data_contrato', 'data_primeiro_venc', 'sa', 'tx_juros', 'prazo', 'cat_prof', 'pr'))

    return {
        'executado_em': datetime.now().isoformat(),
        'total_fichas_sucesso': lote.get('total_fichas_sucesso', 0),
        'total_fichas_erro': lote.get('total_fichas_erro', 0),
        'total_fichas_ignoradas': lote.get('total_fichas_ignoradas', 0),
        'residuos_por_status': dict(por_status),
        'residuos': residuos,
        'contratos_residuo_db': contratos_db,
        'erros_geracao': lote.get('erros', []),
    }


def main():
    payload = run()
    out_dir = os.path.join(os.path.dirname(PROJECT_ROOT), 'exports')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"residuos_fh1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(out_path, 'w', encoding='utf-8') as file_obj:
        json.dump(payload, file_obj, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({'report_file': out_path, **payload}, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()