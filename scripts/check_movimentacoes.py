import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Movimentacao

total = Movimentacao.objects.count()
com_valor = Movimentacao.objects.exclude(valor=0.00).count()
com_data = Movimentacao.objects.exclude(data__isnull=True).count()
com_ambos = Movimentacao.objects.exclude(valor=0.00).exclude(data__isnull=True).count()

print(f"Total movimentações: {total}")
print(f"Com valor > 0: {com_valor}")
print(f"Com data not None: {com_data}")
print(f"Com valor > 0 E data not None: {com_ambos}")

# Amostra
print("\nPrimeiras 5 movimentações:")
for m in Movimentacao.objects.all()[:5]:
    print(f"  {m.codigo} - valor={m.valor} - data={m.data} - tipo={m.tipo}")

print("\nMovimentações com valor > 0:")
for m in Movimentacao.objects.exclude(valor=0.00)[:5]:
    print(f"  {m.codigo} - valor={m.valor} - data={m.data} - tipo={m.tipo}")
