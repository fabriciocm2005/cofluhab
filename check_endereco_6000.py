import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario

# Verificar mutuário 6000
m = Mutuario.objects.filter(codigo='6000').first()

if m:
    print(f"Mutuário: {m.nome}")
    print(f"CPF: {m.cpf}")
    print(f"Código: {m.codigo}")
    print(f"Tem endereco_fk: {m.endereco_fk is not None}")
    if m.endereco_fk:
        print(f"Endereço: {m.endereco_fk.endereco}, {m.endereco_fk.numero}")
        print(f"Cidade: {m.endereco_fk.cidade}")
    else:
        print("SEM ENDEREÇO VINCULADO")
else:
    print("Mutuário 6000 não encontrado!")
