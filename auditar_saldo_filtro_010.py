import os
from datetime import date
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

DATA_REAL = date(1994, 7, 1)


def converter(valor, dt):
    v = Decimal(str(valor or 0))
    if dt is None or dt >= date(1994, 7, 1):
        return v, Decimal('1')
    if dt >= date(1993, 8, 1):
        return v / Decimal('2750'), Decimal('2750')
    if dt >= date(1989, 1, 16):
        return v / Decimal('2750000'), Decimal('2750000')
    if dt >= date(1986, 2, 28):
        return v / Decimal('2750000000'), Decimal('2750000000')
    return v / Decimal('2750000000000'), Decimal('2750000000000')


def main():
    conjunto = '010'
    qs = Contrato.objects.filter(conjunto__icontains=conjunto)

    total_raw = Decimal('0')
    total_conv = Decimal('0')
    pre94_raw = Decimal('0')
    pre94_conv = Decimal('0')
    pos94_raw = Decimal('0')
    pos94_conv = Decimal('0')

    rows = []
    sem_parcela = 0
    sem_saldo = 0

    for c in qs:
        p = ParcelaContrato.objects.filter(contrato=c).order_by('-nmens').first()
        if not p:
            sem_parcela += 1
            continue
        saldo = p.sddev_original if p.sddev_original not in (None, 0) else p.sddev
        if saldo in (None, 0):
            sem_saldo += 1
            continue
        dt = p.dtvenc
        saldo_raw = Decimal(str(saldo))
        saldo_conv, fator = converter(saldo_raw, dt)

        total_raw += saldo_raw
        total_conv += saldo_conv

        if dt and dt < DATA_REAL:
            pre94_raw += saldo_raw
            pre94_conv += saldo_conv
        else:
            pos94_raw += saldo_raw
            pos94_conv += saldo_conv

        rows.append((saldo_conv, saldo_raw, c.codigo, c.conjunto, dt, fator))

    rows.sort(reverse=True, key=lambda x: x[0])

    print('CONJUNTO:', conjunto)
    print('QTD_CONTRATOS_QUERY:', qs.count())
    print('SEM_PARCELA:', sem_parcela)
    print('SEM_SALDO:', sem_saldo)
    print('TOTAL_RAW:', f'{total_raw:.2f}')
    print('TOTAL_CONVERTIDO:', f'{total_conv:.2f}')
    print('PRE94_RAW:', f'{pre94_raw:.2f}')
    print('PRE94_CONVERTIDO:', f'{pre94_conv:.2f}')
    print('POS94_RAW:', f'{pos94_raw:.2f}')
    print('POS94_CONVERTIDO:', f'{pos94_conv:.2f}')
    print('TOP20_CONVERTIDO:')
    for r in rows[:20]:
        print(f'  contrato={r[2]} conjunto={r[3]} dt={r[4]} fator={r[5]} raw={r[1]:.2f} conv={r[0]:.2f}')


if __name__ == '__main__':
    main()
