#!/usr/bin/env python
"""
DIAGNÓSTICO FCVS - Contrato 6001 (Aldemir Pereira da Silva)
Script para análise detalhada de contratos SFH com cálculo de resíduo FCVS
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Adicionar o diretório pai ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

# Tabela de conversão de moedas (mesma do views.py)
NOMINAL_CONVERSION_FACTORS = [
    (date(1994, 7, 1), 'CRUZEIRO_REAL', Decimal('2750'), 'REAL'),
    (date(1993, 8, 1), 'CRUZEIRO', Decimal('1000'), 'CRUZEIRO_REAL'),
    (date(1990, 3, 16), 'CRUZADO_NOVO', Decimal('1'), 'CRUZEIRO'),
    (date(1989, 1, 16), 'CRUZADO', Decimal('1000'), 'CRUZADO_NOVO'),
    (date(1986, 2, 28), 'CRUZEIRO', Decimal('1000'), 'CRUZADO'),
]

def get_moeda_vigente(data_referencia):
    """Retorna o símbolo da moeda vigente na data"""
    moedas = [
        (date(1994, 7, 1), 'R$'),
        (date(1993, 8, 1), 'CR$ (Real)'),
        (date(1990, 3, 16), 'CR$'),
        (date(1989, 1, 16), 'NCz$'),
        (date(1986, 2, 28), 'Cz$'),
        (date(1900, 1, 1), 'Cr$'),
    ]
    for data_limite, simbolo in moedas:
        if data_referencia >= data_limite:
            return simbolo
    return 'Cr$'

def analisar_contrato(codigo_contrato):
    """Analisa um contrato específico e calcula o FCVS residual"""
    
    print(f"\n{'='*80}")
    print(f"DIAGNÓSTICO FCVS - CONTRATO {codigo_contrato}")
    print(f"{'='*80}")
    
    try:
        contrato = Contrato.objects.get(codigo=codigo_contrato)
    except Contrato.DoesNotExist:
        print(f"❌ Contrato {codigo_contrato} não encontrado!")
        return
    
    # Buscar todas as parcelas
    parcelas = ParcelaContrato.objects.filter(contrato=contrato).order_by('nmens')
    
    if not parcelas.exists():
        print(f"❌ Nenhuma parcela encontrada para o contrato {codigo_contrato}")
        return
    
    primeira = parcelas.first()
    ultima = parcelas.last()
    
    print(f"\n📋 DADOS DO CONTRATO:")
    print(f"   Código: {contrato.codigo}")
    print(f"   Conjunto: {contrato.conjunto}")
    print(f"   Data Contrato: {contrato.data_contrato}")
    print(f"   Prazo: {contrato.prazo} meses")
    print(f"   Saldo Inicial: {primeira.sddev:,.2f} {get_moeda_vigente(primeira.dtvenc)}")
    print(f"   Saldo Final: {ultima.sddev:,.2f} {get_moeda_vigente(ultima.dtvenc)}")
    print(f"   Período: {primeira.dtvenc.strftime('%m/%Y')} a {ultima.dtvenc.strftime('%m/%Y')}")
    
    # Análise de FCVS
    print(f"\n🔍 ANÁLISE DE FCVS RESIDUAL:")
    
    fcvs_acum = Decimal('0')
    anomalias = []
    current_moeda = get_moeda_vigente(primeira.dtvenc)
    
    for i, parcela in enumerate(parcelas):
        if i == 0:
            continue  # Pula a primeira (não tem anterior)
        
        parcela_ant = parcelas[i-1]
        moeda_atual = get_moeda_vigente(parcela.dtvenc)
        
        # Verifica mudança de moeda
        if current_moeda != moeda_atual:
            for data_limite, moeda_anterior, fator, moeda_nova in NOMINAL_CONVERSION_FACTORS:
                if parcela.dtvenc >= data_limite and current_moeda != moeda_nova:
                    fcvs_acum /= fator
                    print(f"   ⚠️  Mês {parcela.nmens}: Mudança de moeda {current_moeda} → {moeda_atual}")
                    print(f"      FCVS acumulado dividido por {fator}")
                    break
            current_moeda = moeda_atual
        
        # Calcula crescimento do saldo (FCVS residual)
        if parcela.sddev and parcela_ant.sddev:
            if parcela.sddev > parcela_ant.sddev:
                crescimento = parcela.sddev - parcela_ant.sddev
                fcvs_acum += crescimento
                
                anomalias.append({
                    'mes': parcela.nmens,
                    'data': parcela.dtvenc,
                    'saldo_ant': parcela_ant.sddev,
                    'saldo_atual': parcela.sddev,
                    'crescimento': crescimento,
                    'moeda': moeda_atual,
                    'correcao': parcela.cm or 0
                })
    
    # Resultados
    print(f"\n📊 RESULTADOS:")
    print(f"   Total de Parcelas: {parcelas.count()}")
    print(f"   Anomalias (Amortização Negativa): {len(anomalias)}")
    print(f"   FCVS Residual Acumulado: {fcvs_acum:,.2f} {current_moeda}")
    
    if anomalias:
        print(f"\n⚠️  MESES COM AMORTIZAÇÃO NEGATIVA (TOP 10):")
        for i, anomalia in enumerate(anomalias[:10]):
            print(f"   {i+1:2d}. Mês {anomalia['mes']:3d} ({anomalia['data'].strftime('%m/%Y')}): "
                  f"Saldo cresceu {anomalia['crescimento']:,.2f} {anomalia['moeda']}")
    
    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES:")
    if fcvs_acum > Decimal('1000'):
        print(f"   ✅ HÁ EVIDÊNCIAS DE FCVS RESIDUAL: {fcvs_acum:,.2f} {current_moeda}")
        print(f"   → Recomendado: Solicitar auditoria à Caixa Econômica Federal")
        print(f"   → Documento: Formulário FH1 para habilitação ao FCVS")
    else:
        print(f"   ⚠️  FCVS RESIDUAL INSIGNIFICANTE: {fcvs_acum:,.2f} {current_moeda}")
        print(f"   → Provavelmente já foi compensado nas correções posteriores")
    
    # Exportar para CSV (opcional)
    print(f"\n💾 EXPORTAR DADOS:")
    print(f"   Para exportar análise completa, execute:")
    print(f"   python diagnostico_6001.py --export {codigo_contrato}")
    
    return fcvs_acum, len(anomalias)

def main():
    """Função principal"""
    if len(sys.argv) > 1:
        codigo = sys.argv[1]
    else:
        codigo = input("Digite o código do contrato (ex: 6001): ").strip()
    
    analisar_contrato(codigo)

if __name__ == "__main__":
    main()