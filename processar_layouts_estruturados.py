"""
Processa os layouts extraídos e cria estruturas organizadas
"""
import json
import re
from typing import Dict, List

def processar_tabela_campos(tabela: List[List], tipo_registro: str) -> List[Dict]:
    """Processa uma tabela de campos e retorna lista estruturada"""
    campos = []
    
    for linha in tabela:
        if not linha or len(linha) < 4:
            continue
        
        # Remove valores None
        linha_limpa = [str(v).strip() if v else "" for v in linha]
        
        # Tenta extrair SEQ, NOME, TIPO, TAM
        seq = linha_limpa[0] if linha_limpa[0] and linha_limpa[0].isdigit() else ""
        
        # Procura nome do campo
        nome = ""
        tipo = ""
        tamanho = ""
        formato = ""
        observacoes = ""
        
        for i, val in enumerate(linha_limpa):
            val_upper = val.upper()
            # Detecta tipo de campo
            if val_upper in ["NUM", "ALFAN", "ALFA", "ALFANUM"]:
                tipo = val_upper
                # Nome geralmente está antes do tipo
                if i > 0:
                    nome = linha_limpa[i-1]
                # Tamanho geralmente está depois do tipo
                if i+1 < len(linha_limpa) and linha_limpa[i+1].isdigit():
                    tamanho = linha_limpa[i+1]
                # Formato e observações vêm depois
                if i+2 < len(linha_limpa):
                    formato = linha_limpa[i+2]
                if i+3 < len(linha_limpa):
                    observacoes = " ".join(linha_limpa[i+3:])
                break
        
        if seq and nome and tipo:
            campo = {
                "seq": int(seq),
                "nome": nome,
                "tipo": tipo.replace("ALFAN", "X").replace("ALFANUM", "X").replace("ALFA", "X").replace("NUM", "N"),
                "tamanho": int(tamanho) if tamanho.isdigit() else 0,
                "formato": formato,
                "obrigatorio": "obrigatório" in observacoes.lower(),
                "descricao": observacoes
            }
            campos.append(campo)
    
    return campos

def extrair_campos_do_texto(texto: str) -> Dict:
    """Extrai especificações de campos do texto bruto"""
    resultado = {}
    
    # Padrão para encontrar seções de registro
    padrao_registro = r'REGISTRO\s+(\d+|[A-Z]+)\s*=>\s*([A-Z]+)\s*\((\d+)\s*bytes\)'
    
    for match in re.finditer(padrao_registro, texto, re.IGNORECASE):
        num_registro = match.group(1)
        tipo_registro = match.group(2)
        tamanho_linha = int(match.group(3))
        
        chave = f"REGISTRO_{num_registro}_{tipo_registro}"
        resultado[chave] = {
            "tipo": tipo_registro,
            "tamanho_linha": tamanho_linha,
            "campos": []
        }
    
    return resultado

def processar_cadmut_2025(dados: Dict) -> Dict:
    """Processa layout CADMUT 2025"""
    resultado = {
        "descricao": "Layouts de Movimentação CADMUT 2025",
        "tipos_registro": {}
    }
    
    # Extrai especificações do texto
    specs = extrair_campos_do_texto(dados["texto_completo"])
    
    # Processa tabelas extraídas
    for tabela_info in dados.get("tabelas", []):
        cabecalho = tabela_info.get("cabecalho", [])
        linhas = tabela_info.get("linhas", [])
        
        # Detecta tipo de registro pela página e conteúdo
        campos = processar_tabela_campos(linhas, "DETALHE")
        
        if campos:
            # Adiciona aos resultados
            tipo_reg = f"TABELA_PAGINA_{tabela_info['pagina']}"
            resultado["tipos_registro"][tipo_reg] = {
                "campos": campos,
                "tamanho_linha": 180  # Padrão CADMUT
            }
    
    return resultado

def main():
    """Processa todos os layouts"""
    print("Carregando layouts extraídos...")
    
    with open("layouts_cef_extraidos_completo.json", "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)
    
    layouts_processados = {}
    
    # Processa CADMUT 2025
    if "Leiautes_Movim_CADMUT_2025" in dados_brutos:
        print("\nProcessando CADMUT 2025...")
        layouts_processados["Leiautes_Movim_CADMUT_2025"] = processar_cadmut_2025(
            dados_brutos["Leiautes_Movim_CADMUT_2025"]
        )
    
    # Salva resultado processado
    with open("layouts_cef_estruturados.json", "w", encoding="utf-8") as f:
        json.dump(layouts_processados, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Layouts processados salvos em: layouts_cef_estruturados.json")
    
    # Estatísticas
    for nome, layout in layouts_processados.items():
        print(f"\n{nome}:")
        print(f"  Tipos de registro: {len(layout.get('tipos_registro', {}))}")
        for tipo, dados in layout.get('tipos_registro', {}).items():
            print(f"    - {tipo}: {len(dados.get('campos', []))} campos")

if __name__ == "__main__":
    main()
