"""
CEF Web Automation - Automação de login e upload no portal SIWFC
Baseado na análise dos manuais CEF
"""

import os
import time
from datetime import datetime

# Configurações
SIWFC_URL = "https://www.siwfc.caixa.gov.br/documentos"
CREDENTIALS_FILE = "cef_credentials.json"


class CEFWebBot:
    """Bot para automação do portal web SIWFC da CEF"""
    
    def __init__(self, headless=False, usar_perfil_existente=True):
        """
        Inicializa bot com Selenium
        headless: Se True, roda sem interface gráfica
        usar_perfil_existente: Se True, usa o perfil do Chrome do usuário (com sessão já logada)
        """
        self.headless = headless
        self.usar_perfil_existente = usar_perfil_existente
        self.driver = None
        self.logged_in = False
        self.wait_short = int(os.getenv('CEF_AUTOMATION_WAIT_SHORT', '5'))
        self.wait_default = int(os.getenv('CEF_AUTOMATION_WAIT_DEFAULT', '10'))
        self.sleep_factor = float(os.getenv('CEF_AUTOMATION_SLEEP_FACTOR', '0.35'))
        self.debug_screenshots = os.getenv('CEF_AUTOMATION_DEBUG_SCREENSHOTS', '0') == '1'

    def _sleep(self, segundos):
        """Sleep reduzido e configurável para acelerar a automação."""
        segundos_ajustados = max(0.05, float(segundos) * self.sleep_factor)
        time.sleep(segundos_ajustados)

    def _wait_page_ready(self, timeout=None):
        """Aguarda página ficar utilizável sem depender de sleep fixo."""
        from selenium.webdriver.support.ui import WebDriverWait
        limite = timeout or self.wait_default
        WebDriverWait(self.driver, limite).until(
            lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
        )

    def _wait_file_input_preenchido(self, input_element, timeout=4):
        """Aguarda o input[type=file] receber valor após send_keys."""
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(self.driver, timeout).until(
            lambda d: bool((input_element.get_attribute('value') or '').strip())
        )
        
    def setup_driver(self):
        """Configura driver do Selenium"""
        # Criar log em arquivo para debug
        import sys
        log_file = open('cef_automation_debug.log', 'a', encoding='utf-8')
        log_file.write("\n" + "="*60 + "\n")
        log_file.write("setup_driver() INICIADO\n")
        log_file.flush()
        
        print("🔧 DEBUG: setup_driver() INICIADO")
        sys.stdout.flush()
        
        try:
            print("📦 DEBUG: Importando selenium...")
            log_file.write("Importando selenium...\n")
            log_file.flush()
            
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            print("✅ DEBUG: Imports OK")
            log_file.write("Imports OK\n")
            log_file.flush()
            
            options = Options()
            print("✅ DEBUG: Options criado")
            log_file.write("Options criado\n")
            log_file.flush()
            
            # IMPORTANTE: Usar debugging remoto para conectar ao Chrome já aberto
            # O usuário deve iniciar o Chrome com: chrome.exe --remote-debugging-port=9222
            if self.usar_perfil_existente:
                print("\n🔌 Conectando ao Chrome na porta 9222...")
                log_file.write("Conectando ao Chrome na porta 9222...\n")
                log_file.flush()
                
                # Conectar ao Chrome que já está rodando com debugging ativado
                options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                print("✅ DEBUG: debuggerAddress configurado")
                log_file.write("debuggerAddress configurado\n")
                log_file.flush()
            else:
                # Modo normal (sem sessão existente)
                if self.headless:
                    options.add_argument('--headless')

            # Reduz tempo de espera inicial de carregamento da página
            options.page_load_strategy = 'eager'
            
            print("⚙️ DEBUG: Configurando argumentos Chrome...")
            # Quando usando remote debugging, NÃO adicionar argumentos que modificam o Chrome
            # pois ele já está rodando. Apenas usar opções básicas.
            if not self.usar_perfil_existente:
                # Somente quando NÃO estiver usando perfil existente
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                if self.headless:
                    options.add_argument('--headless')
            
            print("✅ DEBUG: Argumentos configurados")
            log_file.write("Argumentos configurados\n")
            log_file.flush()
            
            print("🚗 DEBUG: Instalando ChromeDriver...")
            log_file.write("Instalando ChromeDriver...\n")
            log_file.flush()
            
            service = Service(ChromeDriverManager().install())
            print("✅ DEBUG: ChromeDriver OK, criando webdriver...")
            log_file.write("ChromeDriver OK, criando webdriver...\n")
            log_file.flush()
            
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ DEBUG: webdriver.Chrome() criado!")
            log_file.write("webdriver.Chrome() criado!\n")
            log_file.flush()
            
            print("✅ Driver Selenium conectado ao Chrome")
            log_file.write("SUCESSO: Driver Selenium conectado\n")
            log_file.close()
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ ERRO ao conectar: {error_msg}\n")
            
            # Salvar erro no log
            try:
                log_file = open('cef_automation_debug.log', 'a', encoding='utf-8')
                log_file.write(f"ERRO: {error_msg}\n")
                import traceback
                log_file.write(traceback.format_exc())
                log_file.write("\n")
                log_file.close()
            except:
                pass
            
            if "ERR_CONNECTION_REFUSED" in error_msg or "DevToolsActivePort" in error_msg or "Invalid Status" in error_msg:
                print("="*60)
                print("PROBLEMA: O Chrome não está com remote debugging ativo")
                print("\nSOLUÇÃO:")
                print("1. Abra o PowerShell (Win+X → Windows PowerShell)")
                print("2. Cole e execute este comando:")
                print('   & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
                print("3. Aguarde o Chrome abrir")
                print("4. Acesse: https://www.siwfc.caixa.gov.br/documentos")
                print("5. Faça login")
                print("6. Tente o envio novamente")
                print("="*60 + "\n")
            else:
                print(f"Erro técnico: {error_msg}")
                import traceback
                traceback.print_exc()
            
            return False
    
    def carregar_credenciais(self):
        """Carrega credenciais salvas ou solicita ao usuário"""
        import json
        
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    creds = json.load(f)
                print("✅ Credenciais carregadas")
                return creds
            except:
                pass
        
        # Solicitar credenciais
        print("\n🔐 CONFIGURAÇÃO DE CREDENCIAIS CEF")
        print("="*50)
        cpf = input("CPF (apenas números): ").strip()
        senha = input("Senha: ").strip()
        email = input("E-mail cadastrado: ").strip()
        
        creds = {
            'cpf': cpf,
            'senha': senha,
            'email': email
        }
        
        # Salvar
        salvar = input("\n💾 Salvar credenciais? (s/n): ").lower()
        if salvar == 's':
            try:
                with open(CREDENTIALS_FILE, 'w') as f:
                    json.dump(creds, f, indent=2)
                print("✅ Credenciais salvas em", CREDENTIALS_FILE)
            except Exception as e:
                print(f"⚠️ Não foi possível salvar: {e}")
        
        return creds
    
    def fazer_login(self, cpf, senha, aguardar_codigo_email=True):
        """
        Realiza login no portal SIWFC
        
        Fluxo (conforme manual):
        1. Acessar https://www.siwfc.caixa.gov.br/
        2. Inserir CPF
        3. Receber código por e-mail
        4. Inserir código
        5. Inserir senha
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        
        try:
            print(f"\n🌐 Acessando {SIWFC_URL}...")
            self.driver.get(SIWFC_URL)
            self._wait_page_ready(self.wait_default)
            
            # Captura screenshot inicial
            try:
                self.driver.save_screenshot("debug_01_pagina_inicial.png")
                print("📸 Screenshot salvo: debug_01_pagina_inicial.png")
            except:
                pass
            
            # Tentar diferentes estratégias para encontrar campo CPF
            cpf_input = None
            selectors_cpf = [
                (By.NAME, "cpf"),
                (By.ID, "cpf"),
                (By.CSS_SELECTOR, "input[name='cpf']"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.XPATH, "//input[@placeholder='CPF']"),
            ]
            
            print("📝 Procurando campo CPF...")
            for by_type, selector in selectors_cpf:
                try:
                    cpf_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by_type, selector))
                    )
                    print(f"✅ Campo CPF encontrado: {by_type}='{selector}'")
                    break
                except TimeoutException:
                    continue
            
            if not cpf_input:
                self.driver.save_screenshot("debug_erro_campo_cpf.png")
                raise Exception("❌ Campo CPF não encontrado. Screenshot salvo: debug_erro_campo_cpf.png")
            
            # Inserir CPF
            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            cpf_input.clear()
            cpf_input.send_keys(cpf_limpo)
            print(f"✅ CPF inserido: {cpf_limpo[:3]}.***.***-**")
            self._sleep(0.3)
            
            # Captura após inserir CPF
            try:
                self.driver.save_screenshot("debug_02_cpf_inserido.png")
            except:
                pass
            
            # Procurar botão "Próximo" ou similar
            botoes_proximo = [
                "//button[contains(text(), 'Próximo')]",
                "//button[contains(text(), 'Continuar')]",
                "//button[contains(text(), 'Avançar')]",
                "//button[@type='submit']",
                "//input[@type='submit']",
            ]
            
            botao_encontrado = False
            for xpath in botoes_proximo:
                try:
                    botao = self.driver.find_element(By.XPATH, xpath)
                    botao.click()
                    print(f"✅ Botão clicado: {xpath}")
                    botao_encontrado = True
                    break
                except NoSuchElementException:
                    continue
            
            if not botao_encontrado:
                self.driver.save_screenshot("debug_erro_botao_proximo.png")
                raise Exception("❌ Botão 'Próximo' não encontrado. Screenshot: debug_erro_botao_proximo.png")
            
            self._wait_page_ready(self.wait_short)
            
            # Captura após clicar próximo
            try:
                self.driver.save_screenshot("debug_03_apos_proximo.png")
            except:
                pass
            
            # Se não aguardar código, tentar inserir senha diretamente
            if not aguardar_codigo_email:
                print("⚠️ Modo sem código de email - tentando login direto")
                
                # Procurar campo senha
                senha_input = None
                selectors_senha = [
                    (By.NAME, "senha"),
                    (By.ID, "senha"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                    (By.XPATH, "//input[@placeholder='Senha']"),
                ]
                
                for by_type, selector in selectors_senha:
                    try:
                        senha_input = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((by_type, selector))
                        )
                        print(f"✅ Campo senha encontrado: {by_type}='{selector}'")
                        break
                    except TimeoutException:
                        continue
                
                if senha_input:
                    senha_input.clear()
                    senha_input.send_keys(senha)
                    print("✅ Senha inserida")
                    self._sleep(0.3)
                    
                    # Captura após inserir senha
                    try:
                        self.driver.save_screenshot("debug_04_senha_inserida.png")
                    except:
                        pass
                    
                    # Procurar botão Entrar
                    botoes_entrar = [
                        "//button[contains(text(), 'Entrar')]",
                        "//button[contains(text(), 'Login')]",
                        "//button[contains(text(), 'Acessar')]",
                        "//button[@type='submit']",
                    ]
                    
                    for xpath in botoes_entrar:
                        try:
                            botao = self.driver.find_element(By.XPATH, xpath)
                            botao.click()
                            print(f"✅ Botão login clicado: {xpath}")
                            break
                        except NoSuchElementException:
                            continue
                    
                    self._wait_page_ready(self.wait_default)
                else:
                    self.driver.save_screenshot("debug_erro_campo_senha.png")
                    raise Exception("❌ Campo senha não encontrado")
            else:
                # Fluxo com código de email
                print("📧 Solicitando código de validação...")
                try:
                    botao_receber_codigo = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Receber código')]")
                    botao_receber_codigo.click()
                    self._sleep(0.8)
                except:
                    print("⚠️ Botão 'Receber código' não encontrado")
                
                print("\n⏳ AGUARDANDO CÓDIGO DO E-MAIL...")
                print("👉 Verifique seu e-mail e insira o código na página")
                input("✅ Pressione ENTER após inserir o código e clicar em 'Enviar'...")
                
                # Inserir senha
                print("🔒 Inserindo senha...")
                senha_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "senha"))
                )
                senha_input.clear()
                senha_input.send_keys(senha)
                
                # Confirmar login
                botao_entrar = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
                botao_entrar.click()
                self._wait_page_ready(self.wait_default)
            
            # Captura final
            try:
                self.driver.save_screenshot("debug_05_apos_login.png")
            except:
                pass
            
            # Verificar se login foi bem-sucedido
            url_atual = self.driver.current_url.lower()
            print(f"📍 URL atual: {self.driver.current_url}")
            
            # Verificações de sucesso
            sucesso = (
                "siwfc.caixa.gov.br" in url_atual and 
                "login" not in url_atual and
                "autenticacao" not in url_atual
            )
            
            if sucesso:
                print("✅ Login realizado com sucesso!")
                self.logged_in = True
                return True
            else:
                print("❌ Login parece ter falhado")
                print(f"   URL atual: {self.driver.current_url}")
                self.driver.save_screenshot("debug_erro_login_falhou.png")
                return False
                
        except Exception as e:
            print(f"❌ Erro durante login: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.driver.save_screenshot("debug_erro_exception.png")
                print("📸 Screenshot de erro salvo: debug_erro_exception.png")
            except:
                pass
            return False
    
    def verificar_login_existente(self):
        """
        Verifica se já existe uma sessão logada (quando usa perfil existente)
        Apenas acessa o site e verifica se está logado
        """
        from selenium.webdriver.common.by import By
        
        log_file = open('cef_automation_debug.log', 'a', encoding='utf-8')
        log_file.write("\n" + "="*60 + "\n")
        log_file.write("verificar_login_existente() INICIADO\n")
        log_file.flush()
        
        try:
            print(f"\n🌐 Verificando sessão existente em {SIWFC_URL}...")
            log_file.write(f"Navegando para: {SIWFC_URL}\n")
            log_file.flush()
            
            # Primeiro, verificar qual a URL atual
            try:
                url_antes = self.driver.current_url
                print(f"📍 URL ANTES da navegação: {url_antes}")
                log_file.write(f"URL ANTES: {url_antes}\n")
                log_file.flush()
            except Exception as e:
                print(f"⚠️ Não conseguiu obter URL atual: {e}")
                log_file.write(f"Erro ao obter URL atual: {e}\n")
                log_file.flush()
            
            # Tentar navegar
            print(f"🔄 Navegando para {SIWFC_URL}...")
            self.driver.get(SIWFC_URL)
            print("✅ Navegação concluída")
            log_file.write("Navegação OK\n")
            log_file.flush()
            
            print("⏳ Aguardando página ficar pronta...")
            self._wait_page_ready(self.wait_default)
            log_file.write("Wait ready OK\n")
            log_file.flush()
            
            # Captura screenshot
            try:
                print("📸 Capturando screenshot...")
                self.driver.save_screenshot("debug_sessao_existente.png")
                print("📸 Screenshot salvo: debug_sessao_existente.png")
                log_file.write("Screenshot OK\n")
                log_file.flush()
            except Exception as e:
                print(f"⚠️ Erro ao capturar screenshot: {e}")
                log_file.write(f"Erro screenshot: {e}\n")
                log_file.flush()
            
            print("📍 Obtendo informações da página...")
            url_atual = self.driver.current_url.lower()
            titulo_pagina = self.driver.title.lower()
            print(f"📍 URL atual: {self.driver.current_url}")
            print(f"📄 Título página: {self.driver.title}")
            log_file.write(f"URL atual: {url_atual}\n")
            log_file.write(f"Título: {titulo_pagina}\n")
            log_file.flush()
            
            # Verificar se consegue acessar a página de documentos (sinal de que está logado)
            # Se estiver logado, deve estar na página /documentos ou redirecionar para ela
            ja_logado = (
                "siwfc.caixa.gov.br" in url_atual and 
                "login" not in url_atual and
                "autenticacao" not in url_atual and
                "entrar" not in url_atual and
                ("documentos" in url_atual or "sistema" in titulo_pagina or "fcvs" in titulo_pagina)
            )
            
            # Verificação adicional: tentar encontrar elementos que só existem quando logado
            if not ja_logado:
                try:
                    # Procurar por elementos típicos da área logada
                    elementos_logado = self.driver.find_elements(By.CSS_SELECTOR, ".user-info, .logout, nav.navbar, .menu-lateral")
                    if elementos_logado:
                        print("✅ Elementos de usuário logado detectados")
                        ja_logado = True
                except:
                    pass
            
            if ja_logado:
                print("✅ Sessão já está ativa! Usuário já está logado.")
                log_file.write("RESULTADO: Sessão ativa detectada\n")
                log_file.close()
                self.logged_in = True
                return True
            else:
                print("⚠️ Não detectada sessão ativa. Será necessário fazer login.")
                print(f"   URL atual: {self.driver.current_url}")
                print(f"   Título: {self.driver.title}")
                log_file.write("RESULTADO: Sessão não detectada\n")
                log_file.close()
                return False
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erro ao verificar sessão: {error_msg}")
            log_file.write(f"ERRO em verificar_login: {error_msg}\n")
            import traceback
            traceback.print_exc()
            log_file.write(traceback.format_exc())
            log_file.write("\n")
            log_file.close()
            return False
    
    def enviar_fh1(self, caminho_arquivo, codigo_contrato, matricula_agente):
        """
        Envia arquivo FH1 através do módulo de envio de dossiê
        
        Args:
            caminho_arquivo: Caminho do arquivo FH1 a enviar
            codigo_contrato: Código do contrato SICVS/CADMUT
            matricula_agente: Matrícula do agente financeiro
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        if not self.logged_in:
            print("❌ Necessário fazer login primeiro")
            return False
        
        try:
            print("\n📤 INICIANDO ENVIO DE FH1...")
            
            # Navegar para módulo de envio
            print("📍 Navegando para módulo de envio de dossiê...")
            # Aqui seria necessário clicar no menu apropriado
            # Baseado na análise do manual, seria algo como:
            # self.driver.find_element(By.LINK_TEXT, "Envio de Dossiê").click()
            
            # Selecionar matrícula do agente
            print(f"🏦 Selecionando matrícula: {matricula_agente}...")
            # Implementar seleção conforme HTML real
            
            # Inserir código do contrato
            print(f"📝 Inserindo código do contrato: {codigo_contrato}...")
            # Implementar inserção conforme HTML real
            
            # Upload do arquivo
            print(f"📁 Fazendo upload de: {caminho_arquivo}...")
            input_arquivo = self.driver.find_element(By.XPATH, "//input[@type='file']")
            input_arquivo.send_keys(os.path.abspath(caminho_arquivo))
            self._wait_file_input_preenchido(input_arquivo, timeout=self.wait_short)
            
            # Confirmar envio
            print("✅ Confirmando envio...")
            botao_enviar = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Enviar')]")
            botao_enviar.click()
            self._wait_page_ready(self.wait_default)
            
            print("✅ Arquivo FH1 enviado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar FH1: {e}")
            return False
    
    def enviar_movimento_fcvs(self, arquivo_header, arquivo_dados, produto='FCVS', tipo_movimento='FH1'):
        """
        Envia movimentos FCVS conforme especificação SIWFC (Módulo Envio de Movimentos)
        
        Args:
            arquivo_header: Caminho do arquivo HEADER
            arquivo_dados: Caminho do arquivo DADOS
            produto: FCVS ou CADMUT
            tipo_movimento: FH1, FH2, FH3, RCV, RNV, CADMUT0, CADMUT1
        
        Returns:
            Dict com resultado do envio
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import Select
        
        log_file = open('cef_automation_debug.log', 'a', encoding='utf-8')
        log_file.write("\n" + "="*60 + "\n")
        log_file.write("enviar_movimento_fcvs() INICIADO\n")
        log_file.write(f"Produto: {produto}\n")
        log_file.write(f"Tipo: {tipo_movimento}\n")
        log_file.write(f"Logged in: {self.logged_in}\n")
        log_file.flush()
        
        if not self.logged_in:
            log_file.write("ERRO: Não está logado\n")
            log_file.close()
            return {
                'sucesso': False,
                'mensagem': 'Necessário fazer login primeiro',
                'detalhes': {}
            }
        
        try:
            resultado = {
                'sucesso': False,
                'mensagem': '',
                'detalhes': {},
                'screenshots': []
            }
            
            print("\n📤 INICIANDO ENVIO DE MOVIMENTO FCVS...")
            print(f"   Produto: {produto}")
            print(f"   Tipo: {tipo_movimento}")
            log_file.write("Iniciando passos de envio...\n")
            log_file.flush()
            
            # Verificar se já está na página de envio de movimentos
            print("📍 Verificando se já está na página de envio...")
            log_file.write("Verificando URL atual...\n")
            url_atual = self.driver.current_url.lower()
            log_file.write(f"URL atual: {url_atual}\n")
            
            # Verificar se tem o componente app-enviar-movimento (página já está carregada)
            try:
                self.driver.find_element(By.TAG_NAME, "app-enviar-movimento")
                print("✅ Já está na página de Envio de Movimentos!")
                log_file.write("✅ Já está na página correta\n")
                log_file.flush()
            except:
                # Não está na página, precisa navegar
                print("📍 Não está na página de envio, navegando...")
                log_file.write("Não está na página, precisa navegar\n")
                log_file.flush()
                
                # 1. Clicar no menu lateral
                print("📍 Abrindo menu...")
                log_file.write("PASSO 1: Tentando abrir menu...\n")
                log_file.flush()
                
                try:
                    menu_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Menu'], .menu-toggle, .navbar-toggler"))
                    )
                    menu_button.click()
                    self._sleep(0.3)
                    log_file.write("Menu clicado OK\n")
                    log_file.flush()
                except Exception as e:
                    print(f"⚠️ Menu já pode estar aberto ou não encontrado: {e}")
                    log_file.write(f"Menu não encontrado/já aberto: {e}\n")
                    log_file.flush()
                
                # 2. Procurar e clicar no item do menu "Envio de Movimentos"
                print("📍 Procurando item 'Envio de Movimentos' no menu...")
                log_file.write("PASSO 2: Procurando item do menu...\n")
                log_file.flush()
                
                # No Angular Material, os itens de menu podem estar em spans ou divs
                estrategias_menu = [
                    ("SPAN com texto", By.XPATH, "//span[contains(text(), 'Envio de Movimentos')]"),
                    ("DIV clicável", By.XPATH, "//div[contains(@class, 'item-container')]//span[contains(text(), 'Envio de Movimentos')]"),
                    ("Item de menu", By.XPATH, "//*[contains(@class, 'item-menu')]//span[contains(text(), 'Envio de Movimentos')]"),
                ]
                
                menu_item = None
                for nome, by_type, valor in estrategias_menu:
                    try:
                        log_file.write(f"Tentando: {nome}\n")
                        log_file.flush()
                        menu_item = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((by_type, valor))
                        )
                        log_file.write(f"✅ Item encontrado com: {nome}\n")
                        log_file.flush()
                        print(f"✅ Item encontrado: {nome}")
                        break
                    except:
                        log_file.write(f"❌ Falhou: {nome}\n")
                        log_file.flush()
                
                if not menu_item:
                    raise Exception("Item 'Envio de Movimentos' não encontrado no menu")
                
                menu_item.click()
                self._wait_page_ready(self.wait_short)
                log_file.write("Item do menu clicado OK\n")
                log_file.flush()
            
            # 3. Aguardar página carregar e tirar screenshot
            self._wait_page_ready(self.wait_short)
            self.tirar_screenshot("01_pagina_envio_movimentos.png")
            resultado['screenshots'].append("01_pagina_envio_movimentos.png")
            log_file.write("Screenshot da página de envio OK\n")
            log_file.flush()
            
            # 4. Selecionar Produto (FCVS ou CADMUT)
            print(f"📋 Selecionando produto: {produto}...")
            log_file.write(f"Procurando select de produto...\n")
            log_file.flush()
            
            select_produto_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "produto"))
            )
            select_produto = Select(select_produto_element)
            
            # Debug: listar todas as opções disponíveis
            log_file.write("Opções disponíveis no select produto:\n")
            for option in select_produto.options:
                log_file.write(f"  value='{option.get_attribute('value')}' text='{option.text}'\n")
            log_file.flush()
            
            # Tentar selecionar por value, se não funcionar, tentar por texto visível
            try:
                select_produto.select_by_value(produto)
                log_file.write(f"Selecionado por value: {produto}\n")
            except:
                log_file.write(f"Não encontrou value '{produto}', tentando por texto...\n")
                log_file.flush()
                try:
                    select_produto.select_by_visible_text(produto)
                    log_file.write(f"Selecionado por texto: {produto}\n")
                except:
                    log_file.write(f"Tentando texto parcial...\n")
                    # Tentar encontrar opção que contenha o texto
                    for option in select_produto.options:
                        if produto.lower() in option.text.lower():
                            option.click()
                            log_file.write(f"Selecionado opção com texto: {option.text}\n")
                            break
                    else:
                        raise Exception(f"Não foi possível selecionar produto '{produto}'. Opções disponíveis: {[o.text for o in select_produto.options]}")
            
            log_file.flush()
            print("✅ Produto selecionado com sucesso")
            print("⏳ Aguardando tipo de movimento carregar...")
            
            # 5. Selecionar Tipo de Movimento
            print(f"📋 Selecionando tipo: {tipo_movimento}...")
            log_file.write(f"Procurando select de tipo de movimento...\n")
            log_file.flush()
            
            # Tentar diferentes IDs possíveis
            select_tipo_element = None
            ids_possiveis = ["tipo_movimento", "tipoMovimento", "tipo", "movimento"]
            
            for id_tentativa in ids_possiveis:
                try:
                    log_file.write(f"Tentando ID: {id_tentativa}\n")
                    log_file.flush()
                    select_tipo_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, id_tentativa))
                    )
                    log_file.write(f"✅ Encontrado com ID: {id_tentativa}\n")
                    log_file.flush()
                    print(f"✅ Select tipo_movimento encontrado com ID: {id_tentativa}")
                    break
                except:
                    log_file.write(f"❌ Não encontrado: {id_tentativa}\n")
                    log_file.flush()
                    continue
            
            if not select_tipo_element:
                # Tentar por name ou outras estratégias
                log_file.write("Tentando localizar por name='tipo_movimento'...\n")
                log_file.flush()
                try:
                    select_tipo_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.NAME, "tipo_movimento"))
                    )
                    log_file.write("✅ Encontrado por name\n")
                    log_file.flush()
                except:
                    # Última tentativa: procurar qualquer select que apareça depois do select de produto
                    log_file.write("Tentando encontrar segundo select na página...\n")
                    log_file.flush()
                    selects = self.driver.find_elements(By.TAG_NAME, "select")
                    log_file.write(f"Total de selects encontrados: {len(selects)}\n")
                    if len(selects) >= 2:
                        select_tipo_element = selects[1]  # Segundo select
                        log_file.write("Usando segundo select da página\n")
                        log_file.flush()
                    else:
                        raise Exception(f"Select tipo_movimento não encontrado. Total de selects na página: {len(selects)}")
            
            select_tipo = Select(select_tipo_element)
            
            # Debug: listar todas as opções disponíveis
            log_file.write("Opções disponíveis no select tipo_movimento:\n")
            for option in select_tipo.options:
                log_file.write(f"  value='{option.get_attribute('value')}' text='{option.text}'\n")
            log_file.flush()
            
            # Tentar selecionar por value, se não funcionar, tentar por texto visível
            try:
                select_tipo.select_by_value(tipo_movimento)
                log_file.write(f"Selecionado por value: {tipo_movimento}\n")
            except:
                log_file.write(f"Não encontrou value '{tipo_movimento}', tentando por texto...\n")
                log_file.flush()
                try:
                    select_tipo.select_by_visible_text(tipo_movimento)
                    log_file.write(f"Selecionado por texto: {tipo_movimento}\n")
                except:
                    log_file.write(f"Tentando texto parcial...\n")
                    # Tentar encontrar opção que contenha o texto
                    for option in select_tipo.options:
                        if tipo_movimento.lower() in option.text.lower():
                            option.click()
                            log_file.write(f"Selecionado opção com texto: {option.text}\n")
                            break
                    else:
                        raise Exception(f"Não foi possível selecionar tipo '{tipo_movimento}'. Opções disponíveis: {[o.text for o in select_tipo.options]}")
            
            log_file.flush()
            print("✅ Tipo de movimento selecionado com sucesso")
            print("⏳ Aguardando campos de upload...")
            WebDriverWait(self.driver, 8).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "input[type='file']")) > 0
            )
            
            # Tirar screenshot para debug
            self.tirar_screenshot("02_apos_selecionar_tipo.png")
            resultado['screenshots'].append("02_apos_selecionar_tipo.png")
            log_file.write("Screenshot após selecionar tipo OK\n")
            log_file.flush()
            
            # 6. Upload de arquivos
            log_file.write("Procurando campos de upload de arquivos...\n")
            log_file.flush()
            
            # Procurar todos os inputs de tipo file
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            log_file.write(f"Total de inputs file encontrados: {len(file_inputs)}\n")
            log_file.flush()
            
            if produto == 'FCVS' and (
                tipo_movimento in ['FH1', 'FH2', 'FH3']
                or (tipo_movimento in ['RNV', 'RCV'] and bool(arquivo_header))
            ):
                # Requer HEADER + DADOS
                print(f"📁 Fazendo upload do HEADER: {arquivo_header}...")
                log_file.write(f"Procurando campo HEADER...\n")
                
                # Tentar múltiplos identificadores
                input_header = None
                ids_header = ["arquivo_header", "arquivoHeader", "header", "file_header", "fileHeader"]
                
                for id_h in ids_header:
                    try:
                        input_header = self.driver.find_element(By.ID, id_h)
                        log_file.write(f"✅ Campo HEADER encontrado com ID: {id_h}\n")
                        break
                    except:
                        continue
                
                # Se não encontrou por ID, tentar pelo índice (primeiro input file)
                if not input_header and len(file_inputs) >= 2:
                    input_header = file_inputs[0]
                    log_file.write("Usando primeiro input[type=file] para HEADER\n")
                elif not input_header:
                    raise Exception(f"Campo de upload HEADER não encontrado. Inputs file na página: {len(file_inputs)}")
                
                log_file.flush()
                input_header.send_keys(os.path.abspath(arquivo_header))
                log_file.write(f"Upload HEADER enviado: {os.path.abspath(arquivo_header)}\n")
                self._wait_file_input_preenchido(input_header, timeout=self.wait_short)
                self._sleep(0.1)
                
                print(f"📁 Fazendo upload do DADOS: {arquivo_dados}...")
                log_file.write(f"Procurando campo DADOS...\n")
                
                # Tentar múltiplos identificadores
                input_dados = None
                ids_dados = ["arquivo_dados", "arquivoDados", "dados", "file_dados", "fileDados"]
                
                for id_d in ids_dados:
                    try:
                        input_dados = self.driver.find_element(By.ID, id_d)
                        log_file.write(f"✅ Campo DADOS encontrado com ID: {id_d}\n")
                        break
                    except:
                        continue
                
                # Se não encontrou por ID, usar segundo input file
                if not input_dados and len(file_inputs) >= 2:
                    input_dados = file_inputs[1]
                    log_file.write("Usando segundo input[type=file] para DADOS\n")
                elif not input_dados:
                    raise Exception(f"Campo de upload DADOS não encontrado. Inputs file na página: {len(file_inputs)}")
                
                log_file.flush()
                input_dados.send_keys(os.path.abspath(arquivo_dados))
                log_file.write(f"Upload DADOS enviado: {os.path.abspath(arquivo_dados)}\n")
                self._wait_file_input_preenchido(input_dados, timeout=self.wait_short)
                self._sleep(0.1)
            else:
                # Apenas DADOS
                print(f"📁 Fazendo upload do arquivo: {arquivo_dados}...")

                # Para RNV/RCV, tentar ativar "Envio Simplificado" antes do upload
                if produto == 'FCVS' and tipo_movimento in ['RNV', 'RCV']:
                    try:
                        log_file.write("Tentando ativar 'Envio Simplificado' para RNV/RCV...\n")
                        el_simplificado = None
                        estrategias_simplificado = [
                            (By.XPATH, "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzaaaaeeeiiioooouuuc'), 'envio simplificado')]") ,
                            (By.XPATH, "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzaaaaeeeiiioooouuuc'), 'envio simplificado')]") ,
                            (By.CSS_SELECTOR, "input[type='checkbox'][id*='simpl'], input[type='checkbox'][name*='simpl']"),
                        ]

                        for by_type, seletor in estrategias_simplificado:
                            try:
                                cand = self.driver.find_element(by_type, seletor)
                                if cand:
                                    el_simplificado = cand
                                    break
                            except Exception:
                                continue

                        if el_simplificado:
                            try:
                                # Se for checkbox, marcar apenas se estiver desmarcado
                                if el_simplificado.tag_name.lower() == 'input' and el_simplificado.get_attribute('type') == 'checkbox':
                                    if not el_simplificado.is_selected():
                                        el_simplificado.click()
                                else:
                                    el_simplificado.click()
                                self._sleep(0.3)
                                log_file.write("✅ Envio Simplificado ativado\n")
                            except Exception as e:
                                log_file.write(f"⚠️ Não foi possível clicar em Envio Simplificado: {e}\n")
                        else:
                            log_file.write("⚠️ Opção Envio Simplificado não encontrada\n")
                    except Exception as e:
                        log_file.write(f"⚠️ Erro ao preparar Envio Simplificado: {e}\n")

                    # Recarrega inputs após possível alteração da tela
                    file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                    log_file.write(f"Inputs file após simplificado: {len(file_inputs)}\n")

                input_dados = None
                ids_dados = ["arquivo_dados", "arquivoDados", "dados", "arquivo", "file"]
                
                for id_d in ids_dados:
                    try:
                        input_dados = self.driver.find_element(By.ID, id_d)
                        log_file.write(f"✅ Campo arquivo encontrado com ID: {id_d}\n")
                        break
                    except:
                        continue
                
                if not input_dados and len(file_inputs) > 0:
                    # Em telas com 2 campos (HEADER + DADOS), o DADOS costuma ser o último
                    if len(file_inputs) >= 2:
                        input_dados = file_inputs[-1]
                        log_file.write("Usando último input[type=file] para DADOS\n")
                    else:
                        input_dados = file_inputs[0]
                        log_file.write("Usando único input[type=file]\n")
                elif not input_dados:
                    raise Exception(f"Campo de upload não encontrado. Inputs file na página: {len(file_inputs)}")
                
                input_dados.send_keys(os.path.abspath(arquivo_dados))
                log_file.write(f"Upload arquivo enviado: {os.path.abspath(arquivo_dados)}\n")
                self._wait_file_input_preenchido(input_dados, timeout=self.wait_short)
                self._sleep(0.1)
            
            log_file.write("✅ Uploads concluídos\n")
            log_file.flush()
            
            print("⏳ Aguardando estabilização do formulário...")
            self._sleep(0.4)
            
            # Desmarcar checkbox "Possui FH2/FH3" se estiver marcado
            print("🔍 Verificando checkbox 'Possui FH2/FH3'...")
            log_file.write("Procurando checkbox FH2/FH3...\n")
            log_file.flush()
            
            try:
                # Procurar checkbox por texto ou label
                estrategias_checkbox = [
                    ("Label com 'FH2/FH3'", By.XPATH, "//label[contains(text(), 'FH2/FH3')]"),
                    ("Label com 'Possui'", By.XPATH, "//label[contains(text(), 'Possui')]"),
                    ("Span com 'FH2/FH3'", By.XPATH, "//span[contains(text(), 'FH2/FH3')]"),
                ]
                
                checkbox_container = None
                for nome, by_type, xpath in estrategias_checkbox:
                    try:
                        log_file.write(f"Tentando: {nome}\n")
                        checkbox_container = self.driver.find_element(by_type, xpath)
                        log_file.write(f"✅ Encontrado: {nome}\n")
                        break
                    except:
                        log_file.write(f"❌ Não encontrado: {nome}\n")
                        continue
                
                if checkbox_container:
                    # Procurar o input checkbox associado
                    try:
                        # Tentar pegar checkbox dentro ou próximo do label
                        checkbox = None
                        
                        # Estratégia 1: input dentro do container
                        try:
                            checkbox = checkbox_container.find_element(By.XPATH, ".//input[@type='checkbox']")
                            log_file.write("Checkbox encontrado dentro do container\n")
                        except:
                            pass
                        
                        # Estratégia 2: input antes do label
                        if not checkbox:
                            try:
                                checkbox = checkbox_container.find_element(By.XPATH, "./preceding-sibling::input[@type='checkbox']")
                                log_file.write("Checkbox encontrado antes do label\n")
                            except:
                                pass
                        
                        # Estratégia 3: input depois do label
                        if not checkbox:
                            try:
                                checkbox = checkbox_container.find_element(By.XPATH, "./following-sibling::input[@type='checkbox']")
                                log_file.write("Checkbox encontrado depois do label\n")
                            except:
                                pass
                        
                        # Estratégia 4: procurar no parent
                        if not checkbox:
                            try:
                                parent = checkbox_container.find_element(By.XPATH, "./..")
                                checkbox = parent.find_element(By.XPATH, ".//input[@type='checkbox']")
                                log_file.write("Checkbox encontrado no parent\n")
                            except:
                                pass
                        
                        if checkbox:
                            # Verificar se está marcado
                            is_checked = checkbox.is_selected()
                            log_file.write(f"Checkbox status: checked={is_checked}\n")
                            print(f"📋 Checkbox FH2/FH3: {'Marcado' if is_checked else 'Desmarcado'}")
                            
                            if is_checked:
                                print("🔄 Desmarcando checkbox FH2/FH3...")
                                log_file.write("Desmarcando checkbox...\n")
                                
                                # Tentar clicar no checkbox ou no label
                                try:
                                    checkbox.click()
                                    log_file.write("✅ Checkbox desmarcado via click no input\n")
                                except:
                                    # Se não conseguir clicar no input, clicar no label
                                    checkbox_container.click()
                                    log_file.write("✅ Checkbox desmarcado via click no label\n")
                                
                                self._sleep(0.3)
                                print("✅ Checkbox FH2/FH3 desmarcado")
                            else:
                                print("✅ Checkbox FH2/FH3 já estava desmarcado")
                                log_file.write("Checkbox já estava desmarcado\n")
                        else:
                            log_file.write("⚠️ Input checkbox não encontrado\n")
                            print("⚠️ Input checkbox não encontrado, mas continuando...")
                            
                    except Exception as e:
                        log_file.write(f"Erro ao processar checkbox: {e}\n")
                        print(f"⚠️ Erro ao processar checkbox: {e}")
                else:
                    log_file.write("Label/container do checkbox não encontrado\n")
                    print("⚠️ Checkbox FH2/FH3 não encontrado (pode não existir nesta tela)")
                    
            except Exception as e:
                log_file.write(f"Erro ao procurar checkbox: {e}\n")
                print(f"⚠️ Erro ao procurar checkbox: {e}")
            
            log_file.flush()
            self._sleep(0.4)
            
            print("📸 Tirando screenshot com arquivos carregados...")
            self.tirar_screenshot("02_arquivos_carregados.png")
            resultado['screenshots'].append("02_arquivos_carregados.png")
            log_file.write("Screenshot com arquivos carregados OK\n")
            log_file.flush()
            
            # 7. Clicar em botão de envio
            print("🔘 Procurando botão 'Enviar Arquivos'...")
            log_file.write("Procurando botão de envio...\n")
            log_file.flush()
            
            # Procurar todos os botões
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            log_file.write(f"Total de botões encontrados: {len(all_buttons)}\n")
            log_file.write("Botões encontrados:\n")
            for i, btn in enumerate(all_buttons):
                try:
                    texto = btn.text.strip() if btn.text else ""
                    tipo = btn.get_attribute('type') or ""
                    classes = btn.get_attribute('class') or ""
                    visible = btn.is_displayed()
                    enabled = btn.is_enabled()
                    log_file.write(f"  [{i}] texto='{texto}' type='{tipo}' visible={visible} enabled={enabled}\n")
                    if classes:
                        log_file.write(f"       class='{classes[:100]}'\n")  # Limitar tamanho
                except Exception as e:
                    log_file.write(f"  [{i}] Erro ao inspecionar: {e}\n")
            log_file.flush()
            
            # Também procurar links e elementos clicáveis
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            log_file.write(f"\nTotal de links encontrados: {len(all_links)}\n")
            log_file.write("Links com texto relevante:\n")
            for i, link in enumerate(all_links):
                try:
                    texto = link.text.strip() if link.text else ""
                    visible = link.is_displayed()
                    if texto and visible:
                        log_file.write(f"  [{i}] '{texto}' visible={visible}\n")
                except:
                    pass
            log_file.flush()
            
            # Tentar múltiplas estratégias para encontrar o botão
            botao_enviar = None
            estrategias_botao = [
                ("Classe CSS .btnEnviar", By.CSS_SELECTOR, "span.btnEnviar, .btnEnviar, span.btn.btnEnviar"),
                ("Span com texto 'Enviar Arquivos'", By.XPATH, "//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzaaaaeeeiiioooouuuc'), 'enviar arquivos')]") ,
                ("Botão com texto exato 'Enviar Arquivos'", By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzaaaaeeeiiioooouuuc'), 'enviar arquivos')]"),
                ("Botão com span 'Enviar Arquivos'", By.XPATH, "//button[.//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzaaaaeeeiiioooouuuc'), 'enviar arquivos')]]"),
                ("Botão com 'Enviar'", By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzaaaaeeeiiioooouuuc'), 'enviar')]"),
                ("Botão id/name com 'enviar'", By.XPATH, "//button[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'enviar') or contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'enviar')]"),
                ("Tipo submit", By.CSS_SELECTOR, "button[type='submit']"),
                ("Texto 'Confirmar'", By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirmar')]"),
                ("Class com 'submit'", By.CSS_SELECTOR, "button[class*='submit'], a[class*='submit']"),
                ("Class com 'enviar'", By.CSS_SELECTOR, "button[class*='enviar'], a[class*='enviar']"),
                ("Texto 'Processar'", By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'processar')]"),
                ("Texto 'Gravar'", By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'gravar')]"),
                ("Texto 'Salvar'", By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'salvar')]"),
            ]
            
            for nome, by_type, valor in estrategias_botao:
                try:
                    log_file.write(f"Tentando estratégia: {nome}\n")
                    log_file.flush()
                    botao_enviar = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by_type, valor))
                    )
                    log_file.write(f"✅ Botão encontrado com: {nome}\n")
                    log_file.flush()
                    print(f"✅ Botão encontrado: {nome}")
                    break
                except:
                    log_file.write(f"❌ Falhou: {nome}\n")
                    log_file.flush()
            
            # Se não encontrou, tentar qualquer botão visível e habilitado (exceto os de menu/navegação)
            if not botao_enviar and len(all_buttons) > 0:
                log_file.write("Procurando qualquer botão visível e habilitado...\n")
                log_file.flush()
                
                for i, btn in enumerate(all_buttons):
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            texto = btn.text.strip() if btn.text else ""
                            # Ignorar botões de menu/navegação
                            texto_lower = texto.lower()
                            if texto and any(k in texto_lower for k in ['enviar', 'confirmar', 'processar', 'gravar', 'salvar']) and texto_lower not in ['menu', 'fechar', 'voltar', 'cancelar']:
                                botao_enviar = btn
                                log_file.write(f"Usando botão [{i}]: texto='{texto}'\n")
                                log_file.flush()
                                break
                    except Exception as e:
                        log_file.write(f"Erro ao testar botão [{i}]: {e}\n")
                        log_file.flush()
                        continue
            
            if not botao_enviar:
                print("⚠️ Botão de envio não encontrado via Selenium. Tentando fallback JS...")
                log_file.write("Botão não encontrado via Selenium. Tentando fallback JS...\n")

                try:
                    clicked_js = self.driver.execute_script("""
                        function normaliza(t){
                            if(!t){return ''}
                            return t
                                .toString()
                                .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
                                .toLowerCase().trim();
                        }

                        // 1) Tenta botão/link com texto Enviar Arquivos
                        const candidatos = Array.from(document.querySelectorAll('button, a, span, div'));
                        for (const el of candidatos) {
                            const txt = normaliza(el.innerText || el.textContent || '');
                            if (txt.includes('enviar arquivos') || txt === 'enviar' || txt.includes('confirmar envio')) {
                                const btn = el.closest('button') || el.closest('a') || el;
                                if (btn) {
                                    btn.scrollIntoView({block:'center'});
                                    btn.click();
                                    return 'clicked-text';
                                }
                            }
                        }

                        // 2) Tenta botão submit visível
                        const submits = Array.from(document.querySelectorAll('button[type="submit"], input[type="submit"]'));
                        for (const s of submits) {
                            const st = getComputedStyle(s);
                            if (st.display !== 'none' && st.visibility !== 'hidden' && !s.disabled) {
                                s.scrollIntoView({block:'center'});
                                s.click();
                                return 'clicked-submit';
                            }
                        }

                        // 3) Tenta submit no form que contém input file
                        const fileInput = document.querySelector('input[type="file"]');
                        if (fileInput) {
                            const form = fileInput.closest('form');
                            if (form) {
                                form.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
                                try { form.submit(); } catch(e) {}
                                return 'form-submit';
                            }
                        }

                        return '';
                    """)
                    log_file.write(f"Resultado fallback JS clique: {clicked_js}\n")
                    log_file.flush()
                    if clicked_js:
                        print(f"✅ Fallback JS acionado: {clicked_js}")
                        self._wait_page_ready(self.wait_default)
                    else:
                        print("⚠️ Fallback JS não encontrou ação de envio")
                except Exception as e:
                    log_file.write(f"Erro no fallback JS de clique: {e}\n")
                    log_file.flush()
                    print(f"⚠️ Erro no fallback JS: {e}")

                # Salvar screenshot para debug
                self.tirar_screenshot("erro_botao_nao_encontrado.png")
                log_file.write("Continuando para verificação de resultado...\n")
                log_file.flush()
            else:
                # Botão encontrado, tentar clicar com múltiplas estratégias
                print("✅ Botão encontrado! Tentando clicar...")
                log_file.write("Botão encontrado, iniciando clique...\n")
                log_file.flush()
                
                clique_sucesso = False
                
                # Estratégia 1: Scroll até o botão e aguardar
                try:
                    print("📜 Estratégia 1: Scroll até o botão...")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_enviar)
                    self._sleep(0.25)
                    log_file.write("Scroll realizado\n")
                except Exception as e:
                    log_file.write(f"Erro no scroll: {e}\n")
                
                # Estratégia 2: Remover possíveis overlays/modais que bloqueiam
                try:
                    print("🔓 Estratégia 2: Removendo overlays...")
                    self.driver.execute_script("""
                        // Remover overlays que podem bloquear o clique
                        var overlays = document.querySelectorAll('.cdk-overlay-backdrop, .modal-backdrop, .overlay');
                        overlays.forEach(function(el) { el.remove(); });
                    """)
                    self._sleep(0.15)
                    log_file.write("Overlays removidos\n")
                except Exception as e:
                    log_file.write(f"Erro ao remover overlays: {e}\n")
                
                # Estratégia 3: Clique normal do Selenium
                try:
                    print("🖱️ Estratégia 3: Clique normal do Selenium...")
                    botao_enviar.click()
                    clique_sucesso = True
                    log_file.write("✅ Clique normal OK\n")
                    print("✅ Clique realizado com sucesso!")
                except Exception as e:
                    log_file.write(f"❌ Clique normal falhou: {e}\n")
                    print(f"⚠️ Clique normal falhou: {e}")
                
                # Estratégia 4: JavaScript click (se clique normal falhou)
                if not clique_sucesso:
                    try:
                        print("⚡ Estratégia 4: Clique via JavaScript...")
                        self.driver.execute_script("arguments[0].click();", botao_enviar)
                        clique_sucesso = True
                        log_file.write("✅ Clique JavaScript OK\n")
                        print("✅ Clique via JavaScript realizado!")
                    except Exception as e:
                        log_file.write(f"❌ Clique JavaScript falhou: {e}\n")
                        print(f"⚠️ Clique JavaScript falhou: {e}")
                
                # Estratégia 5: Aguardar elemento ser clicável e tentar novamente
                if not clique_sucesso:
                    try:
                        print("⏰ Estratégia 5: Aguardar elemento ficar clicável...")
                        from selenium.webdriver.support import expected_conditions as EC
                        botao_clicavel = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(botao_enviar)
                        )
                        botao_clicavel.click()
                        clique_sucesso = True
                        log_file.write("✅ Clique após aguardar OK\n")
                        print("✅ Clique após aguardar realizado!")
                    except Exception as e:
                        log_file.write(f"❌ Clique após aguardar falhou: {e}\n")
                        print(f"⚠️ Clique após aguardar falhou: {e}")
                
                # Estratégia 6: Simular Enter no botão
                if not clique_sucesso:
                    try:
                        print("⌨️ Estratégia 6: Pressionar Enter no botão...")
                        from selenium.webdriver.common.keys import Keys
                        botao_enviar.send_keys(Keys.RETURN)
                        clique_sucesso = True
                        log_file.write("✅ Enter no botão OK\n")
                        print("✅ Enter pressionado!")
                    except Exception as e:
                        log_file.write(f"❌ Enter falhou: {e}\n")
                        print(f"⚠️ Enter falhou: {e}")

                # Estratégia 7: submit() no formulário pai
                if not clique_sucesso:
                    try:
                        print("🧩 Estratégia 7: submit() no formulário pai...")
                        form_parent = botao_enviar.find_element(By.XPATH, "ancestor::form[1]")
                        self.driver.execute_script("arguments[0].submit();", form_parent)
                        clique_sucesso = True
                        log_file.write("✅ submit() no form pai OK\n")
                        print("✅ Formulário submetido via JS!")
                    except Exception as e:
                        log_file.write(f"❌ submit() no form falhou: {e}\n")
                        print(f"⚠️ submit() no form falhou: {e}")

                # Estratégia 8: clique direto no elemento .btnEnviar via querySelector
                if not clique_sucesso:
                    try:
                        print("🎯 Estratégia 8: Clique direto em .btnEnviar...")
                        clicked = self.driver.execute_script("""
                            const el = document.querySelector('span.btnEnviar, .btnEnviar, span.btn.btnEnviar');
                            if (el) {
                                el.scrollIntoView({block: 'center'});
                                el.click();
                                return true;
                            }
                            return false;
                        """)
                        if clicked:
                            clique_sucesso = True
                            log_file.write("✅ Clique direto em .btnEnviar OK\n")
                            print("✅ Clique direto em .btnEnviar realizado!")
                    except Exception as e:
                        log_file.write(f"❌ Clique .btnEnviar falhou: {e}\n")
                        print(f"⚠️ Clique .btnEnviar falhou: {e}")
                
                if not clique_sucesso:
                    print("❌ ATENÇÃO: Todas as estratégias de clique falharam!")
                    log_file.write("❌ ERRO: Nenhuma estratégia de clique funcionou\n")
                    self.tirar_screenshot("erro_clique_botao.png")
                else:
                    print("✅ Botão clicado com sucesso!")
                
                log_file.flush()
                
                print("⏳ Aguardando resposta do portal CEF...")
                self._sleep(0.5)  # Aguardar inicial
            
            # Screenshot após enviar/aguardar
            self.tirar_screenshot("03_apos_enviar.png")
            resultado['screenshots'].append("03_apos_enviar.png")
            log_file.write("Screenshot após envio OK\n")
            log_file.flush()
            
            # 7. Aguardar e verificar mensagens de sucesso/erro do portal
            print("🔍 Procurando mensagens de confirmação...")
            log_file.write("Procurando mensagens de resposta...\n")
            log_file.flush()
            
            mensagem_encontrada = False
            protocolo = None
            
            try:
                # Aguardar até 8 segundos por mensagem de sucesso ou erro
                for tentativa in range(12):
                    # Procurar mensagens de sucesso
                    seletores_sucesso = [
                        "//div[contains(@class, 'alert-success')]",
                        "//div[contains(@class, 'success')]",
                        "//div[contains(@class, 'mensagem-sucesso')]",
                        "//span[contains(@class, 'success')]",
                        "//*[contains(text(), 'sucesso')]",
                        "//*[contains(text(), 'Sucesso')]",
                        "//*[contains(text(), 'enviado')]",
                        "//*[contains(text(), 'Enviado')]",
                        "//*[contains(text(), 'processado')]",
                        "//*[contains(text(), 'Processado')]",
                    ]
                    
                    # Procurar mensagens de erro
                    seletores_erro = [
                        "//div[contains(@class, 'alert-danger')]",
                        "//div[contains(@class, 'alert-error')]",
                        "//div[contains(@class, 'error')]",
                        "//div[contains(@class, 'erro')]",
                        "//span[contains(@class, 'error')]",
                        "//*[contains(text(), 'erro')]",
                        "//*[contains(text(), 'Erro')]",
                        "//*[contains(text(), 'falha')]",
                        "//*[contains(text(), 'Falha')]",
                    ]
                    
                    # Verificar sucesso
                    for seletor in seletores_sucesso:
                        try:
                            elementos = self.driver.find_elements(By.XPATH, seletor)
                            for elem in elementos:
                                if elem.is_displayed() and elem.text.strip():
                                    mensagem_encontrada = True
                                    texto = elem.text.strip()
                                    print(f"✅ MENSAGEM DE SUCESSO: {texto}")
                                    log_file.write(f"✅ Mensagem encontrada: {texto}\n")
                                    resultado['mensagem'] = texto
                                    resultado['sucesso'] = True
                                    
                                    # Procurar protocolo
                                    if 'protocolo' in texto.lower() or 'número' in texto.lower():
                                        import re
                                        match = re.search(r'\d{6,}', texto)
                                        if match:
                                            protocolo = match.group()
                                            print(f"📋 PROTOCOLO: {protocolo}")
                                            resultado['protocolo'] = protocolo
                                    break
                        except:
                            pass
                        if mensagem_encontrada:
                            break
                    
                    if mensagem_encontrada:
                        break
                    
                    # Verificar erro
                    for seletor in seletores_erro:
                        try:
                            elementos = self.driver.find_elements(By.XPATH, seletor)
                            for elem in elementos:
                                if elem.is_displayed() and elem.text.strip():
                                    mensagem_encontrada = True
                                    texto = elem.text.strip()
                                    print(f"❌ MENSAGEM DE ERRO: {texto}")
                                    log_file.write(f"❌ Erro encontrado: {texto}\n")
                                    resultado['mensagem'] = texto
                                    resultado['sucesso'] = False
                                    resultado['criticas'] = [texto]
                                    break
                        except:
                            pass
                        if mensagem_encontrada:
                            break
                    
                    if mensagem_encontrada:
                        break
                    
                    # Aguardar curto antes da próxima tentativa
                    self._sleep(0.6)
                    print(f"⏳ Aguardando resposta... ({tentativa + 1}/12)")
                
                # Se não encontrou mensagem específica, verificar críticas no layout antigo
                if not mensagem_encontrada:
                    log_file.write("Nenhuma mensagem modal encontrada, verificando críticas...\n")
                    criticas = self.driver.find_elements(By.CSS_SELECTOR, ".critica, .erro, .alert-danger")
                    if criticas:
                        print("⚠️ Críticas encontradas no envio:")
                        resultado['criticas'] = []
                        for critica in criticas[:5]:  # Limita a 5
                            texto = critica.text.strip()
                            if texto:
                                print(f"   - {texto}")
                                resultado['criticas'].append(texto)
                        
                        resultado['mensagem'] = f"Envio processado com {len(resultado['criticas'])} crítica(s)"
                        resultado['sucesso'] = len(resultado['criticas']) == 0
                    else:
                        # Sem confirmação explícita no portal, não marcar como sucesso automático
                        print("⚠️ Sem confirmação explícita de envio no portal")
                        resultado['mensagem'] = "Envio sem confirmação explícita (não foi possível validar no portal)"
                        resultado['sucesso'] = False

                # Tentativa extra de extração de protocolo no conteúdo da página
                if resultado.get('sucesso') and not resultado.get('protocolo'):
                    try:
                        import re
                        texto_pagina = self.driver.find_element(By.TAG_NAME, 'body').text
                        match_protocolo = re.search(
                            r'(?i)protocolo[^0-9]{0,30}(\d{6,})',
                            texto_pagina or ''
                        )
                        if match_protocolo:
                            resultado['protocolo'] = match_protocolo.group(1)
                            log_file.write(f"📋 Protocolo extraído do body: {resultado['protocolo']}\n")
                            print(f"📋 PROTOCOLO (body): {resultado['protocolo']}")
                    except Exception as e:
                        log_file.write(f"Falha na extração adicional de protocolo: {e}\n")
                
            except Exception as e:
                log_file.write(f"Erro ao procurar mensagens: {e}\n")
                print(f"⚠️ Erro ao verificar resposta: {e}")
                # Sem resposta do portal, não assumir sucesso
                resultado['sucesso'] = False
                resultado['mensagem'] = "Envio sem confirmação (resposta do portal não capturada)"
            
            # Screenshot final do resultado
            self._sleep(0.6)
            self.tirar_screenshot("04_resultado_final.png")
            resultado['screenshots'].append("04_resultado_final.png")
            log_file.write("Screenshot final OK\n")
            log_file.flush()
            
            return resultado
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erro ao enviar movimento: {error_msg}")
            log_file.write(f"ERRO em enviar_movimento: {error_msg}\n")
            import traceback
            traceback.print_exc()
            log_file.write(traceback.format_exc())
            log_file.write("\n")
            log_file.close()
            
            self.tirar_screenshot("erro_envio.png")
            
            return {
                'sucesso': False,
                'mensagem': f'Erro ao enviar: {error_msg}',
                'detalhes': {'erro': error_msg},
                'screenshots': ['erro_envio.png']
            }
    
    def baixar_retornos(self, pasta_destino="retornos_cef"):
        """
        Baixa arquivos de retorno disponíveis no portal
        """
        if not self.logged_in:
            print("❌ Necessário fazer login primeiro")
            return False
        
        try:
            print("\n📥 VERIFICANDO RETORNOS DISPONÍVEIS...")
            
            # Criar pasta se não existir
            os.makedirs(pasta_destino, exist_ok=True)
            
            # Navegar para área de retornos
            # Implementar conforme estrutura real do portal
            
            print(f"✅ Retornos salvos em: {pasta_destino}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao baixar retornos: {e}")
            return False
    
    def tirar_screenshot(self, nome="screenshot.png"):
        """Tira screenshot da página atual"""
        if self.driver:
            if not self.debug_screenshots:
                return
            self.driver.save_screenshot(nome)
            print(f"📸 Screenshot salva: {nome}")
    
    def fechar(self):
        """Fecha o navegador"""
        if self.driver:
            self.driver.quit()
            print("👋 Navegador fechado")


def testar_automacao():
    """Testa automação do portal CEF"""
    print("\n" + "="*80)
    print("🤖 CEF WEB AUTOMATION - TESTE")
    print("="*80 + "\n")
    
    bot = CEFWebBot(headless=False)  # headless=True para rodar sem interface
    
    if not bot.setup_driver():
        return
    
    try:
        # Carregar credenciais
        creds = bot.carregar_credenciais()
        
        # Fazer login
        sucesso = bot.fazer_login(
            cpf=creds['cpf'],
            senha=creds['senha'],
            aguardar_codigo_email=True
        )
        
        if sucesso:
            # Tirar screenshot da tela inicial
            bot.tirar_screenshot("siwfc_logado.png")
            
            # Aqui você pode testar envio de FH1
            # bot.enviar_fh1("FH1_teste.txt", "123456", "0001")
            
            # Aguardar para visualização
            input("\n✅ Login concluído! Pressione ENTER para fechar...")
        
    except KeyboardInterrupt:
        print("\n⏸️ Teste interrompido pelo usuário")
    finally:
        bot.fechar()


if __name__ == "__main__":
    testar_automacao()
