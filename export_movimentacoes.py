import os
import django
import csv
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import ConjuntoHabitacional, Mutuario, Endereco, Movimentacao

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
CSV_PATH = os.path.join(LOG_DIR, 'movimentacao_export.csv')
LOG_PATH = os.path.join(LOG_DIR, 'movimentacao_import.log')


def export_movimentacoes(limit=None):
    qs = Movimentacao.objects.all().order_by('id')
    if limit:
        qs = qs[:limit]

    total = qs.count()

    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(['id', 'codigo', 'codimovel', 'conjunto', 'tipo', 'data', 'valor', 'descricao'])
        for m in qs:
            writer.writerow([
                m.id,
                m.codigo,
                m.codimovel,
                m.conjunto,
                m.tipo,
                m.data.isoformat() if m.data else '',
                f"{m.valor}",
                m.descricao,
            ])

    # build log
    counts = {
        'ConjuntoHabitacional': ConjuntoHabitacional.objects.count(),
        'Mutuario': Mutuario.objects.count(),
        'Endereco': Endereco.objects.count(),
        'Movimentacao_exported': total,
        'Movimentacao_in_db': Movimentacao.objects.count(),
    }

    with open(LOG_PATH, 'w', encoding='utf-8') as flog:
        flog.write(f"Export run: {datetime.utcnow().isoformat()}Z\n")
        for k, v in counts.items():
            flog.write(f"{k}: {v}\n")
        flog.write('\n')
        flog.write('Note: CSV path: ' + CSV_PATH + '\n')

    print('Export completed:')
    for k, v in counts.items():
        print(f" - {k}: {v}")
    print('CSV ->', CSV_PATH)
    print('Log ->', LOG_PATH)


if __name__ == '__main__':
    export_movimentacoes()
