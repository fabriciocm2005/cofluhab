"""
Preenche cidade dos endereços baseado no conjunto habitacional
"""
import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario, Endereco

print("=" * 80)
print("PREENCHENDO CIDADE BASEADO NO CONJUNTO")
print("=" * 80)

# Mapeamento conjunto -> cidade
CONJUNTO_CIDADE = {
    '001': 'NOVA FRIBURGO',
    '002': 'NOVA FRIBURGO',
    '003': 'NOVA FRIBURGO',
    '004': 'NOVA FRIBURGO',
    '005': 'NOVA FRIBURGO',
    '006': 'NOVA FRIBURGO',
    '008': 'NOVA FRIBURGO',
    '009': 'NOVA FRIBURGO',
    '010': 'MARICÁ',
    '011': 'MARICÁ',
    '012': 'NOVA FRIBURGO',
}

print("\n📋 Mapeamento Conjunto -> Cidade:")
for conj, cidade in CONJUNTO_CIDADE.items():
    print(f"   {conj}: {cidade}")

print("\n🔍 Processando mutuários...")

atualizados = 0
sem_conjunto = 0

for mutuario in Mutuario.objects.select_related('endereco_fk').all():
    # Pular se não tem endereço vinculado
    if not mutuario.endereco_fk:
        continue
    
    # Pular se já tem cidade
    if mutuario.endereco_fk.cidade:
        continue
    
    # Verificar se tem conjunto
    if not mutuario.conjunto:
        sem_conjunto += 1
        continue
    
    # Buscar cidade pelo conjunto
    cidade = CONJUNTO_CIDADE.get(mutuario.conjunto)
    
    if cidade:
        mutuario.endereco_fk.cidade = cidade
        mutuario.endereco_fk.save(update_fields=['cidade'])
        atualizados += 1
        
        if atualizados <= 5:
            print(f"  ✓ Mutuário {mutuario.codigo} (Conjunto {mutuario.conjunto}): {cidade}")

print(f"\n✅ {atualizados} endereços atualizados com cidade")
print(f"⚠️  {sem_conjunto} mutuários sem conjunto")

# Relatório por conjunto
print("\n" + "=" * 80)
print("RELATÓRIO POR CONJUNTO")
print("=" * 80)

from django.db.models import Count

for conjunto, cidade in sorted(CONJUNTO_CIDADE.items()):
    com_cidade = Mutuario.objects.filter(
        conjunto=conjunto,
        endereco_fk__cidade=cidade
    ).count()
    
    sem_cidade = Mutuario.objects.filter(
        conjunto=conjunto,
        endereco_fk__isnull=False,
        endereco_fk__cidade=''
    ).count()
    
    total_conjunto = Mutuario.objects.filter(conjunto=conjunto).count()
    
    print(f"\nConjunto {conjunto} - {cidade}:")
    print(f"   Total: {total_conjunto} mutuários")
    print(f"   Com cidade: {com_cidade}")
    print(f"   Sem cidade: {sem_cidade}")

print("\n✅ PROCESSAMENTO CONCLUÍDO!")
