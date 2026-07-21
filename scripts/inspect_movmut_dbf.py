import os, sys
# ensure project root on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Path to target DBF (adjust if you want a different file)
DBF_PATH = os.path.join(ROOT, 'dados_antigos', 'MOVMUT.DBF')

print('Inspecting DBF:', DBF_PATH)

try:
    from dbfread import DBF
except Exception as e:
    print('dbfread not available:', e)
    sys.exit(1)

# Print field structure and first N records
N = 12
try:
    table = DBF(DBF_PATH, encoding='latin-1', char_decode_errors='ignore')
except Exception as e:
    print('Failed opening DBF:', e)
    sys.exit(1)

print('\nFields:')
for f in table.field_names:
    print(' -', f)

print('\nFirst {} records (as dicts):'.format(N))
count = 0
for rec in table:
    print(rec)
    count += 1
    if count >= N:
        break

print('\nTotal records in DBF (scanning):')
# count (fastish)
cnt = 0
for _ in table:
    cnt += 1
print(cnt)
