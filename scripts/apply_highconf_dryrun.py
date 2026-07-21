"""
Dry-run updater for high-confidence Contrato->Mutuario links.

Behavior (default dry-run):
- Reads `exports/contrato_mutuario_highconf.csv`.
- Writes `exports/contrato_mutuario_apply_preview.csv` with the rows and counts.
- Writes `exports/contrato_mutuario_apply.sql` containing SQL to create a non-invasive mapping table
  `contrato_mutuario_map` and `INSERT OR REPLACE` statements for each mapping.

Apply mode (--apply):
- Executes the SQL against the project's SQLite DB (`db.sqlite3`) to create the mapping table
  and insert mapping rows. This does NOT modify Django models or add foreign keys; it's reversible
  and non-destructive (stored in a separate table).

Usage:
  python scripts\apply_highconf_dryrun.py        # dry-run, produce CSV + SQL file
  python scripts\apply_highconf_dryrun.py --apply   # execute SQL against db.sqlite3

"""
import csv, os, sys, sqlite3
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXPORT_DIR = os.path.join(ROOT, 'exports')
HIGHCONF = os.path.join(EXPORT_DIR, 'contrato_mutuario_highconf.csv')
SQL_OUT = os.path.join(EXPORT_DIR, 'contrato_mutuario_apply.sql')
PREVIEW = os.path.join(EXPORT_DIR, 'contrato_mutuario_apply_preview.csv')
DB = os.path.join(ROOT, 'db.sqlite3')

if not os.path.exists(HIGHCONF):
    print('High-confidence CSV not found:', HIGHCONF)
    sys.exit(1)

apply_mode = False
if len(sys.argv) > 1 and sys.argv[1] == '--apply':
    apply_mode = True

rows = []
with open(HIGHCONF, encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        try:
            contrato_id = int(row.get('contrato_id') or 0)
            mutuario_id = int((row.get('mutuario_id') or '').strip() or 0)
            score = float(row.get('score') or 0.0)
            method = row.get('method') or ''
        except Exception:
            continue
        if contrato_id and mutuario_id:
            rows.append((contrato_id, mutuario_id, score, method))

# write preview CSV
with open(PREVIEW, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['contrato_id','mutuario_id','score','method'])
    for r in rows:
        w.writerow(r)

# write SQL file: create mapping table and inserts
with open(SQL_OUT, 'w', encoding='utf-8') as f:
    f.write('-- Generated: %s\n' % datetime.utcnow().isoformat())
    f.write('-- Table: contrato_mutuario_map (contrato_id PRIMARY KEY, mutuario_id INTEGER, score REAL, method TEXT)\n')
    f.write('BEGIN TRANSACTION;\n')
    f.write('CREATE TABLE IF NOT EXISTS contrato_mutuario_map (contrato_id INTEGER PRIMARY KEY, mutuario_id INTEGER, score REAL, method TEXT);\n')
    for contrato_id, mutuario_id, score, method in rows:
        # Use parameter-like formatting carefully for readability; actual execution uses sqlite3
        stmt = "INSERT OR REPLACE INTO contrato_mutuario_map (contrato_id, mutuario_id, score, method) VALUES (%d, %d, %s, '%s');\n" % (contrato_id, mutuario_id, repr(score), str(method).replace("'", "''"))
        f.write(stmt)
    f.write('COMMIT;\n')

print('WROTE preview:', PREVIEW)
print('WROTE sql:', SQL_OUT)
print('ROWS TO APPLY:', len(rows))

if apply_mode:
    if not os.path.exists(DB):
        print('DB file not found:', DB)
        sys.exit(1)
    print('Applying SQL to DB (db.sqlite3) — creating mapping table and inserting rows')
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # read sql and execute
    with open(SQL_OUT, 'r', encoding='utf-8') as f:
        sql = f.read()
    try:
        conn.executescript(sql)
        conn.commit()
        print('APPLIED OK')
    except Exception as e:
        print('SQL apply error:', e)
    finally:
        conn.close()
else:
    print('Dry-run only. To apply, re-run with --apply')
