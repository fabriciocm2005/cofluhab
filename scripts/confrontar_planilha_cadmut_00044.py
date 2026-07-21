"""
Confronta a planilha CADMUT 00044 COFLUHAB enviada pela CEF com o banco local.

Gera um CSV com um registro por linha da planilha, classificando:
- contrato ausente no banco
- mutuário ausente no banco
- divergência de nome
- divergência de endereço
- divergência em ambos
- ok

Uso:
  python cofluhab/scripts/confrontar_planilha_cadmut_00044.py
"""

import csv
import os
import re
import sys
import json
import unicodedata
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher

import django

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cofluhab.settings")
django.setup()

from principal.models import Contrato, Mutuario


CSV_PATH = os.path.join(PROJECT_ROOT, "manual", "Cadmut 00044 COFLUHAB.csv")
EXPORT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "exports"))

ADDRESS_STOPWORDS = {
    "R", "RUA", "AV", "AVENIDA", "ESTR", "ESTRADA", "ETR", "TR", "TRAVESSA",
    "LOT", "LOTE", "QD", "QUADRA", "Q", "CASA", "AP", "APT", "BLOCO", "CJ",
    "CONJ", "CONJUNTO", "PRQ", "PARQUE", "RESIDENCIAL", "FASE", "SN", "S", "N",
}

ADDRESS_REPLACEMENTS = {
    " ET R ": " ESTRADA ",
    " ETR ": " ESTRADA ",
    " ESTR ": " ESTRADA ",
    " AV ": " AVENIDA ",
    " R ": " RUA ",
    " TR ": " TRAVESSA ",
    " LOT ": " LOTE ",
    " PRQ ": " PARQUE ",
    " RESID ": " RESIDENCIAL ",
    " CONS ": " CONSELHEIRO ",
}

STRUCTURED_TOKEN_RE = re.compile(r"^(?:L|Q)?[0-9]+[A-Z]?$|^Q[A-Z0-9]+$|^L[A-Z0-9]+$")
C_BROKEN_PATTERN = re.compile(r"(?<=[A-Z])[_\u0080\u0081\u0082\u0083\u0084\u0085\u0086\u0087\u0088\u0089\u008A\u008B\u008C\u008D\u008E\u008F\u0090\u0091\u0092\u0093\u0094\u0095\u0096\u0097\u0098\u0099\u009A\u009B\u009C\u009D\u009E\u009F](?=[A-Z])")


def strip_accents(value):
    return "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))


def normalize_spaces(value):
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value):
    text = str(value or "").replace("\ufeff", "").replace('"', " ")
    text = strip_accents(text.upper())
    text = f" {text} "
    for old, new in ADDRESS_REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r"\bFASE\s+II\b", "FASE 2", text)
    text = re.sub(r"\bFASE\s+I\b", "FASE 1", text)
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    text = re.sub(r"\bL\s+(\d+[A-Z]?)\b", r"L\1", text)
    text = re.sub(r"\bQ\s+(\d+[A-Z]?)\b", r"Q\1", text)
    text = re.sub(r"\bQ\s+([A-Z])\b", r"Q\1", text)
    text = re.sub(r"\bLOTE\s+(\d+[A-Z]?)\b", r"L\1", text)
    text = re.sub(r"\bL0+(\d+[A-Z]?)\b", r"L\1", text)
    text = re.sub(r"\bQ0+(\d+[A-Z]?)\b", r"Q\1", text)
    return normalize_spaces(text)


def normalize_contract_code(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    return str(int(digits))


def sanitize_export_text(value):
    text = str(value or "")
    text = text.replace("\ufeff", "")
    text = C_BROKEN_PATTERN.sub("C", text)
    text = text.replace("\u0080", "C")
    text = text.replace("_", "C")
    text = strip_accents(text)
    text = "".join(ch if ch.isprintable() else " " for ch in text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_db_address(mutuario):
    parts = [
        getattr(mutuario, "endereco", "") or "",
        getattr(mutuario, "numero", "") or "",
        getattr(mutuario, "compl", "") or "",
        getattr(mutuario, "bairro", "") or "",
        getattr(mutuario, "cidade", "") or "",
        getattr(mutuario, "uf", "") or "",
    ]
    return normalize_spaces(" ".join(str(part).strip() for part in parts if str(part).strip()))


def tokenize_address(value):
    tokens = []
    for token in normalize_text(value).split():
        if token in ADDRESS_STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def address_matches(sheet_address, db_address):
    sheet_norm = normalize_text(sheet_address)
    db_norm = normalize_text(db_address)
    if not sheet_norm or not db_norm:
        return False
    if sheet_norm == db_norm:
        return True
    if sheet_norm in db_norm or db_norm in sheet_norm:
        return True

    ratio = SequenceMatcher(None, sheet_norm, db_norm).ratio()
    if ratio >= 0.82:
        return True

    sheet_tokens = tokenize_address(sheet_address)
    db_tokens = tokenize_address(db_address)
    if not sheet_tokens or not db_tokens:
        return False

    sheet_set = set(sheet_tokens)
    db_set = set(db_tokens)
    common = sheet_set & db_set
    overlap = len(common) / max(1, min(len(sheet_set), len(db_set)))

    sheet_structured = {token for token in sheet_tokens if STRUCTURED_TOKEN_RE.match(token)}
    db_structured = {token for token in db_tokens if STRUCTURED_TOKEN_RE.match(token)}
    if sheet_structured and db_structured:
        structured_overlap = len(sheet_structured & db_structured) / len(sheet_structured)
        if structured_overlap < 0.6:
            return False

    return overlap >= 0.55


def classify_row(contrato, mutuario, sheet_name, sheet_address):
    if not contrato:
        return "contrato_ausente"
    if not mutuario:
        return "mutuario_ausente"

    name_match = normalize_text(sheet_name) == normalize_text(mutuario.nome)
    addr_match = address_matches(sheet_address, build_db_address(mutuario))

    if name_match and addr_match:
        return "ok"
    if not name_match and not addr_match:
        return "divergencia_nome_endereco"
    if not name_match:
        return "divergencia_nome"
    return "divergencia_endereco"


def load_sheet_rows():
    rows = []
    with open(CSV_PATH, "r", encoding="latin-1", newline="") as file_obj:
        reader = csv.reader(file_obj, delimiter=";")
        for line_number, row in enumerate(reader, start=1):
            if not row:
                continue
            contrato_codigo = normalize_contract_code(row[9] if len(row) > 9 else "")
            sheet_name = normalize_spaces((row[0] if len(row) > 0 else "").replace("\ufeff", "").replace('"', ""))
            sheet_address = normalize_spaces(row[5] if len(row) > 5 else "")
            rows.append({
                "line_number": line_number,
                "sheet_name": sheet_name,
                "sheet_contract": contrato_codigo,
                "sheet_address": sheet_address,
                "sheet_city_code": normalize_spaces(row[6] if len(row) > 6 else ""),
                "sheet_uf": normalize_spaces(row[7] if len(row) > 7 else ""),
                "sheet_matricula": normalize_spaces(row[8] if len(row) > 8 else ""),
                "sheet_status": normalize_spaces(row[19] if len(row) > 19 else ""),
                "sheet_programa": normalize_spaces(row[22] if len(row) > 22 else ""),
                "sheet_ref": normalize_spaces(row[33] if len(row) > 33 else ""),
            })
    return rows


def export_report(sheet_rows, contratos_map, mutuarios_map):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(EXPORT_DIR, f"confronto_cadmut_00044_{timestamp}.csv")

    fieldnames = [
        "line_number",
        "classificacao",
        "sheet_contract",
        "sheet_name",
        "sheet_address",
        "db_contrato",
        "db_nome",
        "db_endereco",
        "db_conjunto",
        "db_ocorrencia",
        "name_match",
        "address_match",
        "sheet_status",
        "sheet_programa",
        "sheet_ref",
    ]

    summary = Counter()
    missing_contract_codes = []
    valid_sheet_contracts = 0

    with open(output_path, "w", encoding="utf-8-sig", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for row in sheet_rows:
            contract_code = row["sheet_contract"]
            contrato = contratos_map.get(contract_code)
            mutuario = mutuarios_map.get(contract_code)
            classification = classify_row(contrato, mutuario, row["sheet_name"], row["sheet_address"])

            if contract_code:
                valid_sheet_contracts += 1
            if classification == "contrato_ausente" and contract_code:
                missing_contract_codes.append(contract_code)

            name_match = bool(mutuario and normalize_text(row["sheet_name"]) == normalize_text(mutuario.nome))
            db_address = build_db_address(mutuario) if mutuario else ""
            addr_match = bool(mutuario and address_matches(row["sheet_address"], db_address))
            summary[classification] += 1

            writer.writerow({
                "line_number": row["line_number"],
                "classificacao": classification,
                "sheet_contract": contract_code,
                "sheet_name": sanitize_export_text(row["sheet_name"]),
                "sheet_address": sanitize_export_text(row["sheet_address"]),
                "db_contrato": sanitize_export_text(getattr(contrato, "codigo", "") if contrato else ""),
                "db_nome": sanitize_export_text(getattr(mutuario, "nome", "") if mutuario else ""),
                "db_endereco": sanitize_export_text(db_address),
                "db_conjunto": sanitize_export_text(getattr(contrato, "conjunto", "") if contrato else ""),
                "db_ocorrencia": sanitize_export_text(getattr(contrato, "ocorrencia", "") if contrato else ""),
                "name_match": "SIM" if name_match else "NAO",
                "address_match": "SIM" if addr_match else "NAO",
                "sheet_status": sanitize_export_text(row["sheet_status"]),
                "sheet_programa": sanitize_export_text(row["sheet_programa"]),
                "sheet_ref": sanitize_export_text(row["sheet_ref"]),
            })

    return {
        "output_path": output_path,
        "total_linhas_planilha": len(sheet_rows),
        "contratos_validos_planilha": valid_sheet_contracts,
        "resumo": dict(summary),
        "amostra_contratos_ausentes": missing_contract_codes[:20],
    }


def main():
    sheet_rows = load_sheet_rows()
    contratos_map = {normalize_contract_code(obj.codigo): obj for obj in Contrato.objects.all().only("codigo", "conjunto", "ocorrencia")}
    mutuarios_map = {normalize_contract_code(obj.codigo): obj for obj in Mutuario.objects.all().only("codigo", "nome", "endereco", "numero", "compl", "bairro", "cidade", "uf")}

    result = export_report(sheet_rows, contratos_map, mutuarios_map)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()