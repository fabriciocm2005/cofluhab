import os, sys, glob, csv, shutil, time
from decimal import Decimal, InvalidOperation

# ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
import django
django.setup()
from principal.models import Contrato, ParcelaContrato
from django.db import transaction

from dbfread import DBF

DB_PATH_GLOB = os.path.join(ROOT, 'dados_antigos', 'MOVMUT*.DBF')
DB_FILES = sorted(glob.glob(DB_PATH_GLOB))
EXPORT_DIR = os.path.join(ROOT, 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)

# backup DB
DBFILE = os.path.join(ROOT, 'db.sqlite3')
if os.path.exists(DBFILE):
    bak = DBFILE + '.movmut.bak-' + time.strftime('%Y%m%d-%H%M%S')
    shutil.copy2(DBFILE, bak)
    print('Database backup created:', bak)

# helpers
CONTROL_CHARS = bytes(range(0, 32))

def clean_bytes_to_text(b):
    if b is None:
        return ''
    if isinstance(b, str):
        return b.strip()
    if not isinstance(b, (bytes, bytearray)):
        return str(b).strip()
    # decode latin-1 and remove control chars
    s = b.decode('latin-1', 'ignore')
    # remove non-printables
    s = ''.join(ch for ch in s if ord(ch) >= 32)
    return s.strip()


def parse_decimal_field(v):
    if v is None:
        return None
    # if already numeric type
    try:
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
    except Exception:
        pass
    # raw bytes or string
    s = clean_bytes_to_text(v)
    if s == '':
        return None
    # replace comma decimal separators
    s2 = s.replace('\x00', '').replace('\x10', '').replace(',', '.')
    # remove any currency signs or letters
    import re
    s3 = re.sub(r"[^0-9.\-]", "", s2)
    if s3 in ('', '.', '-'): 
        return None
    try:
        return Decimal(s3)
    except InvalidOperation:
        # try extracting numbers
        m = re.search(r"-?[0-9]+(?:\.[0-9]+)?", s3)
        if m:
            try:
                return Decimal(m.group(0))
            except InvalidOperation:
                return None
        return None


def parse_int_field(v):
    if v is None:
        return None
    if isinstance(v, int):
        return v
    s = clean_bytes_to_text(v)
    if s == '':
        return None
    try:
        return int(s)
    except Exception:
        import re
        m = re.search(r"-?[0-9]+", s)
        if m:
            return int(m.group(0))
        return None


def parse_date_field(v):
    # dbfread may already return date objects
    if v is None:
        return None
    import datetime
    if isinstance(v, datetime.date):
        return v
    s = clean_bytes_to_text(v)
    if s == '':
        return None
    # try ISO
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y%m%d'):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            pass
    # try to extract yyyy, mm, dd groups
    import re
    m = re.search(r'(\d{4}).?(\d{1,2}).?(\d{1,2})', s)
    if m:
        y, mo, d = m.groups()
        try:
            return datetime.date(int(y), int(mo), int(d))
        except Exception:
            return None
    return None

# iterate DBF files
summary = []
errors = []

# preload existing contratos into memory to avoid repeated DB queries
from django.db import connection
contratos_cache = {}
try:
    for c in Contrato.objects.all():
        contratos_cache[(c.codigo, (c.conjunto or '').strip())] = c
except Exception:
    # if loading fails (very large table), keep cache empty and fall back to DB get/create
    contratos_cache = {}

for path in DB_FILES:
    print('\nProcessing', path)
    try:
        table = DBF(path, encoding='latin-1', raw=True)
    except Exception as e:
        print('Failed to open', path, '->', e)
        errors.append((path, 'open', str(e)))
        continue

    processed = 0
    created_contratos = 0
    created_parcelas = 0

    # transaction per file for safety
    with transaction.atomic():
        iterator = iter(table)
        while True:
            try:
                rec = next(iterator)
            except StopIteration:
                break
            except Exception as e:
                # parser error when reading a record; log and continue
                errors.append((path, 'iter-error', str(e)))
                processed += 1
                continue
            processed += 1
            try:
                # fields we expect (case-insensitive)
                codigo = clean_bytes_to_text(rec.get('CODIGO') or rec.get('codigo'))
                conj = clean_bytes_to_text(rec.get('CONJ') or rec.get('conj'))
                nmens = parse_int_field(rec.get('NMENS') or rec.get('nmens'))
                dtvenc = parse_date_field(rec.get('DTVENC') or rec.get('dtvenc'))
                dtpgto = parse_date_field(rec.get('DTPGTO') or rec.get('dtpgto'))

                juros = parse_decimal_field(rec.get('JUROS') or rec.get('juros'))
                amort = parse_decimal_field(rec.get('AMORT') or rec.get('amort'))
                seguro = parse_decimal_field(rec.get('SEGURO') or rec.get('seguro'))
                tca = parse_decimal_field(rec.get('TCA') or rec.get('tca'))
                fcvs = parse_decimal_field(rec.get('FCVS') or rec.get('fcvs'))
                em = parse_decimal_field(rec.get('EM') or rec.get('em'))
                rp = parse_decimal_field(rec.get('RP') or rec.get('rp'))
                cm = parse_decimal_field(rec.get('CM') or rec.get('cm'))
                sddev = parse_decimal_field(rec.get('SDDEV') or rec.get('sddev'))
                vlautent = parse_decimal_field(rec.get('VLAUTENT') or rec.get('vlautent'))
                seq = parse_int_field(rec.get('SEQ') or rec.get('seq'))
                lote = clean_bytes_to_text(rec.get('LOTE') or rec.get('lote'))
                sinal = clean_bytes_to_text(rec.get('SINAL') or rec.get('sinal'))
                chave = clean_bytes_to_text(rec.get('CHAVE') or rec.get('chave'))
                conversor = None
                try:
                    convv = rec.get('CONVERSOR') or rec.get('conversor')
                    if convv is not None:
                        conversor = float(clean_bytes_to_text(convv) or 0)
                except Exception:
                    conversor = None

                if not codigo:
                    errors.append((path, processed, 'missing codigo', rec))
                    continue

                key = (codigo, (conj or '').strip())
                contrato = contratos_cache.get(key)
                if contrato is None:
                    # create new contrato and cache it
                    contrato = Contrato(codigo=codigo, conjunto=conj or '')
                    try:
                        contrato.chave = chave
                        contrato.lote = lote
                        contrato.sinal = sinal
                        contrato.conversor = conversor
                        contrato.save()
                        created_contratos += 1
                    except Exception as e:
                        errors.append((path, processed, 'contrato-create:' + str(e)))
                        continue
                    contratos_cache[key] = contrato

                # parcela unique by contrato + nmens
                if nmens is None:
                    # store anyway but with nmens -1 to avoid unique constraint issues
                    nmens_key = -1
                else:
                    nmens_key = nmens

                parcela, pcreated = ParcelaContrato.objects.update_or_create(
                    contrato=contrato,
                    nmens=nmens_key,
                    defaults={
                        'dtvenc': dtvenc,
                        'dtpgto': dtpgto,
                        'juros': juros,
                        'amort': amort,
                        'seguro': seguro,
                        'tca': tca,
                        'fcvs': fcvs,
                        'em': em,
                        'rp': rp,
                        'cm': cm,
                        'sddev': sddev,
                        'vlautent': vlautent,
                        'seq': seq,
                        'lote': lote,
                        'sinal': sinal,
                        'chave': chave,
                        'conversor': conversor,
                    }
                )
                if pcreated:
                    created_parcelas += 1

            except Exception as e:
                errors.append((path, processed, str(e)))

    print('Processed', processed, 'rows -> new contratos', created_contratos, 'new parcelas', created_parcelas)
    summary.append((path, processed, created_contratos, created_parcelas))

# write error log
errfile = os.path.join(EXPORT_DIR, 'movmut_import_errors.csv')
if errors:
    with open(errfile, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['file','row','error','raw'])
        for e in errors:
            w.writerow([e[0], e[1], e[2], str(e[3]) if len(e) > 3 else ''])
    print('Wrote errors to', errfile)

# summary CSV
sumfile = os.path.join(EXPORT_DIR, 'movmut_import_summary.csv')
with open(sumfile, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['file','rows','new_contratos','new_parcelas'])
    for s in summary:
        w.writerow(s)
print('\nImport summary written to', sumfile)
print('Done')
