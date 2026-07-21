"""
Converte os 219 contratos com moedas antigas para Real
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

from django.db import connection
from principal.models import Contrato, ParcelaContrato

def identificar_moeda(data_parcela):
    """
    Identifica a moeda e fator de conversão baseado na data
    """
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

def converter_contratos(modo='simulacao'):
    """
    Converte contratos com moedas antigas
    
    Args:
        modo: 'simulacao' ou 'aplicar'
        
    Returns:
        lista de códigos de contratos convertidos
    """
    print(f"\n[2] Modo: {modo.upper()}")
    print("=" * 100)
    
    # Coletar contratos que precisam conversão
    contratos_converter = []
    
    print("\n    Analisando contratos...")
    for contrato in Contrato.objects.all():
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if ultima_parcela and ultima_parcela.sddev:
            moeda, fator = identificar_moeda(ultima_parcela.dtvenc)
            
            # Precisa conversão se fator > 1
            if fator > 1:
                saldo_original = ultima_parcela.sddev
                saldo_convertido = converter_para_real(saldo_original, fator)
                
                contratos_converter.append({
                    'contrato': contrato,
                    'codigo': contrato.codigo,
                    'conjunto': contrato.conjunto,
                    'parcela': ultima_parcela,
                    'data': ultima_parcela.dtvenc,
                    'moeda': moeda,
                    'fator': fator,
                    'saldo_original': saldo_original,
                    'saldo_convertido': saldo_convertido
                })
    
    print(f"    [OK] {len(contratos_converter)} contratos precisam conversao\n")
    
    # Ordenar por saldo original (maior primeiro)
    contratos_converter.sort(key=lambda x: x['saldo_original'], reverse=True)
    
    # Mostrar top 10
    print("    Top 10 contratos a serem convertidos:")
    print(f"    {'Contrato':15} {'Data':12} {'Moeda':25} {'Saldo Original':20} {'Saldo Real':20}")
    print("    " + "-" * 95)
    
    for i, info in enumerate(contratos_converter[:10], 1):
        print(f"    {info['codigo']:15} {info['data'].strftime('%d/%m/%Y'):12} "
              f"{info['moeda']:25} R$ {info['saldo_original']:17,.2f} R$ {info['saldo_convertido']:17,.2f}")
    
    print()
    
    # Resumo
    total_original = sum(c['saldo_original'] for c in contratos_converter)
    total_convertido = sum(c['saldo_convertido'] for c in contratos_converter)
    
    print(f"\n    RESUMO DA CONVERSAO:")
    print(f"    Contratos: {len(contratos_converter)}")
    print(f"    Total Original (moedas antigas): R$ {total_original:,.2f}")
    print(f"    Total Convertido (Real): R$ {total_convertido:,.2f}")
    print(f"    Reducao: R$ {total_original - total_convertido:,.2f}")
    
    # Aplicar conversão se modo = 'aplicar'
    if modo == 'aplicar':
        print(f"\n[3] Aplicando conversoes...")
        
        contador = 0
        for info in contratos_converter:
            parcela = info['parcela']
            
            # Guardar valor original
            parcela.sddev_original = info['saldo_original']
            
            # Atualizar para valor convertido
            parcela.sddev = info['saldo_convertido']
            
            parcela.save()
            contador += 1
            
            if contador % 50 == 0:
                print(f"    {contador}/{len(contratos_converter)} convertidos...")
        
        print(f"    [OK] {contador} contratos convertidos com sucesso!")
        print(f"\n    IMPORTANTE: O campo 'sddev_original' preserva os valores antigos")
        
        # Retornar códigos e valores dos contratos convertidos
        codigos = [c['codigo'] for c in contratos_converter]
        valores = {c['codigo']: c['saldo_convertido'] for c in contratos_converter}
        return codigos, valores
    else:
        print(f"\n[3] Simulacao concluida - nenhuma alteracao feita")
        print(f"\n    Para aplicar as conversoes, execute:")
        print(f"    py scripts\\converter_219_contratos.py --aplicar")
        
        # Retornar códigos e valores mesmo em simulação (para cálculo de IPCA)
        codigos = [c['codigo'] for c in contratos_converter]
        valores = {c['codigo']: c['saldo_convertido'] for c in contratos_converter}
        return codigos, valores

def aplicar_correcao_ipca(modo='simulacao', contratos_ja_convertidos=None, valores_convertidos=None):
    """
    Aplica correção IPCA de maio/2019 a novembro/2025
    Apenas em contratos já em Real ou recém convertidos
    
    Args:
        contratos_ja_convertidos: lista de códigos de contratos que foram convertidos
        valores_convertidos: dict com {codigo: saldo_convertido} para usar em simulação
    """
    print(f"\n[4] Correcao Monetaria (IPCA mai/2019 a nov/2025)")
    print("=" * 100)
    
    # Fator IPCA acumulado (aproximado)
    fator_ipca = Decimal('1.4146')  # 41,46%
    
    print(f"\n    Fator de correcao: {fator_ipca} (+41,46%)")
    print(f"    Aplicando em todos os contratos (ja em Real + convertidos)...")
    
    # Converter lista para set para busca rápida
    codigos_convertidos = set(contratos_ja_convertidos or [])
    valores_dict = valores_convertidos or {}
    
    # Coletar todos contratos em Real
    contratos_corrigir = []
    
    for contrato in Contrato.objects.all():
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if ultima_parcela and ultima_parcela.sddev:
            moeda, fator = identificar_moeda(ultima_parcela.dtvenc)
            
            # Aplicar apenas se já está em Real (fator == 1) OU foi convertido nesta execução
            if fator == 1 or contrato.codigo in codigos_convertidos:
                # Em simulação, usar valor convertido; em aplicar, usar valor do banco
                if modo == 'simulacao' and contrato.codigo in valores_dict:
                    saldo_atual = valores_dict[contrato.codigo]
                else:
                    saldo_atual = ultima_parcela.sddev
                    
                saldo_corrigido = saldo_atual * fator_ipca
                
                contratos_corrigir.append({
                    'contrato': contrato,
                    'codigo': contrato.codigo,
                    'parcela': ultima_parcela,
                    'saldo_maio_2019': saldo_atual,
                    'saldo_nov_2025': saldo_corrigido,
                    'correcao': saldo_corrigido - saldo_atual
                })
    
    print(f"    [OK] {len(contratos_corrigir)} contratos para correcao\n")
    
    # Resumo
    total_maio_2019 = sum(c['saldo_maio_2019'] for c in contratos_corrigir if c['saldo_maio_2019'] > 0)
    total_nov_2025 = sum(c['saldo_nov_2025'] for c in contratos_corrigir if c['saldo_nov_2025'] > 0)
    total_correcao = total_nov_2025 - total_maio_2019
    
    # Separar positivos e negativos
    positivos = [c for c in contratos_corrigir if c['saldo_maio_2019'] > 0]
    negativos = [c for c in contratos_corrigir if c['saldo_maio_2019'] <= 0]
    
    print(f"\n    RESUMO DA CORRECAO:")
    print(f"    Contratos com saldo positivo: {len(positivos)}")
    print(f"    Contratos com saldo negativo/zero: {len(negativos)}")
    print(f"    Total: {len(contratos_corrigir)}")
    print()
    print(f"    Total Maio/2019: R$ {total_maio_2019:,.2f}")
    print(f"    Total Nov/2025: R$ {total_nov_2025:,.2f}")
    print(f"    Correcao aplicada: R$ {total_correcao:,.2f} (+{((total_nov_2025/total_maio_2019 - 1) * 100) if total_maio_2019 > 0 else 0:.2f}%)")
    
    if modo == 'aplicar':
        print(f"\n[5] Aplicando correcoes IPCA...")
        
        contador = 0
        for info in contratos_corrigir:
            parcela = info['parcela']
            parcela.sddev = info['saldo_nov_2025']
            parcela.save()
            contador += 1
            
            if contador % 100 == 0:
                print(f"    {contador}/{len(contratos_corrigir)} corrigidos...")
        
        print(f"    [OK] {contador} contratos corrigidos com sucesso!")
    else:
        print(f"\n[5] Simulacao concluida - nenhuma alteracao feita")
    
    return len(contratos_corrigir)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Converte 219 contratos e aplica correcao IPCA')
    parser.add_argument('--aplicar', action='store_true', 
                       help='Aplica as conversoes (padrao: simulacao)')
    parser.add_argument('--apenas-conversao', action='store_true',
                       help='Apenas converte moedas, sem correcao IPCA')
    parser.add_argument('--apenas-ipca', action='store_true',
                       help='Apenas aplica correcao IPCA (requer conversao previa)')
    
    args = parser.parse_args()
    
    modo = 'aplicar' if args.aplicar else 'simulacao'
    
    print("=" * 100)
    print("CONVERSAO DE MOEDAS ANTIGAS E ATUALIZACAO MONETARIA")
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
    
    # Conversão de moedas
    codigos_convertidos = []
    valores_convertidos = {}
    
    if not args.apenas_ipca:
        resultado = converter_contratos(modo)
        if isinstance(resultado, tuple):
            codigos_convertidos, valores_convertidos = resultado
        else:
            codigos_convertidos = resultado
    
    # Correção IPCA
    if not args.apenas_conversao:
        qtd_corrigidos = aplicar_correcao_ipca(modo, codigos_convertidos, valores_convertidos)
    
    print("\n" + "=" * 100)
    print("PROCESSO CONCLUIDO")
    print("=" * 100)
    
    if modo == 'simulacao':
        print("\nEsta foi uma SIMULACAO. Para aplicar as mudancas:")
        print("py scripts\\converter_219_contratos.py --aplicar")
    else:
        print("\nConversoes aplicadas com sucesso!")
        print("Valores originais preservados no campo 'sddev_original'")

if __name__ == '__main__':
    main()
