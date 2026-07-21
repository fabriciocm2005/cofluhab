import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

# Analisar o contrato 006020 que está com saldo negativo
contrato = Contrato.objects.filter(codigo='006020').first()

if contrato:
    print(f"Contrato: {contrato.codigo} - Conjunto: {contrato.conjunto}")
    print(f"Conversor: {contrato.conversor}")
    print()
    
    parcelas = ParcelaContrato.objects.filter(contrato=contrato).order_by('nmens')
    total = parcelas.count()
    print(f"Total de parcelas: {total}\n")
    
    print("Primeiras 10 parcelas:")
    print("-" * 150)
    print(f"{'Nº':<5} {'Venc':<12} {'Pgto':<12} {'Juros':<12} {'Amort':<12} {'Seguro':<12} {'FCVS':<12} {'EM':<12} {'Vlr Parc':<12} {'Saldo Dev':<15}")
    print("-" * 150)
    
    for p in parcelas[:10]:
        print(f"{p.nmens:<5} {str(p.dtvenc):<12} {str(p.dtpgto):<12} {float(p.juros or 0):<12.2f} {float(p.amort or 0):<12.2f} "
              f"{float(p.seguro or 0):<12.2f} {float(p.fcvs or 0):<12.2f} {float(p.em or 0):<12.2f} "
              f"{float(p.vlautent or 0):<12.2f} {float(p.sddev or 0):<15.2f}")
    
    print("\nÚltimas 10 parcelas:")
    print("-" * 150)
    print(f"{'Nº':<5} {'Venc':<12} {'Pgto':<12} {'Juros':<12} {'Amort':<12} {'Seguro':<12} {'FCVS':<12} {'EM':<12} {'Vlr Parc':<12} {'Saldo Dev':<15}")
    print("-" * 150)
    
    for p in parcelas[total-10:]:
        print(f"{p.nmens:<5} {str(p.dtvenc):<12} {str(p.dtpgto):<12} {float(p.juros or 0):<12.2f} {float(p.amort or 0):<12.2f} "
              f"{float(p.seguro or 0):<12.2f} {float(p.fcvs or 0):<12.2f} {float(p.em or 0):<12.2f} "
              f"{float(p.vlautent or 0):<12.2f} {float(p.sddev or 0):<15.2f}")
    
    # Verificar se há amortização negativa
    print("\n--- Análise de Amortização Negativa ---")
    
    amort_negativas = parcelas.filter(amort__lt=0).count()
    print(f"Parcelas com amortização negativa: {amort_negativas}")
    
    saldo_negativo = parcelas.filter(sddev__lt=0).count()
    print(f"Parcelas com saldo devedor negativo: {saldo_negativo}")
    
    # Verificar evolução do saldo
    print("\n--- Evolução do Saldo (primeiras 20 parcelas) ---")
    saldo_anterior = None
    for p in parcelas[:20]:
        variacao = ""
        if saldo_anterior is not None:
            diff = float(p.sddev or 0) - saldo_anterior
            variacao = f"({diff:+.2f})"
        print(f"Parcela {p.nmens}: Saldo = R$ {float(p.sddev or 0):.2f} {variacao}")
        saldo_anterior = float(p.sddev or 0)

else:
    print("Contrato 006020 não encontrado")
