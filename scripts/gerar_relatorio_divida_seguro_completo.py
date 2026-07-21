"""
Processador consolidado de relatórios de divida/seguro (2010-2019).

Processa 3 tipos de PDFs:
1. CAD APOLICE (2016-2019) - Por contrato detalhado
2. RIE_OFI (2010-2015) - Inclusões/exclusões detalhadas
3. RMO_OFI (2010-2019) - Resumo mensal por plano

Gera relatórios consolidados por ano + laudo unificado.

Uso:
  python gerar_relatorio_divida_seguro_completo.py
"""

import csv
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import django
import pdfplumber
from django.db.models import Count, Max, Min

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cofluhab.settings")
django.setup()

from principal.models import Contrato, Mutuario  # noqa: E402

# Caminhos
PDF_BASE_DIR = os.path.join(PROJECT_ROOT, "manual", "divida_seguro")
EXPORT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "exports"))

# Regex patterns para CAD APOLICE (mesmo formato do divida_seguro_01_2019.pdf)
PDF_FIF_LINE = re.compile(
    r"^\s*(\d{15})\s+(.+?)\s+"  # NUM.FIF + NOME
    r"(\d{1,3},\d{2})\s+"  # PERC1
    r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"  # 3x BASE
    r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"  # 3x PRM (DFI, MIP, CRD)
    r"(\d+)$"  # PRZ
)

PDF_CONTRATO_LINE = re.compile(r"^\s*(\d{6})\s+\d{2}/\d{4}\s+")


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
    """Extrai ano e mês do nome do arquivo (ex: CAD APOLICE 07_2016.pdf → (2016, 7))."""
    match = re.search(r'(\d{2})_(\d{4})', filename)
    if match:
        month, year = int(match.group(1)), int(match.group(2))
        return year, month
    return 0, 0


def process_cad_apolice_folder() -> List[dict]:
    """Processa todos os CAD APOLICE PDFs."""
    print("[CAD APOLICE] Processando...")
    results = []
    
    cad_folder = os.path.join(PDF_BASE_DIR, "CAD_APOLICE")
    if not os.path.exists(cad_folder):
        print(f"  [!] Pasta não encontrada: {cad_folder}")
        return results
    
    pdf_files = sorted(Path(cad_folder).glob("*.pdf"))
    print(f"  [FILES] {len(pdf_files)} PDFs encontrados")
    
    for pdf_path in pdf_files:
        year, month = extract_year_month_from_filename(pdf_path.name)
        if year == 0:
            continue
            
        try:
            seen = set()
            all_lines = []
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                        all_lines.extend(text.splitlines())
                    except Exception as page_err:
                        print(f"    [WARN] Erro na página {page_idx + 1}: {str(page_err)[:50]}...")
                        continue
            
            if not all_lines:
                print(f"  [!] {pdf_path.name}: sem conteúdo extraível")
                continue
            
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
            
            print(f"  [OK] {pdf_path.name}: {len(seen)} contratos")
        except Exception as e:
            print(f"  [ERROR] Erro em {pdf_path.name}: {str(e)[:80]}...")
    
    return results


def process_rie_ofi_folder() -> List[dict]:
    """Processa todos os RIE_OFI PDFs."""
    print("[RIE_OFI] Processando...")
    results = []
    
    rie_folder = os.path.join(PDF_BASE_DIR, "RIE_OFI")
    if not os.path.exists(rie_folder):
        print(f"  [!] Pasta não encontrada: {rie_folder}")
        return results
    
    pdf_files = sorted(Path(rie_folder).glob("*.pdf"))
    print(f"  [FILES] {len(pdf_files)} PDFs encontrados")
    
    # RIE segue padrão: RIE_OFI_YYYY_NN.pdf
    rie_pattern = re.compile(r'RIE_OFI_(\d{4})_\d{2}\.pdf')
    
    for pdf_path in pdf_files:
        match = rie_pattern.search(pdf_path.name)
        if not match:
            continue
        
        year = int(match.group(1))
        
        try:
            seen = set()
            all_lines = []
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                        all_lines.extend(text.splitlines())
                    except Exception as page_err:
                        print(f"    [WARN] Erro na página {page_idx + 1}: {str(page_err)[:50]}...")
                        continue
            
            if not all_lines:
                print(f"  [WARN] {pdf_path.name}: sem conteúdo extraível")
                continue
            
            # RIE tem formato similar ao CAD APOLICE
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
                                    "tipo": "RIE_OFI",
                                    "ano": year,
                                    "mes": 1,  # RIE é anual
                                    "contrato_pdf": code,
                                    "nome_pdf": nome_pdf,
                                    "valor_seguro_pdf": valor_seguro,
                                    "fonte": pdf_path.name,
                                })
                            i = j
                            break
                i += 1
            
            print(f"  [OK] {pdf_path.name}: {len(seen)} contratos")
        except Exception as e:
            print(f"  [ERROR] Erro em {pdf_path.name}: {str(e)[:80]}...")
    
    return results


def process_rmo_ofi_folder() -> List[dict]:
    """Processa todos os RMO_OFI PDFs (agregado por plano)."""
    print("[RMO_OFI] Processando (resumo por plano)...")
    results = []
    
    rmo_folder = os.path.join(PDF_BASE_DIR, "RMO_OFI")
    if not os.path.exists(rmo_folder):
        print(f"  [!] Pasta não encontrada: {rmo_folder}")
        return results
    
    pdf_files = sorted(Path(rmo_folder).glob("*.pdf"))
    print(f"  [FILES] {len(pdf_files)} PDFs encontrados")
    
    # RMO segue padrão: RMO_OFI_YYYY_NN.pdf
    rmo_pattern = re.compile(r'RMO_OFI_(\d{4})_(\d{2})\.pdf')
    
    for pdf_path in pdf_files:
        match = rmo_pattern.search(pdf_path.name)
        if not match:
            continue
        
        year, month = int(match.group(1)), int(match.group(2))
        
        try:
            all_text = ""
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                        all_text += text + "\n"
                    except Exception as page_err:
                        print(f"    [ERROR] Erro na página {page_idx + 1}: {str(page_err)[:50]}...")
                        continue
            
            if not all_text.strip():
                print(f"  [!] {pdf_path.name}: sem conteúdo extraível")
                continue
            
            # RMO é um RESUMO por plano, não é por contrato individual
            # Extrair total de operações e prêmios
            total_match = re.search(r'TOTAL\s+([\d,]+)\s+([\d.,]+)', all_text)
            if total_match:
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
            
            print(f"  [OK] {pdf_path.name}: agregado por plano")
        except Exception as e:
            print(f"  [ERROR] Erro em {pdf_path.name}: {str(e)[:80]}...")
    
    return results


def map_contracts() -> Dict[str, Contrato]:
    """Mapeia códigos para objetos Contrato."""
    contract_map = {}
    for contract in Contrato.objects.all().only("id", "codigo", "ocorrencia", "prazo"):
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


def export_results(cad_results: List[dict], rie_results: List[dict], rmo_results: List[dict]) -> Tuple[str, str]:
    """Exporta resultados consolidados para CSV e Markdown."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_path = os.path.join(EXPORT_DIR, f"divida_seguro_consolidado_{ts}.csv")
    md_path = os.path.join(EXPORT_DIR, f"laudo_divida_seguro_consolidado_{ts}.md")
    
    contracts = map_contracts()
    mutuario_names = map_mutuario_names()
    
    # Consolidar CAD + RIE (por contrato)
    all_by_contrato = defaultdict(list)
    for entry in cad_results + rie_results:
        code = entry["contrato_pdf"]
        all_by_contrato[code].append(entry)
    
    # Gerar CSV
    rows = []
    for code, entries in sorted(all_by_contrato.items()):
        contract = contracts.get(code)
        entry = entries[0]  # Pega primeira ocorrência
        
        nome = entry["nome_pdf"] or mutuario_names.get(code, "")
        status = "ENCONTRADO" if contract else "NAO_ENCONTRADO_NO_BANCO"
        valor = f"{entry['valor_seguro_pdf']:.2f}".replace(".", ",")
        
        rows.append({
            "contrato_pdf": code,
            "contrato_db": str(contract.codigo) if contract else "",
            "nome_mutuario": nome,
            "status": status,
            "ano_primeiro_registro": min(e["ano"] for e in entries),
            "ano_ultimo_registro": max(e["ano"] for e in entries),
            "tipo_relatorio": ", ".join(set(e["tipo"] for e in entries)),
            "valor_seguro_pdf": valor,
            "fonte": entries[0]["fonte"],
        })
    
    fields = [
        "contrato_pdf", "contrato_db", "nome_mutuario", "status",
        "ano_primeiro_registro", "ano_ultimo_registro", "tipo_relatorio",
        "valor_seguro_pdf", "fonte"
    ]
    
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    
    # Gerar Markdown
    found_count = sum(1 for r in rows if r["status"] == "ENCONTRADO")
    missing_count = len(rows) - found_count
    
    total_cad = len(cad_results)
    total_rie = len(rie_results)
    total_rmo = len(rmo_results)
    
    md_lines = [
        "# Relatório Consolidado de Dívida/Seguro (2010-2019)",
        "",
        f"- Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"- Período: 2010 a 2019",
        "",
        "## Resumo de Processamento",
        f"- **CAD APOLICE (2016-2019)**: {total_cad} contratos",
        f"- **RIE_OFI (2010-2015)**: {total_rie} contratos",
        f"- **RMO_OFI (2010-2019)**: {total_rmo} registros agregados por plano",
        f"- **Total de contratos únicos**: {len(rows)}",
        f"- **Encontrados na base**: {found_count}",
        f"- **Não encontrados**: {missing_count}",
        "",
        "## Análise Financeira",
    ]
    
    valores_pdf = [float(r["valor_seguro_pdf"].replace(",", ".")) for r in rows if r["valor_seguro_pdf"]]
    if valores_pdf:
        total_seguro = sum(valores_pdf)
        media_seguro = total_seguro / len(valores_pdf)
        md_lines.extend([
            f"- **Total seguro PDF (CAD+RIE)**: R$ {total_seguro:,.2f}".replace(".", "_").replace(",", ".").replace("_", ","),
            f"- **Média por contrato**: R$ {media_seguro:,.2f}".replace(".", "_").replace(",", ".").replace("_", ","),
        ])
    
    md_lines.extend([
        "",
        "## Distribuição por Tipo de Relatório",
    ])
    
    # Contar ocorrências por tipo
    type_counter = Counter()
    for entries in all_by_contrato.values():
        for e in entries:
            type_counter[e["tipo"]] += 1
    
    for report_type, count in type_counter.most_common():
        md_lines.append(f"- {report_type}: {count} contratos")
    
    md_lines.extend([
        "",
        "## Arquivo Detalhado",
        f"- CSV completo: {csv_path}",
    ])
    
    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(md_lines))
    
    return csv_path, md_path


def main() -> int:
    print("\n" + "="*70)
    print("PROCESSADOR CONSOLIDADO DE DIVIDA/SEGURO (2010-2019)")
    print("="*70 + "\n")
    
    # Processar todos os tipos
    cad_results = process_cad_apolice_folder()
    print()
    rie_results = process_rie_ofi_folder()
    print()
    rmo_results = process_rmo_ofi_folder()
    print()
    
    if not cad_results and not rie_results:
        print("[ERROR] Nenhum contrato foi extraído!")
        return 1
    
    # Exportar
    csv_path, md_path = export_results(cad_results, rie_results, rmo_results)
    
    print("\n" + "="*70)
    print("[OK] PROCESSAMENTO CONCLUÍDO!")
    print("="*70)
    print(f"CSV: {csv_path}")
    print(f"LAUDO: {md_path}")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
