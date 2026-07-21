"""
Confronta o relatorio PDF "divida seguro 01_2019.pdf" com a base local.

Objetivo:
- Extrair contratos cobrados no relatorio de seguro de jan/2019
- Identificar, para cada contrato, evidencias de finalizacao
  (prazo, liquidacao, sinistro ou outro evento)
- Gerar relatorio probatorio (CSV + Markdown)

Uso:
  c:/Users/fabri/cofluhab/venv_django/Scripts/python.exe cofluhab/scripts/confrontar_divida_seguro_012019.py
"""

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


PDF_PATH = os.path.join(PROJECT_ROOT, "manual", "divida seguro 01_2019.pdf")
DATA_COBRANCA_CEF = date(2019, 1, 1)
EXPORT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "exports"))

LIQ_REGEX = re.compile(r"LIQ|LIQUID|QUITA|QUIT", re.IGNORECASE)
SIN_REGEX = re.compile(r"SINIST", re.IGNORECASE)
# Linha 1 do par: NUM.FIF (15 d) + NOME + PERC + 3xBASE + 3xPRM + PRZ
# Captura: NUM.FIF, NOME, e todos os valores numéricos (base + prêmios + prazo)
PDF_FIF_LINE = re.compile(
    r"^\s*(\d{15})\s+(.+?)\s+"  # NUM.FIF + NOME
    r"(\d{1,3},\d{2})\s+"  # PERC1
    r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"  # 3x BASE
    r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"  # 3x PRM (DFI, MIP, CRD)
    r"(\d+)$"  # PRZ
)
# Linha 2 do par: NUM.CONTRATO (6 dígitos) + DT.RIE (mm/aaaa)
PDF_CONTRATO_LINE = re.compile(r"^\s*(\d{6})\s+\d{2}/\d{4}\s+")


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
    """Parse valor monetário brasileiro (ex: 1.234,56 → 1234.56)."""
    if not text:
        return 0.0
    clean = text.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def extract_contracts_from_pdf(pdf_path: str) -> List[Tuple[str, str, float]]:
    """Retorna lista de (codigo_normalizado, nome_do_pdf, valor_seguro_pdf) extraídos do PDF.
    O nome vem da linha NUM.FIF (15 dígitos) imediatamente antes da linha NUM.CONTRATO.
    O valor de seguro do PDF eh calculado como soma direta:
      PRM-DFI + PRM-MIP + PRM-CRD
    Todas as páginas são concatenadas antes do pareamento para capturar pares
    que quebram entre páginas.
    """
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
            
            # Procura a próxima linha com NUM.CONTRATO (até 4 linhas à frente)
            for j in range(i + 1, min(i + 5, len(all_lines))):
                cont_match = PDF_CONTRATO_LINE.match(all_lines[j])
                if cont_match:
                    raw_code = cont_match.group(1)
                    normalized = normalize_contract_code(raw_code)
                    if normalized and normalized not in seen:
                        seen.add(normalized)
                        results.append((normalized, nome_pdf, valor_seguro_pdf))
                    i = j  # avança para a linha do contrato
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
    """Retorna dict {codigo_normalizado: nome} a partir do modelo Mutuario."""
    names: Dict[str, str] = {}
    for m in Mutuario.objects.all().only("codigo", "nome"):
        code = normalize_contract_code(m.codigo)
        if code and code not in names:
            names[code] = (m.nome or "").strip()
    return names


def meses_entre_datas(data1: Optional[date], data2: date) -> int:
    """Calcula diferença em meses entre duas datas.
    Retorna número de meses (positivo se data2 > data1).
    """
    if not data1:
        return 0
    anos_diff = data2.year - data1.year
    meses_diff = data2.month - data1.month
    total_meses = anos_diff * 12 + meses_diff
    return max(0, total_meses)


def distancia_cobranca(final_date: Optional[date]) -> Tuple[str, str]:
    """Calcula distância entre data de finalização e a cobrança CEF (01/01/2019).
    Retorna (distancia_dias, descricao_legivel).
    """
    if not final_date:
        return ("", "")
    ref = DATA_COBRANCA_CEF
    delta = ref - final_date
    days = delta.days
    if days <= 0:
        # Finalizado DEPOIS da cobrança — situação irregular
        return (str(abs(days)), f"COBRADO {abs(days)} dias ANTES da finalizacao")
    anos = days // 365
    meses = (days % 365) // 30
    partes = []
    if anos:
        partes.append(f"{anos} ano{'s' if anos > 1 else ''}")
    if meses:
        partes.append(f"{meses} mes{'es' if meses > 1 else ''}")
    if not partes:
        partes.append(f"{days} dias")
    descricao = f"Finalizado ha {', '.join(partes)} antes da cobranca CEF"
    return (str(days), descricao)


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
        reason = "LIQUIDACAO"
        final_date = liq_date or last_pgto or last_venc or prazo_end
        evidence = f"ocorrencia={ocorr or 'N/A'}; movimentos_liq={len(liquid_dates)}"
        return reason, final_date, evidence

    if sin_date or ocorr == "SIT":
        reason = "SINISTRO"
        final_date = sin_date or last_pgto or last_venc or prazo_end
        evidence = f"ocorrencia={ocorr or 'N/A'}; movimentos_sinistro={len(sin_dates)}"
        return reason, final_date, evidence

    if reached_prazo or ocorr == "TPZ":
        reason = "PRAZO_FINALIZADO"
        final_date = prazo_end or last_venc or last_pgto
        evidence = f"ocorrencia={ocorr or 'N/A'}; prazo={prazo}; max_nmens={max_nmens or 0}"
        return reason, final_date, evidence

    if ocorr:
        reason = f"EVENTO_{ocorr}"
        final_date = last_pgto or last_venc or prazo_end
        evidence = f"ocorrencia={ocorr}; sem marcador explicito em movimentos"
        return reason, final_date, evidence

    reason = "SEM_EVIDENCIA_FORTE"
    final_date = last_pgto or last_venc or prazo_end
    evidence = "sem ocorrencia e sem movimento de liquidacao/sinistro"
    return reason, final_date, evidence


def build_report_rows(pdf_entries: List[Tuple[str, str, float]]) -> List[dict]:
    contracts = map_contracts()
    mutuario_names = map_mutuario_names()
    contract_ids = [obj.id for obj in contracts.values()]
    parcelas_stats = map_parcelas_stats(contract_ids)

    rows: List[dict] = []
    for code, nome_pdf, valor_seguro_pdf in pdf_entries:
        contract = contracts.get(code)
        if not contract:
            rows.append(
                {
                    "contrato_pdf": code,
                    "contrato_db": "",
                    "nome_mutuario": nome_pdf,
                    "status_confronto": "NAO_ENCONTRADO_NO_BANCO",
                    "motivo_finalizacao": "",
                    "data_finalizacao": "",
                    "data_cobranca_cef": DATA_COBRANCA_CEF.strftime("%d/%m/%Y"),
                    "valor_seguro_pdf": "",
                }
            )
            continue

        pinfo = parcelas_stats.get(contract.id, {})
        movements = load_movements_for_contract(contract)
        reason, final_date, evidence = classify_finalization(contract, pinfo, movements)
        # Prioriza nome do PDF; fallback para o banco
        nome = nome_pdf or mutuario_names.get(normalize_contract_code(contract.codigo), "")
        dist_dias, dist_desc = distancia_cobranca(final_date)

        rows.append(
            {
                "contrato_pdf": code,
                "contrato_db": str(contract.codigo),
                "nome_mutuario": nome,
                "status_confronto": "ENCONTRADO",
                "motivo_finalizacao": reason,
                "data_finalizacao": final_date.strftime("%d/%m/%Y") if final_date else "",
                "data_cobranca_cef": DATA_COBRANCA_CEF.strftime("%d/%m/%Y"),
                "meses_apos_finalizacao": meses_entre_datas(final_date, DATA_COBRANCA_CEF),
                "valor_seguro_pdf": f"{valor_seguro_pdf:.2f}".replace(".", ","),
            }
        )

    return rows


def export_outputs(rows: List[dict], total_pdf_contracts: int) -> Tuple[str, str]:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = os.path.join(EXPORT_DIR, f"confronto_divida_seguro_012019_{ts}.csv")
    md_path = os.path.join(EXPORT_DIR, f"laudo_divida_seguro_012019_{ts}.md")

    fields = [
        "contrato_pdf",
        "contrato_db",
        "nome_mutuario",
        "status_confronto",
        "motivo_finalizacao",
        "data_finalizacao",
        "data_cobranca_cef",
        "meses_apos_finalizacao",
        "valor_seguro_pdf",
    ]

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    found_rows = [r for r in rows if r["status_confronto"] == "ENCONTRADO"]
    missing_rows = [r for r in rows if r["status_confronto"] != "ENCONTRADO"]

    reasons = Counter(r["motivo_finalizacao"] for r in found_rows if r["motivo_finalizacao"])

    # Estatísticas de distância não são mais necessárias (colunas removidas)

    # Estatísticas de valor de seguro
    # Formatar valor_seguro_pdf com vírgula
    valores_pdf = [float(r["valor_seguro_pdf"].replace(",", ".")) for r in found_rows if r.get("valor_seguro_pdf")]

    total_seguro_pdf = sum(valores_pdf) if valores_pdf else 0
    media_seguro_pdf = total_seguro_pdf / len(valores_pdf) if valores_pdf else 0

    md_lines = [
        "# Laudo de Confrontacao - Divida Seguro 01/2019",
        "",
        f"- Data de geracao: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"- Data da cobranca CEF: {DATA_COBRANCA_CEF.strftime('%d/%m/%Y')}",
        f"- Contratos extraidos do PDF: {total_pdf_contracts}",
        f"- Contratos encontrados na base: {len(found_rows)}",
        f"- Contratos nao encontrados na base: {len(missing_rows)}",
        "",
        "## Distribuicao por motivo de finalizacao",
    ]

    for reason, count in reasons.most_common():
        md_lines.append(f"- {reason}: {count}")

    md_lines.extend([
        "",
        "## Analise Financeira de Seguro",
        f"- **Total seguro no PDF** (PRM-DFI + PRM-MIP + PRM-CRD): R$ {total_seguro_pdf:,.2f}".replace(".", "_").replace(",", ".").replace("_", ","),
        f"- Media por contrato no PDF: R$ {media_seguro_pdf:,.2f}",
        "- Regra aplicada por contrato: valor_seguro_pdf = PRM-DFI + PRM-MIP + PRM-CRD.",
        "",
        "## Contratos nao encontrados na base",
    ])

    if missing_rows:
        for row in missing_rows[:100]:
            md_lines.append(f"- {row['contrato_pdf']}")
    else:
        md_lines.append("- Nenhum")

    md_lines.extend([
        "",
        "## Arquivo detalhado",
        f"- CSV completo: {csv_path}",
    ])

    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(md_lines))

    return csv_path, md_path


def main() -> int:
    if not os.path.exists(PDF_PATH):
        print(f"ERRO: PDF nao encontrado em {PDF_PATH}")
        return 1

    pdf_entries = extract_contracts_from_pdf(PDF_PATH)
    if not pdf_entries:
        print("ERRO: Nenhum contrato foi extraido do PDF.")
        return 1

    rows = build_report_rows(pdf_entries)
    csv_path, md_path = export_outputs(rows, len(pdf_entries))

    print("OK")
    print(f"CONTRATOS_PDF={len(pdf_entries)}")
    print(f"CSV={csv_path}")
    print(f"LAUDO={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
