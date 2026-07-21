"""
Script para normalizar códigos de contratos
Remove zeros à esquerda de códigos numéricos
"""
import os
import sys
import django
import sqlite3

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato

print("=" * 80)
print("NORMALIZANDO CÓDIGOS DE CONTRATOS")
print("=" * 80)

# Buscar todos os contratos
contratos = Contrato.objects.all()
print(f"Total de contratos: {contratos.count()}")

atualizados = 0
removidos = 0

for contrato in contratos:
    codigo_original = contrato.codigo
    
    # Tentar converter para número e remover zeros à esquerda
    try:
        # Se é numérico, normalizar
        if codigo_original.isdigit():
            codigo_normalizado = str(int(codigo_original))
            
            if codigo_normalizado != codigo_original:
                # Verificar se já existe outro contrato com o código normalizado
                outro = Contrato.objects.filter(codigo=codigo_normalizado).exclude(id=contrato.id).first()
                
                if outro:
                    print(f"⚠️  Duplicata encontrada: '{codigo_original}' → '{codigo_normalizado}'")
                    print(f"   Contrato original (id={outro.id}): {codigo_normalizado}")
                    print(f"   Contrato duplicado (id={contrato.id}): {codigo_original}")
                    print(f"   ❌ REMOVENDO contrato duplicado id={contrato.id}")
                    contrato.delete()
                    removidos += 1
                else:
                    # Atualizar código
                    print(f"✏️  Normalizando: '{codigo_original}' → '{codigo_normalizado}'")
                    contrato.codigo = codigo_normalizado
                    contrato.save()
                    atualizados += 1
    except:
        pass

print(f"\n✅ Códigos normalizados: {atualizados}")
print(f"❌ Contratos duplicados removidos: {removidos}")
print("=" * 80)
