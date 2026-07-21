import os
import sys
import django

os.chdir(r'C:\Users\fabri\cofluhab\cofluhab')
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

print("="*80)
print("TESTE OPCAO 3 - VALIDACAO PREVENTIVA")
print("="*80)

from principal.models import Contrato
from principal.validators import validar_antes_exportar, pode_exportar

# Pegar primeiro contrato
contrato = Contrato.objects.first()
print(f"\nContrato testado: ID {contrato.id}, Codigo {contrato.codigo}")

# Executar validacao
validacao = validar_antes_exportar(contrato)

print(f"\n{'='*80}")
print("RESULTADO DA VALIDACAO")
print(f"{'='*80}")
print(f"Valido: {validacao['valido']}")
print(f"Total de problemas: {validacao['total_problemas']}")

# Erros
if validacao['erros']:
    print(f"\nERROS CRITICOS ({len(validacao['erros'])}):")
    for erro in validacao['erros']:
        print(f"  Campo: {erro['campo']}")
        print(f"  Mensagem: {erro['mensagem']}")
        print(f"  Sugestao: {erro['sugestao']}")
        print()

# Warnings
if validacao['warnings']:
    print(f"\nALERTAS ({len(validacao['warnings'])}):")
    for warning in validacao['warnings']:
        print(f"  Campo: {warning['campo']}")
        print(f"  Mensagem: {warning['mensagem']}")
        print(f"  Sugestao: {warning['sugestao']}")
        print()

# Info
if validacao['info']:
    print(f"\nINFORMACOES ({len(validacao['info'])}):")
    for info in validacao['info']:
        print(f"  Campo: {info['campo']}")
        print(f"  Mensagem: {info['mensagem']}")
        print()

# Pode exportar?
pode_exp, motivo = pode_exportar(contrato)
print(f"\n{'='*80}")
print(f"PODE EXPORTAR: {'SIM' if pode_exp else 'NAO'}")
if motivo:
    print(f"Motivo: {motivo}")
print(f"{'='*80}")

print("\nTESTE CONCLUIDO - OPCAO 3 FUNCIONANDO!")
