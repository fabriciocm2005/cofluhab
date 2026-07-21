"""
Rotina de saneamento para CADMUT/FH1.

Objetivo:
- preencher campos em aviso ("amarelos") com fontes seguras e regras deriváveis;
- reaproveitar a cascata de DBFs legados já auditada;
- validar o lote FH1 final e separar os casos ainda não saneáveis.

Uso:
  python cofluhab/scripts/saneamento_cadmut_fh1.py --modo analisar
  python cofluhab/scripts/saneamento_cadmut_fh1.py --modo aplicar
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from datetime import datetime
from decimal import Decimal
import io

import django

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.db import transaction, connection
from principal.models import Contrato, Mutuario, ParcelaContrato
from principal.agente_qualidade_contrato import AgenteQualidadeContrato
from principal.ficha_generators import gerar_lote_fh1_separado
from principal.fh1_validator import run_fh1_precheck_agent
from scripts.backfill_cadastro_cascade import (
    CONTRATO_FIELD_MAP,
    MUTUARIO_FIELD_MAP,
    load_source_maps,
    pick_from_sources,
    is_missing_model_value,
    is_useful_source_value,
    normalize_code,
)


DEFAULT_OCORRENCIA = 'SET'


def build_mutuario_maps():
    contrato_to_mutuario = {}
    with connection.cursor() as cur:
        cur.execute('SELECT contrato_id, mutuario_id FROM contrato_mutuario_map ORDER BY rowid')
        for contrato_id, mutuario_id in cur.fetchall():
            if contrato_id not in contrato_to_mutuario:
                contrato_to_mutuario[contrato_id] = mutuario_id

    mutuario_ids = list(set(contrato_to_mutuario.values()))
    mutuarios = {m.id: m for m in Mutuario.objects.filter(id__in=mutuario_ids)} if mutuario_ids else {}
    return contrato_to_mutuario, mutuarios


def linked_mutuario(contrato, contrato_to_mutuario, mutuarios):
    mutuario_id = contrato_to_mutuario.get(contrato.id)
    if mutuario_id:
        return mutuarios.get(mutuario_id)
    if contrato.conjunto:
        return Mutuario.objects.filter(conjunto=contrato.conjunto).first()
    return None


def sanitize_cep(cep):
    digits = ''.join(ch for ch in str(cep or '') if ch.isdigit())
    if len(digits) == 8:
        return f'{digits[:5]}-{digits[5:]}'
    return str(cep or '').strip()


def summarize_modes(contratos):
    ocorrencias = Counter()
    cat_prof_por_conjunto = defaultdict(Counter)
    cod_imovel_por_conjunto = defaultdict(Counter)

    for contrato in contratos:
        if contrato.ocorrencia:
            ocorrencias[str(contrato.ocorrencia).strip().upper()] += 1
        if contrato.conjunto and contrato.cat_prof:
            cat_prof_por_conjunto[str(contrato.conjunto).strip()][str(contrato.cat_prof).strip()] += 1
        if contrato.conjunto and contrato.cod_imovel:
            cod_imovel_por_conjunto[str(contrato.conjunto).strip()][str(contrato.cod_imovel).strip()] += 1

    moda_ocorrencia = ocorrencias.most_common(1)[0][0] if ocorrencias else DEFAULT_OCORRENCIA
    return moda_ocorrencia, cat_prof_por_conjunto, cod_imovel_por_conjunto


def apply_contract_sources(contrato, sources, changes):
    changed_fields = set()
    for model_field, source_fields in CONTRATO_FIELD_MAP.items():
        current = getattr(contrato, model_field)
        if not is_missing_model_value(model_field, current):
            continue
        picked, src = pick_from_sources(normalize_code(contrato.codigo), model_field, source_fields, sources)
        if not is_useful_source_value(model_field, picked):
            continue
        setattr(contrato, model_field, picked)
        changed_fields.add(model_field)
        changes.append({'tipo': 'contrato', 'codigo': str(contrato.codigo), 'campo': model_field, 'origem': f'dbf:{src}'})
    return changed_fields


def apply_mutuario_sources(mutuario, sources, changes):
    changed_fields = set()
    for model_field, source_fields in MUTUARIO_FIELD_MAP.items():
        current = getattr(mutuario, model_field)
        if not is_missing_model_value(model_field, current):
            continue
        picked, src = pick_from_sources(normalize_code(mutuario.codigo), model_field, source_fields, sources)
        if not is_useful_source_value(model_field, picked):
            continue
        setattr(mutuario, model_field, picked)
        changed_fields.add(model_field)
        changes.append({'tipo': 'mutuario', 'codigo': str(mutuario.codigo), 'campo': model_field, 'origem': f'dbf:{src}'})
    return changed_fields


def apply_derived_contract_rules(contrato, mutuario, moda_ocorrencia, cat_prof_por_conjunto, cod_imovel_por_conjunto, changes):
    changed_fields = set()
    parcelas_qs = ParcelaContrato.objects.filter(contrato=contrato)
    primeira = parcelas_qs.order_by('nmens').first()
    ultima = parcelas_qs.order_by('-nmens').first()

    if not contrato.data_primeiro_venc and primeira and primeira.dtvenc:
        contrato.data_primeiro_venc = primeira.dtvenc
        changed_fields.add('data_primeiro_venc')
        changes.append({'tipo': 'contrato', 'codigo': str(contrato.codigo), 'campo': 'data_primeiro_venc', 'origem': 'parcela:dTVENC-primeira'})

    if not contrato.prazo and ultima and ultima.nmens:
        contrato.prazo = ultima.nmens
        changed_fields.add('prazo')
        changes.append({'tipo': 'contrato', 'codigo': str(contrato.codigo), 'campo': 'prazo', 'origem': 'parcela:max-nmens'})

    if not contrato.cod_imovel and mutuario and getattr(mutuario, 'codimovel', None):
        contrato.cod_imovel = mutuario.codimovel
        changed_fields.add('cod_imovel')
        changes.append({'tipo': 'contrato', 'codigo': str(contrato.codigo), 'campo': 'cod_imovel', 'origem': 'mutuario:codimovel'})

    if not contrato.cod_imovel and contrato.conjunto:
        moda = cat_mode(cod_imovel_por_conjunto[str(contrato.conjunto).strip()])
        if moda:
            contrato.cod_imovel = moda
            changed_fields.add('cod_imovel')
            changes.append({'tipo': 'contrato', 'codigo': str(contrato.codigo), 'campo': 'cod_imovel', 'origem': 'contrato:moda-conjunto'})

    if not contrato.ocorrencia:
        contrato.ocorrencia = moda_ocorrencia
        changed_fields.add('ocorrencia')
        changes.append({'tipo': 'contrato', 'codigo': str(contrato.codigo), 'campo': 'ocorrencia', 'origem': 'contrato:moda-global'})

    if not contrato.cat_prof and contrato.conjunto:
        moda_cat = cat_mode(cat_prof_por_conjunto[str(contrato.conjunto).strip()])
        if moda_cat:
            contrato.cat_prof = moda_cat
            changed_fields.add('cat_prof')
            changes.append({'tipo': 'contrato', 'codigo': str(contrato.codigo), 'campo': 'cat_prof', 'origem': 'contrato:moda-conjunto'})

    return changed_fields


def cat_mode(counter_obj):
    if not counter_obj:
        return ''
    return counter_obj.most_common(1)[0][0]


def apply_derived_mutuario_rules(mutuario, contrato, changes):
    changed_fields = set()
    endereco_fk = getattr(mutuario, 'endereco_fk', None)
    for field in ['endereco', 'numero', 'compl', 'bairro', 'cidade', 'cep', 'uf']:
        current = getattr(mutuario, field, None)
        fallback = getattr(endereco_fk, field, None) if endereco_fk else None
        if is_missing_model_value(field, current) and not is_missing_model_value(field, fallback):
            setattr(mutuario, field, fallback)
            changed_fields.add(field)
            changes.append({'tipo': 'mutuario', 'codigo': str(mutuario.codigo), 'campo': field, 'origem': 'endereco_fk'})

    if mutuario.cep:
        novo_cep = sanitize_cep(mutuario.cep)
        if novo_cep and novo_cep != mutuario.cep:
            mutuario.cep = novo_cep
            changed_fields.add('cep')
            changes.append({'tipo': 'mutuario', 'codigo': str(mutuario.codigo), 'campo': 'cep', 'origem': 'normalizacao:cep'})

    if not mutuario.codimovel and contrato and contrato.cod_imovel:
        mutuario.codimovel = contrato.cod_imovel
        changed_fields.add('codimovel')
        changes.append({'tipo': 'mutuario', 'codigo': str(mutuario.codigo), 'campo': 'codimovel', 'origem': 'contrato:cod_imovel'})

    if (mutuario.renda is None or Decimal(str(mutuario.renda or 0)) == 0) and getattr(mutuario, 'crenda', None):
        mutuario.renda = mutuario.crenda
        changed_fields.add('renda')
        changes.append({'tipo': 'mutuario', 'codigo': str(mutuario.codigo), 'campo': 'renda', 'origem': 'mutuario:crenda'})

    if (mutuario.crenda is None or Decimal(str(mutuario.crenda or 0)) == 0) and getattr(mutuario, 'renda', None):
        mutuario.crenda = mutuario.renda
        changed_fields.add('crenda')
        changes.append({'tipo': 'mutuario', 'codigo': str(mutuario.codigo), 'campo': 'crenda', 'origem': 'mutuario:renda'})

    return changed_fields


def quality_snapshot(limit=None):
    contratos = Contrato.objects.order_by('id')
    if limit:
        contratos = contratos[:limit]

    contadores = Counter()
    exemplos = defaultdict(list)
    for contrato in contratos:
        relatorio = AgenteQualidadeContrato(contrato=contrato).inspecionar()
        for item in relatorio.avisos:
            chave = f'{item.categoria}.{item.campo}'
            contadores[chave] += 1
            if len(exemplos[chave]) < 5:
                exemplos[chave].append(str(contrato.codigo))
    return {
        'avisos_por_campo': dict(contadores.most_common()),
        'exemplos': dict(exemplos),
    }


def fh1_snapshot():
    contratos = list(Contrato.objects.order_by('id'))
    with redirect_stdout(io.StringIO()):
        lote = gerar_lote_fh1_separado(contratos, matricula='00044', numero_lote='001')
    pre = run_fh1_precheck_agent(lote.get('header_conteudo', ''), lote.get('dados_conteudo', ''), expected_ufs='33', expected_matricula='000442')
    return {
        'total_fichas': lote.get('total_fichas', 0),
        'total_fichas_sucesso': lote.get('total_fichas_sucesso', 0),
        'total_fichas_erro': lote.get('total_fichas_erro', 0),
        'erros_geracao': lote.get('erros', []),
        'precheck_ok': pre.get('ok', False),
        'precheck_erros': pre.get('errors', []),
    }


def run(modo='analisar'):
    apply_changes = modo == 'aplicar'
    sources = load_source_maps()
    contratos = list(Contrato.objects.order_by('id'))
    contrato_to_mutuario, mutuarios = build_mutuario_maps()
    moda_ocorrencia, cat_prof_por_conjunto, cod_imovel_por_conjunto = summarize_modes(contratos)

    before_quality = quality_snapshot()
    before_fh1 = fh1_snapshot()
    changes = []

    after_quality = None
    after_fh1 = None
    with transaction.atomic():
        for contrato in contratos:
            mutuario = linked_mutuario(contrato, contrato_to_mutuario, mutuarios)

            contrato_fields = set()
            contrato_fields |= apply_contract_sources(contrato, sources, changes)
            contrato_fields |= apply_derived_contract_rules(contrato, mutuario, moda_ocorrencia, cat_prof_por_conjunto, cod_imovel_por_conjunto, changes)
            if contrato_fields:
                contrato.save(update_fields=sorted(contrato_fields))

            if not mutuario:
                continue

            mutuario_fields = set()
            mutuario_fields |= apply_mutuario_sources(mutuario, sources, changes)
            mutuario_fields |= apply_derived_mutuario_rules(mutuario, contrato, changes)
            if mutuario_fields:
                mutuario.save(update_fields=sorted(mutuario_fields))

        after_quality = quality_snapshot()
        after_fh1 = fh1_snapshot()
        if not apply_changes:
            transaction.set_rollback(True)

    resumo_alteracoes = Counter(f"{item['tipo']}.{item['campo']}" for item in changes)
    return {
        'modo': modo,
        'executado_em': datetime.now().isoformat(),
        'fontes_dbf': [s['file'] for s in sources],
        'defaults_controlados': {
            'ocorrencia_global': moda_ocorrencia,
        },
        'antes': {
            'qualidade': before_quality,
            'fh1': before_fh1,
        },
        'alteracoes': {
            'total': len(changes),
            'por_campo': dict(resumo_alteracoes.most_common()),
            'amostra': changes[:100],
        },
        'depois': {
            'qualidade': after_quality,
            'fh1': after_fh1,
        },
    }


class nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--modo', choices=['analisar', 'aplicar'], default='analisar')
    args = parser.parse_args()
    print(json.dumps(run(args.modo), ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()