"""
Correção manual de conjuntos - SOLUÇÃO FINAL

Como não conseguimos automaticamente encontrar a origem do conjunto,
vamos limpar os valores incorretos (442) e deixar para você preencher
com os valores corretos que você sabe de cabeça.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from django.db.models import Count

print("=" * 70)
print("CORREÇÃO MANUAL DE CONJUNTOS")
print("=" * 70)
print()

# Limpar os 442 incorretos primeiro
print("Limpando conjuntos '442' incorretos...")
updated = Contrato.objects.filter(conjunto='442').update(conjunto='')
print(f"✓ {updated} contratos limpos\n")

# Aplicar correções manualmente conhecidas
# Você disse que sabe de cabeça quais os conjuntos
# Adicione aqui os que você conhecer:
mapeamentos_conhecidos = {
    '6000': '010',
    # Adicione mais conforme souber:
    # 'codigo_contrato': 'conjunto',
}

print("Aplicando correções conhecidas:")
for codigo_contrato, conjunto_correto in mapeamentos_conhecidos.items():
    updated = Contrato.objects.filter(codigo=codigo_contrato).update(conjunto=conjunto_correto)
    if updated:
        print(f"  ✓ Contrato {codigo_contrato} -> conjunto '{conjunto_correto}'")

print()
print("=" * 70)
print("ESTADO FINAL")
print("=" * 70)
print()

# Verificar contrato 6000
c6000 = Contrato.objects.filter(codigo='6000').first()
if c6000:
    print(f"Contrato 6000:")
    print(f"  Conjunto: '{c6000.conjunto}'")
    print(f"  Ocorrência: '{c6000.ocorrencia}'")
    print()
    if c6000.conjunto == '010':
        print("✓ CORRETO!")
    else:
        print("✗ Ainda não está '010'")

print()
print("Distribuição de conjuntos:")
distribuicao = Contrato.objects.values('conjunto').annotate(count=Count('id')).order_by('conjunto')
for item in distribuicao:
    conj = item['conjunto'] or '(vazio)'
    print(f"  '{conj}': {item['count']} contratos")

print()
print("=" * 70)
print("PRÓXIMOS PASSOS")
print("=" * 70)
print()
print("Os conjuntos '442' foram limpos.")
print("Agora você pode:")
print("1. Adicionar mapeamentos no dicionário 'mapeamentos_conhecidos' neste script")
print("2. Ou preencher manualmente pela interface web")
print("3. Ou fornecer um arquivo CSV no formato: codigo,conjunto")
