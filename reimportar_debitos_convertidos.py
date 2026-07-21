#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reimportar débitos de prestação com conversões monetárias corretas
BACKUP será criado antes de executar
"""

import os
import django
import shutil
from datetime import date, datetime
from dbfread import DBF

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato

# Funções de conversão monetária
def converter_para_real(valor, data_vencimento):
    """
    Converte valor de moeda antiga para Real baseado na data de vencimento
    
    Histórico de moedas:
    - Até 27/02/1986: Cruzeiro (Cr$)
    - 28/02/1986 a 15/01/1989: Cruzado (Cz$) - corte 3 zeros (÷1000)
    - 16/01/1989 a 15/03/1990: Cruzado Novo (NCz$) - corte 3 zeros (÷1000) 
    - 16/03/1990 a 31/07/1993: Cruzeiro (Cr$) - mantém valor
    - 01/08/1993 a 30/06/1994: Cruzeiro Real (CR$) - corte 3 zeros (÷1000)
    - A partir de 01/07/1994: Real (R$) - fator 2750 (÷2750)
    """
    if not data_vencimento or not valor:
        return 0.0
    
    try:
        valor_convertido = float(valor)
        
        # Até 27/02/1986: Cruzeiro antigo -> precisa passar por todas conversões
        if data_vencimento < date(1986, 2, 28):
            valor_convertido = valor_convertido / 1000  # Cr$ -> Cz$ (corte 3 zeros)
            valor_convertido = valor_convertido / 1000  # Cz$ -> NCz$ (corte 3 zeros)
            valor_convertido = valor_convertido / 1000  # Cr$ (novo) -> CR$ (corte 3 zeros)
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # 28/02/1986 a 15/01/1989: Cruzado
        elif data_vencimento < date(1989, 1, 16):
            valor_convertido = valor_convertido / 1000  # Cz$ -> NCz$ (corte 3 zeros)
            valor_convertido = valor_convertido / 1000  # Cr$ (novo) -> CR$ (corte 3 zeros)
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # 16/01/1989 a 15/03/1990: Cruzado Novo
        elif data_vencimento < date(1990, 3, 16):
            valor_convertido = valor_convertido / 1000  # Cr$ (novo) -> CR$ (corte 3 zeros)
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # 16/03/1990 a 31/07/1993: Cruzeiro (retorno)
        elif data_vencimento < date(1993, 8, 1):
            valor_convertido = valor_convertido / 1000  # Cr$ -> CR$ (corte 3 zeros)
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # 01/08/1993 a 30/06/1994: Cruzeiro Real
        elif data_vencimento < date(1994, 7, 1):
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # A partir de 01/07/1994: já é Real
        
        return valor_convertido
    
    except:
        return 0.0


def reimportar_debitos():
    """Reimporta todos os débitos com conversões corretas"""
    
    print("\n" + "="*100)
    print("REIMPORTAÇÃO DE DÉBITOS COM CONVERSÃO MONETÁRIA")
    print("="*100)
    
    # 1. FAZER BACKUP
    print("\n1️⃣ Criando backup do banco de dados...")
    backup_name = f"db.sqlite3.backup-antes-correcao-debitos-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    try:
        shutil.copy2('db.sqlite3', backup_name)
        print(f"   ✅ Backup criado: {backup_name}")
    except Exception as e:
        print(f"   ❌ Erro ao criar backup: {e}")
        return
    
    # 2. LIMPAR DÉBITOS EXISTENTES
    print("\n2️⃣ Limpando débitos existentes...")
    contratos_atualizados = 0
    for contrato in Contrato.objects.all():
        if contrato.debito_total or contrato.debito_prestacao:
            contrato.debito_total = 0.0
            contrato.debito_prestacao = 0.0
            contrato.save()
            contratos_atualizados += 1
    print(f"   ✅ Zerados débitos de {contratos_atualizados} contratos")
    
    # 3. IMPORTAR DÉBITOS COM CONVERSÃO
    print("\n3️⃣ Importando débitos do DEBPREST.DBF com conversão monetária...")
    
    dbf_path = 'dados_antigos/DEBPREST.DBF'
    
    try:
        db = DBF(dbf_path, encoding='latin1')
        
        # Agrupar débitos por contrato
        debitos_por_contrato = {}
        
        total_registros = 0
        for rec in db:
            total_registros += 1
            
            contrato_codigo = str(rec.get('CONTRATO', '')).strip()
            if not contrato_codigo:
                continue
            
            # Normalizar código (remover zeros à esquerda e depois adicionar de volta)
            try:
                contrato_codigo = str(int(contrato_codigo))
            except:
                continue
            
            vencimento = rec.get('VENCIMENTO')
            total = rec.get('TOTAL', 0.0)
            
            # Converter valor para Real
            valor_convertido = converter_para_real(total, vencimento)
            
            if contrato_codigo not in debitos_por_contrato:
                debitos_por_contrato[contrato_codigo] = 0.0
            
            debitos_por_contrato[contrato_codigo] += valor_convertido
            
            if total_registros % 10000 == 0:
                print(f"   Processados: {total_registros:,} registros...")
        
        print(f"   ✅ Total de registros processados: {total_registros:,}")
        print(f"   ✅ Contratos com débitos: {len(debitos_por_contrato):,}")
        
        # 4. ATUALIZAR CONTRATOS
        print("\n4️⃣ Atualizando contratos com novos valores...")
        
        contratos_atualizados = 0
        contratos_nao_encontrados = 0
        total_debito_geral = 0.0
        
        for codigo, debito_total in debitos_por_contrato.items():
            # Buscar contrato
            contrato = Contrato.objects.filter(codigo=codigo).first()
            
            if contrato:
                contrato.debito_prestacao = debito_total
                contrato.debito_total = debito_total  # Por enquanto, só débito de prestação
                contrato.save()
                
                contratos_atualizados += 1
                total_debito_geral += debito_total
                
                if contratos_atualizados % 500 == 0:
                    print(f"   Atualizados: {contratos_atualizados:,} contratos...")
            else:
                contratos_nao_encontrados += 1
        
        print(f"\n   ✅ Contratos atualizados: {contratos_atualizados:,}")
        print(f"   ⚠️  Contratos não encontrados: {contratos_nao_encontrados}")
        print(f"   💰 Total de débitos (convertido): R$ {total_debito_geral:,.2f}")
        
        # 5. ESTATÍSTICAS
        print("\n5️⃣ Estatísticas finais:")
        print(f"   • Total de contratos: {Contrato.objects.count():,}")
        print(f"   • Contratos com débito: {Contrato.objects.filter(debito_total__gt=0).count():,}")
        print(f"   • Contratos sem débito: {Contrato.objects.filter(debito_total=0).count():,}")
        
        # Maior débito
        maior = Contrato.objects.filter(debito_total__gt=0).order_by('-debito_total').first()
        if maior:
            print(f"   • Maior débito: Contrato {maior.codigo} - R$ {maior.debito_total:,.2f}")
        
        print("\n" + "="*100)
        print("✅ REIMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*100)
        
    except Exception as e:
        print(f"\n❌ ERRO durante importação: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Restaure o backup se necessário:")
        print(f"   cp {backup_name} db.sqlite3")


if __name__ == '__main__':
    print("\n⚠️  ATENÇÃO: Este script vai:")
    print("   1. Criar um backup do banco de dados")
    print("   2. Zerar todos os débitos existentes")
    print("   3. Reimportar com conversões monetárias corretas")
    print()
    
    resposta = input("Deseja continuar? (sim/não): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        reimportar_debitos()
    else:
        print("\n❌ Operação cancelada pelo usuário")
