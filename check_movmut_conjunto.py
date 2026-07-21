"""
Check MOVMUT.DBF (original data file) for the conjunto field of contract 6000
"""

from dbfread import DBF
import sys

# Path to original MOVMUT.DBF
movmut_path = 'dados_antigos/MOVMUT.DBF'

try:
    print("Lendo arquivo MOVMUT.DBF...\n")
    table = DBF(movmut_path, encoding='latin1', ignorecase=True)
    
    # Find records for codigo 6000
    registros_6000 = []
    for record in table:
        codigo = str(record.get('CODIGO', '')).strip()
        if codigo == '6000':
            registros_6000.append(record)
    
    if registros_6000:
        print(f"Encontrados {len(registros_6000)} registros para código 6000\n")
        print("Primeiros 5 registros:")
        for i, record in enumerate(registros_6000[:5], 1):
            conjunto = str(record.get('CONJUNTO', '')).strip()
            tipo = str(record.get('TIPO', '')).strip()
            codimovel = str(record.get('CODIMOVEL', '')).strip()
            print(f"{i}. CODIGO={record.get('CODIGO')}, CONJUNTO='{conjunto}', CODIMOVEL='{codimovel}', TIPO='{tipo}'")
        
        # Get distinct conjunto values
        conjuntos = set()
        for record in registros_6000:
            conjunto = str(record.get('CONJUNTO', '')).strip()
            if conjunto:
                conjuntos.add(conjunto)
        
        print(f"\nValores distintos de CONJUNTO para código 6000:")
        for conj in sorted(conjuntos):
            count = sum(1 for r in registros_6000 if str(r.get('CONJUNTO', '')).strip() == conj)
            print(f"  '{conj}': {count} registros")
    else:
        print("Nenhum registro encontrado para código 6000")
        
except FileNotFoundError:
    print(f"Arquivo não encontrado: {movmut_path}")
    print("\nArquivos disponíveis em dados_antigos/:")
    import os
    if os.path.exists('dados_antigos'):
        files = [f for f in os.listdir('dados_antigos') if f.upper().endswith('.DBF')]
        for f in sorted(files)[:20]:
            print(f"  {f}")
except Exception as e:
    print(f"Erro ao ler arquivo: {e}")
    import traceback
    traceback.print_exc()
