#!/usr/bin/env python
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.views import calcular_fcvs_residual_global

c = Contrato.objects.filter(codigo='1234').first()
if not c:
    c = Contrato.objects.filter(chave='1234').first()
if c:
    print('CONTRATO 1234 - BANCO DE DADOS:')
    print(f'  vlfinanc={c.vlfinanc}')
    print(f'  prestacao_inicial={c.prestacao_inicial}')
    print(f'  prazo={c.prazo}')
    print(f'  tx_juros={c.tx_juros}%')
    print(f'  sa={c.sa}')
    print()
    
    e, a, f = calcular_fcvs_residual_global(c.id)
    m1 = e[0]
    
    print('MES 1 - SIMULACAO (COMPLETO):')
    for k, v in sorted(m1.items()):
        print(f'  {k:20s} = {v}')
else:
    print('Contrato nao encontrado')
