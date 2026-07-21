"""
Tentar ler CADMUT.DBF para encontrar o campo conjunto
"""

from dbfread import DBF
import sys

cadmut_path = 'dados_antigos/CADMUT.DBF'

print("=" * 70)
print(f"Lendo {cadmut_path}")
print("=" * 70)
print()

try:
    table = DBF(cadmut_path, encoding='latin1', ignorecase=True, load=False)
    
    print("Campos disponíveis:")
    for field in table.fields:
        print(f"  {field.name}: {field.type} ({field.length})")
    
    print()
    print("=" * 70)
    print("Procurando registro do contrato 6000...")
    print("=" * 70)
    print()
    
    found = False
    for record in table:
        try:
            codigo = str(record.get('CODIGO', '')).strip()
            cod_imovel = str(record.get('CODIMOVEL', '')).strip()
            
            if codigo == '6000' or codigo == '006000' or codigo == '0006000' or codigo == '00006000':
                found = True
                print(f"Encontrado! Dados do registro:")
                for key, value in record.items():
                    print(f"  {key}: '{value}'")
                break
                
        except Exception as e:
            continue
    
    if not found:
        print("Contrato 6000 não encontrado no CADMUT.DBF")
        print("\nVerificando os primeiros registros para entender a estrutura:")
        for i, record in enumerate(table):
            if i >= 3:
                break
            try:
                codigo = str(record.get('CODIGO', '')).strip()
                print(f"\nRegistro {i+1}: CODIGO={codigo}")
                for key, value in record.items():
                    val_str = str(value)[:50]  # Limitar tamanho
                    print(f"  {key}: '{val_str}'")
            except:
                continue
        
except Exception as e:
    print(f"Erro ao ler arquivo: {e}")
    import traceback
    traceback.print_exc()
