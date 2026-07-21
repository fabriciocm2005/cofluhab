"""
Ler CADMUT.DBF procurando por CODIMOVEL que corresponde ao contrato 6000
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from dbfread import DBF

# Primeiro, pegar o cod_imovel do contrato 6000
contrato = Contrato.objects.get(codigo='6000')
cod_imovel = contrato.cod_imovel
print(f"Contrato 6000 tem cod_imovel: '{cod_imovel}'")
print()

cadmut_path = 'dados_antigos/CADMUT.DBF'

print("=" * 70)
print(f"Procurando CODIMOVEL='{cod_imovel}' no CADMUT.DBF")
print("=" * 70)
print()

try:
    table = DBF(cadmut_path, encoding='latin1', ignorecase=True, load=False)
    
    found = False
    for record in table:
        try:
            codimovel = str(record.get('CODIMOVEL', '')).strip()
            
            # Tentar com e sem zeros
            if codimovel == cod_imovel or codimovel.lstrip('0') == cod_imovel.lstrip('0'):
                found = True
                conjunto = str(record.get('CONJUNTO', '')).strip()
                codigo = str(record.get('CODIGO', '')).strip()
                nome = str(record.get('NOME', '')).strip()
                
                print(f"✓ Encontrado!")
                print(f"  CODIGO (mutuário): {codigo}")
                print(f"  CODIMOVEL: {codimovel}")
                print(f"  CONJUNTO: '{conjunto}'")
                print(f"  NOME: {nome}")
                break
                
        except Exception as e:
            continue
    
    if not found:
        print(f"✗ Não encontrado CODIMOVEL='{cod_imovel}'")
        print("\nMostrando alguns exemplos de CODIMOVEL:")
        for i, record in enumerate(table):
            if i >= 5:
                break
            try:
                codimovel = str(record.get('CODIMOVEL', '')).strip()
                conjunto = str(record.get('CONJUNTO', '')).strip()
                print(f"  CODIMOVEL={codimovel}, CONJUNTO={conjunto}")
            except:
                continue
        
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
