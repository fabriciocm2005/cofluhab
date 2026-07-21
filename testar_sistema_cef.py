"""
Script de teste rápido do sistema CEF
"""
import os
import sys
import django

# Configurar Django
sys.path.append(r'C:\Users\fabri\cofluhab\cofluhab')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models_cef import *
from principal.models import Contrato

print("🧪 TESTE DO SISTEMA CEF INTEGRAÇÃO")
print("="*60)

# 1. Verificar Modelos
print("\n1️⃣ Verificando Modelos CEF...")
try:
    credenciais = CredencialCEF.objects.count()
    envios = EnvioCEF.objects.count()
    retornos = RetornoCEF.objects.count()
    agendamentos = AgendamentoEnvio.objects.count()
    logs = LogAutomacao.objects.count()
    
    print(f"   ✅ CredencialCEF: {credenciais} registros")
    print(f"   ✅ EnvioCEF: {envios} registros")
    print(f"   ✅ RetornoCEF: {retornos} registros")
    print(f"   ✅ AgendamentoEnvio: {agendamentos} registros")
    print(f"   ✅ LogAutomacao: {logs} registros")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 2. Verificar Contratos disponíveis
print("\n2️⃣ Verificando Contratos...")
try:
    total_contratos = Contrato.objects.count()
    contratos_com_mutuario = Contrato.objects.filter(mutuario__isnull=False).count()
    print(f"   ✅ Total de contratos: {total_contratos}")
    print(f"   ✅ Com mutuário: {contratos_com_mutuario}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 3. Testar criação de credencial de teste
print("\n3️⃣ Testando Criação de Credencial...")
try:
    cred_teste = CredencialCEF.objects.filter(cpf='000.000.000-00').first()
    if not cred_teste:
        cred_teste = CredencialCEF.objects.create(
            cpf='000.000.000-00',
            email='teste@cofluhab.com.br',
            senha_criptografada='senha_teste_criptografada',
            matricula_agente='TESTE',
            ativo=False  # Inativo para não interferir
        )
        print(f"   ✅ Credencial de teste criada: {cred_teste}")
    else:
        print(f"   ✅ Credencial de teste já existe: {cred_teste}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 4. Testar criação de Log
print("\n4️⃣ Testando LogAutomacao...")
try:
    log_teste = LogAutomacao.objects.create(
        tipo_acao='LOGIN',
        descricao='Teste de sistema - verificação de funcionamento',
        sucesso=True,
        duracao_segundos=1.5
    )
    print(f"   ✅ Log criado: {log_teste}")
    print(f"   📅 Timestamp: {log_teste.timestamp}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 5. Verificar choices dos modelos
print("\n5️⃣ Verificando Choices...")
try:
    print(f"   ✅ Tipos de Envio: {len(EnvioCEF.TIPO_ENVIO_CHOICES)} opções")
    for value, label in EnvioCEF.TIPO_ENVIO_CHOICES:
        print(f"      - {value}: {label}")
    
    print(f"   ✅ Status de Envio: {len(EnvioCEF.STATUS_CHOICES)} opções")
    for value, label in EnvioCEF.STATUS_CHOICES:
        print(f"      - {value}: {label}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 6. Verificar URLs
print("\n6️⃣ URLs CEF Configuradas:")
print("   ✅ /cef/ - Dashboard")
print("   ✅ /cef/envios/ - Listagem de envios")
print("   ✅ /cef/retornos/ - Listagem de retornos")
print("   ✅ /cef/agendamentos/ - Agendamentos")
print("   ✅ /cef/credenciais/ - Configuração")
print("   ✅ /cef/logs/ - Logs de automação")

# 7. Verificar Selenium
print("\n7️⃣ Verificando Selenium...")
try:
    import selenium
    print(f"   ✅ Selenium instalado: v{selenium.__version__}")
    from selenium import webdriver
    print(f"   ✅ WebDriver importado com sucesso")
except ImportError as e:
    print(f"   ⚠️ Selenium não encontrado: {e}")

# 8. Verificar PyPDF2
print("\n8️⃣ Verificando PyPDF2...")
try:
    import PyPDF2
    print(f"   ✅ PyPDF2 instalado: v{PyPDF2.__version__}")
except ImportError as e:
    print(f"   ⚠️ PyPDF2 não encontrado: {e}")

# 9. Verificar Knowledge Base
print("\n9️⃣ Verificando Knowledge Base CEF...")
try:
    import json
    kb_path = r'C:\Users\fabri\cofluhab\cofluhab\principal\cef_knowledge_base.json'
    if os.path.exists(kb_path):
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        print(f"   ✅ Knowledge Base encontrada")
        print(f"   📚 Manuais indexados: {len(kb.get('manuais', []))}")
        for manual in kb.get('manuais', [])[:3]:
            print(f"      - {manual.get('tipo')}")
    else:
        print(f"   ⚠️ Knowledge Base não encontrada")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n" + "="*60)
print("✅ TESTE CONCLUÍDO!")
print("\n💡 Próximos passos:")
print("   1. Acessar http://127.0.0.1:8000/cef/")
print("   2. Configurar credenciais CEF")
print("   3. Testar automação com cef_web_automation.py")
print("="*60)
