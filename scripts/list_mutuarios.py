import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','cofluhab.settings')
import django
django.setup()
from principal.models import Mutuario
qs = Mutuario.objects.all().order_by('codigo')[:20]
if not qs:
    print('No mutuarios found')
else:
    for m in qs:
        print(f"{m.codigo} | {m.nome} | {m.cpf}")
