import os
import sys
import django
from decimal import Decimal

# Ajustar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
from django.db import transaction

def recalcular_contrato_sem_amort_negativa(contrato):
    """
    Recalcula um contrato SEM permitir amortização negativa.
    
    Regra: Se Vlr_Parcela < Juros, então:
    - Juros recebidos = Vlr_Parcela
    - Amortização = 0
    - Saldo mantém (não cresce)
    
    Se Vlr_Parcela >= Juros:
    - Amortização = Vlr_Parcela - Juros - Seguro - outros
    - Saldo diminui normalmente
    """
    parcelas = ParcelaContrato.objects.filter(contrato=contrato).order_by('nmens')
    
    if not parcelas.exists():
        return 0
    
    alteracoes = 0
    primeira = parcelas.first()
    saldo_atual = primeira.sddev if primeira.sddev else Decimal('0.00')
    
    with transaction.atomic():
        for parcela in parcelas:
            # Valores originais
            vlr_parcela = parcela.vlautent if parcela.vlautent else Decimal('0.00')
            juros_calc = parcela.juros if parcela.juros else Decimal('0.00')
            seguro = parcela.seguro if parcela.seguro else Decimal('0.00')
            tca = parcela.tca if parcela.tca else Decimal('0.00')
            fcvs = parcela.fcvs if parcela.fcvs else Decimal('0.00')
            em = parcela.em if parcela.em else Decimal('0.00')
            
            # Calcular amortização SEM permitir negativa
            if parcela.nmens == 1:
                # Primeira parcela: usar saldo original
                saldo_atual = parcela.sddev if parcela.sddev else Decimal('0.00')
                nova_amort = parcela.amort if parcela.amort else Decimal('0.00')
            else:
                # Valor disponível para amortização
                vlr_disponivel = vlr_parcela - seguro - tca - fcvs
                
                if vlr_disponivel <= juros_calc:
                    # Pagamento insuficiente: não há amortização
                    nova_amort = Decimal('0.00')
                    # Saldo mantém
                    novo_saldo = saldo_atual
                else:
                    # Pagamento suficiente: calcula amortização normal
                    nova_amort = vlr_disponivel - juros_calc
                    
                    # Garantir que amortização não seja maior que o saldo
                    if nova_amort > saldo_atual:
                        nova_amort = saldo_atual
                    
                    # Novo saldo
                    novo_saldo = saldo_atual - nova_amort
                
                # Atualizar se houve mudança
                if parcela.amort != nova_amort or parcela.sddev != novo_saldo:
                    parcela.amort = nova_amort
                    parcela.sddev = novo_saldo
                    parcela.save(update_fields=['amort', 'sddev'])
                    alteracoes += 1
                
                saldo_atual = novo_saldo
    
    return alteracoes

def processar_todos_contratos():
    """Processa todos os contratos do sistema"""
    contratos = Contrato.objects.all().order_by('codigo')
    total = contratos.count()
    processados = 0
    total_alteracoes = 0
    
    print(f"Recalculando {total} contratos SEM amortização negativa...\n")
    print("Isso pode demorar alguns minutos...\n")
    
    for contrato in contratos:
        alteracoes = recalcular_contrato_sem_amort_negativa(contrato)
        total_alteracoes += alteracoes
        processados += 1
        
        if processados % 100 == 0:
            print(f"Processados: {processados}/{total} - Alterações: {total_alteracoes}")
    
    print(f"\n✓ Concluído!")
    print(f"Contratos processados: {processados}")
    print(f"Total de parcelas alteradas: {total_alteracoes}")
    
    # Verificação final
    print("\n--- Verificação Final ---")
    amort_negativas = ParcelaContrato.objects.filter(amort__lt=0).count()
    saldos_negativos = ParcelaContrato.objects.filter(sddev__lt=0).count()
    
    print(f"Parcelas com amortização negativa: {amort_negativas}")
    print(f"Parcelas com saldo devedor negativo: {saldos_negativos}")
    
    if amort_negativas == 0 and saldos_negativos == 0:
        print("\n✓ SUCESSO! Todos os saldos estão positivos e sem amortização negativa.")
    else:
        print("\n⚠ Ainda existem alguns casos. Verifique manualmente.")

if __name__ == '__main__':
    processar_todos_contratos()
