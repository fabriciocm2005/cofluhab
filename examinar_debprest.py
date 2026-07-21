#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Examinar estrutura do DEBPREST.DBF para entender cálculo correto de débito
"""

from dbfread import DBF
import sys

print("="*80)
print("DEBPREST.DBF - Débito de Prestação")
print("="*80)

try:
    db = DBF('dados_antigos/DEBPREST.DBF', encoding='latin1')
    
    print("\nCAMPOS:")
    print("-" * 80)
    print(f"Total de campos: {len(db.field_names)}")
    print(f"Campos: {', '.join(db.field_names)}")
    
    print("\nPRIMEIROS 5 REGISTROS:")
    print("-" * 80)
    
    for i, rec in enumerate(db):
        if i >= 5:
            break
        print(f"\nRegistro {i+1}:")
        for key, value in rec.items():
            print(f"  {key:15s}: {value}")
    
    # Procurar registro do contrato 004062 que o usuário mencionou
    print("\n" + "="*80)
    print("PROCURANDO CONTRATO 004062:")
    print("="*80)
    
    db2 = DBF('dados_antigos/DEBPREST.DBF', encoding='latin1')
    found = False
    for rec in db2:
        # Procurar campo que contenha código de contrato
        for key, value in rec.items():
            if value and str(value).strip() in ['004062', '4062']:
                print(f"\nEncontrado! Registro completo:")
                for k, v in rec.items():
                    print(f"  {k:15s}: {v}")
                found = True
                break
        if found:
            break
    
    if not found:
        print("Contrato 004062 não encontrado nesta tabela")
        
    # Total de registros
    db3 = DBF('dados_antigos/DEBPREST.DBF', encoding='latin1')
    total = sum(1 for _ in db3)
    print(f"\nTotal de registros: {total}")
    
except Exception as e:
    print(f"ERRO ao ler DEBPREST.DBF: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("PRESTAC.DBF - Prestações")
print("="*80)

try:
    db = DBF('dados_antigos/PRESTAC.DBF', encoding='latin1')
    
    print("\nCAMPOS:")
    print("-" * 80)
    print(f"Total de campos: {len(db.field_names)}")
    print(f"Campos: {', '.join(db.field_names)}")
    
    print("\nPRIMEIROS 3 REGISTROS:")
    print("-" * 80)
    
    for i, rec in enumerate(db):
        if i >= 3:
            break
        print(f"\nRegistro {i+1}:")
        for key, value in rec.items():
            print(f"  {key:15s}: {value}")
            
    # Total de registros
    db2 = DBF('dados_antigos/PRESTAC.DBF', encoding='latin1')
    total = sum(1 for _ in db2)
    print(f"\nTotal de registros: {total}")
    
except Exception as e:
    print(f"ERRO ao ler PRESTAC.DBF: {e}")

print("\n" + "="*80)
print("ATRASO.DBF - Prestações em Atraso")
print("="*80)

try:
    db = DBF('dados_antigos/ATRASO.DBF', encoding='latin1')
    
    print("\nCAMPOS:")
    print("-" * 80)
    print(f"Total de campos: {len(db.field_names)}")
    print(f"Campos: {', '.join(db.field_names)}")
    
    print("\nPRIMEIROS 3 REGISTROS:")
    print("-" * 80)
    
    for i, rec in enumerate(db):
        if i >= 3:
            break
        print(f"\nRegistro {i+1}:")
        for key, value in rec.items():
            print(f"  {key:15s}: {value}")
            
    # Total de registros
    db2 = DBF('dados_antigos/ATRASO.DBF', encoding='latin1')
    total = sum(1 for _ in db2)
    print(f"\nTotal de registros: {total}")
    
except Exception as e:
    print(f"ERRO ao ler ATRASO.DBF: {e}")
