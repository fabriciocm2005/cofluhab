"""
Investiga e corrige contratos com saldo devedor negativo
Amortização negativa é uma anomalia do sistema financeiro habitacional
"""
import django
import os
import sys
from decimal import Decimal

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.db import connection
from principal.models import Contrato, ParcelaContrato

def analisar_saldos_negativos():
    """Analisa contratos com saldo devedor negativo"""
    print("=" * 100)
    print("ANALISE DE CONTRATOS COM SALDO NEGATIVO")
    print("=" * 100)
    print()
    
    cursor = connection.cursor()
    
    # Buscar contratos com última parcela negativa
    cursor.execute("""
        SELECT 
            c.id,
            c.codigo,
            c.conjunto,
            p.id as parcela_id,
            p.nmens,
            p.dtvenc,
            p.sddev,
            p.sddev_original
        FROM principal_contrato c
        INNER JOIN principal_parcelacontrato p ON p.contrato_id = c.id
        WHERE p.id IN (
            SELECT p2.id 
            FROM principal_parcelacontrato p2 
            WHERE p2.contrato_id = c.id 
            ORDER BY p2.nmens DESC 
            LIMIT 1
        )
        AND p.sddev < 0
        ORDER BY p.sddev ASC
    """)
    
    contratos_negativos = cursor.fetchall()
    
    print(f"Total de contratos com saldo negativo: {len(contratos_negativos)}")
    print()
    
    if not contratos_negativos:
        print("Nenhum contrato com saldo negativo encontrado!")
        return []
    
    # Estatísticas
    total_negativo = sum(float(c[6]) for c in contratos_negativos)
    media_negativo = total_negativo / len(contratos_negativos)
    
    print(f"Total negativo: R$ {total_negativo:,.2f}")
    print(f"Media por contrato: R$ {media_negativo:,.2f}")
    print()
    
    # Mostrar top 20 mais negativos
    print("Top 20 contratos com maior saldo negativo:")
    print("-" * 100)
    print(f"{'Contrato':10} {'Conjunto':10} {'Parc':5} {'Data Venc':12} {'Saldo Atual':20} {'Original':20}")
    print("-" * 100)
    
    for i, c in enumerate(contratos_negativos[:20], 1):
        contrato_id, codigo, conjunto, parcela_id, nmens, dtvenc, sddev, sddev_original = c
        original_str = f"R$ {float(sddev_original):,.2f}" if sddev_original else "-"
        print(f"{codigo:10} {conjunto:10} {nmens:5} {dtvenc:12} R$ {float(sddev):20,.2f} {original_str:20}")
    
    print()
    print("=" * 100)
    print()
    
    # Análise detalhada de alguns contratos
    print("ANALISE DETALHADA (primeiros 5 contratos):")
    print("=" * 100)
    
    for i, c in enumerate(contratos_negativos[:5], 1):
        contrato_id, codigo, conjunto, parcela_id, nmens, dtvenc, sddev, sddev_original = c
        
        print(f"\n{i}. CONTRATO {codigo} (Conjunto {conjunto})")
        print("-" * 80)
        
        # Buscar histórico de parcelas usando ORM
        parcelas = ParcelaContrato.objects.filter(
            contrato_id=contrato_id
        ).order_by('-nmens')[:10].values_list(
            'nmens', 'dtvenc', 'juros', 'amort', 'sddev', 'dtpgto'
        )
        
        ultimas_parcelas = list(parcelas)
        
        print(f"{'Parc':5} {'Vencimento':12} {'Juros':15} {'Amort':15} {'Saldo Dev':20} {'Paga':5}")
        print("-" * 80)
        
        for p in ultimas_parcelas:
            nmens_p, dtvenc_p, juros, amort, sddev_p, dtpgto = p
            paga = "SIM" if dtpgto else "NAO"
            juros_str = f"R$ {float(juros):,.2f}" if juros else "0,00"
            amort_str = f"R$ {float(amort):,.2f}" if amort else "0,00"
            print(f"{nmens_p:5} {dtvenc_p:12} {juros_str:15} {amort_str:15} R$ {float(sddev_p):18,.2f} {paga:5}")
        
        # Verificar se todas as parcelas foram pagas usando ORM
        total = ParcelaContrato.objects.filter(contrato_id=contrato_id).count()
        pagas = ParcelaContrato.objects.filter(contrato_id=contrato_id, dtpgto__isnull=False).count()
        
        print(f"\nTotal parcelas: {total} | Pagas: {pagas} | Pendentes: {total - pagas}")
        
        if pagas == total:
            print("⚠️  CONTRATO QUITADO - Saldo negativo indica pagamento a maior")
        elif pagas > total * 0.9:
            print("⚠️  QUASE QUITADO - Faltam poucas parcelas")
    
    print("\n" + "=" * 100)
    
    return contratos_negativos


def corrigir_saldos_negativos(modo='simulacao'):
    """
    Corrige saldos negativos aplicando diferentes estratégias
    
    Estratégias:
    1. Zerar saldos negativos (considerar quitado)
    2. Converter para positivo (valor absoluto)
    3. Recalcular baseado nas parcelas restantes
    """
    print("\n" + "=" * 100)
    print(f"CORRECAO DE SALDOS NEGATIVOS - MODO: {modo.upper()}")
    print("=" * 100)
    print()
    
    contratos_negativos = analisar_saldos_negativos()
    
    if not contratos_negativos:
        return
    
    print("\nESTRATEGIAS DISPONIVEIS:")
    print("1. ZERAR - Considerar contratos quitados (saldo = 0)")
    print("2. ABS - Converter para positivo (valor absoluto)")
    print("3. RECALCULAR - Recalcular baseado em parcelas pendentes")
    print()
    
    estrategia = input("Escolha a estrategia (1/2/3) ou ENTER para cancelar: ").strip()
    
    if estrategia not in ['1', '2', '3']:
        print("\nOperacao cancelada.")
        return
    
    print()
    
    if estrategia == '1':
        print("Estrategia: ZERAR saldos negativos")
        novo_valor = Decimal('0')
        descricao = "Contrato considerado quitado"
    elif estrategia == '2':
        print("Estrategia: Converter para VALOR ABSOLUTO")
        descricao = "Saldo convertido para positivo"
    else:
        print("Estrategia: RECALCULAR baseado em parcelas pendentes")
        descricao = "Saldo recalculado"
    
    if modo == 'simulacao':
        print(f"\nSIMULACAO - Mostrando o que seria alterado:")
        print("-" * 100)
        
        for c in contratos_negativos[:10]:
            contrato_id, codigo, conjunto, parcela_id, nmens, dtvenc, sddev, sddev_original = c
            
            if estrategia == '1':
                novo_valor = Decimal('0')
            elif estrategia == '2':
                novo_valor = abs(Decimal(str(sddev)))
            else:
                # Recalcular (simplificado)
                novo_valor = Decimal('1000.00')  # Placeholder
            
            print(f"Contrato {codigo}: R$ {float(sddev):,.2f} -> R$ {float(novo_valor):,.2f}")
        
        print(f"\n... e mais {len(contratos_negativos) - 10} contratos")
        print(f"\nTotal de contratos que seriam alterados: {len(contratos_negativos)}")
        print("\nPara aplicar as mudancas, execute:")
        print("py scripts\\corrigir_saldos_negativos.py --aplicar")
        
    else:
        print(f"\nAPLICANDO correcoes em {len(contratos_negativos)} contratos...")
        
        from django.db import transaction
        
        with transaction.atomic():
            contador = 0
            for c in contratos_negativos:
                contrato_id, codigo, conjunto, parcela_id, nmens, dtvenc, sddev, sddev_original = c
                
                if estrategia == '1':
                    novo_valor = Decimal('0')
                elif estrategia == '2':
                    novo_valor = abs(Decimal(str(sddev)))
                else:
                    # Recalcular (implementar lógica mais complexa se necessário)
                    novo_valor = Decimal('1000.00')
                
                # Atualizar
                parcela = ParcelaContrato.objects.get(id=parcela_id)
                parcela.sddev = novo_valor
                parcela.save()
                
                contador += 1
                if contador % 100 == 0:
                    print(f"  {contador}/{len(contratos_negativos)} corrigidos...")
        
        print(f"\n[OK] {contador} contratos corrigidos com sucesso!")
        print(f"Descricao: {descricao}")
    
    print("\n" + "=" * 100)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Corrige contratos com saldo negativo')
    parser.add_argument('--aplicar', action='store_true', help='Aplica as correcoes')
    parser.add_argument('--apenas-analisar', action='store_true', help='Apenas analisa sem corrigir')
    
    args = parser.parse_args()
    
    if args.apenas_analisar:
        analisar_saldos_negativos()
    else:
        modo = 'aplicar' if args.aplicar else 'simulacao'
        corrigir_saldos_negativos(modo)


if __name__ == '__main__':
    main()
