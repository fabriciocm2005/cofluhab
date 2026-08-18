"""Layouts fixos e interpretacao dos arquivos da avaliacao atuarial FCVS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


@dataclass(frozen=True)
class FieldSpec:
    number: int
    name: str
    start: int
    end: int
    kind: str
    decimals: int = 0

    @property
    def width(self) -> int:
        return self.end - self.start + 1


ACTIVE_FIELDS = (
    FieldSpec(1, "data_posicao", 1, 6, "date_yyyymm"),
    FieldSpec(2, "matricula_af", 7, 12, "numeric"),
    FieldSpec(3, "numero_contrato", 13, 25, "text"),
    FieldSpec(4, "hipoteca", 26, 26, "numeric"),
    FieldSpec(5, "fgts", 27, 27, "numeric"),
    FieldSpec(6, "data_nascimento", 28, 35, "date_yyyymmdd"),
    FieldSpec(7, "data_contrato", 36, 43, "date_yyyymmdd"),
    FieldSpec(8, "data_termino_prazo", 44, 49, "date_yyyymm"),
    FieldSpec(9, "plano", 50, 52, "text"),
    FieldSpec(10, "st", 53, 53, "numeric"),
    FieldSpec(11, "rj", 54, 54, "text"),
    FieldSpec(12, "rr", 55, 56, "numeric"),
    FieldSpec(13, "index", 57, 59, "text"),
    FieldSpec(14, "taxa_juros", 60, 65, "numeric", 4),
    FieldSpec(15, "sd_contabil", 66, 74, "numeric", 2),
    FieldSpec(16, "sd_pro_rata", 75, 83, "numeric", 2),
    FieldSpec(17, "sd_pro_lei_10150", 84, 92, "numeric", 2),
    FieldSpec(18, "prestacao_aj", 93, 100, "numeric", 2),
    FieldSpec(19, "razao_acres_decres", 101, 108, "numeric", 2),
    FieldSpec(20, "seguro_mip_dfi", 109, 116, "numeric", 2),
    FieldSpec(21, "seguro_credito", 117, 124, "numeric", 2),
    FieldSpec(22, "uf", 125, 126, "text"),
    FieldSpec(23, "codigo_municipio", 127, 131, "numeric"),
    FieldSpec(24, "cpf", 132, 142, "numeric"),
)

LIQUIDATED_FIELDS = (
    FieldSpec(1, "data_posicao", 1, 6, "date_yyyymm"),
    FieldSpec(2, "matricula_af", 7, 12, "numeric"),
    FieldSpec(3, "fgts", 13, 13, "numeric"),
    FieldSpec(4, "tipo_evento", 14, 16, "text"),
    FieldSpec(5, "data_evento", 17, 24, "date_yyyymmdd"),
    FieldSpec(6, "numero_contrato", 25, 37, "text"),
    FieldSpec(7, "hipoteca", 38, 38, "numeric"),
    FieldSpec(8, "sd_pos_cont", 39, 47, "numeric", 2),
    FieldSpec(9, "sd_fcvs_lei_10150", 48, 48, "numeric"),
    FieldSpec(10, "taxa_juros", 49, 54, "numeric", 4),
    FieldSpec(11, "uf", 55, 56, "text"),
    FieldSpec(12, "codigo_municipio", 57, 61, "numeric"),
    FieldSpec(13, "data_contrato", 62, 69, "date_yyyymmdd"),
    FieldSpec(14, "cpf", 70, 80, "numeric"),
)

LAYOUTS = {
    "AT": {"label": "Operacoes ativas", "length": 142, "fields": ACTIVE_FIELDS},
    "ANPH": {"label": "Ativas sem expectativa de habilitacao", "length": 142, "fields": ACTIVE_FIELDS},
    "LQ": {"label": "Operacoes liquidadas", "length": 80, "fields": LIQUIDATED_FIELDS},
    "LNPH": {"label": "Liquidadas sem expectativa de habilitacao", "length": 80, "fields": LIQUIDATED_FIELDS},
    "RNV": {"label": "Contratos com RNV", "length": 80, "fields": LIQUIDATED_FIELDS},
    "RR": {"label": "Arquivo resumo", "length": None, "fields": ()},
}

_SUFFIXES = ("ANPH", "LNPH", "RNV", "AT", "LQ", "RR")


def detect_layout(filename: str, line_lengths: Iterable[int]) -> str | None:
    stem = Path(filename).stem.upper().replace(".", "")
    for suffix in _SUFFIXES:
        if stem.endswith(suffix):
            return suffix

    lengths = set(line_lengths)
    if lengths == {142}:
        return "AT"
    if lengths == {20}:
        return "RR"
    return None


def _validate_value(field: FieldSpec, value: str) -> str | None:
    if not value:
        return None
    if field.kind == "numeric" and not value.isdigit():
        return "deve conter apenas digitos"
    if field.kind == "date_yyyymm" and not re.fullmatch(r"\d{6}", value):
        return "deve estar no formato AAAAMM"
    if field.kind == "date_yyyymmdd" and not re.fullmatch(r"\d{8}", value):
        return "deve estar no formato AAAAMMDD"
    return None


def parse_line(line: str, layout: str) -> tuple[dict[str, str], list[str]]:
    spec = LAYOUTS[layout]
    expected = spec["length"]
    errors = []
    if len(line) != expected:
        return {}, [f"comprimento {len(line)}, esperado {expected}"]

    values = {}
    for field in spec["fields"]:
        value = line[field.start - 1:field.end]
        stripped = value.strip()
        values[field.name] = stripped
        error = _validate_value(field, stripped)
        if error:
            errors.append(f"{field.name}: {error}")
    return values, errors


def parse_summary_line(line: str) -> tuple[dict[str, str], list[str]]:
    errors = []
    if len(line) == 20:
        # Arquivo historico encontrado no projeto: AAAA/MM legado em 4 posicoes.
        values = {
            "data_posicao": line[0:4],
            "matricula_af": line[4:10],
            "volume": line[10:11],
            "tipo_resumo": line[11:12].strip(),
            "quantidade": line[12:20],
            "formato": "legado",
        }
    elif len(line) in (22, 24, 25):
        code_length = {22: 1, 24: 3, 25: 4}[len(line)]
        values = {
            "data_posicao": line[0:6],
            "matricula_af": line[6:12],
            "volume": line[12:13],
            "tipo_resumo": line[13:13 + code_length].strip(),
            "quantidade": line[13 + code_length:],
            "formato": "atual",
        }
    else:
        return {}, [f"comprimento {len(line)}, esperado 20, 22, 24 ou 25"]
    if not re.fullmatch(r"\d{4,6}", values["data_posicao"]):
        errors.append("data_posicao: formato de posicao invalido")
    if not values["matricula_af"].isdigit():
        errors.append("matricula_af: deve conter apenas digitos")
    if not values["quantidade"].isdigit():
        errors.append("quantidade: deve conter apenas digitos")
    return values, errors


def analyze_file(filename: str, content: bytes) -> dict:
    text = content.decode("latin-1")
    lines = [line.rstrip("\r") for line in text.splitlines() if line.strip()]
    layout = detect_layout(filename, map(len, lines))
    if layout is None:
        return {
            "filename": filename,
            "layout": None,
            "label": "Nao identificado",
            "total_lines": len(lines),
            "valid_lines": 0,
            "invalid_lines": len(lines),
            "records": [],
            "errors": ["layout nao identificado pelo nome ou comprimento das linhas"],
        }

    records = []
    errors = []
    for number, line in enumerate(lines, 1):
        if layout == "RR":
            values, line_errors = parse_summary_line(line)
        else:
            values, line_errors = parse_line(line, layout)
        if line_errors:
            errors.append({"line": number, "messages": line_errors})
        else:
            records.append(values)

    return {
        "filename": filename,
        "layout": layout,
        "label": LAYOUTS[layout]["label"],
        "line_length": LAYOUTS[layout]["length"],
        "total_lines": len(lines),
        "valid_lines": len(records),
        "invalid_lines": len(lines) - len(records),
        "records": records[:25],
        "errors": errors[:100],
    }
