import os
import glob
from dbfread import DBF

# Procurar por PEDRO PAULO TARDIN ou código 00568
target_name = "PEDRO PAULO TARDIN"
target_codigo = "00568"

dbf_files = glob.glob('dados_antigos/*.DBF')
print(f"Procurando '{target_name}' e código '{target_codigo}' em {len(dbf_files)} arquivos DBF...\n")

found_results = []

for dbf_path in dbf_files:
    filename = os.path.basename(dbf_path)
    
    # Pular arquivos muito grandes ou de pagamento
    if filename.startswith('PGTO') or filename.startswith('SEG'):
        continue
    
    try:
        table = DBF(dbf_path, encoding='latin-1', raw=True, ignore_missing_memofile=True)
        
        for record in table:
            # Converter valores para string
            record_str = str(record).upper()
            
            # Procurar pelo nome
            if 'PEDRO' in record_str and 'TARDIN' in record_str:
                print(f"✓ ENCONTRADO EM: {filename}")
                print(f"  Registro: {record}")
                found_results.append((filename, record))
                print()
            
            # Procurar pelo código (várias variações)
            elif any(cod in record_str for cod in ['00568', '000568', '0568', '568']):
                # Verificar se tem campo CODIGO ou NOME
                has_codigo = any(k.upper() in ['CODIGO', 'COD', 'CODMUT', 'NUMCONT'] for k in record.keys())
                has_nome = any(k.upper() in ['NOME', 'MUTUARIO', 'NOMEMUT'] for k in record.keys())
                
                if has_codigo or has_nome:
                    print(f"✓ Código encontrado em: {filename}")
                    print(f"  Registro: {record}")
                    found_results.append((filename, record))
                    print()
                    break
                    
    except Exception as e:
        # Ignorar erros silenciosamente
        pass

print(f"\n=== RESUMO ===")
print(f"Total de arquivos verificados: {len(dbf_files)}")
print(f"Resultados encontrados: {len(found_results)}")

if not found_results:
    print("\nNão encontrado. Tentando busca em arquivos específicos de cadastro...")
    
    # Buscar especificamente em arquivos de cadastro
    cad_files = ['CADMUT.DBF', 'CADMUT2.DBF', 'CADMUT_2.DBF', 'CAD1.DBF', 'CAD2.DBF', 'CADBAK.DBF']
    
    for filename in cad_files:
        path = os.path.join('dados_antigos', filename)
        if os.path.exists(path):
            print(f"\nVerificando {filename}...")
            try:
                table = DBF(path, encoding='latin-1', raw=True, ignore_missing_memofile=True)
                print(f"  Campos: {table.field_names}")
                print(f"  Total registros: {len(table)}")
                
                # Mostrar primeiros registros
                for i, rec in enumerate(table):
                    if i < 3:
                        print(f"  Exemplo {i+1}: {rec}")
                    else:
                        break
            except Exception as e:
                print(f"  Erro: {e}")
