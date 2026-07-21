"""
Processador consolidado de relatórios de divida/seguro (historico 1992+) - V2 com pypdfium2.

Processa 3 tipos de PDFs:
1. CAD APOLICE (2016-2019) - Por contrato detalhado
2. RIE_OFI (faixa conforme arquivos disponíveis) - Inclusões/exclusões detalhadas
3. RMO_OFI (faixa conforme arquivos disponíveis) - Resumo mensal por plano

Gera relatórios consolidados por ano + laudo unificado.

Uso:
  python gerar_relatorio_divida_seguro_v2.py
"""

import csv
import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import django
import pypdfium2 as pdfium
from django.db.models import Count, Max, Min

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cofluhab.settings")
django.setup()

from principal.models import Contrato, Movimentacao, Mutuario, ParcelaContrato  # noqa: E402

# Caminhos
PDF_BASE_DIR = os.path.join(PROJECT_ROOT, "manual", "divida_seguro")
EXPORT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "exports"))

# Regex patterns
PDF_FIF_LINE = re.compile(
    r"^\s*(\d{15})\s+(.+?)\s+"  # NUM.FIF + NOME
    r"(\d{1,3},\d{2})\s+"  # PERC1
    r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"  # 3x BASE
    r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"  # 3x PRM (DFI, MIP, CRD)
    r"(\d+)$"  # PRZ
)

PDF_CONTRATO_LINE = re.compile(r"^\s*(\d{6})\s+\d{2}/\d{4}\s+")
RIE_FIF_HEADER_LINE = re.compile(r"(\d{15})\s+.+")
RIE_PREMIO_LINE = re.compile(
    r"^\s*[\d.,]+\s+[\d.,]+\s+[\d.,]+\s+([\-\d.,]+)\s+([\-\d.,]+)\s+([\-\d.,]+)\b"
)


def _is_mm_yyyy_token(token: str) -> bool:
    if len(token) != 6 or not token.isdigit():
        return False
    month = int(token[:2])
    year = int(token[2:])
    return 1 <= month <= 12 and 1900 <= year <= 2099


def _extract_contract_from_rie_line(line: str) -> str:
    tokens = re.findall(r"\b\d{6,7}\b", line)
    for token in tokens:
        if token in {"000000", "0000000", "999999", "9999999"}:
            continue
        if _is_mm_yyyy_token(token):
            continue
        return normalize_contract_code(token)
    return ""


def _extract_name_from_rie_line(line: str) -> str:
    # O nome fica entre o NUMERO DA FIF (15 digitos) e os blocos numericos finais.
    line = line.strip()
    fif_match = re.search(r"\d{15}", line)
    if fif_match:
        body = line[fif_match.end():].strip()
    else:
        body = line
    name_match = re.match(r"(.+?)\s+\d{6}\s+\d{1,3}\b", body)
    if name_match:
        return name_match.group(1).strip()
    # Fallback: remove blocos numericos do fim e retorna o texto restante.
    body = re.sub(r"(?:\s+\d{1,7}){2,}\s*$", "", body)
    return body.strip()


def normalize_contract_code(value: str) -> str:
    """Normaliza código do contrato para comparação."""
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    return str(int(digits))


def parse_value(text: str) -> float:
    """Parse valor monetário brasileiro (ex: 1.234,56 → 1234.56)."""
    if not text:
        return 0.0
    clean = text.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def extract_year_month_from_filename(filename: str) -> Tuple[int, int]:
    """Extrai ano e mês do nome do arquivo."""
    match = re.search(r'(\d{2})_(\d{4})', filename)
    if match:
        month, year = int(match.group(1)), int(match.group(2))
        return year, month
    return 0, 0


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrai texto usando pypdfium2 (mais rápido e robusto)."""
    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
        text = ""
        
        for page_idx in range(len(pdf)):
            try:
                page = pdf[page_idx]
                textpage = page.get_textpage()
                page_text = textpage.get_text_range(0, -1)
                text += page_text + "\n"
                textpage.close()
                page.close()
            except Exception as e:
                # Se uma página der erro, continua com as outras
                continue
        
        pdf.close()
        return text
    except Exception as e:
        print(f"    [ERROR] {str(e)[:60]}...")
        return ""


def process_cad_apolice_folder(ano_filtro: Optional[int] = None, max_pdfs: Optional[int] = None) -> List[dict]:
    """Processa todos os CAD APOLICE PDFs."""
    print("[CAD APOLICE] Processando...")
    results = []
    
    cad_folder = os.path.join(PDF_BASE_DIR, "CAD_APOLICE")
    if not os.path.exists(cad_folder):
        print(f"  [WARN] Pasta não encontrada: {cad_folder}")
        return results
    
    pdf_files = sorted(Path(cad_folder).glob("*.pdf"))
    print(f"  [FILES] {len(pdf_files)} PDFs encontrados")
    
    for pdf_idx, pdf_path in enumerate(pdf_files, 1):
        if max_pdfs and pdf_idx > max_pdfs:
            break
        year, month = extract_year_month_from_filename(pdf_path.name)
        if year == 0:
            continue
        if ano_filtro and year != ano_filtro:
            continue
        
        try:
            print(f"    [{pdf_idx}/{len(pdf_files)}] {pdf_path.name}...", end=" ", flush=True)
            
            all_text = extract_text_from_pdf(str(pdf_path))
            if not all_text.strip():
                print("[SKIP: empty]")
                continue
            
            all_lines = all_text.splitlines()
            seen = set()
            
            i = 0
            while i < len(all_lines):
                fif_match = PDF_FIF_LINE.match(all_lines[i])
                if fif_match:
                    nome_pdf = fif_match.group(2).strip()
                    premio_dfi = parse_value(fif_match.group(7))
                    premio_mip = parse_value(fif_match.group(8))
                    premio_crd = parse_value(fif_match.group(9))
                    valor_seguro = premio_dfi + premio_mip + premio_crd
                    
                    for j in range(i + 1, min(i + 5, len(all_lines))):
                        cont_match = PDF_CONTRATO_LINE.match(all_lines[j])
                        if cont_match:
                            code = normalize_contract_code(cont_match.group(1))
                            if code and code not in seen:
                                seen.add(code)
                                results.append({
                                    "tipo": "CAD_APOLICE",
                                    "ano": year,
                                    "mes": month,
                                    "contrato_pdf": code,
                                    "nome_pdf": nome_pdf,
                                    "valor_seguro_pdf": valor_seguro,
                                    "fonte": pdf_path.name,
                                })
                            i = j
                            break
                i += 1
            
            print(f"[OK: {len(seen)} contratos]")
        except Exception as e:
            print(f"[ERROR: {str(e)[:40]}...]")
    
    return results


def process_rie_ofi_folder(ano_filtro: Optional[int] = None, max_pdfs: Optional[int] = None) -> List[dict]:
    """Processa todos os RIE_OFI PDFs."""
    print("[RIE_OFI] Processando...")
    results = []
    
    rie_folder = os.path.join(PDF_BASE_DIR, "RIE_OFI")
    if not os.path.exists(rie_folder):
        print(f"  [WARN] Pasta não encontrada: {rie_folder}")
        return results
    
    pdf_files = sorted(Path(rie_folder).glob("*.pdf"))
    print(f"  [FILES] {len(pdf_files)} PDFs encontrados")
    
    rie_pattern = re.compile(r'RIE_OFI_(\d{4})_\d{2}\.pdf')
    
    for pdf_idx, pdf_path in enumerate(pdf_files, 1):
        if max_pdfs and pdf_idx > max_pdfs:
            break
        match = rie_pattern.search(pdf_path.name)
        if not match:
            continue
        
        year = int(match.group(1))
        if ano_filtro and year != ano_filtro:
            continue
        
        try:
            print(f"    [{pdf_idx}/{len(pdf_files)}] {pdf_path.name}...", end=" ", flush=True)
            
            all_text = extract_text_from_pdf(str(pdf_path))
            if not all_text.strip():
                print("[SKIP: empty]")
                continue
            
            all_lines = all_text.splitlines()
            seen = set()
            
            i = 0
            while i < len(all_lines):
                current_line = all_lines[i]
                header_match = RIE_FIF_HEADER_LINE.search(current_line)
                if header_match:
                    nome_pdf = _extract_name_from_rie_line(current_line)
                    contrato_code = _extract_contract_from_rie_line(current_line)
                    valor_seguro = 0.0

                    for j in range(i, min(i + 6, len(all_lines))):
                        if not contrato_code:
                            contrato_code = _extract_contract_from_rie_line(all_lines[j])

                        premio_match = RIE_PREMIO_LINE.match(all_lines[j])
                        if premio_match:
                            premio_dfi = parse_value(premio_match.group(1))
                            premio_mip = parse_value(premio_match.group(2))
                            premio_crd = parse_value(premio_match.group(3))
                            soma = premio_dfi + premio_mip + premio_crd
                            # Valores negativos ou zero = exclusão/correção, não cobrança
                            valor_seguro = soma if soma > 0.0 else 0.0

                    if contrato_code and contrato_code not in seen:
                        seen.add(contrato_code)
                        results.append({
                            "tipo": "RIE_OFI",
                            "ano": year,
                            "mes": 1,
                            "contrato_pdf": contrato_code,
                            "nome_pdf": nome_pdf,
                            "valor_seguro_pdf": valor_seguro,
                            "fonte": pdf_path.name,
                        })

                i += 1
            
            print(f"[OK: {len(seen)} contratos]")
        except Exception as e:
            print(f"[ERROR: {str(e)[:40]}...]")
    
    return results


def process_rmo_ofi_folder(ano_filtro: Optional[int] = None, max_pdfs: Optional[int] = None) -> List[dict]:
    """Processa RMO_OFI (agregado por plano)."""
    print("[RMO_OFI] Processando...")
    results = []
    
    rmo_folder = os.path.join(PDF_BASE_DIR, "RMO_OFI")
    if not os.path.exists(rmo_folder):
        print(f"  [WARN] Pasta não encontrada: {rmo_folder}")
        return results
    
    pdf_files = sorted(Path(rmo_folder).glob("*.pdf"))
    print(f"  [FILES] {len(pdf_files)} PDFs encontrados")
    
    rmo_pattern = re.compile(r'RMO_OFI_(\d{4})_(\d{2})\.pdf')
    
    for pdf_idx, pdf_path in enumerate(pdf_files, 1):
        if max_pdfs and pdf_idx > max_pdfs:
            break
        match = rmo_pattern.search(pdf_path.name)
        if not match:
            continue
        
        year, month = int(match.group(1)), int(match.group(2))
        if ano_filtro and year != ano_filtro:
            continue
        
        try:
            print(f"    [{pdf_idx}/{len(pdf_files)}] {pdf_path.name}...", end=" ", flush=True)
            
            all_text = extract_text_from_pdf(str(pdf_path))
            if not all_text.strip():
                print("[SKIP: empty]")
                continue
            
            # RMO é resumo por plano
            total_match = re.search(r'TOTAL\s+([\d,]+)\s+([\d.,]+)', all_text)
            if total_match:
                try:
                    total_operacoes = int(total_match.group(1).replace(",", ""))
                    total_premios_str = total_match.group(2)
                    total_premios = parse_value(total_premios_str)
                    
                    results.append({
                        "tipo": "RMO_OFI",
                        "ano": year,
                        "mes": month,
                        "total_operacoes": total_operacoes,
                        "total_premios": total_premios,
                        "fonte": pdf_path.name,
                    })
                    print("[OK: agregado]")
                except:
                    print("[SKIP: parsing error]")
            else:
                print("[SKIP: no TOTAL found]")
        except Exception as e:
            print(f"[ERROR: {str(e)[:40]}...]")
    
    return results


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
    return date(y, m, min(src.day, max_day))


def meses_entre_datas(data1: Optional[date], data2: date) -> int:
    if not data1:
        return 0
    total = (data2.year - data1.year) * 12 + (data2.month - data1.month)
    return max(0, total)


def map_contracts() -> Dict[str, Contrato]:
    """Mapeia códigos para objetos Contrato."""
    contract_map = {}
    for contract in Contrato.objects.all().only("id", "codigo", "ocorrencia", "prazo", "data_contrato", "data_primeiro_venc"):
        code = normalize_contract_code(contract.codigo)
        if code and code not in contract_map:
            contract_map[code] = contract
    return contract_map


def map_mutuario_names() -> Dict[str, str]:
    """Mapeia códigos para nomes de mutuários."""
    names = {}
    for m in Mutuario.objects.all().only("codigo", "nome"):
        code = normalize_contract_code(m.codigo)
        if code and code not in names:
            names[code] = (m.nome or "").strip()
    return names


def map_parcelas_stats(contract_ids) -> Dict[int, dict]:
    from django.db.models import Count
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


def load_movements_for_contract(contract: Contrato):
    LIQ_REGEX = re.compile(r"LIQ|LIQUID|QUITA|QUIT", re.IGNORECASE)
    SIN_REGEX = re.compile(r"SINIST", re.IGNORECASE)
    code = normalize_contract_code(contract.codigo)
    if not code:
        return []
    return list(Movimentacao.objects.filter(codigo=code))


def classify_finalization(contract: Contrato, pinfo: dict, movements) -> Tuple[str, Optional[date], str]:
    LIQ_REGEX = re.compile(r"LIQ|LIQUID|QUITA|QUIT", re.IGNORECASE)
    SIN_REGEX = re.compile(r"SINIST", re.IGNORECASE)
    ocorr = (contract.ocorrencia or "").strip().upper()
    prazo = contract.prazo or 0
    first_venc = pinfo.get("first_venc") if pinfo else None
    last_venc = pinfo.get("last_venc") if pinfo else None
    last_pgto = pinfo.get("last_pgto") if pinfo else None
    max_nmens = pinfo.get("max_nmens") if pinfo else None
    prazo_end = None
    if prazo and first_venc:
        prazo_end = add_months(first_venc, prazo - 1)

    liq_dates = [m.data for m in movements if m.data and LIQ_REGEX.search(getattr(m, "historico", "") or "")]
    sin_dates = [m.data for m in movements if m.data and SIN_REGEX.search(getattr(m, "historico", "") or "")]
    liq_date = min(liq_dates) if liq_dates else None
    sin_date = min(sin_dates) if sin_dates else None
    reached_prazo = bool(prazo and max_nmens and max_nmens >= prazo)

    if liq_date or ocorr == "LIQ":
        return "LIQUIDACAO", liq_date or last_pgto or last_venc or prazo_end, f"ocorrencia={ocorr}"
    if sin_date or ocorr == "SIT":
        return "SINISTRO", sin_date or last_pgto or last_venc or prazo_end, f"ocorrencia={ocorr}"
    if reached_prazo or ocorr == "TPZ":
        return "PRAZO_FINALIZADO", prazo_end or last_venc or last_pgto, f"ocorrencia={ocorr}; prazo={prazo}; max_nmens={max_nmens or 0}"
    if ocorr:
        return f"EVENTO_{ocorr}", last_pgto or last_venc or prazo_end, f"ocorrencia={ocorr}"
    return "SEM_EVIDENCIA_FORTE", last_pgto or last_venc or prazo_end, "sem ocorrencia e sem movimento"


def export_results(
    cad_results: List[dict],
    rie_results: List[dict],
    rmo_results: List[dict],
    ano_filtro: Optional[int] = None,
) -> Tuple[str, str]:
    """Exporta resultados consolidados para CSV e Markdown."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if ano_filtro:
        base_name = f"divida_seguro_{ano_filtro}_{ts}"
        periodo_txt = str(ano_filtro)
    else:
        base_name = f"divida_seguro_consolidado_{ts}"
        anos_processados = sorted({int(e.get("ano", 0)) for e in (cad_results + rie_results + rmo_results) if int(e.get("ano", 0)) > 0})
        if anos_processados:
            periodo_txt = f"{anos_processados[0]}-{anos_processados[-1]}"
        else:
            periodo_txt = "1992+"

    csv_path = os.path.join(EXPORT_DIR, f"{base_name}.csv")
    md_path = os.path.join(EXPORT_DIR, f"laudo_{base_name}.md")
    
    contracts = map_contracts()
    mutuario_names = map_mutuario_names()
    
    if ano_filtro:
        cad_results = [e for e in cad_results if e.get("ano") == ano_filtro]
        rie_results = [e for e in rie_results if e.get("ano") == ano_filtro]
        rmo_results = [e for e in rmo_results if e.get("ano") == ano_filtro]

    # Consolidar CAD + RIE por contrato + competência (ano/mês)
    # Isso preserva a cobrança mensal de um mesmo contrato em múltiplos PDFs.
    all_by_competencia = defaultdict(list)
    for entry in cad_results + rie_results:
        code = entry["contrato_pdf"]
        key = (code, entry.get("ano", 0), entry.get("mes", 0))
        all_by_competencia[key].append(entry)

    # Pré-carregar parcelas e movimentações dos contratos encontrados
    found_ids = [contracts[c].id for (c, _, _) in all_by_competencia if c in contracts]
    parcelas_stats = map_parcelas_stats(found_ids)

    # Gerar CSV
    rows = []
    for (code, _, _), entries in sorted(all_by_competencia.items()):
        contract = contracts.get(code)
        # Mantém uma entrada representativa desta competência (ano/mês)
        entries_sorted = sorted(entries, key=lambda e: (e.get("ano", 0), e.get("mes", 0), e.get("fonte", "")))
        entry = entries_sorted[-1]

        nome = entry["nome_pdf"] or mutuario_names.get(code, "")
        status = "ENCONTRADO" if contract else "NAO_ENCONTRADO_NO_BANCO"
        valor = f"{entry['valor_seguro_pdf']:.2f}".replace(".", ",")

        # Data de cobrança = 1o dia do mês/ano da fonte mais recente
        try:
            data_cob = date(entry["ano"], entry.get("mes", 1) or 1, 1)
        except Exception:
            data_cob = date(entry["ano"], 1, 1)
        data_cob_str = data_cob.strftime("%d/%m/%Y")

        motivo = ""
        data_fin_str = ""
        meses_pos = ""

        if contract:
            pinfo = parcelas_stats.get(contract.id, {})
            movements = load_movements_for_contract(contract)
            motivo, final_date, _ = classify_finalization(contract, pinfo, movements)
            data_fin_str = final_date.strftime("%d/%m/%Y") if final_date else ""
            meses_pos = str(meses_entre_datas(final_date, data_cob)) if final_date else ""

        rows.append({
            "contrato_pdf": code,
            "contrato_db": str(contract.codigo) if contract else "",
            "nome_mutuario": nome,
            "status_confronto": status,
            "motivo_finalizacao": motivo,
            "data_finalizacao": data_fin_str,
            "data_cobranca_cef": data_cob_str,
            "meses_apos_finalizacao": meses_pos,
            "valor_seguro_pdf": valor,
            "fonte": entry["fonte"],
        })
    
    fields = [
        "contrato_pdf", "contrato_db", "nome_mutuario", "status_confronto",
        "motivo_finalizacao", "data_finalizacao", "data_cobranca_cef",
        "meses_apos_finalizacao", "valor_seguro_pdf", "fonte",
    ]
    
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    
    # Gerar Markdown
    found_count = sum(1 for r in rows if r["status_confronto"] == "ENCONTRADO")
    missing_count = len(rows) - found_count
    
    total_cad = len(cad_results)
    total_rie = len(rie_results)
    total_rmo = len(rmo_results)
    
    md_lines = [
        f"# Relatorio de Divida/Seguro ({periodo_txt})",
        "",
        f"- Data de geracao: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"- Periodo: {periodo_txt}",
        "",
        "## Resumo de Processamento",
        f"- **CAD APOLICE**: {total_cad} contratos",
        f"- **RIE_OFI**: {total_rie} contratos",
        f"- **RMO_OFI**: {total_rmo} registros agregados por plano",
        f"- **Total de contratos unicos**: {len(rows)}",
        f"- **Encontrados na base**: {found_count}",
        f"- **Nao encontrados**: {missing_count}",
        "",
        "## Analise Financeira",
    ]
    
    valores_pdf = [float(r["valor_seguro_pdf"].replace(",", ".")) for r in rows if r["valor_seguro_pdf"]]
    if valores_pdf:
        total_seguro = sum(valores_pdf)
        media_seguro = total_seguro / len(valores_pdf)
        md_lines.extend([
            f"- **Total seguro PDF (CAD+RIE)**: R$ {total_seguro:,.2f}".replace(".", "_").replace(",", ".").replace("_", ","),
            f"- **Media por contrato**: R$ {media_seguro:,.2f}".replace(".", "_").replace(",", ".").replace("_", ","),
        ])
    
    reason_counter = Counter(r["motivo_finalizacao"] for r in rows if r["motivo_finalizacao"])
    md_lines.extend([
        "",
        "## Distribuicao por Motivo de Finalizacao",
    ])
    for reason, count in reason_counter.most_common():
        md_lines.append(f"- {reason}: {count}")

    md_lines.extend([
        "",
        "## Distribuicao por Fonte",
    ])
    fonte_counter = Counter(r["fonte"] for r in rows)
    for fonte, count in sorted(fonte_counter.most_common()):
        md_lines.append(f"- {fonte}: {count} contratos")
    
    md_lines.extend([
        "",
        "## Arquivo Detalhado",
        f"- CSV completo: {csv_path}",
    ])
    
    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(md_lines))
    
    return csv_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera relatorio de divida/seguro consolidado ou por ano.")
    parser.add_argument("--ano", type=int, default=None, help="Ano especifico (ex: 1992)")
    parser.add_argument(
        "--tipo",
        choices=["ALL", "CAD", "RIE", "RMO"],
        default="ALL",
        help="Processa apenas um tipo de relatorio quando necessario",
    )
    parser.add_argument(
        "--max-pdfs",
        type=int,
        default=None,
        help="Limite de PDFs por tipo (debug/performance)",
    )
    args = parser.parse_args()

    print("\n" + "="*70)
    if args.ano:
        print(f"PROCESSADOR DE DIVIDA/SEGURO - ANO {args.ano} - V2")
    else:
        print("PROCESSADOR CONSOLIDADO DE DIVIDA/SEGURO (HISTORICO 1992+) - V2")
    print("="*70 + "\n")
    
    # Processar todos os tipos
    cad_results = []
    rie_results = []
    rmo_results = []

    if args.tipo in {"ALL", "CAD"}:
        cad_results = process_cad_apolice_folder(ano_filtro=args.ano, max_pdfs=args.max_pdfs)
        print()

    if args.tipo in {"ALL", "RIE"}:
        rie_results = process_rie_ofi_folder(ano_filtro=args.ano, max_pdfs=args.max_pdfs)
        print()

    if args.tipo in {"ALL", "RMO"}:
        rmo_results = process_rmo_ofi_folder(ano_filtro=args.ano, max_pdfs=args.max_pdfs)
        print()
    
    if not cad_results and not rie_results:
        print("[ERROR] Nenhum contrato foi extraido!")
        return 1
    
    # Exportar
    csv_path, md_path = export_results(cad_results, rie_results, rmo_results, ano_filtro=args.ano)
    
    print("\n" + "="*70)
    print("[OK] PROCESSAMENTO CONCLUIDO!")
    print("="*70)
    print(f"CSV: {csv_path}")
    print(f"LAUDO: {md_path}")
    print(f"Contratos CAD APOLICE: {len(cad_results)}")
    print(f"Contratos RIE_OFI: {len(rie_results)}")
    print(f"Registros RMO_OFI: {len(rmo_results)}")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
