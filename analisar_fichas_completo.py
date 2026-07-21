"""
Script Avançado: Agente CEF Integration Bot - Análise Completa
Estuda TODAS as fichas de envio/retorno e códigos de interpretação
"""
import os
import sys
import json
from pathlib import Path
import re

# Configurar paths
BASE_DIR = Path(r'C:\Users\fabri\cofluhab\cofluhab')
MANUAIS_DIR = Path(r'C:\Users\fabri\cofluhab\dados_antigos\manuais')
sys.path.append(str(BASE_DIR))

# Importar o agente
os.chdir(BASE_DIR)
from principal.cef_integration_bot import ler_pdf, analisar_manuais_cef

print("🤖 CEF INTEGRATION BOT - ANÁLISE AVANÇADA COMPLETA")
print("="*70)
print("📚 Estudando TODAS as fichas e códigos dos manuais CEF...")
print()

# Estrutura para armazenar conhecimento completo
conhecimento_completo = {
    "data_analise": "2026-01-23",
    "fichas_envio": {},
    "fichas_retorno": {},
    "codigos_interpretacao": {},
    "processos": {},
    "validacoes": {}
}

# ============================================================================
# 1. ANÁLISE DO MANUAL SIWFC (Portal Web)
# ============================================================================
print("📖 1. ANALISANDO MANUAL SIWFC (Portal Web)...")
siwfc_path = MANUAIS_DIR / "Manual_SIWFC_MAR_2025.pdf"

if siwfc_path.exists():
    texto_siwfc = ler_pdf(str(siwfc_path))
    
    # Extrair informações do portal
    conhecimento_completo["processos"]["portal_web"] = {
        "url": "https://www.siwfc.caixa.gov.br/",
        "login": {
            "etapa1": "Inserir CPF",
            "etapa2": "Validação por e-mail",
            "etapa3": "Inserir senha"
        },
        "modulos": []
    }
    
    # Buscar módulos disponíveis
    if "módulo" in texto_siwfc.lower() or "menu" in texto_siwfc.lower():
        linhas = texto_siwfc.split('\n')
        for i, linha in enumerate(linhas):
            if 'módulo' in linha.lower() or 'menu' in linha.lower():
                conhecimento_completo["processos"]["portal_web"]["modulos"].append(
                    linha.strip()[:100]
                )
    
    print(f"   ✅ Portal Web: URL, login e {len(conhecimento_completo['processos']['portal_web']['modulos'])} módulos identificados")
else:
    print("   ⚠️ Manual SIWFC não encontrado")

# ============================================================================
# 2. ANÁLISE COMPLETA DOS LAYOUTS FCVS (Todas as Fichas)
# ============================================================================
print("\n📖 2. ANALISANDO LAYOUTS FCVS (Todas as Fichas de Envio)...")
fcvs_path = MANUAIS_DIR / "Leiautes_Movim_FCVS - 2025 - V2.pdf"

if fcvs_path.exists():
    texto_fcvs = ler_pdf(str(fcvs_path))
    
    # Identificar todas as fichas mencionadas
    fichas_encontradas = []
    
    # Padrões para identificar fichas
    padroes_fichas = [
        r'FH[0-9]',  # FH1, FH2, etc
        r'RCV',
        r'RNV',
        r'CADMUT',
        r'DOSSI[EÊ]',
        r'COMPLEMENTAR',
        r'MOVIMENTA[ÇC][ÃA]O',
        r'REGISTRO.*TIPO',
    ]
    
    for padrao in padroes_fichas:
        matches = re.finditer(padrao, texto_fcvs, re.IGNORECASE)
        for match in matches:
            ficha = match.group(0).upper()
            if ficha not in fichas_encontradas:
                fichas_encontradas.append(ficha)
    
    # Analisar estrutura de cada ficha
    linhas = texto_fcvs.split('\n')
    ficha_atual = None
    
    for i, linha in enumerate(linhas):
        linha_upper = linha.upper()
        
        # Detectar início de definição de ficha
        for ficha_nome in fichas_encontradas:
            if ficha_nome in linha_upper and ('REGISTRO' in linha_upper or 'TIPO' in linha_upper):
                ficha_atual = ficha_nome
                
                if ficha_atual not in conhecimento_completo["fichas_envio"]:
                    conhecimento_completo["fichas_envio"][ficha_atual] = {
                        "descricao": linha.strip()[:200],
                        "campos": [],
                        "tamanho_registro": 0,
                        "observacoes": []
                    }
        
        # Extrair campos (formato típico: SEQ NOME TIPO TAM FORMATO OBSERVAÇÕES)
        if ficha_atual and any(word in linha_upper for word in ['SEQ', 'NOME', 'CAMPO', 'TIPO']):
            # Próximas linhas podem conter campos
            for j in range(i+1, min(i+50, len(linhas))):
                linha_campo = linhas[j].strip()
                
                # Parar se linha vazia ou novo cabeçalho
                if not linha_campo or any(word in linha_campo.upper() for word in ['REGISTRO', 'TIPO DE', 'PARA TODOS']):
                    break
                
                # Tentar extrair informação do campo
                if linha_campo and len(linha_campo) > 20:
                    conhecimento_completo["fichas_envio"][ficha_atual]["campos"].append({
                        "definicao": linha_campo[:150]
                    })
    
    # Buscar informações sobre tipos de movimento
    if "TIPO DE MOVIMENTO" in texto_fcvs.upper() or "POSIÇÃO 424" in texto_fcvs.upper():
        conhecimento_completo["fichas_envio"]["TIPOS_MOVIMENTO"] = {
            "descricao": "Posição 424 diferencia o tipo de movimento",
            "codigos": []
        }
        
        # Tentar extrair códigos de movimento
        for i, linha in enumerate(linhas):
            if '424' in linha or 'tipo de movimento' in linha.lower():
                # Capturar próximas linhas com códigos
                for j in range(i, min(i+30, len(linhas))):
                    if any(char.isdigit() for char in linhas[j]):
                        conhecimento_completo["fichas_envio"]["TIPOS_MOVIMENTO"]["codigos"].append(
                            linhas[j].strip()[:100]
                        )
    
    print(f"   ✅ Fichas de Envio Identificadas: {len(conhecimento_completo['fichas_envio'])}")
    for ficha, info in conhecimento_completo["fichas_envio"].items():
        campos_count = len(info.get("campos", []))
        print(f"      • {ficha}: {campos_count} campos detectados")

else:
    print("   ⚠️ Manual FCVS Layouts não encontrado")

# ============================================================================
# 3. ANÁLISE DE LAYOUTS DE RETORNO
# ============================================================================
print("\n📖 3. ANALISANDO ARQUIVOS DE RETORNO...")

# Arquivos de retorno geralmente estão no mesmo manual de layouts
if fcvs_path.exists():
    # Buscar seções de retorno
    retorno_patterns = [
        r'RETORNO',
        r'RESPOSTA',
        r'ARQUIVO.*RETORNO',
        r'PROCESSAMENTO',
        r'RESULTADO',
        r'CRÍTICA',
        r'ERRO',
        r'REJEIÇÃO'
    ]
    
    texto_fcvs_upper = texto_fcvs.upper()
    linhas = texto_fcvs.split('\n')
    
    for i, linha in enumerate(linhas):
        linha_upper = linha.upper()
        
        # Detectar seções de retorno
        for pattern in retorno_patterns:
            if re.search(pattern, linha_upper):
                tipo_retorno = pattern.replace(r'\.*', '').strip()
                
                if tipo_retorno not in conhecimento_completo["fichas_retorno"]:
                    conhecimento_completo["fichas_retorno"][tipo_retorno] = {
                        "descricao": linha.strip()[:200],
                        "campos": [],
                        "codigos_possiveis": []
                    }
                
                # Capturar informações das próximas linhas
                for j in range(i+1, min(i+20, len(linhas))):
                    linha_info = linhas[j].strip()
                    if linha_info and len(linha_info) > 10:
                        conhecimento_completo["fichas_retorno"][tipo_retorno]["campos"].append(
                            linha_info[:150]
                        )
    
    print(f"   ✅ Tipos de Retorno Identificados: {len(conhecimento_completo['fichas_retorno'])}")
    for retorno in conhecimento_completo["fichas_retorno"].keys():
        print(f"      • {retorno}")

# ============================================================================
# 4. ANÁLISE DO MANUAL CADMUT (Cadastro de Mutuários)
# ============================================================================
print("\n📖 4. ANALISANDO LAYOUTS CADMUT (Cadastro de Mutuários)...")
cadmut_path = MANUAIS_DIR / "Leiautes_Movim_CADMUT - 2025.pdf"

if cadmut_path.exists():
    texto_cadmut = ler_pdf(str(cadmut_path))
    
    conhecimento_completo["fichas_envio"]["CADMUT"] = {
        "descricao": "Cadastro de Mutuários",
        "campos": [],
        "tipos_registro": []
    }
    
    linhas = texto_cadmut.split('\n')
    
    # Extrair estrutura
    for i, linha in enumerate(linhas):
        if any(word in linha.upper() for word in ['REGISTRO', 'CAMPO', 'TIPO']):
            for j in range(i+1, min(i+30, len(linhas))):
                linha_campo = linhas[j].strip()
                if linha_campo and len(linha_campo) > 20:
                    conhecimento_completo["fichas_envio"]["CADMUT"]["campos"].append(
                        linha_campo[:150]
                    )
    
    campos = len(conhecimento_completo["fichas_envio"]["CADMUT"]["campos"])
    print(f"   ✅ CADMUT: {campos} campos identificados")
else:
    print("   ⚠️ Manual CADMUT não encontrado")

# ============================================================================
# 5. ANÁLISE DO ROTEIRO (Normas e Códigos)
# ============================================================================
print("\n📖 5. ANALISANDO ROTEIRO DE ANÁLISE (Códigos e Normas)...")
roteiro_path = MANUAIS_DIR / "Anexos-do-Roteiro-de-Analise-do-FCVS.pdf"

if roteiro_path.exists():
    try:
        texto_roteiro = ler_pdf(str(roteiro_path))
    except Exception as e:
        print(f"   ⚠️ Erro ao ler PDF do Roteiro: {e}")
        print(f"   ℹ️ Continuando sem análise do roteiro...")
        texto_roteiro = ""
    
    linhas = texto_roteiro.split('\n') if texto_roteiro else []
    
    # Buscar códigos de erro/validação
    codigo_atual = None
    
    for i, linha in enumerate(linhas):
        linha_upper = linha.upper()
        
        # Detectar códigos (formato comum: número seguido de descrição)
        match_codigo = re.match(r'^([0-9]{1,4})\s*[-–]\s*(.+)', linha)
        if match_codigo:
            codigo = match_codigo.group(1)
            descricao = match_codigo.group(2).strip()
            
            conhecimento_completo["codigos_interpretacao"][codigo] = {
                "descricao": descricao[:200],
                "categoria": "validacao",
                "detalhes": []
            }
            codigo_atual = codigo
        
        # Se estamos dentro de um código, capturar detalhes
        elif codigo_atual and linha.strip() and len(linha.strip()) > 10:
            if codigo_atual in conhecimento_completo["codigos_interpretacao"]:
                conhecimento_completo["codigos_interpretacao"][codigo_atual]["detalhes"].append(
                    linha.strip()[:150]
                )
        
        # Detectar procedimentos/normas
        if any(word in linha_upper for word in ['PROCEDIMENTO', 'NORMA', 'REGRA', 'DEVE', 'OBRIGATÓRIO']):
            if "procedimentos" not in conhecimento_completo["validacoes"]:
                conhecimento_completo["validacoes"]["procedimentos"] = []
            
            conhecimento_completo["validacoes"]["procedimentos"].append(
                linha.strip()[:200]
            )
    
    codigos = len(conhecimento_completo["codigos_interpretacao"])
    procedimentos = len(conhecimento_completo["validacoes"].get("procedimentos", []))
    print(f"   ✅ Códigos de Interpretação: {codigos} identificados")
    print(f"   ✅ Procedimentos/Normas: {procedimentos} identificados")
else:
    print("   ⚠️ Roteiro de Análise não encontrado")

# ============================================================================
# 6. SALVAR CONHECIMENTO COMPLETO
# ============================================================================
print("\n💾 SALVANDO CONHECIMENTO COMPLETO...")

output_path = BASE_DIR / "cef_conhecimento_completo.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(conhecimento_completo, f, ensure_ascii=False, indent=2)

print(f"   ✅ Salvo em: {output_path}")

# ============================================================================
# 7. GERAR DOCUMENTAÇÃO MARKDOWN
# ============================================================================
print("\n📄 GERANDO DOCUMENTAÇÃO ESTRUTURADA...")

doc_path = BASE_DIR / "CEF_FICHAS_E_CODIGOS.md"
with open(doc_path, 'w', encoding='utf-8') as f:
    f.write("# 📚 CEF - Fichas e Códigos Completos\n\n")
    f.write("**Gerado automaticamente pelo CEF Integration Bot**\n\n")
    f.write(f"**Data da análise**: {conhecimento_completo['data_analise']}\n\n")
    f.write("---\n\n")
    
    # Fichas de Envio
    f.write("## 📤 FICHAS DE ENVIO\n\n")
    for ficha, info in conhecimento_completo["fichas_envio"].items():
        f.write(f"### {ficha}\n\n")
        f.write(f"**Descrição**: {info.get('descricao', 'N/A')}\n\n")
        
        campos = info.get('campos', [])
        if campos:
            f.write(f"**Campos identificados**: {len(campos)}\n\n")
            f.write("```\n")
            for campo in campos[:20]:  # Primeiros 20 campos
                f.write(f"{campo.get('definicao', campo)}\n")
            if len(campos) > 20:
                f.write(f"... e mais {len(campos) - 20} campos\n")
            f.write("```\n\n")
    
    # Fichas de Retorno
    f.write("\n## 📥 FICHAS DE RETORNO\n\n")
    for retorno, info in conhecimento_completo["fichas_retorno"].items():
        f.write(f"### {retorno}\n\n")
        f.write(f"**Descrição**: {info.get('descricao', 'N/A')}\n\n")
        
        campos = info.get('campos', [])
        if campos:
            f.write("**Estrutura**:\n```\n")
            for campo in campos[:15]:
                f.write(f"{campo}\n")
            f.write("```\n\n")
    
    # Códigos de Interpretação
    f.write("\n## 🔍 CÓDIGOS DE INTERPRETAÇÃO\n\n")
    for codigo, info in sorted(conhecimento_completo["codigos_interpretacao"].items()):
        f.write(f"### Código {codigo}\n\n")
        f.write(f"**Descrição**: {info.get('descricao', 'N/A')}\n\n")
        
        detalhes = info.get('detalhes', [])
        if detalhes:
            f.write("**Detalhes**:\n")
            for detalhe in detalhes[:5]:
                f.write(f"- {detalhe}\n")
            f.write("\n")
    
    # Processos
    f.write("\n## ⚙️ PROCESSOS\n\n")
    if "portal_web" in conhecimento_completo["processos"]:
        portal = conhecimento_completo["processos"]["portal_web"]
        f.write("### Portal Web SIWFC\n\n")
        f.write(f"**URL**: {portal.get('url', 'N/A')}\n\n")
        f.write("**Login**:\n")
        for etapa, desc in portal.get('login', {}).items():
            f.write(f"- {etapa}: {desc}\n")
        f.write("\n")

print(f"   ✅ Documentação salva em: {doc_path}")

# ============================================================================
# 8. RESUMO FINAL
# ============================================================================
print("\n" + "="*70)
print("✅ ANÁLISE COMPLETA CONCLUÍDA!")
print("="*70)
print(f"\n📊 ESTATÍSTICAS:")
print(f"   • Fichas de Envio: {len(conhecimento_completo['fichas_envio'])}")
print(f"   • Fichas de Retorno: {len(conhecimento_completo['fichas_retorno'])}")
print(f"   • Códigos de Interpretação: {len(conhecimento_completo['codigos_interpretacao'])}")
print(f"   • Procedimentos/Normas: {len(conhecimento_completo['validacoes'].get('procedimentos', []))}")

print(f"\n📁 ARQUIVOS GERADOS:")
print(f"   1. {output_path}")
print(f"   2. {doc_path}")

print("\n🎯 PRÓXIMOS PASSOS:")
print("   1. Implementar parsers para cada tipo de ficha")
print("   2. Criar validadores baseados nos códigos")
print("   3. Implementar interpretador de retornos")
print("   4. Adicionar geradores automáticos de fichas")
print("\n" + "="*70)
