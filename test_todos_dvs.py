"""
Testa todos os DVs possíveis (0-9) para matrícula 000044
Envia para CEF e vê qual funciona
"""
import os
import sys
import django

sys.path.append(r'C:\Users\fabri\cofluhab\cofluhab')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.ficha_generators import gerar_lote_fh1_separado
from datetime import datetime

# Busca um contrato para testar
contratos = Contrato.objects.all()[:1]
if not contratos:
    print("❌ Nenhum contrato encontrado no banco")
    sys.exit(1)

print("🧪 TESTE DE DVs PARA MATRÍCULA 000044")
print("="*70)
print(f"📝 Testando com contrato: {contratos[0].codigo}")
print()

# Testa cada DV possível
for dv in range(10):
    matricula_teste = f"00004{dv}"  # 6 dígitos: 000044 + DV
    print(f"\n🔍 Testando matrícula: {matricula_teste}")
    
    try:
        resultado = gerar_lote_fh1_separado(
            contratos=list(contratos),
            matricula='00004',  # Passa sem DV
            numero_lote='001'
        )
        
        # Mostra o que foi gerado
        if resultado['total_fichas'] > 0:
            header = resultado['header_conteudo']
            dados = resultado['dados_conteudo'].split('\n')[0] if resultado['dados_conteudo'] else ''
            
            print(f"   ✅ Header gerado (primeiro 30 chars): {header[:30]}")
            print(f"   ✅ Posição 3-8 (Matrícula+DV): {header[2:8]}")
            
            if len(dados) > 8:
                print(f"   ✅ Dados posição 3-8: {dados[2:8]}")
        else:
            print(f"   ⚠️ Nenhuma ficha gerada")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

print("\n" + "="*70)
print("TESTE CONCLUÍDO")
print("Agora teste cada matrícula no portal e veja qual passa!")
