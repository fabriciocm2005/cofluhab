#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Investigar valores reais do contrato 6080
"""

from dbfread import DBF
from datetime import date

print("="*100)
print("INVESTIGAÇÃO DETALHADA - CONTRATO 6080")
print("="*100)

db = DBF('dados_antigos/DEBPREST.DBF', encoding='latin1')

debitos = []
for rec in db:
    contrato = str(rec.get('CONTRATO', '')).strip()
    if contrato in ['006080', '6080']:
        debitos.append(rec)

print(f"\nTotal de débitos: {len(debitos)}")

# Analisar por faixas de data
faixas = {
    'Antes de 1990': [],
    '1990-1993': [],
    '1993-1994': [],
    'Após 1994': []
}

for deb in debitos:
    vencimento = deb.get('VENCIMENTO')
    total = float(deb.get('TOTAL', 0))
    
    if not vencimento:
        continue
    
    if vencimento < date(1990, 1, 1):
        faixas['Antes de 1990'].append(total)
    elif vencimento < date(1993, 8, 1):
        faixas['1990-1993'].append(total)
    elif vencimento < date(1994, 7, 1):
        faixas['1993-1994'].append(total)
    else:
        faixas['Após 1994'].append(total)

print("\nDistribuição de valores por período:")
print("-" * 100)

for periodo, valores in faixas.items():
    if valores:
        media = sum(valores) / len(valores)
        minimo = min(valores)
        maximo = max(valores)
        total = sum(valores)
        print(f"\n{periodo}:")
        print(f"  Quantidade: {len(valores)}")
        print(f"  Média: R$ {media:.2f}")
        print(f"  Mínimo: R$ {minimo:.2f}")
        print(f"  Máximo: R$ {maximo:.2f}")
        print(f"  Total: R$ {total:.2f}")

# Mostrar alguns exemplos de cada período
print("\n" + "="*100)
print("EXEMPLOS DE VALORES POR PERÍODO")
print("="*100)

for periodo_nome, periodo_valores in [
    ('Antes de 1990 (Cruzado)', debitos[:5]),
    ('1990-1993 (Cruzeiro)', [d for d in debitos if d.get('VENCIMENTO') and date(1990,1,1) <= d.get('VENCIMENTO') < date(1993,8,1)][:5]),
    ('1993-1994 (Cruzeiro Real)', [d for d in debitos if d.get('VENCIMENTO') and date(1993,8,1) <= d.get('VENCIMENTO') < date(1994,7,1)][:5]),
    ('Após 1994 (Real)', [d for d in debitos if d.get('VENCIMENTO') and d.get('VENCIMENTO') >= date(1994,7,1)][:5])
]:
    print(f"\n{periodo_nome}:")
    print(f"{'Prestação':<10} {'Vencimento':<12} {'Valor':<15} {'Moradia':<10} {'EM':<10}")
    print("-" * 60)
    for d in periodo_valores:
        if d.get('VENCIMENTO'):
            print(f"{d.get('PRESTACAO', 0):<10} {str(d.get('VENCIMENTO')):<12} R$ {float(d.get('TOTAL', 0)):>10.2f} {float(d.get('MORADIA', 0)):>8.2f} {float(d.get('EM', 0)):>8.2f}")

# Verificar se valores já estão em Real
print("\n" + "="*100)
print("ANÁLISE: Os valores JÁ ESTÃO EM REAL?")
print("="*100)

# Pegar valores de 1994 em diante (que sabemos que são Real)
valores_real = [float(d.get('TOTAL', 0)) for d in debitos if d.get('VENCIMENTO') and d.get('VENCIMENTO') >= date(1994, 7, 1)]

if valores_real:
    media_real = sum(valores_real) / len(valores_real)
    print(f"\nValores após 07/1994 (Real confirmado):")
    print(f"  Média: R$ {media_real:.2f}")
    print(f"  Mínimo: R$ {min(valores_real):.2f}")
    print(f"  Máximo: R$ {max(valores_real):.2f}")

# Comparar com valores antigos
valores_antigos = [float(d.get('TOTAL', 0)) for d in debitos if d.get('VENCIMENTO') and d.get('VENCIMENTO') < date(1990, 1, 1)]

if valores_antigos:
    media_antiga = sum(valores_antigos) / len(valores_antigos)
    print(f"\nValores antes de 1990 (moeda antiga):")
    print(f"  Média: R$ {media_antiga:.2f}")
    print(f"  Mínimo: R$ {min(valores_antigos):.2f}")
    print(f"  Máximo: R$ {max(valores_antigos):.2f}")
    
    if media_antiga > 50:  # Se a média é maior que 50, provavelmente já está em Real
        print("\n⚠️  CONCLUSÃO: Os valores antigos parecem GRANDES demais para serem moeda antiga!")
        print("    Possibilidade: Os valores JÁ FORAM CONVERTIDOS no arquivo DBF original")
        print("    Solução: NÃO aplicar conversão, usar valores diretos!")
