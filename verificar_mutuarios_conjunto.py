import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario, Contrato

conjunto = '010'

qtd_mutuarios = Mutuario.objects.filter(conjunto=conjunto).count()
qtd_contratos = Contrato.objects.filter(conjunto=conjunto).count()

print(f"\n=== CONJUNTO {conjunto} ===")
print(f"Mutuários no banco: {qtd_mutuarios}")
print(f"Contratos no banco: {qtd_contratos}")
print(f"Diferença: {qtd_contratos - qtd_mutuarios}")

# Verificar quantos mutuários existem no arquivo TXT
txt_path = r'C:\Users\fabri\cofluhab\dados_antigos\acerto_cadmut\Mutuario.txt'
contador = 0
with open(txt_path, 'r', encoding='latin-1') as f:
    next(f)  # Pular cabeçalho
    for linha in f:
        campos = linha.strip().split('\t')
        if len(campos) >= 2:
            conjunto_txt = campos[0].strip()
            # 000442 = conjunto 010
            if conjunto_txt == '000442':
                contador += 1

print(f"Mutuários no Mutuario.txt (conjunto 000442): {contador}")
print(f"Diferença TXT vs Banco: {contador - qtd_mutuarios}")
