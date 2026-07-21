# -*- coding: utf-8 -*-
"""
Script para Calcular Saldo Devedor Atualizado em Real
Converte apenas o SALDO FINAL (última parcela) para Real atual
Mantém histórico original intacto
"""

import django
import os
import sys
from datetime import datetime, date
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
import sqlite3


def adicionar_campo_saldo_real():
    """Adiciona campo sddev_real_atual na tabela de contratos"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se campo já existe
        cursor.execute("PRAGMA table_info(principal_contrato)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        if 'sddev_real_atual' not in colunas:
            print("Adicionando campo 'sddev_real_atual' na tabela de contratos...")
            cursor.execute("""
                ALTER TABLE principal_contrato 
                ADD COLUMN sddev_real_atual DECIMAL(15, 2) DEFAULT 0
            """)
            conn.commit()
            print("[OK] Campo adicionado com sucesso!")
        else:
            print("[INFO] Campo 'sddev_real_atual' ja existe")
        
        # Adicionar também data da última atualização
        if 'data_ultima_atualizacao' not in colunas:
            cursor.execute("""
                ALTER TABLE principal_contrato 
                ADD COLUMN data_ultima_atualizacao DATE
            """)
            conn.commit()
            print("[OK] Campo 'data_ultima_atualizacao' adicionado!")
        
    except Exception as e:
        print(f"[ERRO] {e}")
    finally:
        conn.close()


def converter_para_real(valor, data_referencia):
    """Converte valor histórico para Real"""
    if isinstance(data_referencia, str):
        data_referencia = datetime.strptime(data_referencia, '%d/%m/%Y').date()
    elif isinstance(data_referencia, datetime):
        data_referencia = data_referencia.date()
    
    fator = Decimal('1.0')
    
    # 1994-07-01: Cruzeiro Real -> Real (÷ 2.750)
    if data_referencia < date(1994, 7, 1):
        fator = fator / Decimal('2750')
    
    # 1993-08-01: Cruzeiro -> Cruzeiro Real (÷ 1.000)
    if data_referencia < date(1993, 8, 1):
        fator = fator / Decimal('1000')
    
    # 1989-01-16: Cruzado -> Cruzado Novo (÷ 1.000)
    if data_referencia < date(1989, 1, 16):
        fator = fator / Decimal('1000')
    
    # 1986-02-28: Cruzeiro -> Cruzado (÷ 1.000)
    if data_referencia < date(1986, 2, 28):
        fator = fator / Decimal('1000')
    
    # 1967-02-13: Cruzeiro -> Cruzeiro Novo (÷ 1.000)
    if data_referencia < date(1967, 2, 13):
        fator = fator / Decimal('1000')
    
    return valor * fator


def calcular_saldos_reais(modo='simulacao'):
    """
    Calcula saldo devedor atual em Real para cada contrato
    Converte apenas o SALDO FINAL da última parcela
    """
    print("\n" + "="*80)
    print(f"{'SIMULACAO' if modo == 'simulacao' else 'APLICANDO'} - CALCULO DE SALDOS EM REAL")
    print("="*80 + "\n")
    
    if modo == 'aplicar':
        adicionar_campo_saldo_real()
    
    total_contratos = 0
    total_convertidos = 0
    total_ja_em_real = 0
    total_sem_saldo = 0
    
    exemplos_conversao = []
    exemplos_ja_real = []
    
    saldo_total_original = Decimal('0')
    saldo_total_convertido = Decimal('0')
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    for contrato in Contrato.objects.all():
        total_contratos += 1
        
        # Pegar ÚLTIMA parcela (saldo mais recente)
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if not ultima_parcela or not ultima_parcela.sddev:
            total_sem_saldo += 1
            continue
        
        saldo_original = ultima_parcela.sddev
        data_parcela = ultima_parcela.dtvenc
        
        # Verificar se já está em Real
        if data_parcela >= date(1994, 7, 1):
            # Já está em Real
            saldo_em_real = saldo_original
            total_ja_em_real += 1
            
            if len(exemplos_ja_real) < 3:
                exemplos_ja_real.append({
                    'contrato': contrato.codigo,
                    'data': data_parcela,
                    'saldo': saldo_original
                })
        else:
            # Precisa converter
            saldo_em_real = converter_para_real(saldo_original, data_parcela)
            total_convertidos += 1
            
            if len(exemplos_conversao) < 10:
                exemplos_conversao.append({
                    'contrato': contrato.codigo,
                    'data': data_parcela,
                    'saldo_original': saldo_original,
                    'saldo_real': saldo_em_real,
                    'fator': saldo_em_real / saldo_original if saldo_original != 0 else 0
                })
        
        saldo_total_original += saldo_original
        saldo_total_convertido += saldo_em_real
        
        # Salvar no banco
        if modo == 'aplicar':
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE principal_contrato 
                SET sddev_real_atual = ?, data_ultima_atualizacao = ?
                WHERE id = ?
            """, (float(saldo_em_real), date.today(), contrato.id))
            conn.commit()
            conn.close()
    
    # Mostrar exemplos
    print("EXEMPLOS DE CONVERSAO (moedas antigas -> Real):")
    print("-" * 80)
    for ex in exemplos_conversao:
        print(f"\nContrato {ex['contrato']} (data: {ex['data']}):")
        print(f"  Saldo na moeda antiga: {ex['saldo_original']:,.2f}")
        print(f"  Saldo em Real: R$ {ex['saldo_real']:,.2f}")
        print(f"  Fator de conversao: {ex['fator']:.10f}")
    
    print("\n" + "="*80)
    print("EXEMPLOS JA EM REAL (parcelas pos-1994):")
    print("-" * 80)
    for ex in exemplos_ja_real:
        print(f"Contrato {ex['contrato']} ({ex['data']}): R$ {ex['saldo']:,.2f}")
    
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    print(f"Total de Contratos: {total_contratos}")
    print(f"Contratos convertidos (moedas antigas): {total_convertidos}")
    print(f"Contratos ja em Real: {total_ja_em_real}")
    print(f"Contratos sem saldo: {total_sem_saldo}")
    print(f"\nSaldo Total (valores originais): {saldo_total_original:,.2f}")
    print(f"Saldo Total em Real: R$ {saldo_total_convertido:,.2f}")
    print("="*80 + "\n")
    
    if modo == 'aplicar':
        print("[OK] SALDOS CALCULADOS E SALVOS COM SUCESSO!")
        print("[OK] Campo 'sddev_real_atual' atualizado em todos os contratos")
    else:
        print("[AVISO] MODO SIMULACAO - Nenhuma alteracao foi salva")
        print("        Para aplicar, execute: py scripts/calcular_saldos_reais.py --aplicar")
    
    print("\n" + "="*80 + "\n")
    
    return {
        'total_contratos': total_contratos,
        'convertidos': total_convertidos,
        'ja_em_real': total_ja_em_real,
        'saldo_total_real': float(saldo_total_convertido)
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Calcular saldo devedor atual em Real'
    )
    parser.add_argument(
        '--aplicar',
        action='store_true',
        help='Aplicar calculo e salvar no banco (padrao: simulacao)'
    )
    
    args = parser.parse_args()
    
    modo = 'aplicar' if args.aplicar else 'simulacao'
    
    if modo == 'aplicar':
        print("\n" + "="*80)
        print("ATENCAO: CALCULO DE SALDOS EM REAL!")
        print("="*80)
        print("   Esta operacao ira:")
        print("   1. Adicionar campo 'sddev_real_atual' na tabela de contratos")
        print("   2. Converter saldo final de cada contrato para Real")
        print("   3. MANTER historico original intacto (parcelas nao serao alteradas)")
        print("   ")
        print("   [!] RECOMENDACAO: Faca backup do banco antes!")
        print("   ")
        print("   Comando de backup:")
        print("   copy db.sqlite3 db.sqlite3.backup-antes-calculo-real")
        print("="*80 + "\n")
        
        resposta = input("Deseja continuar? (digite 'SIM' para confirmar): ")
        
        if resposta.upper() != 'SIM':
            print("\n[CANCELADO] Operacao cancelada pelo usuario.")
            return
    
    try:
        calcular_saldos_reais(modo)
    except Exception as e:
        print(f"\n[ERRO] Falha na execucao: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
