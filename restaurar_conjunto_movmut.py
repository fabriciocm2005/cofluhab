"""
Restaurar o conjunto correto a partir do arquivo MOVMUT.DBF original

O campo CONJUNTO no MOVMUT.DBF tem o valor correto (ex: "010")
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from dbfread import DBF
from collections import defaultdict

print("=" * 70)
print("RESTAURANDO CONJUNTO A PARTIR DO MOVMUT.DBF")
print("=" * 70)
print()

movmut_path = 'dados_antigos/MOVMUT.DBF'

if not os.path.exists(movmut_path):
    print(f"Erro: Arquivo não encontrado: {movmut_path}")
    exit(1)

print(f"Lendo {movmut_path}...")
print("(pode levar alguns minutos...)")
print()

# Mapear código do contrato -> conjunto
# Vamos pegar o conjunto mais comum para cada código
conjunto_por_codigo = defaultdict(lambda: defaultdict(int))

try:
    table = DBF(movmut_path, encoding='latin1', ignorecase=True, load=False)
    
    total = 0
    erros = 0
    
    for record in table:
        try:
            codigo = str(record.get('CODIGO', '')).strip()
            conjunto = str(record.get('CONJUNTO', '')).strip()
            
            if codigo and conjunto:
                # Normalizar código (remover zeros à esquerda)
                codigo_norm = codigo.lstrip('0') or '0'
                # Manter conjunto COM zeros à esquerda!
                conjunto_por_codigo[codigo_norm][conjunto] += 1
                total += 1
                
                if total % 10000 == 0:
                    print(f"  Processados {total} registros...")
                    
        except Exception as e:
            erros += 1
            if erros <= 10:
                print(f"  Erro ao processar registro: {e}")
    
    print(f"\n✓ Lidos {total} registros do MOVMUT.DBF")
    print(f"  Códigos únicos encontrados: {len(conjunto_por_codigo)}")
    print(f"  Erros: {erros}")
    
except Exception as e:
    print(f"Erro ao ler arquivo DBF: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 70)
print("ATUALIZANDO CONTRATOS")
print("=" * 70)
print()

# Para cada código, pegar o conjunto mais comum
conjunto_final = {}
for codigo, conjuntos in conjunto_por_codigo.items():
    # Pegar o conjunto com mais ocorrências
    conjunto_mais_comum = max(conjuntos.items(), key=lambda x: x[1])[0]
    conjunto_final[codigo] = conjunto_mais_comum

# Verificar contrato 6000
if '6000' in conjunto_final:
    print(f"Conjunto encontrado para código 6000: '{conjunto_final['6000']}'")
    print()

# Atualizar contratos
contratos = Contrato.objects.all()
atualizados = 0
nao_encontrados = 0

for contrato in contratos:
    codigo = contrato.codigo.lstrip('0') or '0'
    
    if codigo in conjunto_final:
        novo_conjunto = conjunto_final[codigo]
        if contrato.conjunto != novo_conjunto:
            contrato.conjunto = novo_conjunto
            contrato.save(update_fields=['conjunto'])
            atualizados += 1
            
            if atualizados <= 10:
                print(f"  Atualizado contrato {contrato.codigo}: conjunto='{novo_conjunto}'")
    else:
        nao_encontrados += 1

print()
print(f"✓ {atualizados} contratos atualizados")
print(f"  {nao_encontrados} contratos sem correspondência no MOVMUT")

print()
print("=" * 70)
print("VERIFICAÇÃO")
print("=" * 70)
print()

# Verificar contrato 6000
c6000 = Contrato.objects.filter(codigo='6000').first()
if c6000:
    print(f"Contrato 6000:")
    print(f"  Conjunto: '{c6000.conjunto}'")
    print(f"  Ocorrência: '{c6000.ocorrencia}'")

# Mostrar distribuição final
from django.db.models import Count
print()
print("Distribuição final de conjuntos:")
distribuicao = Contrato.objects.values('conjunto').annotate(count=Count('id')).order_by('-count')[:20]
for item in distribuicao:
    conj = item['conjunto'] or '(vazio)'
    print(f"  '{conj}': {item['count']} contratos")
