"""
Importa campos adicionais do CADBAK.DBF para complementar os contratos.

Observacao: CADMUT.DBF nesta base historica pode nao ter registros ativos.
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from dbfread import DBF

def importar_campos_adicionais():
    """Importa campos adicionais do CADBAK.DBF para os contratos"""

    dbf_path = os.path.join('dados_antigos', 'CADBAK.DBF')
    
    if not os.path.exists(dbf_path):
        print(f"❌ Arquivo {dbf_path} não encontrado")
        return
    
    print(f"📖 Lendo {dbf_path}...")
    table = DBF(dbf_path, encoding='latin1')
    
    total = 0
    atualizados = 0
    nao_encontrados = 0
    
    for record in table:
        total += 1
        
        codigo = record.get('CODIGO', '').strip()
        if not codigo:
            continue
        
        try:
            contrato = Contrato.objects.get(codigo=codigo)
            
            # Atualizar campos adicionais
            contrato.cod_imovel = record.get('CODIMOVEL', '').strip()
            contrato.data_contrato = record.get('DTASSIN')
            contrato.data_primeiro_venc = record.get('PRIMVENC')
            contrato.sa = record.get('SA', '').strip()
            contrato.tx_juros = record.get('TXJUROS')
            contrato.prazo = record.get('PRAZO')
            contrato.cat_prof = record.get('CATPROF', '').strip()
            contrato.pr = record.get('PR', '').strip()
            
            contrato.save()
            atualizados += 1
            
            if atualizados % 100 == 0:
                print(f"  Processados: {atualizados}...")
                
        except Contrato.DoesNotExist:
            nao_encontrados += 1
    
    print(f"\n✅ Importação concluída!")
    print(f"   Total registros CADBAK: {total}")
    print(f"   Contratos atualizados: {atualizados}")
    print(f"   Não encontrados: {nao_encontrados}")
    
    # Mostrar exemplo
    print(f"\n📋 Exemplo - Contrato 006333:")
    try:
        c = Contrato.objects.get(codigo='006333')
        print(f"   Código Imóvel: {c.cod_imovel}")
        print(f"   Data Contrato: {c.data_contrato}")
        print(f"   Data 1º Venc: {c.data_primeiro_venc}")
        print(f"   SA: {c.sa}")
        print(f"   Taxa Juros: {c.tx_juros}")
        print(f"   Prazo: {c.prazo}")
        print(f"   Cat Prof: {c.cat_prof}")
        print(f"   PR: {c.pr}")
    except Contrato.DoesNotExist:
        print("   Contrato 006333 não encontrado")

if __name__ == '__main__':
    importar_campos_adicionais()
