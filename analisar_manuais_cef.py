"""
Script para análise detalhada dos manuais CEF
Extrai informações sobre autenticação, endpoints, layouts e procedimentos
"""

import sys
import os

# Adicionar ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from principal.cef_integration_bot import (
    analisar_manuais_cef,
    ler_pdf,
    extrair_info_tecnica,
    construir_knowledge_base,
    MANUAIS_PATH
)

def main():
    print("\n" + "="*80)
    print("🤖 CEF INTEGRATION BOT - ANÁLISE DE MANUAIS")
    print("="*80 + "\n")
    
    # 1. Listar manuais disponíveis
    print("📚 PASSO 1: Identificando manuais...\n")
    print(analisar_manuais_cef())
    
    # 2. Construir knowledge base
    print("\n" + "="*80)
    print("📦 PASSO 2: Construindo knowledge base...")
    print("="*80 + "\n")
    print(construir_knowledge_base())
    
    # 3. Analisar manual do SIWFC (Sistema Web)
    print("\n" + "="*80)
    print("🌐 PASSO 3: Analisando Manual do Sistema Web (SIWFC)...")
    print("="*80 + "\n")
    
    manual_web = os.path.join(MANUAIS_PATH, "Manual_SIWFC_MAR_2025.pdf")
    if os.path.exists(manual_web):
        print("📖 Lendo Manual_SIWFC_MAR_2025.pdf...\n")
        conteudo = ler_pdf(manual_web)
        print(conteudo)
        
        # Salvar extrato para análise
        extrato_path = "extrato_manual_siwfc.txt"
        with open(extrato_path, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"\n✅ Extrato salvo em: {extrato_path}")
    
    # 4. Analisar layouts FCVS
    print("\n" + "="*80)
    print("📋 PASSO 4: Analisando Layouts FCVS...")
    print("="*80 + "\n")
    
    manual_fcvs = os.path.join(MANUAIS_PATH, "Leiautes_Movim_FCVS - 2025 - V2.pdf")
    if os.path.exists(manual_fcvs):
        print("📖 Lendo Leiautes_Movim_FCVS - 2025 - V2.pdf...\n")
        conteudo_fcvs = ler_pdf(manual_fcvs)
        
        # Procurar por informações sobre FH1
        if "FH1" in conteudo_fcvs:
            print("✅ Encontrado layout FH1 no manual!")
            linhas_fh1 = [l for l in conteudo_fcvs.split('\n') if 'FH1' in l]
            print("\n📌 Referências ao FH1:")
            for linha in linhas_fh1[:10]:
                print(f"  • {linha.strip()}")
        
        # Salvar extrato
        extrato_fcvs_path = "extrato_layouts_fcvs.txt"
        with open(extrato_fcvs_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_fcvs)
        print(f"\n✅ Extrato salvo em: {extrato_fcvs_path}")
    
    # 5. Buscar informações específicas
    print("\n" + "="*80)
    print("🔍 PASSO 5: Buscando informações específicas...")
    print("="*80 + "\n")
    
    topicos = ['login', 'autenticacao', 'upload', 'envio', 'retorno', 'endpoint', 'URL']
    
    for topico in topicos:
        print(f"\n🔎 Buscando: {topico}")
        print("-" * 40)
        resultado = extrair_info_tecnica('web', topico)
        if "não encontrado" not in resultado.lower():
            print(resultado[:500] + "...")
    
    print("\n" + "="*80)
    print("✅ ANÁLISE CONCLUÍDA!")
    print("="*80)
    print("\n📊 Próximos passos:")
    print("1. Revisar extratos gerados (extrato_manual_siwfc.txt, extrato_layouts_fcvs.txt)")
    print("2. Identificar URLs de autenticação")
    print("3. Mapear endpoints de upload/download")
    print("4. Criar automação de login")
    print("5. Implementar upload de FH1/RCV")
    print("\n")

if __name__ == "__main__":
    main()
