"""
Testar novo cálculo de débito com conversão monetária para o contrato 6080
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
    
    # Se data é None ou já é Real (após 01/07/1994), retornar direto
    if data_vencimento is None or data_vencimento >= date(1994, 7, 1):
        return valor_convertido
    
    # Aplicar conversões monetárias em cascata baseado na data
    # Até 27/02/1986: Cruzeiro antigo
    if data_vencimento < date(1986, 2, 28):
        valor_convertido = valor_convertido / Decimal('1000')  # Cr$ → Cz$
        valor_convertido = valor_convertido / Decimal('1000')  # Cz$ → NCz$
        valor_convertido = valor_convertido / Decimal('1000')  # NCz$ → CR$
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
        
    # 28/02/1986 - 15/01/1989: Cruzado
    elif data_vencimento < date(1989, 1, 16):
        valor_convertido = valor_convertido / Decimal('1000')  # Cz$ → NCz$
        valor_convertido = valor_convertido / Decimal('1000')  # NCz$ → CR$
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
        
    # 16/01/1989 - 15/03/1990: Cruzado Novo
    elif data_vencimento < date(1990, 3, 16):
        valor_convertido = valor_convertido / Decimal('1000')  # NCz$ → CR$
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
        
    # 16/03/1990 - 31/07/1993: Cruzeiro
    elif data_vencimento < date(1993, 8, 1):
        valor_convertido = valor_convertido / Decimal('1000')  # Cr$ → CR$
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
        
    # 01/08/1993 - 30/06/1994: Cruzeiro Real
    elif data_vencimento < date(1994, 7, 1):
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
    
    return valor_convertido

print("=" * 80)
print("TESTE: NOVO CÁLCULO DE DÉBITO COM CONVERSÃO MONETÁRIA")
print("=" * 80)

try:
    c = Contrato.objects.get(codigo='6080')
    print(f"\n✓ Contrato: {c.codigo} - Conjunto {c.conjunto}")
    
    parcelas_aberto = ParcelaContrato.objects.filter(contrato=c, dtpgto__isnull=True).order_by('nmens')
    print(f"✓ Parcelas em aberto: {parcelas_aberto.count()}")
    
    ate_data = date.today()
    taxa_mora = Decimal('0.000333')  # 0,0333% ao dia (1% ao mês)
    
    total_encargo = Decimal('0')
    total_mora = Decimal('0')
    total_geral = Decimal('0')
    
    print("\n" + "=" * 80)
    print("PRIMEIRAS 10 PARCELAS (COM CONVERSÃO):")
    print("=" * 80)
    
    for i, p in enumerate(parcelas_aberto[:10], 1):
        # Valor do encargo
        if p.vlautent and p.vlautent > 0:
            encargo_original = p.vlautent
        else:
            encargo_original = Decimal('0')
            if p.juros: encargo_original += p.juros
            if p.amort: encargo_original += p.amort
            if p.seguro: encargo_original += p.seguro
            if p.tca: encargo_original += p.tca
            if p.fcvs: encargo_original += p.fcvs
            if p.em: encargo_original += p.em
            if p.rp: encargo_original += p.rp
        
        # Aplicar conversão
        encargo_convertido = converter_valor_para_real(encargo_original, p.dtvenc)
        
        # Mora
        if p.dtvenc:
            dias_atraso = (ate_data - p.dtvenc).days
            if dias_atraso < 0:
                dias_atraso = 0
        else:
            dias_atraso = 0
        
        mora_total = encargo_convertido * taxa_mora * dias_atraso
        total_parcela = encargo_convertido + mora_total
        
        print(f"\nParcela {p.nmens} (Venc: {p.dtvenc})")
        print(f"  Original: R$ {encargo_original:,.2f}")
        print(f"  Convertido: R$ {encargo_convertido:,.8f}")
        print(f"  Dias atraso: {dias_atraso}")
        print(f"  Mora: R$ {mora_total:,.8f}")
        print(f"  Total: R$ {total_parcela:,.8f}")
    
    print("\n" + "=" * 80)
    print("CALCULANDO TOTAL (TODAS AS PARCELAS):")
    print("=" * 80)
    
    for p in parcelas_aberto:
        # Valor do encargo
        if p.vlautent and p.vlautent > 0:
            encargo_original = p.vlautent
        else:
            encargo_original = Decimal('0')
            if p.juros: encargo_original += p.juros
            if p.amort: encargo_original += p.amort
            if p.seguro: encargo_original += p.seguro
            if p.tca: encargo_original += p.tca
            if p.fcvs: encargo_original += p.fcvs
            if p.em: encargo_original += p.em
            if p.rp: encargo_original += p.rp
        
        # Aplicar conversão
        encargo_convertido = converter_valor_para_real(encargo_original, p.dtvenc)
        
        # Mora
        if p.dtvenc:
            dias_atraso = (ate_data - p.dtvenc).days
            if dias_atraso < 0:
                dias_atraso = 0
        else:
            dias_atraso = 0
        
        mora_total = encargo_convertido * taxa_mora * dias_atraso
        
        total_encargo += encargo_convertido
        total_mora += mora_total
        total_geral += encargo_convertido + mora_total
    
    print(f"\n💰 TOTAL ENCARGO (convertido): R$ {total_encargo:,.2f}")
    print(f"💰 TOTAL MORA: R$ {total_mora:,.2f}")
    print(f"💰 TOTAL GERAL: R$ {total_geral:,.2f}")
    
    print("\n" + "=" * 80)
    print("ANÁLISE:")
    print("=" * 80)
    
    if total_geral < 500000:
        print(f"✅ SUCESSO! Valor dentro do esperado (< R$ 500.000,00)")
        print(f"   Total: R$ {total_geral:,.2f}")
    else:
        print(f"⚠️  Valor ainda alto: R$ {total_geral:,.2f}")
        print(f"   Esperado: < R$ 500.000,00")
    
    print("\n" + "=" * 80)
    print("COMPARAÇÃO:")
    print("=" * 80)
    print(f"ANTES (sem conversão): R$ 61.006.652,38")
    print(f"DEPOIS (com conversão): R$ {total_geral:,.2f}")
    redução = ((61006652.38 - float(total_geral)) / 61006652.38) * 100
    print(f"REDUÇÃO: {redução:.2f}%")
    print("=" * 80)
    
except Contrato.DoesNotExist:
    print("\n❌ Contrato 6080 não encontrado!")
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
