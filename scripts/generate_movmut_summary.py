import os
import csv
from datetime import datetime

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cofluhab.settings")

django.setup()

from principal.models import Contrato, ParcelaContrato  # noqa: E402

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "exports", "movmut_import_summary.csv")
OUTPUT = os.path.abspath(OUTPUT)

# Basic counts
contrato_count = Contrato.objects.count()
parcela_count = ParcelaContrato.objects.count()

# Date range (due dates and payment dates)
qs = ParcelaContrato.objects.exclude(dtvenc__isnull=True)
min_venc = qs.order_by("dtvenc").values_list("dtvenc", flat=True).first()
max_venc = qs.order_by("-dtvenc").values_list("dtvenc", flat=True).first()

qs_pg = ParcelaContrato.objects.exclude(dtpgto__isnull=True)
min_pg = qs_pg.order_by("dtpgto").values_list("dtpgto", flat=True).first()
max_pg = qs_pg.order_by("-dtpgto").values_list("dtpgto", flat=True).first()

# Installment number range
min_nmens = ParcelaContrato.objects.order_by("nmens").values_list("nmens", flat=True).first()
max_nmens = ParcelaContrato.objects.order_by("-nmens").values_list("nmens", flat=True).first()

# Sample 5 parcelas (codigo, nmens, dtvenc, dtpgto, amort, juros)
samples = list(
    ParcelaContrato.objects.select_related("contrato").order_by("contrato__codigo", "nmens")[:5]
)

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["generated_at", datetime.utcnow().isoformat()])
    w.writerow(["contrato_count", contrato_count])
    w.writerow(["parcela_count", parcela_count])
    w.writerow(["min_venc", min_venc])
    w.writerow(["max_venc", max_venc])
    w.writerow(["min_pg", min_pg])
    w.writerow(["max_pg", max_pg])
    w.writerow(["min_nmens", min_nmens])
    w.writerow(["max_nmens", max_nmens])
    w.writerow([])
    w.writerow(["sample_codigo", "nmens", "dtvenc", "dtpgto", "amort", "juros"])
    for s in samples:
        w.writerow([
            s.contrato.codigo,
            s.nmens,
            s.dtvenc,
            s.dtpgto,
            s.amort,
            s.juros,
        ])

print(f"Summary written to {OUTPUT}")
