import os, sys, csv
# ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
import django
django.setup()
from principal.models import Movimentacao

EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)

OUT = os.path.join(EXPORT_DIR, 'movimentacoes_unmatched_rich.csv')
LIMIT = 200

qs = Movimentacao.objects.filter(mutuario_fk__isnull=True).order_by('id')[:LIMIT]

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id','codigo','codimovel','conjunto','tipo','data','valor','descricao'])
    for m in qs:
        d = m.data.isoformat() if m.data else ''
        writer.writerow([m.id, m.codigo, m.codimovel or '', m.conjunto or '', m.tipo or '', d, str(m.valor) if m.valor is not None else '', m.descricao or ''])

print('Wrote', OUT, 'rows=', len(qs))
