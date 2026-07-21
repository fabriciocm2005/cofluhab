"""
Atualiza dados dos conjuntos habitacionais
"""
import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import ConjuntoHabitacional

# Dados atualizados dos conjuntos
conjuntos_data = [
    {'conjunto': '001', 'nome': 'TIRADENTES', 'contrato': '001093269'},
    {'conjunto': '002', 'nome': 'SOLARES II', 'contrato': '001093269'},
    {'conjunto': '003', 'nome': 'OLARIA', 'contrato': '001452210'},
    {'conjunto': '004', 'nome': 'DOM BOSCO', 'contrato': '001307240'},
    {'conjunto': '005', 'nome': 'J DE BARRO', 'contrato': '001505241'},
    {'conjunto': '006', 'nome': 'J GUANABARA', 'contrato': '001093269'},
    {'conjunto': '008', 'nome': 'VALENCA I', 'contrato': '001093269'},
    {'conjunto': '009', 'nome': 'VALENCA II', 'contrato': '001093269'},
    {'conjunto': '010', 'nome': 'S STA PAULA', 'contrato': '001151034'},
    {'conjunto': '011', 'nome': 'MARAMBAIA', 'contrato': '001150020'},
    {'conjunto': '012', 'nome': 'PROGR CEMAC', 'contrato': '001093269'},
]

print("=" * 80)
print("ATUALIZANDO CONJUNTOS HABITACIONAIS")
print("=" * 80)

for data in conjuntos_data:
    conjunto, created = ConjuntoHabitacional.objects.update_or_create(
        conjunto=data['conjunto'],
        defaults={
            'nome': data['nome'],
            'contrato': data['contrato']
        }
    )
    
    if created:
        print(f"✅ Criado: {data['conjunto']} - {data['nome']}")
    else:
        print(f"♻️  Atualizado: {data['conjunto']} - {data['nome']}")

print("\n" + "=" * 80)
print("LISTAGEM FINAL DOS CONJUNTOS")
print("=" * 80)

from principal.models import Mutuario

for conj in ConjuntoHabitacional.objects.all().order_by('conjunto'):
    qtd_mutuarios = Mutuario.objects.filter(conjunto=conj.conjunto).count()
    print(f"{conj.conjunto} | {conj.nome:20s} | {conj.contrato} | {qtd_mutuarios} mutuários")

print("\n✅ CONJUNTOS ATUALIZADOS COM SUCESSO!")
