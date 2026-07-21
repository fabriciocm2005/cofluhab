import os
import sys
import django

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cofluhab.settings")
django.setup()

from principal.models import ParcelaContrato, Contrato

# Pega um contrato como exemplo: 5695 (ARGEMIRO)
contratos = Contrato.objects.filter(codigo='5695')
for c in contratos:
    print(f'Contrato: {c.codigo}')
    parcelas = ParcelaContrato.objects.filter(contrato=c).order_by('nmens')
    print(f'Total de parcelas: {parcelas.count()}')
    seg_total = sum(float(p.seguro or 0) for p in parcelas)
    print(f'Seguro total (parcelas somadas): {seg_total}')
    print('Primeiras 5 parcelas:')
    for p in parcelas[:5]:
        print(f'  Parcela {p.nmens}: venc={p.dtvenc}, seguro={p.seguro}, pgto={p.dtpgto}')
    if parcelas.count() > 5:
        print('  ...')
        print('Últimas 5 parcelas:')
        for p in parcelas[parcelas.count()-5:]:
            print(f'  Parcela {p.nmens}: venc={p.dtvenc}, seguro={p.seguro}, pgto={p.dtpgto}')
