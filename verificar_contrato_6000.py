import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario

print("=" * 80)
print("🔍 VERIFICANDO CONTRATO 6000")
print("=" * 80)

# Busca contrato
contrato = Contrato.objects.filter(codigo='6000').first()

if not contrato:
    print("❌ Contrato 6000 não encontrado")
    exit()

print(f"\n✅ Contrato encontrado: {contrato.codigo}")
print(f"   Conjunto: {contrato.conjunto}")

# Verifica mutuários vinculados ao conjunto do contrato
if contrato.conjunto:
    mutuarios_conjunto = Mutuario.objects.filter(conjunto=contrato.conjunto)
    print(f"\n📋 Mutuários do conjunto '{contrato.conjunto}': {mutuarios_conjunto.count()}")
    
    if mutuarios_conjunto.count() > 0:
        for idx, m in enumerate(mutuarios_conjunto[:5], 1):
            print(f"\n   Mutuário #{idx}:")
            print(f"     ID: {m.id}")
            print(f"     Código: {m.codigo}")
            print(f"     Nome: '{m.nome}' (len={len(m.nome)})")
            print(f"     CPF: '{m.cpf}' (len={len(m.cpf)})")
            print(f"     Data Nasc: {m.dtnasc}")
            print(f"     Endereço: '{m.endereco}'")
            print(f"     Número: '{m.numero}'")
            print(f"     Cidade: '{m.cidade}'")
            print(f"     UF: '{m.uf}'")
    else:
        print(f"   ❌ Nenhum mutuário encontrado para o conjunto '{contrato.conjunto}'")
else:
    print(f"   ⚠️  Contrato sem conjunto definido")

# Remove as verificações antigas
print(f"\n🔧 Como o FH1Generator deve buscar dados:")
# Remove as verificações antigas
print(f"\n🔧 Como o FH1Generator deve buscar dados:")
print(f"   1. Buscar mutuários por: Mutuario.objects.filter(conjunto='{contrato.conjunto}')")
print(f"   2. Pegar o primeiro: .first()")

primeiro_mut = Mutuario.objects.filter(conjunto=contrato.conjunto).first()
if primeiro_mut:
    print(f"   ✅ Primeiro mutuário encontrado: {primeiro_mut.nome}")
else:
    print(f"   ❌ Nenhum mutuário encontrado pelo conjunto")

print("\n" + "=" * 80)
