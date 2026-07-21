import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','cofluhab.settings')
django.setup()
from principal.models import ConjuntoHabitacional, Mutuario, Endereco, Movimentacao
print('Counts:', ConjuntoHabitacional.objects.count(), Mutuario.objects.count(), Endereco.objects.count(), Movimentacao.objects.count())
