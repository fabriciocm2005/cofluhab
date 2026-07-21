"""
ANÁLISE COMPLETA DE TODOS OS 7 LAYOUTS CEF
Gera especificações estruturadas para uso nos parsers
"""
import json
import re

print("="*80)
print("CARREGANDO DADOS EXTRAÍDOS...")
print("="*80)

with open("layouts_cef_extraidos_completo.json", "r", encoding="utf-8") as f:
    dados_brutos = json.load(f)

print(f"✅ {len(dados_brutos)} layouts carregados")

# =========================================================================
# Função para analisar texto e encontrar especificações
# =========================================================================
def analisar_texto_layout(texto: str) -> dict:
    """Analisa texto e extrai padrões de layout"""
    info = {
        "tipos_registro": [],
        "tamanhos": [],
        "campos_encontrados": []
    }
    
    # Busca padrões de REGISTRO
    for match in re.finditer(r'REGISTRO\s+(\d+|[A-Z]+)\s*=>\s*([A-Z]+)\s*\((\d+)\s*bytes?\)', texto, re.IGNORECASE):
        info["tipos_registro"].append({
            "numero": match.group(1),
            "tipo": match.group(2),
            "tamanho": int(match.group(3))
        })
    
    # Busca padrões de tamanho de linha
    for match in re.finditer(r'(\d+)\s*bytes', texto, re.IGNORECASE):
        info["tamanhos"].append(int(match.group(1)))
    
    return info

# =========================================================================
# RESUMO GERAL DOS DADOS EXTRAÍDOS
# =========================================================================
print("\n" + "="*80)
print("RESUMO DOS LAYOUTS EXTRAÍDOS")
print("="*80)

for nome, dados in dados_brutos.items():
    print(f"\n📄 {nome}:")
    print(f"   Descrição: {dados.get('descricao', 'N/A')}")
    
    if "texto_completo" in dados:
        analise = analisar_texto_layout(dados["texto_completo"])
        print(f"   Tipos de registro encontrados: {len(analise['tipos_registro'])}")
        for reg in analise['tipos_registro'][:5]:  # Mostra até 5
            print(f"     • Registro {reg['numero']} - {reg['tipo']} ({reg['tamanho']} bytes)")
    
    if "tabelas" in dados:
        print(f"   Tabelas extraídas: {len(dados['tabelas'])}")
        if dados['tabelas']:
            print(f"     • Primeira tabela: {len(dados['tabelas'][0].get('linhas', []))} linhas")
    
    if "tipos_registro" in dados and isinstance(dados["tipos_registro"], dict):
        print(f"   Abas/Planilhas Excel: {len(dados['tipos_registro'])}")
        for aba in list(dados['tipos_registro'].keys())[:5]:
            print(f"     • {aba}")

# =========================================================================
# Exporta dados importantes para análise manual
# =========================================================================
print("\n" + "="*80)
print("EXPORTANDO DADOS PARA ANÁLISE DETALHADA")
print("="*80)

# 1. FCVS 2025
if "Leiautes_Movim_FCVS_2025_V2" in dados_brutos:
    fcvs_data = dados_brutos["Leiautes_Movim_FCVS_2025_V2"]
    with open("analise_fcvs_2025.txt", "w", encoding="utf-8") as f:
        f.write("LAYOUT FCVS 2025 V2\n")
        f.write("="*80 + "\n\n")
        f.write(fcvs_data.get("texto_completo", ""))
    print("✅ analise_fcvs_2025.txt criado")

# 2. CADMUT Espelho  
if "Leiaute_CADMUT_Espelho" in dados_brutos:
    espelho_data = dados_brutos["Leiaute_CADMUT_Espelho"]
    with open("analise_cadmut_espelho.txt", "w", encoding="utf-8") as f:
        f.write("LAYOUT CADMUT ESPELHO\n")
        f.write("="*80 + "\n\n")
        f.write(espelho_data.get("texto_completo", ""))
    print("✅ analise_cadmut_espelho.txt criado")

# 3. M460301
if "Leiaute_M460301" in dados_brutos:
    m460301_data = dados_brutos["Leiaute_M460301"]
    with open("analise_m460301.txt", "w", encoding="utf-8") as f:
        f.write("LAYOUT M460301\n")
        f.write("="*80 + "\n\n")
        f.write(m460301_data.get("texto_completo", ""))
    print("✅ analise_m460301.txt criado")

# 4. M460401
if "Leiaute_M460401" in dados_brutos:
    m460401_data = dados_brutos["Leiaute_M460401"]
    with open("analise_m460401.txt", "w", encoding="utf-8") as f:
        f.write("LAYOUT M460401\n")
        f.write("="*80 + "\n\n")
        f.write(m460401_data.get("texto_completo", ""))
    print("✅ analise_m460401.txt criado")

# 5. M460801
if "Leiaute_M460801" in dados_brutos:
    m460801_data = dados_brutos["Leiaute_M460801"]
    with open("analise_m460801.txt", "w", encoding="utf-8") as f:
        f.write("LAYOUT M460801\n")
        f.write("="*80 + "\n\n")
        f.write(m460801_data.get("texto_completo", ""))
    print("✅ analise_m460801.txt criado")

# 6. FCVS3026 Excel
if "Leiaute_FCVS3026" in dados_brutos:
    fcvs3026_data = dados_brutos["Leiaute_FCVS3026"]
    with open("analise_fcvs3026_excel.json", "w", encoding="utf-8") as f:
        json.dump(fcvs3026_data, f, ensure_ascii=False, indent=2)
    print("✅ analise_fcvs3026_excel.json criado")

# =========================================================================
# ESTATÍSTICAS FINAIS
# =========================================================================
print("\n" + "="*80)
print("ESTATÍSTICAS GERAIS")
print("="*80)

total_registros = 0
total_tabelas = 0

for nome, dados in dados_brutos.items():
    if "texto_completo" in dados:
        analise = analisar_texto_layout(dados["texto_completo"])
        total_registros += len(analise["tipos_registro"])
    if "tabelas" in dados:
        total_tabelas += len(dados["tabelas"])

print(f"\n📊 Total de tipos de registro identificados: {total_registros}")
print(f"📊 Total de tabelas extraídas: {total_tabelas}")

print("\n" + "="*80)
print("PRÓXIMOS PASSOS")
print("="*80)
print("""
1. Analise os arquivos TXT gerados para ver o texto completo de cada layout
2. Analise o JSON do FCVS3026 (Excel) para ver as abas e colunas
3. Use essas informações para criar as especificações estruturadas completas
4. Os arquivos gerados são:
   - analise_fcvs_2025.txt
   - analise_cadmut_espelho.txt
   - analise_m460301.txt
   - analise_m460401.txt
   - analise_m460801.txt
   - analise_fcvs3026_excel.json
""")
