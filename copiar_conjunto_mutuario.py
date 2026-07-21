"""
SOLUÇÃO FINAL: Copiar conjunto do Mutuario para o Contrato
usando o campo codimovel como chave
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario
from django.db.models import Count

print("=" * 70)
print("COPIANDO CONJUNTO DO MUTUARIO PARA O CONTRATO")
print("=" * 70)
print()

# Criar um mapeamento codimovel -> conjunto
print("Criando mapeamento codimovel -> conjunto...")
conjunto_por_codimovel = {}

for mutuario in Mutuario.objects.exclude(conjunto='').exclude(codimovel=''):
    # Normalizar codimovel (remover zeros)
    codimovel_norm = mutuario.codimovel.lstrip('0') or '0'
    conjunto_por_codimovel[codimovel_norm] = mutuario.conjunto

print(f"✓ {len(conjunto_por_codimovel)} mapeamentos criados")
print()

# Mostrar alguns exemplos
print("Exemplos de mapeamento:")
for i, (cod, conj) in enumerate(list(conjunto_por_codimovel.items())[:10]):
    print(f"  codimovel {cod} -> conjunto '{conj}'")

print()
print("=" * 70)
print("ATUALIZANDO CONTRATOS")
print("=" * 70)
print()

atualizados = 0
nao_encontrados = 0

for contrato in Contrato.objects.all():
    if not contrato.cod_imovel:
        nao_encontrados += 1
        continue
    
    # Normalizar cod_imovel
    cod_imovel_norm = contrato.cod_imovel.lstrip('0') or '0'
    
    if cod_imovel_norm in conjunto_por_codimovel:
        novo_conjunto = conjunto_por_codimovel[cod_imovel_norm]
        
        if contrato.conjunto != novo_conjunto:
            contrato.conjunto = novo_conjunto
            contrato.save(update_fields=['conjunto'])
            atualizados += 1
            
            if atualizados <= 10:
                print(f"  Contrato {contrato.codigo}: cod_imovel {contrato.cod_imovel} -> conjunto '{novo_conjunto}'")
    else:
        nao_encontrados += 1

print()
print(f"✓ {atualizados} contratos atualizados")
print(f"  {nao_encontrados} contratos sem correspondência")

print()
print("=" * 70)
print("VERIFICAÇÃO FINAL")
print("=" * 70)
print()

# Verificar contrato 6000
c6000 = Contrato.objects.filter(codigo='6000').first()
if c6000:
    print(f"Contrato 6000:")
    print(f"  Código: {c6000.codigo}")
    print(f"  Cod Imóvel: {c6000.cod_imovel}")
    print(f"  Conjunto: '{c6000.conjunto}'")
    print(f"  Ocorrência: '{c6000.ocorrencia}'")
    print()
    
    # Verificar se está correto
    if c6000.conjunto == '010':
        print("✓ CORRETO! Conjunto está '010' conforme esperado!")
    else:
        print(f"✗ Esperado '010', mas está '{c6000.conjunto}'")
        # Tentar buscar o mutuário manualmente
        cod_imovel_norm = c6000.cod_imovel.lstrip('0') or '0'
        mutuario = Mutuario.objects.filter(codimovel__endswith=cod_imovel_norm).first()
        if mutuario:
            print(f"  Mutuário encontrado: {mutuario.codigo} - {mutuario.nome}")
            print(f"  Conjunto do mutuário: '{mutuario.conjunto}'")

print()
print("Distribuição final de conjuntos:")
distribuicao = Contrato.objects.values('conjunto').annotate(count=Count('id')).order_by('conjunto')
for item in distribuicao:
    conj = item['conjunto'] or '(vazio)'
    if item['count'] > 0:
        print(f"  '{conj}': {item['count']} contratos")
