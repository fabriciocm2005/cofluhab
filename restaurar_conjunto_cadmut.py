"""
SOLUÇÃO FINAL: Restaurar conjunto do CADMUT.DBF

O CADMUT.DBF tem:
- CODIGO (código do mutuário)
- CONJUNTO (o valor correto com zeros, ex: "010")

Vamos:
1. Ler CADMUT.DBF e mapear CODIGO -> CONJUNTO
2. Para cada Contrato, pegar o mutuário associado
3. Atualizar o conjunto do contrato com base no conjunto do mutuário
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario
from dbfread import DBF
from collections import defaultdict

print("=" * 70)
print("RESTAURANDO CONJUNTO A PARTIR DO CADMUT.DBF")
print("=" * 70)
print()

cadmut_path = 'dados_antigos/CADMUT.DBF'

print(f"Lendo {cadmut_path}...")
print()

# Mapear código do mutuário -> conjunto
conjunto_por_mutuario = {}

try:
    table = DBF(cadmut_path, encoding='latin1', ignorecase=True, load=False)
    
    total = 0
    com_conjunto = 0
    
    for record in table:
        try:
            codigo = str(record.get('CODIGO', '')).strip()
            conjunto = str(record.get('CONJUNTO', '')).strip()
            
            if codigo:
                # Normalizar código mutuário (remover zeros)
                codigo_norm = codigo.lstrip('0') or '0'
                
                if conjunto:
                    conjunto_por_mutuario[codigo_norm] = conjunto
                    com_conjunto += 1
                
                total += 1
                
                if total % 1000 == 0:
                    print(f"  Processados {total} registros...")
                    
        except Exception as e:
            continue
    
    print(f"\n✓ Lidos {total} registros do CADMUT.DBF")
    print(f"  Mutuários com conjunto: {com_conjunto}")
    
except Exception as e:
    print(f"Erro ao ler arquivo DBF: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

if not conjunto_por_mutuario:
    print("\n✗ Nenhum conjunto encontrado no CADMUT.DBF")
    exit(1)

print()
print("Exemplos de mapeamento:")
for i, (cod, conj) in enumerate(list(conjunto_por_mutuario.items())[:10]):
    print(f"  Mutuário {cod} -> Conjunto '{conj}'")

print()
print("=" * 70)
print("ATUALIZANDO CONTRATOS")
print("=" * 70)
print()

# Atualizar contratos
contratos = Contrato.objects.select_related('mutuario_principal').all()
atualizados = 0
nao_encontrados = 0
sem_mutuario = 0

for contrato in contratos:
    if not contrato.mutuario_principal:
        sem_mutuario += 1
        continue
    
    # Código do mutuário normalizado
    codigo_mutuario = contrato.mutuario_principal.codigo.lstrip('0') or '0'
    
    if codigo_mutuario in conjunto_por_mutuario:
        novo_conjunto = conjunto_por_mutuario[codigo_mutuario]
        
        if contrato.conjunto != novo_conjunto:
            contrato.conjunto = novo_conjunto
            contrato.save(update_fields=['conjunto'])
            atualizados += 1
            
            if atualizados <= 10:
                print(f"  Contrato {contrato.codigo}: mutuário {codigo_mutuario} -> conjunto '{novo_conjunto}'")
    else:
        nao_encontrados += 1

print()
print(f"✓ {atualizados} contratos atualizados")
print(f"  {nao_encontrados} contratos: mutuário sem conjunto no CADMUT")
print(f"  {sem_mutuario} contratos sem mutuário associado")

print()
print("=" * 70)
print("VERIFICAÇÃO FINAL")
print("=" * 70)
print()

# Verificar contrato 6000
c6000 = Contrato.objects.select_related('mutuario_principal').filter(codigo='6000').first()
if c6000:
    print(f"Contrato 6000:")
    print(f"  Conjunto: '{c6000.conjunto}'")
    print(f"  Ocorrência: '{c6000.ocorrencia}'")
    if c6000.mutuario_principal:
        print(f"  Mutuário: {c6000.mutuario_principal.codigo} - {c6000.mutuario_principal.nome}")

# Mostrar distribuição final
from django.db.models import Count
print()
print("Distribuição final de conjuntos:")
distribuicao = Contrato.objects.values('conjunto').annotate(count=Count('id')).order_by('conjunto')
for item in distribuicao:
    conj = item['conjunto'] or '(vazio)'
    if item['count'] > 0:
        print(f"  '{conj}': {item['count']} contratos")
