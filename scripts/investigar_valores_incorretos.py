"""
Investiga contratos com valores incorretos (moedas antigas não convertidas)
Identifica contratos que precisam de conversão de moeda
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

def identificar_moeda(data_parcela, valor):
    """
    Identifica a moeda baseado na data da parcela
    e se o valor parece estar em moeda antiga
    """
    if data_parcela < date(1967, 2, 13):
        return 'Cr$ (Cruzeiro antigo)', 1_000_000_000_000
    elif data_parcela < date(1986, 2, 28):
        return 'Cr$ (Cruzeiro)', 1_000_000_000
    elif data_parcela < date(1989, 1, 16):
        return 'Cz$ (Cruzado)', 1_000_000
    elif data_parcela < date(1990, 3, 16):
        return 'NCz$ (Cruzado Novo)', 1_000
    elif data_parcela < date(1993, 8, 1):
        return 'Cr$ (Cruzeiro)', 1_000
    elif data_parcela < date(1994, 7, 1):
        return 'CR$ (Cruzeiro Real)', 2_750
    else:
        return 'R$ (Real)', 1

def converter_para_real(valor, fator_conversao):
    """Converte valor de moeda antiga para Real"""
    return valor / Decimal(str(fator_conversao))

def main():
    print("=" * 100)
    print("INVESTIGACAO DE CONTRATOS COM VALORES INCORRETOS")
    print("=" * 100)
    print()
    
    # Coletar todos os contratos com suas últimas parcelas DE UMA VEZ (otimização)
    print("[Carregando dados...]")
    todos_contratos = []
    
    for contrato in Contrato.objects.select_related().all():
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if ultima_parcela and ultima_parcela.sddev:
            todos_contratos.append({
                'contrato': contrato.codigo,
                'conjunto': contrato.conjunto,
                'saldo': ultima_parcela.sddev,
                'data': ultima_parcela.dtvenc
            })
    
    print(f"[{len(todos_contratos)} contratos carregados]")
    print()
    
    # Analisar contratos por faixas de valor
    faixas = [
        (Decimal('0'), Decimal('1000'), 'Ate R$ 1.000'),
        (Decimal('1000'), Decimal('10000'), 'R$ 1.000 a R$ 10.000'),
        (Decimal('10000'), Decimal('100000'), 'R$ 10.000 a R$ 100.000'),
        (Decimal('100000'), Decimal('1000000'), 'R$ 100.000 a R$ 1.000.000'),
        (Decimal('1000000'), Decimal('10000000'), 'R$ 1 milhao a R$ 10 milhoes'),
        (Decimal('10000000'), Decimal('999999999999'), 'Acima de R$ 10 milhoes'),
    ]
    
    print("1. DISTRIBUICAO POR FAIXA DE SALDO:")
    print("-" * 100)
    
    total_geral = Decimal('0')
    contratos_suspeitos = []
    
    for min_val, max_val, descricao in faixas:
        qtd = 0
        soma = Decimal('0')
        
        for c in todos_contratos:
            saldo = c['saldo']
            
            if min_val <= saldo < max_val:
                qtd += 1
                soma += saldo
                
                # Contratos suspeitos: saldo > R$ 100.000
                if saldo >= Decimal('100000'):
                    contratos_suspeitos.append(c)
        
        total_geral += soma
        
        if qtd > 0:
            media = soma / qtd
            print(f"{descricao:35} | Qtd: {qtd:5} | Total: R$ {soma:20,.2f} | Media: R$ {media:15,.2f}")
    
    print("-" * 100)
    print(f"{'TOTAL GERAL':35} | Qtd: {Contrato.objects.count():5} | Total: R$ {total_geral:20,.2f}")
    print()
    
    # Analisar os contratos suspeitos em detalhes
    print()
    print("2. CONTRATOS SUSPEITOS (Saldo >= R$ 100.000):")
    print("-" * 100)
    print(f"Total de contratos suspeitos: {len(contratos_suspeitos)}")
    print()
    
    if contratos_suspeitos:
        # Ordenar por saldo (maior primeiro)
        contratos_suspeitos.sort(key=lambda x: x['saldo'], reverse=True)
        
        print("Top 20 contratos com maiores saldos:")
        print()
        print(f"{'Contrato':15} {'Conjunto':10} {'Data Parc.':12} {'Saldo Atual':20} {'Moeda':25} {'Saldo em Real':20}")
        print("-" * 100)
        
        for i, info in enumerate(contratos_suspeitos[:20], 1):
            moeda, fator = identificar_moeda(info['data'], info['saldo'])
            saldo_real = converter_para_real(info['saldo'], fator)
            
            print(f"{info['contrato']:15} {info['conjunto']:10} "
                  f"{info['data'].strftime('%d/%m/%Y'):12} "
                  f"R$ {info['saldo']:17,.2f} {moeda:25} R$ {saldo_real:17,.2f}")
    
    # Análise por período da última parcela
    print()
    print()
    print("3. ANALISE POR PERIODO DA ULTIMA PARCELA:")
    print("-" * 100)
    
    periodos = [
        (date(1980, 1, 1), date(1990, 1, 1), 'Anos 80 (1980-1989)'),
        (date(1990, 1, 1), date(1995, 1, 1), 'Anos 90-94 (moedas antigas)'),
        (date(1995, 1, 1), date(2000, 1, 1), 'Anos 95-99 (Real)'),
        (date(2000, 1, 1), date(2010, 1, 1), 'Anos 2000-2009'),
        (date(2010, 1, 1), date(2020, 1, 1), 'Anos 2010-2019'),
        (date(2020, 1, 1), date(2030, 1, 1), 'Anos 2020+'),
    ]
    
    for data_inicio, data_fim, descricao in periodos:
        qtd = 0
        soma = Decimal('0')
        soma_convertida = Decimal('0')
        
        for c in todos_contratos:
            if data_inicio <= c['data'] < data_fim:
                qtd += 1
                soma += c['saldo']
                
                # Converter para Real
                moeda, fator = identificar_moeda(c['data'], c['saldo'])
                saldo_real = converter_para_real(c['saldo'], fator)
                soma_convertida += saldo_real
        
        if qtd > 0:
            media = soma / qtd
            media_conv = soma_convertida / qtd
            print(f"{descricao:30} | Qtd: {qtd:5} | Total: R$ {soma:20,.2f} | "
                  f"Convertido: R$ {soma_convertida:17,.2f} | Media: R$ {media_conv:12,.2f}")
    
    print()
    print("=" * 100)
    print()
    
    # Calcular total se todos fossem convertidos
    print("4. SIMULACAO DE CONVERSAO COMPLETA:")
    print("-" * 100)
    
    total_atual = Decimal('0')
    total_convertido = Decimal('0')
    qtd_convertidos = 0
    qtd_ja_real = 0
    
    for c in todos_contratos:
        total_atual += c['saldo']
        
        moeda, fator = identificar_moeda(c['data'], c['saldo'])
        saldo_real = converter_para_real(c['saldo'], fator)
        total_convertido += saldo_real
        
        if fator > 1:
            qtd_convertidos += 1
        else:
            qtd_ja_real += 1
    
    print(f"Contratos que precisam conversao: {qtd_convertidos:,}")
    print(f"Contratos ja em Real: {qtd_ja_real:,}")
    print()
    print(f"Total ATUAL (sem conversao): R$ {total_atual:,.2f}")
    print(f"Total CONVERTIDO para Real: R$ {total_convertido:,.2f}")
    print()
    print(f"Diferenca: R$ {total_atual - total_convertido:,.2f}")
    print()
    
    # Calcular com correção monetária após conversão
    fator_ipca = Decimal('1.4146')  # maio/2019 a nov/2025
    total_com_correcao = total_convertido * fator_ipca
    
    print(f"Total convertido + correcao IPCA (mai/2019 a nov/2025): R$ {total_com_correcao:,.2f}")
    print()
    print("=" * 100)

if __name__ == '__main__':
    main()
