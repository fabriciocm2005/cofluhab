import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Movimentacao

print("=== Teste Django ORM - Movimentações ===\n")

total = Movimentacao.objects.count()
print(f"Total: {total}")

if total > 0:
    print(f"\nPrimeiros 5:")
    for m in Movimentacao.objects.all()[:5]:
        print(f"  {m.codigo} - {m.data} - {m.tipo} - {m.valor}")
    
    print(f"\nÚltimos 5 (order_by -data):")
    for m in Movimentacao.objects.all().order_by('-data')[:5]:
        print(f"  {m.codigo} - {m.data} - {m.tipo} - {m.valor}")
else:
    print("Nenhum registro encontrado!")
