import os, glob, csv, time
from decimal import Decimal
# similar parsing helpers but no DB writes
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH_GLOB = os.path.join(ROOT, 'dados_antigos', 'MOVMUT*.DBF')
EXPORT_DIR = os.path.join(ROOT, 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)

try:
    from dbfread import DBF
except Exception as e:
    print('dbfread missing', e)
    raise

import re

def clean_bytes_to_text(b):
    if b is None:
        return ''
    if isinstance(b, str):
        return b.strip()
    if not isinstance(b, (bytes, bytearray)):
        return str(b).strip()
    s = b.decode('latin-1', 'ignore')
    s = ''.join(ch for ch in s if ord(ch) >= 32)
    return s.strip()

def parse_decimal_field(v):
    if v is None:
        return None
    try:
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
    except Exception:
        pass
    s = clean_bytes_to_text(v)
    if s == '':
        return None
    s2 = s.replace('\x00','').replace('\x10','').replace(',','.')
    s3 = re.sub(r'[^0-9.\-]', '', s2)
    if s3 in ('', '.', '-'): return None
    try:
        return Decimal(s3)
    except Exception:
        m = re.search(r'-?[0-9]+(?:\.[0-9]+)?', s3)
        return Decimal(m.group(0)) if m else None

def parse_int_field(v):
    if v is None: return None
    if isinstance(v, int): return v
    s = clean_bytes_to_text(v)
    if s=='': return None
    try:
        return int(s)
    except Exception:
        m = re.search(r'-?[0-9]+', s)
        return int(m.group(0)) if m else None

def parse_date_field(v):
    import datetime
    if v is None: return None
    if isinstance(v, datetime.date): return v
    s = clean_bytes_to_text(v)
    if s=='': return None
    for fmt in ('%Y-%m-%d','%d/%m/%Y','%Y%m%d'):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            pass
    m = re.search(r'(\d{4}).?(\d{1,2}).?(\d{1,2})', s)
    if m:
        y,mo,d = m.groups()
        try:
            return datetime.date(int(y),int(mo),int(d))
        except Exception:
            return None
    return None

files = sorted(glob.glob(DB_PATH_GLOB))
summary = []
for path in files:
    print('Processing', path)
    try:
        table = DBF(path, encoding='latin-1', raw=True)
    except Exception as e:
        print('open error', e)
        summary.append((path, 0, 'open-error'))
        continue
    cnt = 0
    sample_rows = []
    for rec in table:
        cnt += 1
        if cnt <= 20:
            codigo = clean_bytes_to_text(rec.get('CODIGO') or rec.get('codigo'))
            conj = clean_bytes_to_text(rec.get('CONJ') or rec.get('conj'))
            nmens = parse_int_field(rec.get('NMENS') or rec.get('nmens'))
            dtvenc = parse_date_field(rec.get('DTVENC') or rec.get('dtvenc'))
            juros = parse_decimal_field(rec.get('JUROS') or rec.get('juros'))
            amort = parse_decimal_field(rec.get('AMORT') or rec.get('amort'))
            vlaut = parse_decimal_field(rec.get('VLAUTENT') or rec.get('vlautent'))
            sample_rows.append((codigo, conj, nmens, str(dtvenc) if dtvenc else '', str(juros) if juros else '', str(amort) if amort else '', str(vlaut) if vlaut else ''))
    summary.append((path, cnt, len(sample_rows)))
    # write sample per file
    out = os.path.join(EXPORT_DIR, os.path.basename(path) + '.sample.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['codigo','conj','nmens','dtvenc','juros','amort','vlautent'])
        w.writerows(sample_rows)
    print('WROTE sample', out)

# write overall summary
sumf = os.path.join(EXPORT_DIR, 'movmut_dryrun_summary.csv')
with open(sumf, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['file','rows','sample_rows'])
    for s in summary:
        w.writerow(s)
print('WROTE', sumf)
