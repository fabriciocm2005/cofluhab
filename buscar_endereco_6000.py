from dbfread import DBF

def safe_text(value):
    if value is None:
        return ''
    if isinstance(value, bytes):
        return value.decode('latin-1', errors='ignore').strip()
    return str(value).strip()

# Buscar código 6000 no CADEND.DBF
dbf_path = 'dados_antigos/CADEND.DBF'
table = DBF(dbf_path, raw=True)

print("Procurando código 6000 no CADEND.DBF...")
encontrado = False

for record in table:
    try:
        codigo = safe_text(record.get('CODIGO', ''))
        
        # Normalizar para comparar
        try:
            codigo_norm = str(int(codigo))
        except:
            codigo_norm = codigo
        
        if codigo_norm == '6000':
            print(f"\n✅ ENCONTRADO!")
            print(f"Código: {codigo}")
            print(f"Endereço: {safe_text(record.get('ENDERECO', ''))}")
            print(f"Número: {safe_text(record.get('NUMERO', ''))}")
            print(f"Bairro: {safe_text(record.get('BAIRRO', ''))}")
            print(f"Cidade: {safe_text(record.get('CIDADE', ''))}")
            print(f"CEP: {safe_text(record.get('CEP', ''))}")
            encontrado = True
            break
    except Exception as e:
        continue

if not encontrado:
    print("\n❌ Código 6000 NÃO encontrado no CADEND.DBF")
    print("\nVerificando códigos próximos...")
    table = DBF(dbf_path, raw=True)
    for record in table:
        try:
            codigo = safe_text(record.get('CODIGO', ''))
            try:
                codigo_norm = str(int(codigo))
            except:
                codigo_norm = codigo
            
            if codigo_norm.startswith('60') and len(codigo_norm) == 4:
                print(f"  Código: {codigo_norm}")
        except:
            continue
