from dbfread import DBF
import os

os.chdir('dados_antigos')
files = ['MOVMUT.DBF', 'A000442.DBF', 'CAD1.DBF', 'CAD2.DBF']

for f in files:
    if os.path.exists(f):
        count = len(list(DBF(f, encoding='latin1')))
        print(f'{f}: {count} records')
    else:
        print(f'{f}: not found')
