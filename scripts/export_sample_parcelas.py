import os, sqlite3, csv
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXPORT_DIR = os.path.join(ROOT, 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)
DB = os.path.join(ROOT, 'db.sqlite3')

out = os.path.join(EXPORT_DIR, 'movmut_sample_parcelas.csv')
con = sqlite3.connect(DB)
cur = con.cursor()
# get 20 sample parcelas and also sample for codigo 000442 if present
cur.execute("SELECT p.id, c.codigo, p.nmens, p.dtvenc, p.juros, p.amort, p.vlautent FROM principal_parcelacontrato p JOIN principal_contrato c ON p.contrato_id=c.id ORDER BY c.codigo, p.nmens LIMIT 200")
rows = cur.fetchall()
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['id','codigo','nmens','dtvenc','juros','amort','vlautent'])
    for r in rows:
        w.writerow(r)
print('WROTE', out)
con.close()
