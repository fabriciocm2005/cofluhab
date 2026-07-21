import os
from dbfread import DBF

# Lista de arquivos mais completos
files_to_check = ['CAD1.DBF', 'CAD2.DBF', 'CADBAK.DBF', 'cad1012.dbf']

target_codigo = '00568'

print(f"Procurando codigo {target_codigo}...\n")

for filename in files_to_check:
    path = os.path.join('dados_antigos', filename)
    if not os.path.exists(path):
        continue
        
    try:
        table = DBF(path, encoding='latin-1', raw=True, ignore_missing_memofile=True)
        
        for record in table:
            codigo_raw = record.get('CODIGO', b'')
            if isinstance(codigo_raw, bytes):
                codigo = codigo_raw.decode('latin-1', 'ignore').strip()
            else:
                codigo = str(codigo_raw).strip()
            
            if codigo == target_codigo or codigo == '0' + target_codigo or codigo == '000' + target_codigo:
                print(f"ENCONTRADO em {filename}!")
                print(f"CODIGO: {codigo}")
                
                # Nome
                nome_raw = record.get('NOME', b'')
                if isinstance(nome_raw, bytes):
                    nome = nome_raw.decode('latin-1', 'ignore').strip()
                else:
                    nome = str(nome_raw).strip()
                print(f"NOME: {nome}")
                
                # Conjunto
                conjunto_raw = record.get('CONJUNTO', b'')
                if isinstance(conjunto_raw, bytes):
                    conjunto = conjunto_raw.decode('latin-1', 'ignore').strip()
                else:
                    conjunto = str(conjunto_raw).strip()
                print(f"CONJUNTO: {conjunto}")
                
                # CPF
                cpf_raw = record.get('CPF', b'')
                if isinstance(cpf_raw, bytes):
                    cpf = cpf_raw.decode('latin-1', 'ignore').strip()
                else:
                    cpf = str(cpf_raw).strip()
                print(f"CPF: {cpf}")
                
                print()
                break
                
    except Exception as e:
        print(f"Erro em {filename}: {e}")

print("\nAgora verificando quais codigos de contratos sem mutuario existem em CAD1.DBF...")

# Ler CAD1 completo
cad1_codigos = set()
try:
    table = DBF('dados_antigos/CAD1.DBF', encoding='latin-1', raw=True, ignore_missing_memofile=True)
    for record in table:
        codigo_raw = record.get('CODIGO', b'')
        if isinstance(codigo_raw, bytes):
            codigo = codigo_raw.decode('latin-1', 'ignore').strip()
        else:
            codigo = str(codigo_raw).strip()
        cad1_codigos.add(codigo)
    print(f"Total codigos em CAD1.DBF: {len(cad1_codigos)}")
except Exception as e:
    print(f"Erro lendo CAD1: {e}")
