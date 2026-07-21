"""
Script para extrair layouts de campos posicionais dos manuais CEF
Analisa PDFs e Excel para extrair especificações completas de layouts
"""
import json
import re
from pathlib import Path
import pdfplumber
import pandas as pd
from typing import Dict, List, Any

# Caminhos dos arquivos
ARQUIVOS = {
    "Leiautes_Movim_CADMUT_2025": r"C:\Users\fabri\cofluhab\dados_antigos\manuais\Leiautes_Movim_CADMUT - 2025.pdf",
    "Leiautes_Movim_FCVS_2025_V2": r"C:\Users\fabri\cofluhab\dados_antigos\manuais\Leiautes_Movim_FCVS - 2025 - V2.pdf",
    "Leiaute_CADMUT_Espelho": r"C:\Users\fabri\cofluhab\dados_antigos\manuais\Leiaute_CADMUT_Espelho.pdf",
    "Leiaute_M460301": r"C:\Users\fabri\cofluhab\dados_antigos\manuais\Leiaute_M460301.pdf",
    "Leiaute_M460401": r"C:\Users\fabri\cofluhab\dados_antigos\manuais\Leiaute_M460401.pdf",
    "Leiaute_M460801": r"C:\Users\fabri\cofluhab\dados_antigos\manuais\Leiaute_M460801.pdf",
    "Leiaute_FCVS3026": r"C:\Users\fabri\cofluhab\dados_antigos\manuais\Leiaute_FCVS3026_TR1_a_TR9_270417.xls",
}

def extrair_texto_pdf(caminho: str) -> str:
    """Extrai todo o texto de um PDF"""
    texto_completo = []
    with pdfplumber.open(caminho) as pdf:
        for i, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text()
            if texto:
                texto_completo.append(f"\n=== PÁGINA {i+1} ===\n")
                texto_completo.append(texto)
    return "\n".join(texto_completo)

def extrair_tabelas_pdf(caminho: str) -> List[List[Any]]:
    """Extrai todas as tabelas de um PDF"""
    todas_tabelas = []
    with pdfplumber.open(caminho) as pdf:
        for i, pagina in enumerate(pdf.pages):
            tabelas = pagina.extract_tables()
            if tabelas:
                for j, tabela in enumerate(tabelas):
                    todas_tabelas.append({
                        "pagina": i + 1,
                        "tabela_num": j + 1,
                        "dados": tabela
                    })
    return todas_tabelas

def processar_excel_fcvs3026(caminho: str) -> Dict:
    """Processa o arquivo Excel do FCVS3026"""
    try:
        # Tenta ler com pandas
        xls = pd.ExcelFile(caminho, engine='xlrd')
        resultado = {
            "descricao": "Layout FCVS3026 - Arquivo de Posição",
            "tipos_registro": {}
        }
        
        for nome_aba in xls.sheet_names:
            print(f"  Processando aba: {nome_aba}")
            df = pd.read_excel(xls, sheet_name=nome_aba)
            
            # Extrai informações da aba
            resultado["tipos_registro"][nome_aba] = {
                "descricao": f"Registro tipo {nome_aba}",
                "colunas": df.columns.tolist(),
                "dados": df.to_dict('records')
            }
        
        return resultado
    except Exception as e:
        print(f"  Erro ao processar Excel: {e}")
        return None

def analisar_layout_cadmut_2025(caminho: str) -> Dict:
    """Analisa Leiautes_Movim_CADMUT - 2025.pdf"""
    print(f"\nAnalisando: {Path(caminho).name}")
    texto = extrair_texto_pdf(caminho)
    tabelas = extrair_tabelas_pdf(caminho)
    
    resultado = {
        "descricao": "Layouts de Movimentação CADMUT 2025",
        "texto_completo": texto,
        "tabelas_extraidas": len(tabelas),
        "tabelas": []
    }
    
    # Processa cada tabela encontrada
    for tab_info in tabelas:
        tabela = tab_info["dados"]
        if tabela and len(tabela) > 0:
            resultado["tabelas"].append({
                "pagina": tab_info["pagina"],
                "cabecalho": tabela[0] if tabela else [],
                "linhas": tabela[1:] if len(tabela) > 1 else []
            })
    
    return resultado

def analisar_layout_fcvs_2025(caminho: str) -> Dict:
    """Analisa Leiautes_Movim_FCVS - 2025 - V2.pdf"""
    print(f"\nAnalisando: {Path(caminho).name}")
    texto = extrair_texto_pdf(caminho)
    tabelas = extrair_tabelas_pdf(caminho)
    
    resultado = {
        "descricao": "Layouts de Movimentação FCVS 2025 Versão 2",
        "texto_completo": texto,
        "tabelas_extraidas": len(tabelas),
        "tabelas": []
    }
    
    for tab_info in tabelas:
        tabela = tab_info["dados"]
        if tabela and len(tabela) > 0:
            resultado["tabelas"].append({
                "pagina": tab_info["pagina"],
                "cabecalho": tabela[0] if tabela else [],
                "linhas": tabela[1:] if len(tabela) > 1 else []
            })
    
    return resultado

def analisar_layout_cadmut_espelho(caminho: str) -> Dict:
    """Analisa Leiaute_CADMUT_Espelho.pdf"""
    print(f"\nAnalisando: {Path(caminho).name}")
    texto = extrair_texto_pdf(caminho)
    tabelas = extrair_tabelas_pdf(caminho)
    
    resultado = {
        "descricao": "Layout do Espelho CADMUT",
        "texto_completo": texto,
        "tabelas_extraidas": len(tabelas),
        "tabelas": []
    }
    
    for tab_info in tabelas:
        tabela = tab_info["dados"]
        if tabela and len(tabela) > 0:
            resultado["tabelas"].append({
                "pagina": tab_info["pagina"],
                "cabecalho": tabela[0] if tabela else [],
                "linhas": tabela[1:] if len(tabela) > 1 else []
            })
    
    return resultado

def analisar_layout_m460301(caminho: str) -> Dict:
    """Analisa Leiaute_M460301.pdf"""
    print(f"\nAnalisando: {Path(caminho).name}")
    texto = extrair_texto_pdf(caminho)
    tabelas = extrair_tabelas_pdf(caminho)
    
    resultado = {
        "descricao": "Layout M460301",
        "texto_completo": texto,
        "tabelas_extraidas": len(tabelas),
        "tabelas": []
    }
    
    for tab_info in tabelas:
        tabela = tab_info["dados"]
        if tabela and len(tabela) > 0:
            resultado["tabelas"].append({
                "pagina": tab_info["pagina"],
                "cabecalho": tabela[0] if tabela else [],
                "linhas": tabela[1:] if len(tabela) > 1 else []
            })
    
    return resultado

def analisar_layout_m460401(caminho: str) -> Dict:
    """Analisa Leiaute_M460401.pdf"""
    print(f"\nAnalisando: {Path(caminho).name}")
    texto = extrair_texto_pdf(caminho)
    tabelas = extrair_tabelas_pdf(caminho)
    
    resultado = {
        "descricao": "Layout M460401",
        "texto_completo": texto,
        "tabelas_extraidas": len(tabelas),
        "tabelas": []
    }
    
    for tab_info in tabelas:
        tabela = tab_info["dados"]
        if tabela and len(tabela) > 0:
            resultado["tabelas"].append({
                "pagina": tab_info["pagina"],
                "cabecalho": tabela[0] if tabela else [],
                "linhas": tabela[1:] if len(tabela) > 1 else []
            })
    
    return resultado

def analisar_layout_m460801(caminho: str) -> Dict:
    """Analisa Leiaute_M460801.pdf"""
    print(f"\nAnalisando: {Path(caminho).name}")
    texto = extrair_texto_pdf(caminho)
    tabelas = extrair_tabelas_pdf(caminho)
    
    resultado = {
        "descricao": "Layout M460801",
        "texto_completo": texto,
        "tabelas_extraidas": len(tabelas),
        "tabelas": []
    }
    
    for tab_info in tabelas:
        tabela = tab_info["dados"]
        if tabela and len(tabela) > 0:
            resultado["tabelas"].append({
                "pagina": tab_info["pagina"],
                "cabecalho": tabela[0] if tabela else [],
                "linhas": tabela[1:] if len(tabela) > 1 else []
            })
    
    return resultado

def main():
    """Função principal que processa todos os arquivos"""
    print("="*80)
    print("EXTRAÇÃO DE LAYOUTS CEF")
    print("="*80)
    
    layouts_extraidos = {}
    
    # Processa cada arquivo
    for nome, caminho in ARQUIVOS.items():
        if not Path(caminho).exists():
            print(f"\n❌ ARQUIVO NÃO ENCONTRADO: {caminho}")
            continue
        
        print(f"\n{'='*80}")
        print(f"Processando: {nome}")
        print(f"{'='*80}")
        
        try:
            if nome == "Leiautes_Movim_CADMUT_2025":
                layouts_extraidos[nome] = analisar_layout_cadmut_2025(caminho)
            elif nome == "Leiautes_Movim_FCVS_2025_V2":
                layouts_extraidos[nome] = analisar_layout_fcvs_2025(caminho)
            elif nome == "Leiaute_CADMUT_Espelho":
                layouts_extraidos[nome] = analisar_layout_cadmut_espelho(caminho)
            elif nome == "Leiaute_M460301":
                layouts_extraidos[nome] = analisar_layout_m460301(caminho)
            elif nome == "Leiaute_M460401":
                layouts_extraidos[nome] = analisar_layout_m460401(caminho)
            elif nome == "Leiaute_M460801":
                layouts_extraidos[nome] = analisar_layout_m460801(caminho)
            elif nome == "Leiaute_FCVS3026":
                layouts_extraidos[nome] = processar_excel_fcvs3026(caminho)
            
            if layouts_extraidos.get(nome):
                print(f"✅ Processado com sucesso!")
                if "tabelas_extraidas" in layouts_extraidos[nome]:
                    print(f"   Tabelas encontradas: {layouts_extraidos[nome]['tabelas_extraidas']}")
        
        except Exception as e:
            print(f"❌ ERRO ao processar {nome}: {e}")
            import traceback
            traceback.print_exc()
    
    # Salva resultado em JSON
    output_file = "layouts_cef_extraidos_completo.json"
    print(f"\n{'='*80}")
    print(f"Salvando resultados em: {output_file}")
    print(f"{'='*80}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(layouts_extraidos, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ CONCLUÍDO! Arquivo salvo: {output_file}")
    print(f"\nResumo:")
    for nome, dados in layouts_extraidos.items():
        if dados:
            print(f"  • {nome}: OK")
        else:
            print(f"  • {nome}: Não processado")

if __name__ == "__main__":
    main()
