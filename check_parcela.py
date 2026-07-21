import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import ParcelaContrato, Contrato

print("="*80)
print("VERIFICANDO CONTRATO 004062 - PARCELA 84")
print("="*80)

parcela = ParcelaContrato.objects.filter(contrato__codigo='004062', nmens=84).first()

if parcela:
    print(f"\nParcela encontrada:")
    print(f"  Contrato: {parcela.contrato.codigo}")
    print(f"  Número: {parcela.nmens}")
    print(f"  Vencimento: {parcela.dtvenc}")
    print(f"  Pagamento: {parcela.dtpgto}")
    print(f"\nVALORES:")
    print(f"  vlautent: {parcela.vlautent}")
    print(f"  sddev: {parcela.sddev}")
    print(f"  sddev_original: {parcela.sddev_original}")
    print(f"\nCOMPONENTES:")
    print(f"  juros: {parcela.juros}")
    print(f"  amort: {parcela.amort}")
    print(f"  seguro: {parcela.seguro}")
    print(f"  tca: {parcela.tca}")
    print(f"  fcvs: {parcela.fcvs}")
    print(f"  em: {parcela.em}")
    print(f"  rp: {parcela.rp}")
    print(f"  cm: {parcela.cm}")
    
    # Calcular soma
    soma = (parcela.juros or 0) + (parcela.amort or 0) + (parcela.seguro or 0) + \
           (parcela.tca or 0) + (parcela.fcvs or 0) + (parcela.em or 0) + (parcela.rp or 0)
    
    print(f"\nSoma dos componentes: {soma}")
    print(f"Valor que deveria ser (usuário mencionou): R$ 85,71")
    
    print("\n" + "="*80)
    print("PRIMEIRAS 5 PARCELAS EM ABERTO:")
    print("="*80)
    
    parcelas_abertas = ParcelaContrato.objects.filter(
        contrato__codigo='004062', 
        dtpgto__isnull=True
    ).order_by('nmens')[:5]
    
    for p in parcelas_abertas:
        soma_comp = (p.juros or 0) + (p.amort or 0) + (p.seguro or 0) + \
                    (p.tca or 0) + (p.fcvs or 0) + (p.em or 0) + (p.rp or 0)
        print(f"\nParcela {p.nmens} - Venc: {p.dtvenc}")
        print(f"  vlautent: {p.vlautent}")
        print(f"  sddev: {p.sddev}")
        print(f"  Soma comp: {soma_comp}")
else:
    print("Parcela não encontrada!")
