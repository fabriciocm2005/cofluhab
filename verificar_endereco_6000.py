"""
Script para adicionar endereço manualmente ao mutuário 6000
"""
import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario, Endereco

print("=" * 80)
print("VERIFICANDO E ADICIONANDO ENDEREÇO PARA MUTUÁRIO 6000")
print("=" * 80)

# Buscar mutuário
mutuario = Mutuario.objects.filter(codigo='6000').first()

if not mutuario:
    print("\n❌ Mutuário 6000 não encontrado!")
    sys.exit(1)

print(f"\n✅ Mutuário encontrado:")
print(f"   Nome: {mutuario.nome}")
print(f"   CPF: {mutuario.cpf}")
print(f"   Conjunto: {mutuario.conjunto}")

if mutuario.endereco_fk:
    print(f"\n✅ Já tem endereço:")
    print(f"   Endereço: {mutuario.endereco_fk.endereco}, {mutuario.endereco_fk.numero}")
    print(f"   Cidade: {mutuario.endereco_fk.cidade}")
else:
    print(f"\n⚠️  SEM endereço vinculado")
    print(f"\nPara adicionar endereço, forneça os dados:")
    print(f"   EXEMPLO:")
    print(f"   Endereço: RUA EXEMPLO")
    print(f"   Número: 123")
    print(f"   Bairro: BAIRRO EXEMPLO")
    print(f"   Cidade: NOVA FRIBURGO")
    print(f"   CEP: 28600-000")
    print(f"\nOu verifique se existe no arquivo CADEND.DBF com outro código")

print("\n" + "=" * 80)
