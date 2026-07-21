"""
Diagnóstico do preenchimento de cidades
"""
import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario, Endereco

print("=" * 80)
print("DIAGNÓSTICO - CIDADES DOS ENDEREÇOS")
print("=" * 80)

# Verificar mutuário 6000 especificamente
m = Mutuario.objects.filter(codigo='6000').first()

if m:
    print(f"\n✅ Mutuário 6000:")
    print(f"   Nome: {m.nome}")
    print(f"   Conjunto: {m.conjunto}")
    print(f"   Tem endereco_fk: {m.endereco_fk is not None}")
    
    if m.endereco_fk:
        print(f"   Endereço ID: {m.endereco_fk.id}")
        print(f"   Endereço: {m.endereco_fk.endereco}")
        print(f"   Número: {m.endereco_fk.numero}")
        print(f"   Cidade: '{m.endereco_fk.cidade}'")
        print(f"   UF: {m.endereco_fk.uf}")
        print(f"   CEP: {m.endereco_fk.cep}")
    else:
        print("   ❌ SEM ENDERECO_FK!")
else:
    print("\n❌ Mutuário 6000 não encontrado!")

# Estatísticas gerais
print("\n" + "=" * 80)
print("ESTATÍSTICAS GERAIS")
print("=" * 80)

total_mutuarios = Mutuario.objects.count()
com_endereco = Mutuario.objects.filter(endereco_fk__isnull=False).count()
sem_endereco = total_mutuarios - com_endereco

print(f"\nMutuários:")
print(f"   Total: {total_mutuarios}")
print(f"   Com endereco_fk: {com_endereco}")
print(f"   Sem endereco_fk: {sem_endereco}")

# Verificar endereços por conjunto
print("\n" + "=" * 80)
print("ENDEREÇOS POR CONJUNTO")
print("=" * 80)

conjuntos = ['001', '002', '003', '004', '005', '006', '008', '009', '010', '011', '012']

for conj in conjuntos:
    mutuarios_conj = Mutuario.objects.filter(conjunto=conj)
    total = mutuarios_conj.count()
    com_end = mutuarios_conj.filter(endereco_fk__isnull=False).count()
    com_cidade = mutuarios_conj.filter(endereco_fk__isnull=False, endereco_fk__cidade__gt='').count()
    sem_cidade = com_end - com_cidade
    
    print(f"\nConjunto {conj}:")
    print(f"   Total: {total}")
    print(f"   Com endereço: {com_end}")
    print(f"   Com cidade: {com_cidade}")
    print(f"   Sem cidade: {sem_cidade}")
    
    # Mostrar exemplo de mutuário sem cidade
    if sem_cidade > 0:
        exemplo = mutuarios_conj.filter(
            endereco_fk__isnull=False, 
            endereco_fk__cidade=''
        ).first()
        if exemplo:
            print(f"   Exemplo sem cidade: {exemplo.codigo} - Endereço ID: {exemplo.endereco_fk.id}")

print("\n✅ DIAGNÓSTICO CONCLUÍDO!")
