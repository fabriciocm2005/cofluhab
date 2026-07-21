"""
Versão SQL direta - Muito mais rápida
Converte os 219 contratos com moedas antigas para Real
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

def identificar_fator(data_str):
    """Retorna fator de conversão baseado na data"""
    data = date.fromisoformat(data_str) if isinstance(data_str, str) else data_str
    
    if data < date(1967, 2, 13):
        return 1_000_000_000_000
    elif data < date(1986, 2, 28):
        return 1_000_000_000
    elif data < date(1989, 1, 16):
        return 1_000_000
    elif data < date(1990, 3, 16):
        return 1_000
    elif data < date(1993, 8, 1):
        return 1_000
    elif data < date(1994, 7, 1):
        return 2_750
    else:
        return 1

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--aplicar', action='store_true')
    args = parser.parse_args()
    
    modo = 'aplicar' if args.aplicar else 'simulacao'
    
    print("=" * 100)
    print(f"CONVERSAO DE MOEDAS E IPCA - MODO: {modo.upper()}")
    print("=" * 100)
    
    # Adicionar campo se não existir
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(principal_parcelacontrato)")
        colunas = [row[1] for row in cursor.fetchall()]
        
        if 'sddev_original' not in colunas:
            print("\nAdicionando campo 'sddev_original'...")
            cursor.execute("ALTER TABLE principal_parcelacontrato ADD COLUMN sddev_original DECIMAL(24, 2)")
            print("[OK] Campo adicionado")
    
    # Buscar última parcela de cada contrato via SQL
    print("\nAnalisando contratos...")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                c.id as contrato_id,
                c.codigo,
                c.conjunto,
                p.id as parcela_id,
                p.dtvenc,
                p.sddev
            FROM principal_contrato c
            INNER JOIN principal_parcelacontrato p ON p.contrato_id = c.id
            WHERE p.id IN (
                SELECT p2.id 
                FROM principal_parcelacontrato p2 
                WHERE p2.contrato_id = c.id 
                ORDER BY p2.nmens DESC 
                LIMIT 1
            )
            AND p.sddev IS NOT NULL
            ORDER BY p.sddev DESC
        """)
        
        dados = cursor.fetchall()
    
    print(f"[OK] {len(dados)} contratos carregados\n")
    
    # Processar
    converter = []
    ja_real = []
    
    for row in dados:
        contrato_id, codigo, conjunto, parcela_id, dtvenc, sddev = row
        fator = identificar_fator(dtvenc)
        
        info = {
            'contrato_id': contrato_id,
            'codigo': codigo,
            'parcela_id': parcela_id,
            'dtvenc': dtvenc,
            'sddev': Decimal(str(sddev)),
            'fator': fator
        }
        
        if fator > 1:
            info['sddev_convertido'] = info['sddev'] / Decimal(str(fator))
            converter.append(info)
        else:
            ja_real.append(info)
    
    print(f"Contratos que precisam conversao: {len(converter)}")
    print(f"Contratos ja em Real: {len(ja_real)}\n")
    
    # Top 10 conversões
    print("Top 10 contratos a serem convertidos:")
    print(f"{'Contrato':15} {'Data':12} {'Saldo Original':20} {'Saldo Convertido':20}")
    print("-" * 70)
    
    for i, info in enumerate(converter[:10], 1):
        print(f"{info['codigo']:15} {info['dtvenc']:12} R$ {info['sddev']:17,.2f} R$ {info['sddev_convertido']:17,.2f}")
    
    # Totais
    total_original = sum(c['sddev'] for c in converter)
    total_convertido = sum(c['sddev_convertido'] for c in converter)
    
    print(f"\nRESUMO CONVERSAO:")
    print(f"Total Original: R$ {total_original:,.2f}")
    print(f"Total Convertido: R$ {total_convertido:,.2f}")
    print(f"Reducao: R$ {total_original - total_convertido:,.2f}\n")
    
    # Aplicar IPCA
    fator_ipca = Decimal('1.4146')
    print(f"IPCA mai/2019 a nov/2025: {fator_ipca} (+41,46%)\n")
    
    # Calcular totais finais
    total_maio_2019 = total_convertido + sum(c['sddev'] for c in ja_real if c['sddev'] > 0)
    total_nov_2025 = total_maio_2019 * fator_ipca
    
    print(f"TOTAIS FINAIS:")
    print(f"Total Maio/2019 (apos conversao): R$ {total_maio_2019:,.2f}")
    print(f"Total Nov/2025 (com IPCA): R$ {total_nov_2025:,.2f}")
    print(f"Correcao aplicada: R$ {total_nov_2025 - total_maio_2019:,.2f}\n")
    
    if modo == 'aplicar':
        print("Aplicando conversoes...")
        
        from django.db import transaction
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Atualizar contratos convertidos
                contador = 0
                for info in converter:
                    saldo_final = info['sddev_convertido'] * fator_ipca
                    cursor.execute(
                        "UPDATE principal_parcelacontrato SET sddev_original = %s, sddev = %s WHERE id = %s",
                        [float(info['sddev']), float(saldo_final), info['parcela_id']]
                    )
                    contador += 1
                    if contador % 50 == 0:
                        print(f"  {contador}/{len(converter)} convertidos...")
                
                print(f"  Total convertidos: {contador}/{len(converter)}")
                
                # Atualizar contratos já em Real (apenas IPCA)
                contador = 0
                for info in ja_real:
                    saldo_final = info['sddev'] * fator_ipca
                    cursor.execute(
                        "UPDATE principal_parcelacontrato SET sddev = %s WHERE id = %s",
                        [float(saldo_final), info['parcela_id']]
                    )
                    contador += 1
                    if contador % 500 == 0:
                        print(f"  {contador}/{len(ja_real)} atualizados...")
                
                print(f"  Total atualizados com IPCA: {contador}/{len(ja_real)}")
        
        print(f"[OK] {len(converter)} contratos convertidos")
        print(f"[OK] {len(ja_real)} contratos atualizados com IPCA")
        print("\nCampo 'sddev_original' preserva os valores antigos")
    else:
        print("SIMULACAO - Para aplicar: py scripts\\converter_sql.py --aplicar")
    
    print("\n" + "=" * 100)

if __name__ == '__main__':
    main()
