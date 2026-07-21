# -*- coding: utf-8 -*-
"""
Conversão de Valores Históricos para Real
Considera todas as mudanças de moeda do Brasil
"""

import django
import os
import sys
from datetime import datetime
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato


def converter_para_real(valor, data_referencia):
    """
    Converte valor histórico para Real considerando mudanças de moeda
    
    Args:
        valor: Valor na moeda da época
        data_referencia: Data do valor (datetime ou string 'DD/MM/AAAA')
    
    Returns:
        Decimal: Valor convertido para Real (R$)
    """
    if isinstance(data_referencia, str):
        data_referencia = datetime.strptime(data_referencia, '%d/%m/%Y')
    elif hasattr(data_referencia, 'date') and not isinstance(data_referencia, datetime):
        # Se for date, converter para datetime
        data_referencia = datetime.combine(data_referencia, datetime.min.time())
    
    # Fatores de conversão acumulados
    fator = Decimal('1.0')
    
    # 1994-07-01: Cruzeiro Real -> Real (divide por 2.750)
    if data_referencia < datetime(1994, 7, 1):
        fator = fator / Decimal('2750')
    
    # 1993-08-01: Cruzeiro -> Cruzeiro Real (divide por 1.000)
    if data_referencia < datetime(1993, 8, 1):
        fator = fator / Decimal('1000')
    
    # 1990-03-16: Cruzado Novo -> Cruzeiro (sem corte de zeros)
    # Mesma denominação, só mudou nome
    
    # 1989-01-16: Cruzado -> Cruzado Novo (divide por 1.000)
    if data_referencia < datetime(1989, 1, 16):
        fator = fator / Decimal('1000')
    
    # 1986-02-28: Cruzeiro -> Cruzado (divide por 1.000)
    if data_referencia < datetime(1986, 2, 28):
        fator = fator / Decimal('1000')
    
    # 1970-05-15: Cruzeiro Novo -> Cruzeiro (sem corte de zeros)
    # Só voltou o nome
    
    # 1967-02-13: Cruzeiro -> Cruzeiro Novo (divide por 1.000)
    if data_referencia < datetime(1967, 2, 13):
        fator = fator / Decimal('1000')
    
    return valor * fator


def identificar_moeda(data):
    """Identifica qual moeda estava em vigor na data"""
    from datetime import date
    
    if isinstance(data, str):
        data = datetime.strptime(data, '%d/%m/%Y').date()
    elif isinstance(data, datetime):
        data = data.date()
    
    if data >= date(1994, 7, 1):
        return "Real (R$)"
    elif data >= date(1993, 8, 1):
        return "Cruzeiro Real (CR$)"
    elif data >= date(1990, 3, 16):
        return "Cruzeiro (Cr$)"
    elif data >= date(1989, 1, 16):
        return "Cruzado Novo (NCz$)"
    elif data >= date(1986, 2, 28):
        return "Cruzado (Cz$)"
    elif data >= date(1970, 5, 15):
        return "Cruzeiro (Cr$)"
    elif data >= date(1967, 2, 13):
        return "Cruzeiro Novo (NCr$)"
    else:
        return "Cruzeiro (Cr$)"


def analisar_datas_parcelas():
    """Analisa as datas das parcelas para identificar período dos dados"""
    print("\n" + "="*80)
    print("ANALISE DAS DATAS DAS PARCELAS")
    print("="*80 + "\n")
    
    # Pegar amostra de contratos
    contratos_amostra = Contrato.objects.all()[:100]
    
    datas_encontradas = []
    
    for contrato in contratos_amostra:
        parcelas = ParcelaContrato.objects.filter(contrato=contrato).order_by('nmens')
        
        if parcelas.exists():
            primeira = parcelas.first()
            ultima = parcelas.last()
            
            # Verificar se tem campo de data
            if hasattr(primeira, 'dtvenc') and primeira.dtvenc:
                datas_encontradas.append({
                    'contrato': contrato.codigo,
                    'primeira_data': primeira.dtvenc,
                    'ultima_data': ultima.dtvenc if hasattr(ultima, 'dtvenc') else None,
                    'primeira_parcela': primeira.nmens,
                    'ultima_parcela': ultima.nmens,
                    'saldo_atual': ultima.sddev if ultima.sddev else Decimal('0')
                })
    
    if datas_encontradas:
        print(f"Encontradas {len(datas_encontradas)} contratos com datas\n")
        print("Primeiros 10 contratos:")
        for item in datas_encontradas[:10]:
            print(f"\nContrato {item['contrato']}:")
            print(f"  Primeira parcela (mes {item['primeira_parcela']}): {item['primeira_data']}")
            print(f"  Moeda na epoca: {identificar_moeda(item['primeira_data'])}")
            print(f"  Ultima parcela (mes {item['ultima_parcela']}): {item['ultima_data']}")
            print(f"  Saldo atual no banco: {item['saldo_atual']:,.2f}")
    else:
        print("ATENCAO: Nenhuma parcela com campo de data encontrada!")
        print("Precisamos identificar a data por outro meio (campo nmens, tabela contrato, etc)")
    
    print("\n" + "="*80 + "\n")
    
    return datas_encontradas


def testar_conversao():
    """Testa conversão de valores históricos"""
    print("\n" + "="*80)
    print("TESTE DE CONVERSAO DE MOEDAS")
    print("="*80 + "\n")
    
    exemplos = [
        ('15/04/1991', Decimal('1207860.36'), 'Cruzeiro'),
        ('01/07/1994', Decimal('100.00'), 'Real'),
        ('15/03/1986', Decimal('1000000.00'), 'Cruzeiro (pre-Cruzado)'),
        ('01/05/2019', Decimal('10000.00'), 'Real'),
    ]
    
    for data_str, valor_original, moeda_desc in exemplos:
        moeda = identificar_moeda(data_str)
        valor_real = converter_para_real(valor_original, data_str)
        
        print(f"Data: {data_str}")
        print(f"  Moeda identificada: {moeda}")
        print(f"  Valor original: {valor_original:,.2f} ({moeda_desc})")
        print(f"  Valor em Real: R$ {valor_real:,.2f}")
        print()
    
    print("="*80 + "\n")


def main():
    print("\n" + "="*80)
    print("INVESTIGACAO: VALORES HISTORICOS E MUDANCAS DE MOEDA")
    print("="*80 + "\n")
    
    # 1. Testar conversões
    testar_conversao()
    
    # 2. Analisar datas das parcelas
    datas_parcelas = analisar_datas_parcelas()
    
    # 3. Verificar estrutura da tabela
    print("\n" + "="*80)
    print("ESTRUTURA DA TABELA DE PARCELAS")
    print("="*80 + "\n")
    
    parcela_exemplo = ParcelaContrato.objects.first()
    if parcela_exemplo:
        print("Campos disponiveis na tabela ParcelaContrato:")
        for field in parcela_exemplo._meta.fields:
            valor = getattr(parcela_exemplo, field.name, None)
            print(f"  {field.name}: {valor} (tipo: {field.get_internal_type()})")
    
    print("\n" + "="*80)
    print("\nRECOMENDACAO:")
    print("  1. Verificar se existe campo de DATA nas parcelas")
    print("  2. Se nao houver data, usar a data de INICIO do contrato")
    print("  3. Converter todos os saldos usando a funcao converter_para_real()")
    print("  4. Atualizar banco com valores corrigidos ANTES de aplicar correcao monetaria")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
