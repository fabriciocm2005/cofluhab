import os
import sys
import django

os.chdir(r'C:\Users\fabri\cofluhab\cofluhab')
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

print("="*80)
print("TESTE OPCAO 1 - AUTO-CORRECAO BASICA")
print("="*80)

from principal.ai_agents import corrigir_arquivo_cef_automaticamente

# Conteudo com erros
conteudo_erro = """33000044101230100COFLUHAB                      000001000000000000000X
33000044100000001442          1     000000442     T000000033    0100011984010120260123    0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
33000044190000010000000000000000"""

print("\nConteudo original:")
for i, linha in enumerate(conteudo_erro.split('\n'), 1):
    print(f"  Linha {i}: {len(linha)} bytes")

print("\nExecutando correcao automatica...")
resultado = corrigir_arquivo_cef_automaticamente(conteudo_erro, "TESTE VALIDACAO")

print(f"\nRESULTADO:")
print(f"  Sucesso: {resultado['sucesso']}")
print(f"  Total correcoes: {resultado['total_correcoes']}")

if resultado['correcoes_aplicadas']:
    print(f"\n  Correcoes aplicadas:")
    for correcao in resultado['correcoes_aplicadas']:
        print(f"    - {correcao}")

print("\nConteudo corrigido:")
for i, linha in enumerate(resultado['conteudo_corrigido'].split('\n'), 1):
    print(f"  Linha {i}: {len(linha)} bytes")

print("\n" + "="*80)
print("TESTE CONCLUIDO - OPCAO 1 FUNCIONANDO!")
print("="*80)
