"""
Verificar se a conversão está funcionando para TODOS os contratos com débito
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
from decimal import Decimal
from datetime import date

def converter_valor_para_real(valor, data_vencimento):
    """Converte valor da moeda histórica para Real baseado na data de vencimento"""
    if valor is None or valor == 0:
        return Decimal('0')
    
    valor_convertido = Decimal(str(valor))
    
    if data_vencimento is None or data_vencimento >= date(1994, 7, 1):
        return valor_convertido
    
    if data_vencimento < date(1986, 2, 28):
        valor_convertido = valor_convertido / Decimal('1000')
        valor_convertido = valor_convertido / Decimal('1000')
        valor_convertido = valor_convertido / Decimal('1000')
        valor_convertido = valor_convertido / Decimal('2750')
    elif data_vencimento < date(1989, 1, 16):
        valor_convertido = valor_convertido / Decimal('1000')
        valor_convertido = valor_convertido / Decimal('1000')
        valor_convertido = valor_convertido / Decimal('2750')
    elif data_vencimento < date(1990, 3, 16):
        valor_convertido = valor_convertido / Decimal('1000')
        valor_convertido = valor_convertido / Decimal('2750')
    elif data_vencimento < date(1993, 8, 1):
        valor_convertido = valor_convertido / Decimal('1000')
        valor_convertido = valor_convertido / Decimal('2750')
    elif data_vencimento < date(1994, 7, 1):
        valor_convertido = valor_convertido / Decimal('2750')
    
    return valor_convertido

print("=" * 80)
print("VERIFICAÇÃO: DÉBITOS DE TODOS OS CONTRATOS")
print("=" * 80)

# Buscar alguns contratos com débito
contratos_query = Contrato.objects.filter(parcelas__dtpgto__isnull=True).distinct()[:10]

ate_data = date.today()
taxa_mora = Decimal('0.000333')

print(f"\nAnalisando primeiros 10 contratos com débito...")
print("\n" + "=" * 80)

contratos_problematicos = []
total_geral = Decimal('0')

for contrato in contratos_query:
    parcelas_aberto = ParcelaContrato.objects.filter(
        contrato=contrato,
        dtpgto__isnull=True
    ).order_by('nmens')
    
    total_debito = Decimal('0')
    
    for p in parcelas_aberto:
        if p.vlautent and p.vlautent > 0:
            encargo = p.vlautent
        else:
            encargo = Decimal('0')
            if p.juros: encargo += p.juros
            if p.amort: encargo += p.amort
            if p.seguro: encargo += p.seguro
            if p.tca: encargo += p.tca
            if p.fcvs: encargo += p.fcvs
            if p.em: encargo += p.em
            if p.rp: encargo += p.rp
        
        # Converter
        encargo = converter_valor_para_real(encargo, p.dtvenc)
        
        # Mora
        if p.dtvenc:
            dias_atraso = (ate_data - p.dtvenc).days
            if dias_atraso < 0:
                dias_atraso = 0
        else:
            dias_atraso = 0
        
        mora_total = encargo * taxa_mora * dias_atraso
        total_debito += encargo + mora_total
    
    total_geral += total_debito
    
    print(f"\nContrato {contrato.codigo} (Conjunto {contrato.conjunto}):")
    print(f"  Parcelas em aberto: {parcelas_aberto.count()}")
    print(f"  Total débito: R$ {total_debito:,.2f}")
    
    # Marcar se parecer problemático
    if total_debito > 500000:
        contratos_problematicos.append({
            'codigo': contrato.codigo,
            'conjunto': contrato.conjunto,
            'debito': total_debito
        })
        print(f"  ⚠️  ATENÇÃO: Débito acima de R$ 500.000!")

print("\n" + "=" * 80)
print("RESUMO:")
print("=" * 80)
print(f"\nTotal geral analisado: R$ {total_geral:,.2f}")
print(f"Contratos problemáticos (> R$ 500k): {len(contratos_problematicos)}")

if contratos_problematicos:
    print("\n⚠️  CONTRATOS COM DÉBITO ACIMA DE R$ 500.000:")
    for c in contratos_problematicos:
        print(f"  - Contrato {c['codigo']} (Conjunto {c['conjunto']}): R$ {c['debito']:,.2f}")
else:
    print("\n✅ TODOS OS CONTRATOS ESTÃO COM VALORES NORMAIS!")

print("\n" + "=" * 80)
