"""
Extract high-confidence contrato->mutuario matches from `exports/contrato_mutuario_map.csv`.
Default threshold: 0.3 (adjustable via SCORE_THRESHOLD variable).
Writes `exports/contrato_mutuario_highconf.csv` with the selected rows and prints counts.
"""
import csv, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXPORT_DIR = os.path.join(ROOT, 'exports')
MAP = os.path.join(EXPORT_DIR, 'contrato_mutuario_map.csv')
OUT = os.path.join(EXPORT_DIR, 'contrato_mutuario_highconf.csv')
SCORE_THRESHOLD = 0.3

if not os.path.exists(MAP):
    print('Mapping file not found:', MAP)
    sys.exit(1)

with open(MAP, encoding='utf-8') as f:
    r = csv.DictReader(f)
    rows = list(r)

selected = []
for row in rows:
    try:
        s = float(row.get('score') or 0.0)
    except Exception:
        s = 0.0
    if s >= SCORE_THRESHOLD and (row.get('mutuario_id') or '').strip():
        selected.append(row)

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    if selected:
        w = csv.DictWriter(f, fieldnames=selected[0].keys())
        w.writeheader()
        w.writerows(selected)
    else:
        # write header from original map if possible
        with open(MAP, encoding='utf-8') as mf:
            mr = csv.reader(mf)
            header = next(mr)
        w = csv.writer(f)
        w.writerow(header)

print('TOTAL MAP ROWS:', len(rows))
print('SELECTED (score >=', SCORE_THRESHOLD, 'and has mutuario_id):', len(selected))
print('WROTE:', OUT)
