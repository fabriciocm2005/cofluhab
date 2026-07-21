import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.ficha_generators import FH1Generator

print("=" * 80)
print("🔧 TESTANDO FH1Generator")
print("=" * 80)

# Busca contrato 6000
contrato = Contrato.objects.filter(codigo='6000').first()

if not contrato:
    print("❌ Contrato não encontrado")
    exit()

print(f"\n✅ Contrato: {contrato.codigo}")
print(f"   Conjunto: {contrato.conjunto}")

# Testa geração
print(f"\n🔨 Gerando ficha FH1...")
fh1_gen = FH1Generator(validar=False)

try:
    linha, erros = fh1_gen.gerar_de_contrato(contrato)
    
    print(f"\n✅ Ficha gerada com sucesso!")
    print(f"   Tamanho: {len(linha)} caracteres")
    print(f"   Erros: {len(erros)}")
    
    print(f"\n📋 Primeiros 100 caracteres:")
    print(f"   [{linha[:100]}]")
    
    print(f"\n📋 Posições específicas:")
    if len(linha) >= 23:
        print(f"   01-02: UFS = '{linha[0:2]}'")
        print(f"   03-08: MAT = '{linha[2:8]}'")
        print(f"   09-22: ZEROS = '{linha[8:22]}'")
        print(f"   23: TIPO REG = '{linha[22]}'")
    
    if len(linha) >= 70:
        print(f"   27-66: NOME = '{linha[26:66]}'")
        print(f"   68-84: CPF = '{linha[67:84]}'")
    
    print(f"\n📋 Últimos 50 caracteres:")
    print(f"   [{linha[-50:]}]")
    
except Exception as e:
    print(f"\n❌ ERRO ao gerar ficha: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
