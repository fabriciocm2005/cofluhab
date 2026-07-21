import os
from dbfread import DBF

# Arquivos de cadastro de mutuários
cad_files = [
    'CADMUT.DBF',
    'CADMUT2.DBF', 
    'CADMUT_2.DBF',
    'CADMUT__BK.DBF',
    'cadmutbk.dbf',
    'CAD1.DBF',
    'CAD2.DBF',
    'CADBAK.DBF',
    'CADOK.DBF',
    'cad1012.dbf'
]

print("Procurando 'PEDRO PAULO TARDIN' e código '00568' em arquivos de cadastro...\n")

for filename in cad_files:
    path = os.path.join('dados_antigos', filename)
    if not os.path.exists(path):
        continue
        
    print(f"=== {filename} ===")
    try:
        table = DBF(path, encoding='latin-1', raw=True, ignore_missing_memofile=True)
        print(f"Campos: {table.field_names}")
        print(f"Total registros: {len(table)}")
        
        found = False
        for record in table:
            # Procurar por PEDRO e TARDIN
            record_str = ' '.join(str(v) for v in record.values()).upper()
            
            if 'PEDRO' in record_str and 'TARDIN' in record_str:
                print(f"\n✓✓✓ ENCONTRADO!")
                for key, val in record.items():
                    print(f"  {key}: {val}")
                found = True
                break
            
            # Procurar por código 00568
            if '00568' in record_str or '000568' in record_str:
                # Verificar se é um código de mutuário
                codigo_field = None
                for key in record.keys():
                    if key.upper() in ['CODIGO', 'COD', 'CODMUT']:
                        codigo = str(record[key]).strip()
                        if '568' in codigo:
                            print(f"\n✓ Código {codigo} encontrado:")
                            for k, v in record.items():
                                print(f"  {k}: {v}")
                            found = True
                            break
        
        if not found:
            print("  (não encontrado neste arquivo)")
        print()
            
    except Exception as e:
        print(f"  Erro: {e}\n")

# Também procurar em MOVMUT para ver se tem o nome lá
print("\n=== Verificando MOVMUT.DBF ===")
try:
    table = DBF('dados_antigos/MOVMUT.DBF', encoding='latin-1', raw=True, ignore_missing_memofile=True)
    print(f"Campos MOVMUT: {table.field_names}")
    
    # Procurar registros com código 00568
    count = 0
    for record in table:
        codigo = str(record.get('CODIGO', '')).strip()
        if codigo == '00568' or codigo == '000568':
            if count == 0:
                print(f"\nPrimeiro registro com código 00568:")
                for k, v in record.items():
                    print(f"  {k}: {v}")
            count += 1
            if count >= 3:
                break
    
    print(f"Total registros com código 00568: {count}")
except Exception as e:
    print(f"Erro: {e}")
