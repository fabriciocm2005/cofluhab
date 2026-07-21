"""
Backfill em cascata de cadastro/contrato usando fontes DBF legadas.

Ordem de prioridade validada pela auditoria:
1) CADBAK.DBF
2) CAD1.DBF
3) CAD2.DBF
4) cad1012.dbf
5) CADMUT270204.DBF

Uso:
  python cofluhab/scripts/backfill_cadastro_cascade.py
"""

import os
import sys
import json
import io
import re
from contextlib import redirect_stdout
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import django
from dbfread import DBF

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cofluhab.settings")
django.setup()

from django.db import transaction
from principal.models import Contrato, Mutuario
from principal.ficha_generators import gerar_lote_fh1_separado
from principal.fh1_validator import run_fh1_precheck_agent


DBF_SOURCES = [
    "CADBAK.DBF",
    "CAD1.DBF",
    "CAD2.DBF",
    "cad1012.dbf",
    "CADMUT270204.DBF",
    "CADMUT2.DBF",
    "cadmutbk.dbf",
    "CADMUT_2.DBF",
    "CADOK.DBF",
    "CADMUT__BK.DBF",
    "cofluhab.dbf",
]

BASE_DIR = os.path.join(PROJECT_ROOT, "dados_antigos")

CONTRATO_FIELD_MAP = {
    "cod_imovel": ["CODIMOVEL"],
    "data_contrato": ["DTASSIN", "DATA_CONT"],
    "data_primeiro_venc": ["PRIMVENC"],
    "sa": ["SA", "SIST_AMORT"],
    "tx_juros": ["TXJUROS", "TAXA_JUROS"],
    "prazo": ["PRAZO"],
    "cat_prof": ["CATPROF"],
    "pr": ["PR", "PLANO"],
}

MUTUARIO_FIELD_MAP = {
    "codimovel": ["CODIMOVEL"],
    "conjunto": ["CONJUNTO"],
    "conjseg": ["CONJSEG"],
    "nome": ["NOME"],
    "ident": ["IDENT"],
    "orgao": ["ORGAO"],
    "dtnasc": ["DTNASC"],
    "cpf": ["CPF"],
    "renda": ["RENDA"],
    "crenda": ["CRENDA"],
    "endereco": ["ENDERECO"],
    "numero": ["NUMERO"],
    "compl": ["COMPL"],
    "tipoimovel": ["TIPOIMOVEL"],
    "bairro": ["BAIRRO"],
    "cidade": ["CIDADE", "MUNICIPIO"],
    "cep": ["CEP"],
    "uf": ["UF"],
}

CONTRATO_CRITICOS = [
    "data_contrato",
    "data_primeiro_venc",
    "sa",
    "tx_juros",
    "prazo",
    "cat_prof",
    "pr",
]

MUTUARIO_CRITICOS = [
    "endereco",
    "numero",
    "cidade",
    "cep",
    "uf",
]

NUMERO_FROM_ENDERECO_PATTERNS = [
    re.compile(r",\s*-\s*L\s*(\d{1,5}[A-Z]?)\b", re.IGNORECASE),
    re.compile(r",\s*(\d{1,5}[A-Z]?)\b"),
    re.compile(r"\bL\s*(\d{1,5}[A-Z]?)\b", re.IGNORECASE),
]


def normalize_code(value):
    text = to_text(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return ""
    return str(int(digits))


def to_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("latin-1", errors="ignore").strip()
    return str(value).strip()


def parse_date(value):
    text = to_text(value)
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) != 8:
        return None
    try:
        year = int(digits[0:4])
        month = int(digits[4:6])
        day = int(digits[6:8])
        return date(year, month, day)
    except ValueError:
        return None


def parse_decimal(value):
    text = to_text(value)
    if not text:
        return None
    text = text.replace(" ", "").replace(",", ".")
    try:
        dec = Decimal(text)
    except InvalidOperation:
        return None
    return dec


def parse_int(value):
    text = to_text(value)
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def extract_numero_from_endereco(value):
    text = to_text(value)
    if not text:
        return None
    for pattern in NUMERO_FROM_ENDERECO_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def source_value_to_model(model_field, raw_value):
    if model_field in {"data_contrato", "data_primeiro_venc", "dtnasc"}:
        return parse_date(raw_value)
    if model_field in {"tx_juros", "renda", "crenda"}:
        return parse_decimal(raw_value)
    if model_field == "prazo":
        return parse_int(raw_value)
    return to_text(raw_value)


def is_missing_model_value(model_field, value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if model_field in {"tx_juros", "renda", "crenda"}:
        try:
            return Decimal(value) == 0
        except Exception:
            return False
    if model_field == "prazo":
        try:
            return int(value) == 0
        except Exception:
            return False
    return False


def is_useful_source_value(model_field, value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if model_field in {"tx_juros", "renda", "crenda"}:
        return value != 0
    if model_field == "prazo":
        return value != 0
    return True


def load_source_maps():
    sources = []
    for file_name in DBF_SOURCES:
        path = os.path.join(BASE_DIR, file_name)
        if not os.path.exists(path):
            continue
        table = DBF(path, raw=True, encoding="latin-1", ignore_missing_memofile=True)
        field_map = {f.upper(): f for f in table.field_names}
        cod_field = field_map.get("CODIGO") or field_map.get("CTR_AGENTE")
        if not cod_field:
            continue
        by_code = {}
        for record in table:
            code = normalize_code(record.get(cod_field))
            if not code:
                continue
            if code not in by_code:
                by_code[code] = record
        sources.append({
            "file": file_name,
            "rows": len(by_code),
            "field_map": field_map,
            "records": by_code,
        })
    return sources


def pick_from_sources(code, model_field, source_fields, sources):
    for source in sources:
        rec = source["records"].get(code)
        if not rec:
            continue
        for source_field in source_fields:
            real_field = source["field_map"].get(source_field)
            if not real_field:
                continue
            candidate = source_value_to_model(model_field, rec.get(real_field))
            if is_useful_source_value(model_field, candidate):
                return candidate, source["file"]
        if model_field == "numero":
            endereco_field = source["field_map"].get("ENDERECO")
            if endereco_field:
                extracted = extract_numero_from_endereco(rec.get(endereco_field))
                if is_useful_source_value(model_field, extracted):
                    return extracted, source["file"]
    return None, None


def gather_stats():
    contrato_total = Contrato.objects.count()
    mutuario_total = Mutuario.objects.count()

    contrato_missing = {
        f: sum(1 for c in Contrato.objects.all().only(*CONTRATO_CRITICOS) if is_missing_model_value(f, getattr(c, f, None)))
        for f in CONTRATO_CRITICOS
    }
    mutuario_missing = {
        f: sum(1 for m in Mutuario.objects.all().only(*MUTUARIO_CRITICOS) if is_missing_model_value(f, getattr(m, f, None)))
        for f in MUTUARIO_CRITICOS
    }

    return {
        "contrato_total": contrato_total,
        "mutuario_total": mutuario_total,
        "contrato_missing": contrato_missing,
        "mutuario_missing": mutuario_missing,
    }


def run_backfill(sources):
    contrato_updates = 0
    mutuario_updates = 0
    contrato_by_source = {s["file"]: 0 for s in sources}
    mutuario_by_source = {s["file"]: 0 for s in sources}

    with transaction.atomic():
        contratos = list(Contrato.objects.all())
        for contrato in contratos:
            code = normalize_code(contrato.codigo)
            if not code:
                continue
            changed = False
            used_sources = set()
            for model_field, source_fields in CONTRATO_FIELD_MAP.items():
                current = getattr(contrato, model_field)
                if not is_missing_model_value(model_field, current):
                    continue
                picked, src = pick_from_sources(code, model_field, source_fields, sources)
                if not is_useful_source_value(model_field, picked):
                    continue
                setattr(contrato, model_field, picked)
                changed = True
                if src:
                    used_sources.add(src)
            if changed:
                contrato.save(update_fields=list(CONTRATO_FIELD_MAP.keys()))
                contrato_updates += 1
                for src in used_sources:
                    contrato_by_source[src] += 1

        mutuarios = list(Mutuario.objects.all())
        for mutuario in mutuarios:
            code = normalize_code(mutuario.codigo)
            if not code:
                continue
            changed = False
            used_sources = set()
            for model_field, source_fields in MUTUARIO_FIELD_MAP.items():
                current = getattr(mutuario, model_field)
                if not is_missing_model_value(model_field, current):
                    continue
                picked, src = pick_from_sources(code, model_field, source_fields, sources)
                if not is_useful_source_value(model_field, picked):
                    continue
                setattr(mutuario, model_field, picked)
                changed = True
                if src:
                    used_sources.add(src)
            if changed:
                mutuario.save(update_fields=list(MUTUARIO_FIELD_MAP.keys()))
                mutuario_updates += 1
                for src in used_sources:
                    mutuario_by_source[src] += 1

    return {
        "contratos_atualizados": contrato_updates,
        "mutuarios_atualizados": mutuario_updates,
        "contratos_por_fonte": contrato_by_source,
        "mutuarios_por_fonte": mutuario_by_source,
    }


def run_fh1_precheck_snapshot():
    contratos = list(Contrato.objects.order_by("id"))
    if not contratos:
        return {"ok": False, "erro": "Sem contratos para precheck."}

    with redirect_stdout(io.StringIO()):
        lote = gerar_lote_fh1_separado(contratos, matricula="000442", numero_lote="001")
    header = lote.get("header_conteudo", "")
    dados = lote.get("dados_conteudo", "")
    pre = run_fh1_precheck_agent(header, dados, expected_ufs="33", expected_matricula="000442")

    return {
        "total_registros": pre.get("total_registros", 0),
        "ok": pre.get("ok", False),
        "total_erros": len(pre.get("errors", [])),
        "total_avisos": len(pre.get("warnings", [])),
        "erros_top10": pre.get("errors", [])[:10],
        "avisos_top10": pre.get("warnings", [])[:10],
    }


def main():
    started_at = datetime.now().isoformat()
    sources = load_source_maps()

    before = gather_stats()
    backfill = run_backfill(sources)
    after = gather_stats()
    precheck = run_fh1_precheck_snapshot()

    payload = {
        "started_at": started_at,
        "sources": [{"file": s["file"], "distinct_codes": s["rows"]} for s in sources],
        "before": before,
        "backfill": backfill,
        "after": after,
        "delta": {
            "contrato_missing_reduction": {
                k: before["contrato_missing"][k] - after["contrato_missing"][k]
                for k in CONTRATO_CRITICOS
            },
            "mutuario_missing_reduction": {
                k: before["mutuario_missing"][k] - after["mutuario_missing"][k]
                for k in MUTUARIO_CRITICOS
            },
        },
        "fh1_precheck": precheck,
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
