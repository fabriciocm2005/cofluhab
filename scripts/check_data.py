#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Cliente, ConjuntoHabitacional, Mutuario, Endereco, Movimentacao, Contrato, ParcelaContrato

print("=== DADOS NO BANCO DE DADOS ===\n")
print(f"Cliente: {Cliente.objects.count():,}")
print(f"ConjuntoHabitacional: {ConjuntoHabitacional.objects.count():,}")
print(f"Mutuario: {Mutuario.objects.count():,}")
print(f"Endereco: {Endereco.objects.count():,}")
print(f"Movimentacao: {Movimentacao.objects.count():,}")
print(f"Contrato: {Contrato.objects.count():,}")
print(f"ParcelaContrato: {ParcelaContrato.objects.count():,}")

print("\n=== AMOSTRAS ===\n")
print("Mutuarios (primeiros 3):")
for m in Mutuario.objects.all()[:3]:
    print(f"  {m.codigo} - {m.nome} - Conjunto: {m.conjunto}")

print("\nMovimentacoes (primeiras 3):")
for mov in Movimentacao.objects.all()[:3]:
    print(f"  {mov.codigo} - {mov.tipo} - Valor: {mov.valor} - Data: {mov.data}")

print("\nContratos (primeiros 3):")
for c in Contrato.objects.all()[:3]:
    print(f"  ID={c.id} Codigo={c.codigo} Conjunto={c.conjunto}")
