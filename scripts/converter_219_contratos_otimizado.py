"""
Versão otimizada - Converte os 219 contratos com moedas antigas para Real
Preserva valor original em novo campo 'sddev_original'
Aplica correção monetária maio/2019 a novembro/2025
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

from django.db import connection, transaction
from principal.models import Contrato, ParcelaContrato

def identificar_moeda(data_parcela):
    """Identifica a moeda e fator de conversão baseado na data"""
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

def adicionar_campo_sddev_original():
    """Adiciona campo sddev_original se não existir"""
    print("\n[1] Verificando estrutura da tabela...")
    
    with connection.cursor() as cursor:
        # Verificar se campo já existe
        cursor.execute("PRAGMA table_info(principal_parcelacontrato)")
        colunas = [row[1] for row in cursor.fetchall()]
        
        if 'sddev_original' in colunas:
            print("    [OK] Campo 'sddev_original' ja existe")
            return True
        
        print("    Adicionando campo 'sddev_original'...")
        cursor.execute("""
            ALTER TABLE principal_parcelacontrato 
            ADD COLUMN sddev_original DECIMAL(24, 2)
        """)
        print("    [OK] Campo adicionado com sucesso")
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Converte 219 contratos e aplica correcao IPCA')
    parser.add_argument('--aplicar', action='store_true', 
                       help='Aplica as conversoes (padrao: simulacao)')
    
    args = parser.parse_args()
    
    modo = 'aplicar' if args.aplicar else 'simulacao'
    
    print("=" * 100)
    print("CONVERSAO DE MOEDAS ANTIGAS E ATUALIZACAO MONETARIA (OTIMIZADO)")
    print("=" * 100)
    
    if modo == 'aplicar':
        print("\n[AVISO] Voce esta prestes a MODIFICAR o banco de dados!")
        print("        Recomenda-se fazer backup antes:")
        print("        copy db.sqlite3 db.sqlite3.backup-antes-conversao")
        resposta = input("\nConfirma a operacao? (digite SIM para confirmar): ")
        
        if resposta.upper() != 'SIM':
            print("\n[CANCELADO] Operacao cancelada pelo usuario")
            return
    
    # Adicionar campo sddev_original
    adicionar_campo_sddev_original()
    
    print(f"\n[2] Modo: {modo.upper()}")
    print("=" * 100)
    
    # ETAPA 1: Coletar TODOS os dados de uma vez
    print("\n    [Carregando dados do banco...]")
    
    dados_contratos = []
    for contrato in Contrato.objects.prefetch_related('parcelas').all():
        ultima_parcela = contrato.parcelas.order_by('-nmens').first()
        
        if ultima_parcela and ultima_parcela.sddev:
            moeda, fator = identificar_moeda(ultima_parcela.dtvenc)
            
            dados_contratos.append({
                'contrato_id': contrato.id,
                'codigo': contrato.codigo,
                'conjunto': contrato.conjunto,
                'parcela_id': ultima_parcela.id,
                'data': ultima_parcela.dtvenc,
                'moeda': moeda,
                'fator': fator,
                'saldo_atual': ultima_parcela.sddev
            })
    
    print(f"    [OK] {len(dados_contratos)} contratos carregados")
    
    # ETAPA 2: Separar por tipo
    converter = [d for d in dados_contratos if d['fator'] > 1]
    ja_real = [d for d in dados_contratos if d['fator'] == 1]
    
    print(f"\n    Contratos que precisam conversao: {len(converter)}")
    print(f"    Contratos ja em Real: {len(ja_real)}")
    
    # ETAPA 3: Converter valores
    print("\n    [Convertendo valores...]")
    
    for dados in converter:
        dados['saldo_original'] = dados['saldo_atual']
        dados['saldo_convertido'] = converter_para_real(dados['saldo_atual'], dados['fator'])
    
    # Ordenar por saldo original (maior primeiro)
    converter.sort(key=lambda x: x['saldo_original'], reverse=True)
    
    # Mostrar top 10
    print("\n    Top 10 contratos a serem convertidos:")
    print(f"    {'Contrato':15} {'Data':12} {'Moeda':25} {'Saldo Original':20} {'Saldo Real':20}")
    print("    " + "-" * 95)
    
    for i, dados in enumerate(converter[:10], 1):
        print(f"    {dados['codigo']:15} {dados['data'].strftime('%d/%m/%Y'):12} "
              f"{dados['moeda']:25} R$ {dados['saldo_original']:17,.2f} R$ {dados['saldo_convertido']:17,.2f}")
    
    # Resumo conversão
    total_original = sum(d['saldo_original'] for d in converter)
    total_convertido = sum(d['saldo_convertido'] for d in converter)
    
    print(f"\n    RESUMO DA CONVERSAO:")
    print(f"    Total Original (moedas antigas): R$ {total_original:,.2f}")
    print(f"    Total Convertido (Real): R$ {total_convertido:,.2f}")
    print(f"    Reducao: R$ {total_original - total_convertido:,.2f}")
    
    # ETAPA 4: Calcular IPCA para TODOS
    print(f"\n[3] Correcao Monetaria (IPCA mai/2019 a nov/2025)")
    print("=" * 100)
    
    fator_ipca = Decimal('1.4146')  # 41,46%
    print(f"\n    Fator de correcao: {fator_ipca} (+41,46%)")
    
    # Calcular sobre valores convertidos (em simulação) ou reais (em aplicar)
    todos_para_ipca = []
    
    # Contratos convertidos - usar valor CONVERTIDO
    for dados in converter:
        saldo_maio_2019 = dados['saldo_convertido']
        saldo_nov_2025 = saldo_maio_2019 * fator_ipca
        
        todos_para_ipca.append({
            'parcela_id': dados['parcela_id'],
            'codigo': dados['codigo'],
            'tipo': 'convertido',
            'saldo_original_moeda': dados['saldo_original'],
            'saldo_maio_2019': saldo_maio_2019,
            'saldo_nov_2025': saldo_nov_2025,
            'correcao': saldo_nov_2025 - saldo_maio_2019
        })
    
    # Contratos já em Real
    for dados in ja_real:
        saldo_maio_2019 = dados['saldo_atual']
        saldo_nov_2025 = saldo_maio_2019 * fator_ipca
        
        todos_para_ipca.append({
            'parcela_id': dados['parcela_id'],
            'codigo': dados['codigo'],
            'tipo': 'ja_real',
            'saldo_maio_2019': saldo_maio_2019,
            'saldo_nov_2025': saldo_nov_2025,
            'correcao': saldo_nov_2025 - saldo_maio_2019
        })
    
    # Filtrar apenas saldos positivos para resumo
    positivos = [d for d in todos_para_ipca if d['saldo_maio_2019'] > 0]
    negativos = [d for d in todos_para_ipca if d['saldo_maio_2019'] <= 0]
    
    total_maio = sum(d['saldo_maio_2019'] for d in positivos)
    total_nov = sum(d['saldo_nov_2025'] for d in positivos)
    total_correcao = total_nov - total_maio
    
    print(f"\n    RESUMO DA CORRECAO:")
    print(f"    Contratos com saldo positivo: {len(positivos)}")
    print(f"    Contratos com saldo negativo/zero: {len(negativos)}")
    print(f"    Total: {len(todos_para_ipca)}")
    print()
    print(f"    Total Maio/2019: R$ {total_maio:,.2f}")
    print(f"    Total Nov/2025: R$ {total_nov:,.2f}")
    print(f"    Correcao aplicada: R$ {total_correcao:,.2f} (+{((total_nov/total_maio - 1) * 100) if total_maio > 0 else 0:.2f}%)")
    
    # ETAPA 5: Aplicar mudanças
    if modo == 'aplicar':
        print(f"\n[4] Aplicando conversoes e correcoes...")
        
        with transaction.atomic():
            # Aplicar conversões
            for dados in converter:
                parcela = ParcelaContrato.objects.get(id=dados['parcela_id'])
                parcela.sddev_original = dados['saldo_original']
                parcela.sddev = dados['saldo_nov_2025']  # Já aplicar com IPCA
                parcela.save()
            
            # Aplicar IPCA nos já em Real
            for dados in [d for d in todos_para_ipca if d['tipo'] == 'ja_real']:
                parcela = ParcelaContrato.objects.get(id=dados['parcela_id'])
                parcela.sddev = dados['saldo_nov_2025']
                parcela.save()
        
        print(f"    [OK] {len(converter)} contratos convertidos")
        print(f"    [OK] {len(ja_real)} contratos atualizados com IPCA")
        print(f"\n    IMPORTANTE: O campo 'sddev_original' preserva os valores antigos")
    else:
        print(f"\n[4] Simulacao concluida - nenhuma alteracao feita")
        print(f"\n    Para aplicar as conversoes, execute:")
        print(f"    py scripts\\converter_219_contratos.py --aplicar")
    
    print("\n" + "=" * 100)
    print("PROCESSO CONCLUIDO")
    print("=" * 100)

if __name__ == '__main__':
    main()
