"""
Analisar parcelas do contrato 6080 para entender de onde vem o valor de R$ 61 milhões
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
from decimal import Decimal

print("=" * 80)
print("ANÁLISE PARCELAS CONTRATO 6080")
print("=" * 80)

try:
    c = Contrato.objects.get(codigo='6080')
    print(f"\n✓ Contrato encontrado: {c.codigo} - Conjunto {c.conjunto}")
    print(f"  Conversor do contrato: {c.conversor}")
    
    # Parcelas em aberto (sem pagamento)
    parcelas_aberto = ParcelaContrato.objects.filter(contrato=c, dtpgto__isnull=True).order_by('nmens')
    print(f"\n📊 Total de parcelas em aberto: {parcelas_aberto.count()}")
    
    # Todas as parcelas
    todas_parcelas = ParcelaContrato.objects.filter(contrato=c).order_by('nmens')
    print(f"📊 Total de parcelas (todas): {todas_parcelas.count()}")
    
    print("\n" + "=" * 80)
    print("PRIMEIRAS 10 PARCELAS EM ABERTO:")
    print("=" * 80)
    
    soma_vlautent = Decimal('0')
    soma_componentes = Decimal('0')
    soma_sddev = Decimal('0')
    
    for i, p in enumerate(parcelas_aberto[:10], 1):
        print(f"\n--- Parcela {p.nmens} ---")
        print(f"  Vencimento: {p.dtvenc}")
        print(f"  vlautent: R$ {p.vlautent:,.2f}" if p.vlautent else "  vlautent: None")
        print(f"  juros: R$ {p.juros:,.2f}" if p.juros else "  juros: None")
        print(f"  amort: R$ {p.amort:,.2f}" if p.amort else "  amort: None")
        print(f"  seguro: R$ {p.seguro:,.2f}" if p.seguro else "  seguro: None")
        print(f"  tca: R$ {p.tca:,.2f}" if p.tca else "  tca: None")
        print(f"  fcvs: R$ {p.fcvs:,.2f}" if p.fcvs else "  fcvs: None")
        print(f"  em: R$ {p.em:,.2f}" if p.em else "  em: None")
        print(f"  rp: R$ {p.rp:,.2f}" if p.rp else "  rp: None")
        print(f"  cm: R$ {p.cm:,.2f}" if p.cm else "  cm: None")
        print(f"  sddev: R$ {p.sddev:,.2f}" if p.sddev else "  sddev: None")
        print(f"  Conversor: {p.conversor}")
        
        # Soma componentes
        comp = Decimal('0')
        if p.juros: comp += p.juros
        if p.amort: comp += p.amort
        if p.seguro: comp += p.seguro
        if p.tca: comp += p.tca
        if p.fcvs: comp += p.fcvs
        if p.em: comp += p.em
        if p.rp: comp += p.rp
        
        print(f"  → Soma componentes: R$ {comp:,.2f}")
        
    print("\n" + "=" * 80)
    print("TOTALIZADORES (TODAS AS PARCELAS EM ABERTO):")
    print("=" * 80)
    
    # Calcular totais
    for p in parcelas_aberto:
        if p.vlautent:
            soma_vlautent += p.vlautent
        
        if p.sddev:
            soma_sddev += p.sddev
        
        comp = Decimal('0')
        if p.juros: comp += p.juros
        if p.amort: comp += p.amort
        if p.seguro: comp += p.seguro
        if p.tca: comp += p.tca
        if p.fcvs: comp += p.fcvs
        if p.em: comp += p.em
        if p.rp: comp += p.rp
        soma_componentes += comp
    
    print(f"\n💰 Soma total vlautent: R$ {soma_vlautent:,.2f}")
    print(f"💰 Soma total componentes (j+a+s+t+f+e+r): R$ {soma_componentes:,.2f}")
    print(f"💰 Soma total sddev (saldo devedor): R$ {soma_sddev:,.2f}")
    
    print("\n" + "=" * 80)
    print("ANÁLISE:")
    print("=" * 80)
    
    if soma_sddev > 1000000:
        print(f"⚠️  SDDEV muito alto! R$ {soma_sddev:,.2f}")
        print("   Possível causa: sddev pode ser SALDO DEVEDOR ACUMULADO, não valor da parcela")
        print("   Solução: Não somar sddev, usar apenas vlautent ou componentes")
    
    if soma_componentes > 1000000:
        print(f"⚠️  Componentes muito altos! R$ {soma_componentes:,.2f}")
        print("   Possível causa: Valores em moeda antiga não convertidos")
        print("   Solução: Aplicar conversor se > 1000")
    
    if soma_vlautent < 100000:
        print(f"✓ vlautent parece correto: R$ {soma_vlautent:,.2f}")
        print("  Este deve ser o valor usado para débito")
    
    print("\n" + "=" * 80)
    print("CONCLUSÃO:")
    print("=" * 80)
    print("O débito deve ser calculado usando:")
    print("1. vlautent (se disponível e > 0)")
    print("2. OU soma dos componentes (juros + amort + seguro + etc)")
    print("3. NÃO usar sddev (é saldo devedor acumulado, não valor da parcela)")
    print("=" * 80)
    
except Contrato.DoesNotExist:
    print("\n❌ Contrato 6080 não encontrado!")
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
