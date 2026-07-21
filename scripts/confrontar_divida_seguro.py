"""
Confronta CAD APOLICE de qualquer mes/ano com a base local.

Uso:
  python confrontar_divida_seguro.py --mes 02 --ano 2019
  python confrontar_divida_seguro.py --mes 03 --ano 2019
  python confrontar_divida_seguro.py --mes 01 --ano 2019   # retrocompativel
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional, Tuple

import django
import pdfplumber
from django.db.models import Count, Max, Min

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cofluhab.settings")
django.setup()

from principal.models import Contrato, Movimentacao, Mutuario, ParcelaContrato  # noqa: E402

EXPORT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "exports"))

LIQ_REGEX = re.compile(r"LIQ|LIQUID|QUITA|QUIT", re.IGNORECASE)
SIN_REGEX = re.compile(r"SINIST", re.IGNORECASE)
PDF_FIF_LINE = re.compile(
    r"^\s*(\d{15})\s+(.+?)\s+"
    r"(\d{1,3},\d{2})\s+"
    r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"
    r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"
    r"(\d+)$"
)
PDF_CONTRATO_LINE = re.compile(r"^\s*(\d{6})\s+\d{2}/\d{4}\s+")


def resolve_pdf_path(mes: str, ano: str) -> str:
    """Busca o PDF do CAD APOLICE em locais conhecidos."""
    candidatos = [
        os.path.join(PROJECT_ROOT, "manual", f"divida seguro {mes}_{ano}.pdf"),
        os.path.join(PROJECT_ROOT, "manual", "divida_seguro", "CAD_APOLICE", f"CAD APOLICE {mes}_{ano}.pdf"),
        os.path.join(PROJECT_ROOT, "manual", "divida_seguro", "CAD_APOLICE", f"CAD APOLICE {mes}_{ano[2:]}.pdf"),
    ]
    for p in candidatos:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        f"PDF nao encontrado para {mes}/{ano}. Tentados:\n" + "\n".join(f"  {c}" for c in candidatos)
    )


def normalize_contract_code(value: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    return str(int(digits))


def add_months(src: date, months: int) -> date:
    y = src.year + (src.month - 1 + months) // 12
    m = (src.month - 1 + months) % 12 + 1
    if m in (1, 3, 5, 7, 8, 10, 12):
        max_day = 31
    elif m in (4, 6, 9, 11):
        max_day = 30
    else:
        leap = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
        max_day = 29 if leap else 28
    d = min(src.day, max_day)
    return date(y, m, d)


def parse_value(text: str) -> float:
    if not text:
        return 0.0
    clean = text.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def extract_contracts_from_pdf(pdf_path: str) -> List[Tuple[str, str, float]]:
    results: List[Tuple[str, str, float]] = []
    seen: set = set()

    all_lines: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            all_lines.extend((page.extract_text() or "").splitlines())

    i = 0
    while i < len(all_lines):
        fif_match = PDF_FIF_LINE.match(all_lines[i])
        if fif_match:
            nome_pdf = fif_match.group(2).strip()
            premio_dfi = parse_value(fif_match.group(7))
            premio_mip = parse_value(fif_match.group(8))
            premio_crd = parse_value(fif_match.group(9))
            valor_seguro_pdf = premio_dfi + premio_mip + premio_crd

            for j in range(i + 1, min(i + 5, len(all_lines))):
                cont_match = PDF_CONTRATO_LINE.match(all_lines[j])
                if cont_match:
                    raw_code = cont_match.group(1)
                    normalized = normalize_contract_code(raw_code)
                    if normalized and normalized not in seen:
                        seen.add(normalized)
                        results.append((normalized, nome_pdf, valor_seguro_pdf))
                    i = j
                    break
        i += 1

    return results


def map_contracts() -> Dict[str, Contrato]:
    contract_map: Dict[str, Contrato] = {}
    for contract in Contrato.objects.all().only("id", "codigo", "ocorrencia", "prazo"):
        code = normalize_contract_code(contract.codigo)
        if code and code not in contract_map:
            contract_map[code] = contract
    return contract_map


def map_mutuario_names() -> Dict[str, str]:
    names: Dict[str, str] = {}
    for m in Mutuario.objects.all().only("codigo", "nome"):
        code = normalize_contract_code(m.codigo)
        if code and code not in names:
            names[code] = (m.nome or "").strip()
    return names


def meses_entre_datas(data1: Optional[date], data2: date) -> int:
    if not data1:
        return 0
    anos_diff = data2.year - data1.year
    meses_diff = data2.month - data1.month
    total_meses = anos_diff * 12 + meses_diff
    return max(0, total_meses)


def map_parcelas_stats(contract_ids: Iterable[int]) -> Dict[int, dict]:
    stats = (
        ParcelaContrato.objects.filter(contrato_id__in=list(contract_ids))
        .values("contrato_id")
        .annotate(
            qtd=Count("id"),
            max_nmens=Max("nmens"),
            first_venc=Min("dtvenc"),
            last_venc=Max("dtvenc"),
            last_pgto=Max("dtpgto"),
        )
    )
    return {row["contrato_id"]: row for row in stats}


def load_movements_for_contract(contract: Contrato) -> List[Movimentacao]:
    q = Movimentacao.objects.none()
    code = normalize_contract_code(contract.codigo)
    if code:
        q = q | Movimentacao.objects.filter(codigo=code)
        q = q | Movimentacao.objects.filter(codigo=str(contract.codigo).strip())
    if getattr(contract, "cod_imovel", ""):
        q = q | Movimentacao.objects.filter(codimovel=str(contract.cod_imovel).strip())
    return list(q.order_by("data").only("data", "tipo", "descricao", "valor"))


def classify_finalization(contract: Contrato, parcela_info: Optional[dict], movements: List[Movimentacao]) -> Tuple[str, Optional[date], str]:
    ocorr = (contract.ocorrencia or "").strip().upper()

    liquid_dates: List[date] = []
    sin_dates: List[date] = []
    for mov in movements:
        blob = f"{mov.tipo or ''} {mov.descricao or ''}"
        if mov.data and LIQ_REGEX.search(blob):
            liquid_dates.append(mov.data)
        if mov.data and SIN_REGEX.search(blob):
            sin_dates.append(mov.data)

    liq_date = max(liquid_dates) if liquid_dates else None
    sin_date = max(sin_dates) if sin_dates else None

    prazo = contract.prazo or 0
    first_venc = parcela_info.get("first_venc") if parcela_info else None
    last_venc = parcela_info.get("last_venc") if parcela_info else None
    last_pgto = parcela_info.get("last_pgto") if parcela_info else None
    max_nmens = parcela_info.get("max_nmens") if parcela_info else None

    prazo_end = None
    if first_venc and prazo and prazo > 0:
        prazo_end = add_months(first_venc, prazo - 1)

    reached_prazo = bool(prazo and max_nmens and max_nmens >= prazo)

    if liq_date or ocorr == "LIQ":
        return "LIQUIDACAO", liq_date or last_pgto or last_venc or prazo_end, f"ocorrencia={ocorr}; movimentos_liq={len(liquid_dates)}"

    if sin_date or ocorr == "SIT":
        return "SINISTRO", sin_date or last_pgto or last_venc or prazo_end, f"ocorrencia={ocorr}; movimentos_sinistro={len(sin_dates)}"

    if reached_prazo or ocorr == "TPZ":
        return "PRAZO_FINALIZADO", prazo_end or last_venc or last_pgto, f"ocorrencia={ocorr}; prazo={prazo}; max_nmens={max_nmens or 0}"

    if ocorr:
        return f"EVENTO_{ocorr}", last_pgto or last_venc or prazo_end, f"ocorrencia={ocorr}"

    return "SEM_EVIDENCIA_FORTE", last_pgto or last_venc or prazo_end, "sem ocorrencia e sem movimento"


def build_report_rows(pdf_entries: List[Tuple[str, str, float]], data_cobranca: date) -> List[dict]:
    contracts = map_contracts()
    mutuario_names = map_mutuario_names()
    contract_ids = [obj.id for obj in contracts.values()]
    parcelas_stats = map_parcelas_stats(contract_ids)

    rows: List[dict] = []
    for code, nome_pdf, valor_seguro_pdf in pdf_entries:
        contract = contracts.get(code)
        if not contract:
            rows.append({
                "contrato_pdf": code,
                "contrato_db": "",
                "nome_mutuario": nome_pdf,
                "status_confronto": "NAO_ENCONTRADO_NO_BANCO",
                "motivo_finalizacao": "",
                "data_finalizacao": "",
                "data_cobranca_cef": data_cobranca.strftime("%d/%m/%Y"),
                "meses_apos_finalizacao": "",
                "valor_seguro_pdf": f"{valor_seguro_pdf:.2f}".replace(".", ","),
            })
            continue

        pinfo = parcelas_stats.get(contract.id, {})
        movements = load_movements_for_contract(contract)
        reason, final_date, _ = classify_finalization(contract, pinfo, movements)
        nome = nome_pdf or mutuario_names.get(normalize_contract_code(contract.codigo), "")

        rows.append({
            "contrato_pdf": code,
            "contrato_db": str(contract.codigo),
            "nome_mutuario": nome,
            "status_confronto": "ENCONTRADO",
            "motivo_finalizacao": reason,
            "data_finalizacao": final_date.strftime("%d/%m/%Y") if final_date else "",
            "data_cobranca_cef": data_cobranca.strftime("%d/%m/%Y"),
            "meses_apos_finalizacao": meses_entre_datas(final_date, data_cobranca),
            "valor_seguro_pdf": f"{valor_seguro_pdf:.2f}".replace(".", ","),
        })

    return rows


def export_outputs(rows: List[dict], total_pdf_contracts: int, mes: str, ano: str, data_cobranca: date) -> Tuple[str, str]:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    periodo = f"{mes}{ano}"

    csv_path = os.path.join(EXPORT_DIR, f"confronto_divida_seguro_{periodo}_{ts}.csv")
    md_path = os.path.join(EXPORT_DIR, f"laudo_divida_seguro_{periodo}_{ts}.md")

    fields = [
        "contrato_pdf", "contrato_db", "nome_mutuario", "status_confronto",
        "motivo_finalizacao", "data_finalizacao", "data_cobranca_cef",
        "meses_apos_finalizacao", "valor_seguro_pdf",
    ]

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    found_rows = [r for r in rows if r["status_confronto"] == "ENCONTRADO"]
    missing_rows = [r for r in rows if r["status_confronto"] != "ENCONTRADO"]
    reasons = Counter(r["motivo_finalizacao"] for r in found_rows if r["motivo_finalizacao"])
    valores_pdf = [float(r["valor_seguro_pdf"].replace(",", ".")) for r in rows if r.get("valor_seguro_pdf")]
    total_seguro_pdf = sum(valores_pdf)

    md_lines = [
        f"# Laudo de Confrontacao - Divida Seguro {mes}/{ano}",
        "",
        f"- Data de geracao: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"- Data da cobranca CEF: {data_cobranca.strftime('%d/%m/%Y')}",
        f"- Contratos extraidos do PDF: {total_pdf_contracts}",
        f"- Contratos encontrados na base: {len(found_rows)}",
        f"- Contratos nao encontrados na base: {len(missing_rows)}",
        "",
        "## Distribuicao por motivo de finalizacao",
    ]
    for reason, count in reasons.most_common():
        md_lines.append(f"- {reason}: {count}")

    total_fmt = f"{total_seguro_pdf:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    md_lines.extend([
        "",
        "## Analise Financeira",
        f"- **Total seguro no PDF**: R$ {total_fmt}",
        "",
        f"## Arquivo detalhado",
        f"- CSV: {csv_path}",
    ])

    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(md_lines))

    return csv_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Confronta CAD APOLICE com base local.")
    parser.add_argument("--mes", required=True, help="Mes de referencia (ex: 01, 02, 03)")
    parser.add_argument("--ano", required=True, help="Ano de referencia (ex: 2019)")
    args = parser.parse_args()

    mes = args.mes.zfill(2)
    ano = args.ano

    try:
        pdf_path = resolve_pdf_path(mes, ano)
    except FileNotFoundError as e:
        print(f"ERRO: {e}")
        return 1

    print(f"PDF: {pdf_path}")
    pdf_entries = extract_contracts_from_pdf(pdf_path)
    if not pdf_entries:
        print("ERRO: Nenhum contrato extraido do PDF.")
        return 1

    print(f"Contratos extraidos: {len(pdf_entries)}")

    mes_int = int(mes)
    ano_int = int(ano)
    data_cobranca = date(ano_int, mes_int, 1)

    rows = build_report_rows(pdf_entries, data_cobranca)
    csv_path, md_path = export_outputs(rows, len(pdf_entries), mes, ano, data_cobranca)

    print("OK")
    print(f"CONTRATOS_PDF={len(pdf_entries)}")
    print(f"CSV={csv_path}")
    print(f"LAUDO={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
