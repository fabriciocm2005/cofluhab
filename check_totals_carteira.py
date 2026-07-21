import os
from datetime import date
from decimal import Decimal

import django
from django.db.models import Value, DecimalField, OuterRef, Subquery, Case, When, F, DateField, Sum
from django.db.models.expressions import ExpressionWrapper
from django.db.models.functions import Coalesce

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

DEC = DecimalField(max_digits=30, decimal_places=6)
ZERO = Value(Decimal('0'), output_field=DEC)

ultima_sddev_original = Subquery(
    ParcelaContrato.objects.filter(contrato=OuterRef('pk')).order_by('-nmens').values('sddev_original')[:1],
    output_field=DecimalField(max_digits=24, decimal_places=2),
)
ultima_sddev = Subquery(
    ParcelaContrato.objects.filter(contrato=OuterRef('pk')).order_by('-nmens').values('sddev')[:1],
    output_field=DecimalField(max_digits=24, decimal_places=2),
)
ultima_dt = Subquery(
    ParcelaContrato.objects.filter(contrato=OuterRef('pk')).order_by('-nmens').values('dtvenc')[:1],
    output_field=DateField(),
)


def total_convertido(qs):
    qs = qs.annotate(
        _saldo_raw=Coalesce(ultima_sddev_original, ultima_sddev, ZERO),
        _ultima_dt=ultima_dt,
    ).annotate(
        saldo_em_real=Case(
            When(_ultima_dt__isnull=True, then=F('_saldo_raw')),
            When(_ultima_dt__gte=date(1994, 7, 1), then=F('_saldo_raw')),
            When(
                _ultima_dt__gte=date(1993, 8, 1),
                then=ExpressionWrapper(F('_saldo_raw') / Value(Decimal('2750'), output_field=DEC), output_field=DEC),
            ),
            When(
                _ultima_dt__gte=date(1989, 1, 16),
                then=ExpressionWrapper(F('_saldo_raw') / Value(Decimal('2750000'), output_field=DEC), output_field=DEC),
            ),
            When(
                _ultima_dt__gte=date(1986, 2, 28),
                then=ExpressionWrapper(F('_saldo_raw') / Value(Decimal('2750000000'), output_field=DEC), output_field=DEC),
            ),
            default=ExpressionWrapper(
                F('_saldo_raw') / Value(Decimal('2750000000000'), output_field=DEC),
                output_field=DEC,
            ),
            output_field=DEC,
        )
    )
    return qs.aggregate(total=Coalesce(Sum('saldo_em_real'), ZERO)).get('total')


if __name__ == '__main__':
    total_geral = total_convertido(Contrato.objects.all())
    q10 = Contrato.objects.filter(conjunto__icontains='10')
    total_10 = total_convertido(q10)
    print(f'TOTAL_GERAL_R$: {total_geral}')
    print(f'TOTAL_CONJ10_R$: {total_10}')
    print(f'QTD_CONTRATOS_CONJ10: {q10.count()}')
