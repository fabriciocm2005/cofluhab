"""
Examinar estrutura do FCVS.DBF do sistema antigo
"""
from dbfread import DBF
import os

fcvs_path = r'C:\Users\fabri\cofluhab\cofluhab\dados_antigos\fcvs\FCVS\FCVS.DBF'

print("=" * 80)
print("ANÁLISE DO SISTEMA ANTIGO DE FCVS")
print("=" * 80)

if os.path.exists(fcvs_path):
    print(f"\n✓ Arquivo encontrado: {fcvs_path}")
    
    try:
        db = DBF(fcvs_path, encoding='latin1', ignore_missing_memofile=True)
        
        print("\n" + "=" * 80)
        print("ESTRUTURA DO ARQUIVO FCVS.DBF:")
        print("=" * 80)
        
        print(f"\nTotal de registros: {len(db)}")
        print(f"\nCampos ({len(db.field_names)}):")
        for i, field_name in enumerate(db.field_names, 1):
            print(f"  {i:2d}. {field_name}")
        
        print("\n" + "=" * 80)
        print("PRIMEIROS 10 REGISTROS:")
        print("=" * 80)
        
        for i, rec in enumerate(db, 1):
            if i > 10:
                break
            print(f"\nRegistro {i}:")
            for field, value in rec.items():
                if value is not None and str(value).strip():
                    print(f"  {field:15s}: {value}")
        
        print("\n" + "=" * 80)
        print("ANÁLISE DE CAMPOS IMPORTANTES:")
        print("=" * 80)
        
        # Procurar por campos relacionados a FCVS, valor, prestação, etc.
        campos_importantes = []
        for field in db.field_names:
            field_lower = field.lower()
            if any(palavra in field_lower for palavra in ['fcvs', 'valor', 'prest', 'saldo', 'vl', 'tot', 'conj', 'codigo', 'nome', 'mes', 'ref']):
                campos_importantes.append(field)
        
        if campos_importantes:
            print(f"\nCampos relacionados a FCVS ({len(campos_importantes)}):")
            for campo in campos_importantes:
                print(f"  - {campo}")
            
            print("\n" + "=" * 80)
            print("AMOSTRA DE DADOS DOS CAMPOS IMPORTANTES:")
            print("=" * 80)
            
            for i, rec in enumerate(db, 1):
                if i > 5:
                    break
                print(f"\nRegistro {i}:")
                for campo in campos_importantes:
                    valor = rec.get(campo)
                    if valor is not None:
                        print(f"  {campo:15s}: {valor}")
        
        print("\n" + "=" * 80)
        print("CONCLUSÕES:")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Erro ao ler arquivo: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"\n❌ Arquivo não encontrado: {fcvs_path}")
