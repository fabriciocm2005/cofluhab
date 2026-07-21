from dbfread import DBF

print("=== CMOVMUT.DBF ===")
dbf = DBF('dados_antigos/CMOVMUT.DBF', encoding='latin-1', raw=True, ignore_missing_memofile=True)
print(f'Campos: {dbf.field_names}')

print('\nPrimeiro registro:')
r = next(iter(DBF('dados_antigos/CMOVMUT.DBF', encoding='latin-1', raw=True, ignore_missing_memofile=True)))
for k, v in r.items():
    print(f'  {k}: {v}')
