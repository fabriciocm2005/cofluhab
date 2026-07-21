import os
import django
from dbfread import DBF
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Movimentacao
from django.db import transaction

DBF_PATH = os.path.join(os.path.dirname(__file__), 'dados_antigos', 'MOVMUT.DBF')


def dec(v):
    if isinstance(v, bytes):
        return v.decode('latin-1', errors='ignore').strip()
    return v


num_re = re.compile(r"[-+]?[0-9]*[\,\.]?[0-9]+")


def parse_decimal(v):
    if v is None:
        return None
    s = dec(v)
    if s == '':
        return None
    m = num_re.search(s)
    if not m:
        return None
    s2 = m.group(0).replace(',', '.')
    try:
        return Decimal(s2)
    except (InvalidOperation, ValueError):
        return None


def parse_date(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    s = dec(v)
    s = s.strip()
    if not s:
        return None
    if len(s) == 8 and s.isdigit():
        try:
            return datetime.strptime(s, '%Y%m%d').date()
        except Exception:
            return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d%m%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


def importar_movimentacao(batch_size=500):
    registros = DBF(DBF_PATH, encoding='latin-1', raw=True, ignore_missing_memofile=True)
    processed = 0
    errors = 0
    batch = []

    def flush_batch(b):
        nonlocal processed, errors
        if not b:
            return
        with transaction.atomic():
            for codigo, codimovel, conjunto, defaults in b:
                try:
                    Movimentacao.objects.update_or_create(
                        codigo=codigo,
                        codimovel=codimovel,
                        conjunto=conjunto,
                        defaults=defaults,
                    )
                    processed += 1
                except Exception as e:
                    errors += 1
                    print(f'ERROR importing movimentacao (codigo={codigo}): {e}')

    total_est = None
    # iterate and accumulate batch entries
    for i, registro in enumerate(registros, start=1):
        codigo = (dec(registro.get('CODIGO') or '')).strip()
        codimovel = (dec(registro.get('CODIMOVEL') or '')).strip()
        conjunto = (dec(registro.get('CONJUNTO') or '')).strip()

        tipo = dec(registro.get('TIPO') or '')
        data = parse_date(registro.get('DATA'))
        valor = parse_decimal(registro.get('VALOR'))
        if valor is None:
            valor = Decimal('0.00')
        descricao = dec(registro.get('DESCRICAO') or '')

        batch.append((codigo, codimovel, conjunto, {
            'tipo': tipo,
            'data': data,
            'valor': valor,
            'descricao': descricao,
        }))

        if len(batch) >= batch_size:
            flush_batch(batch)
            batch.clear()
            print(f'Processed {processed} records so far...')

    # flush remaining
    flush_batch(batch)

    print(f'Importação de movimentações concluída. processed={processed} errors={errors}')


if __name__ == '__main__':
    importar_movimentacao()
