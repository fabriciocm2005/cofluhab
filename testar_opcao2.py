import os
import sys
import django

os.chdir(r'C:\Users\fabri\cofluhab\cofluhab')
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

print("="*80)
print("TESTE DA OPÇÃO 2 - AUTO-FIX INTELIGENTE")
print("="*80)

# Conteúdo com erro intencional (HEADER com 431 bytes, TRAILER com 71 bytes)
conteudo_erro = """33000044101230100COFLUHAB                      000001000000000000000X
33000044100000001442          1     000000442     T000000033    0100011984010120260123    0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
33000044190000010000000000000000"""

print(f"\n📄 Conteúdo original:")
linhas = conteudo_erro.split('\n')
for i, linha in enumerate(linhas, 1):
    if linha:
        print(f"  Linha {i}: {len(linha)} bytes - {linha[:50]}...")

print(f"\n🔍 Testando validação AI...")
from principal.ai_agents import validar_arquivo_com_ai, corrigir_com_agente_autofix

resultado_validacao = validar_arquivo_com_ai(conteudo_erro, "FH1")
print(f"\n{'='*80}")
print(f"Status: {resultado_validacao.get('status', 'DESCONHECIDO')}")
print(f"Aprovado: {resultado_validacao.get('aprovado', False)}")
print(f"\nResultado:\n{resultado_validacao.get('resultado', 'Sem resultado')[:500]}...")
print(f"{'='*80}")

if not resultado_validacao.get('aprovado'):
    print(f"\n🧠 TESTANDO AUTO-FIX INTELIGENTE...")
    print(f"{'='*80}\n")
    
    correcao = corrigir_com_agente_autofix(
        conteudo_erro,
        resultado_validacao.get('resultado', ''),
        "FH1"
    )
    
    print(f"\n✅ Sucesso: {correcao.get('sucesso', False)}")
    print(f"📊 Total correções: {correcao.get('total_correcoes', 0)}")
    
    if correcao.get('correcoes_aplicadas'):
        print(f"\n🔧 Correções aplicadas:")
        for i, corr in enumerate(correcao['correcoes_aplicadas'], 1):
            print(f"  {i}. {corr}")
    
    if correcao.get('analise_ia'):
        print(f"\n💡 ANÁLISE INTELIGENTE DO AGENTE:")
        print(f"{'='*80}")
        print(correcao['analise_ia'])
        print(f"{'='*80}")
    
    if correcao.get('conteudo_corrigido'):
        linhas_corrigidas = correcao['conteudo_corrigido'].split('\n')
        print(f"\n📄 Conteúdo corrigido:")
        for i, linha in enumerate(linhas_corrigidas, 1):
            if linha:
                print(f"  Linha {i}: {len(linha)} bytes - {linha[:50]}...")

print(f"\n{'='*80}")
print("TESTE CONCLUÍDO")
print(f"{'='*80}")
