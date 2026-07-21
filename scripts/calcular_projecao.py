"""
Calcula projeção de atualização monetária
Sem alterar o banco de dados - apenas visualização
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

def main():
    print("=" * 80)
    print("PROJECAO DE ATUALIZACAO MONETARIA")
    print("=" * 80)
    print()
    
    # Pegar saldo total atual (última parcela de cada contrato)
    saldo_total = Decimal('0')
    total_contratos = 0
    
    for contrato in Contrato.objects.all():
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if ultima_parcela and ultima_parcela.sddev:
            saldo_total += ultima_parcela.sddev
            total_contratos += 1
    
    # Fator de correção IPCA de maio/2019 a novembro/2025 (78 meses)
    # Fator aproximado: 41,46%
    fator_correcao = Decimal('1.4146')
    
    # Calcular saldo corrigido
    saldo_corrigido = saldo_total * fator_correcao
    correcao_aplicada = saldo_corrigido - saldo_total
    
    # Exibir resultados
    print(f"Contratos analisados: {total_contratos:,}")
    print()
    print(f"Saldo Total Atual (MAIO/2019): R$ {saldo_total:,.2f}")
    print(f"Fator de Correcao (mai/2019 a nov/2025): {fator_correcao} (+41,46%)")
    print()
    print(f"Saldo Atualizado (NOVEMBRO/2025): R$ {saldo_corrigido:,.2f}")
    print()
    print(f"Correcao Aplicada: R$ {correcao_aplicada:,.2f}")
    print()
    print("=" * 80)
    print()
    print("OBSERVACAO: Estes valores sao apenas uma projecao.")
    print("Nenhuma alteracao foi feita no banco de dados.")
    print("=" * 80)

if __name__ == '__main__':
    main()
