import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario

# Busca contrato 6001
contrato = Contrato.objects.filter(codigo='6001').first()

if contrato:
    print(f"✅ Contrato encontrado: {contrato.codigo}")
    print(f"   Conjunto: {contrato.conjunto}")
    
    # Busca mutuário do conjunto
    mutuario = Mutuario.objects.filter(conjunto=contrato.conjunto).first()
    
    if mutuario:
        print(f"\n✅ Mutuário encontrado:")
        print(f"   Nome: {mutuario.nome}")
        print(f"   CPF: {mutuario.cpf}")
        print(f"   Cidade: {mutuario.cidade}")
        print(f"   UF: {mutuario.uf}")
    else:
        print(f"\n❌ PROBLEMA: Nenhum mutuário encontrado para conjunto {contrato.conjunto}")
        
        # Verifica se existem mutuários no banco
        total_mutuarios = Mutuario.objects.count()
        print(f"   Total de mutuários no sistema: {total_mutuarios}")
        
        if total_mutuarios > 0:
            primeiro = Mutuario.objects.first()
            print(f"   Primeiro mutuário: Conjunto {primeiro.conjunto}, Nome: {primeiro.nome}")
else:
    print("❌ Contrato 6001 não encontrado!")
    
    # Verifica contratos disponíveis
    primeiro_contrato = Contrato.objects.first()
    if primeiro_contrato:
        print(f"   Primeiro contrato no sistema: {primeiro_contrato.codigo}")
