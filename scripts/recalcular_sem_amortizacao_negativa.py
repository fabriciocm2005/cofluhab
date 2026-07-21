import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
from django.db import transaction

def recalcular_sem_amortizacao_negativa():
    """
    Recalcula todos os contratos para que o saldo devedor nunca fique negativo.
    Quando o saldo chegar a zero, ele permanece em zero nas parcelas seguintes.
    """
    contratos = Contrato.objects.all()
    total = contratos.count()
    processados = 0
    ajustados = 0
    
    print(f"Iniciando recálculo de {total} contratos SEM amortização negativa...\n")
    
    for contrato in contratos:
        parcelas = ParcelaContrato.objects.filter(contrato=contrato).order_by('nmens')
        
        if not parcelas.exists():
            continue
        
        # Pegar o saldo inicial da primeira parcela
        primeira = parcelas.first()
        saldo_anterior = primeira.sddev if primeira.sddev else Decimal('0.00')
        
        # Verificar se há saldos negativos
        tem_negativo = any(p.sddev and p.sddev < 0 for p in parcelas)
        
        if tem_negativo:
            ajustados += 1
            
            with transaction.atomic():
                # Recalcular parcela por parcela
                for parcela in parcelas:
                    # Se o saldo anterior já é zero ou negativo, zerar tudo
                    if saldo_anterior <= 0:
                        parcela.sddev = Decimal('0.00')
                        parcela.amort = Decimal('0.00')
                        parcela.juros = Decimal('0.00')
                        parcela.save(update_fields=['sddev', 'amort', 'juros'])
                    else:
                        # Calcular nova amortização baseada no saldo anterior
                        amort_original = parcela.amort if parcela.amort else Decimal('0.00')
                        
                        # Se a amortização for maior que o saldo, limitar
                        if amort_original > saldo_anterior:
                            amort_ajustada = saldo_anterior
                            parcela.amort = amort_ajustada
                        else:
                            amort_ajustada = amort_original
                        
                        # Novo saldo = saldo anterior - amortização
                        novo_saldo = saldo_anterior - amort_ajustada
                        
                        # Garantir que não seja negativo
                        if novo_saldo < 0:
                            novo_saldo = Decimal('0.00')
                        
                        parcela.sddev = novo_saldo
                        parcela.save(update_fields=['sddev', 'amort'])
                        
                        saldo_anterior = novo_saldo
        
        processados += 1
        if processados % 100 == 0:
            print(f"Processados: {processados}/{total} - Ajustados: {ajustados}")
    
    print(f"\n✓ Concluído!")
    print(f"Total processados: {processados}")
    print(f"Contratos ajustados (tinham saldo negativo): {ajustados}")
    
    # Verificar resultado
    print("\n--- Verificação ---")
    negativos_restantes = ParcelaContrato.objects.filter(sddev__lt=0).count()
    print(f"Parcelas com saldo negativo restantes: {negativos_restantes}")
    
    if negativos_restantes == 0:
        print("✓ Sucesso! Nenhum saldo negativo encontrado.")
    else:
        print("⚠ Ainda existem alguns saldos negativos. Pode ser necessário ajuste manual.")

if __name__ == '__main__':
    recalcular_sem_amortizacao_negativa()
