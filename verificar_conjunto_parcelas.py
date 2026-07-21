"""
Script para verificar o campo conjunto nas parcelas do contrato 6000
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

print("Verificando conjunto nas parcelas do contrato 6000...\n")

try:
    contrato = Contrato.objects.get(codigo='6000')
    print(f"Contrato atual:")
    print(f"  Código: {contrato.codigo}")
    print(f"  Conjunto: '{contrato.conjunto}'")
    print(f"  Ocorrência: '{contrato.ocorrencia}'")
    print()
    
    # Buscar parcelas
    parcelas = ParcelaContrato.objects.filter(contrato=contrato)
    
    print(f"Total de parcelas: {parcelas.count()}")
    print()
    
    # Listar valores distintos de conjunto nas parcelas
    conjuntos_distintos = parcelas.values_list('conjunto', flat=True).distinct().order_by('conjunto')
    print(f"Valores distintos de conjunto nas parcelas:")
    for conj in conjuntos_distintos:
        count = parcelas.filter(conjunto=conj).count()
        print(f"  '{conj}': {count} parcelas")
    
    print()
    
    # Mostrar algumas parcelas como exemplo
    print("Primeiras 5 parcelas:")
    for p in parcelas[:5]:
        print(f"  Parcela {p.numero_parcela}: conjunto='{p.conjunto}', lote='{p.lote}'")
    
except Contrato.DoesNotExist:
    print("Contrato 6000 não encontrado")
except Exception as e:
    print(f"Erro: {e}")
