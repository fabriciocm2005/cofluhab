"""
Script de teste para verificar conexão com Chrome via remote debugging
"""

import socket
import sys

print("\n" + "="*60)
print("TESTE DE CONEXÃO - CHROME REMOTE DEBUGGING")
print("="*60)

# 1. Verificar porta 9222
print("\n1️⃣ Verificando se porta 9222 está acessível...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
result = sock.connect_ex(('127.0.0.1', 9222))
sock.close()

if result == 0:
    print("   ✅ Porta 9222 está ACESSÍVEL")
else:
    print("   ❌ Porta 9222 NÃO está acessível")
    print("\n   Execute no PowerShell:")
    print('   Start-Process "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" -ArgumentList "--remote-debugging-port=9222 --user-data-dir=C:\\temp\\chrome_debug_profile"')
    sys.exit(1)

# 2. Tentar conectar com Selenium
print("\n2️⃣ Tentando conectar Selenium ao Chrome...")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    print("   ✅ Selenium CONECTADO ao Chrome!")
    print(f"   📍 URL atual: {driver.current_url}")
    print(f"   📄 Título: {driver.title}")
    
    # Testar navegação
    print("\n3️⃣ Testando navegação para SIWFC...")
    driver.get("https://www.siwfc.caixa.gov.br/documentos")
    
    import time
    time.sleep(3)
    
    print(f"   📍 Nova URL: {driver.current_url}")
    print(f"   📄 Novo título: {driver.title}")
    
    print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("="*60)
    print("\nO Selenium está funcionando corretamente.")
    print("Agora você pode usar o envio automático no sistema Django.\n")
    
    input("Pressione ENTER para fechar o navegador de teste...")
    driver.quit()
    
except Exception as e:
    print(f"   ❌ ERRO ao conectar: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*60)
    sys.exit(1)
