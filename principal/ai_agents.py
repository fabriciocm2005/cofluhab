"""
Sistema de Agentes AI para COFLUHAB
Agentes especializados em análise de contratos, validação de dados e integração CEF
"""

try:
    # from crewai import Agent, Task, Crew
    # from crewai.tools import tool
    CREWAI_DISPONIVEL = True
except Exception as e:
    # Captura qualquer erro na importação do CrewAI
    CREWAI_DISPONIVEL = False
    print(f"⚠️ CrewAI não disponível: {e}")
    
    # Fallback se CrewAI não estiver instalado ou com problemas
    def tool(func_or_name):
        if callable(func_or_name):
            return func_or_name
        def decorator(func):
            return func
        return decorator
    
    class Agent:
        def __init__(self, **kwargs):
            self.config = kwargs
    
    class Task:
        def __init__(self, **kwargs):
            self.config = kwargs
    
    class Crew:
        def __init__(self, **kwargs):
            self.config = kwargs
        def kickoff(self):
            return "⚠️ CrewAI não está instalado corretamente. Há conflitos de versões com as dependências."


# ===== FERRAMENTAS CUSTOMIZADAS =====

@tool("Validador de Arquivos CEF")
def validar_arquivo_cef(conteudo: str) -> str:
    """
    Valida estrutura de arquivos CEF (FH1, RCV, etc.)
    Retorna relatório de validação com erros encontrados.
    """
    erros = []
    linhas = conteudo.strip().split('\n')
    
    if not linhas:
        return "❌ Arquivo vazio"
    
    # Validar HEADER
    if len(linhas) > 0:
        header = linhas[0]
        if len(header) != 430:
            erros.append(f"HEADER: {len(header)} bytes (esperado 430)")
        if not header.startswith('33'):
            erros.append("HEADER: UFS inválido (esperado '33')")
    
    # Validar TRAILER
    if len(linhas) > 1:
        trailer = linhas[-1]
        if len(trailer) != 430:
            erros.append(f"TRAILER: {len(trailer)} bytes (esperado 430)")
    
    if erros:
        return "❌ ERROS ENCONTRADOS:\n" + "\n".join(erros)
    
    return f"✅ Arquivo válido: {len(linhas)} linhas, estrutura correta"


@tool("Analisador de Contratos")
def analisar_contrato(contrato_id: int) -> str:
    """
    Analisa dados de um contrato específico.
    Retorna informações sobre saldo, parcelas e situação.
    """
    try:
        from principal.models import Contrato, ParcelaContrato
        
        contrato = Contrato.objects.get(id=contrato_id)
        parcelas = ParcelaContrato.objects.filter(contrato=contrato)
        
        total_parcelas = parcelas.count()
        pagas = parcelas.filter(pago=True).count()
        em_aberto = total_parcelas - pagas
        
        return f"""
📊 ANÁLISE DO CONTRATO {contrato.codigo}:
• Total de parcelas: {total_parcelas}
• Parcelas pagas: {pagas}
• Parcelas em aberto: {em_aberto}
• Situação: {'✅ Regular' if em_aberto == 0 else '⚠️ Pendências'}
"""
    except Exception as e:
        return f"❌ Erro ao analisar contrato: {str(e)}"


@tool("Gerador de Relatórios")
def gerar_relatorio(tipo: str, dados: str) -> str:
    """
    Gera relatório formatado baseado no tipo solicitado.
    Tipos: 'validacao', 'contrato', 'fcvs'
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    relatorio = f"""
{'='*80}
RELATÓRIO COFLUHAB - {tipo.upper()}
Data/Hora: {timestamp}
{'='*80}

{dados}

{'='*80}
Gerado automaticamente por AI Agent
{'='*80}
"""
    return relatorio


# ===== AGENTES ESPECIALIZADOS (Lazy Loading) =====

# Variáveis globais para cache dos agentes
_qa_engineer = None
_backend_engineer = None
_data_analyst = None
_compliance_officer = None
_autofix_engineer = None  # Novo agente

def get_qa_engineer():
    """Cria e retorna o agente QA Engineer (singleton)"""
    global _qa_engineer
    if _qa_engineer is None and CREWAI_DISPONIVEL:
        _qa_engineer = Agent(
            role="QA Engineer - Validação CEF",
            goal="Garantir que todos os arquivos enviados à CEF estejam 100% conformes com as especificações",
            backstory="""Você é um especialista em qualidade de software com experiência 
            em integração bancária. Sua missão é validar rigorosamente cada arquivo antes 
            do envio, garantindo que não haja rejeições pela CEF.""",
            tools=[validar_arquivo_cef, gerar_relatorio],
            verbose=True,
            allow_delegation=False
        )
    return _qa_engineer

def get_backend_engineer():
    """Cria e retorna o agente Backend Engineer (singleton)"""
    global _backend_engineer
    if _backend_engineer is None and CREWAI_DISPONIVEL:
        _backend_engineer = Agent(
            role="Backend Engineer - Correção de Dados",
            goal="Identificar e corrigir problemas em contratos e arquivos de exportação",
            backstory="""Você é um desenvolvedor backend especializado em sistemas financeiros.
            Quando bugs ou inconsistências são encontrados, você analisa o código e os dados
            para propor soluções técnicas precisas.""",
            tools=[analisar_contrato, gerar_relatorio],
            verbose=True,
            allow_delegation=True
        )
    return _backend_engineer

def get_data_analyst():
    """Cria e retorna o agente Data Analyst (singleton)"""
    global _data_analyst
    if _data_analyst is None and CREWAI_DISPONIVEL:
        _data_analyst = Agent(
            role="Data Analyst - Análise FCVS",
            goal="Analisar dados de contratos e identificar padrões, anomalias e oportunidades",
            backstory="""Você é um analista de dados especializado em FCVS (Fundo de 
            Compensação de Variações Salariais). Sua expertise permite identificar 
            contratos com problemas, valores divergentes e situações que requerem atenção.""",
            tools=[analisar_contrato, gerar_relatorio],
            verbose=True,
            allow_delegation=False
        )
    return _data_analyst

def get_compliance_officer():
    """Cria e retorna o agente Compliance Officer (singleton)"""
    global _compliance_officer
    if _compliance_officer is None and CREWAI_DISPONIVEL:
        _compliance_officer = Agent(
            role="Compliance Officer - Regulamentação CEF",
            goal="Garantir conformidade legal e regulatória de todas as operações com a CEF",
            backstory="""Você é um especialista em compliance e regulamentação bancária.
            Conhece profundamente as normas da CEF e garante que todas as operações
            estejam em conformidade com a legislação vigente.""",
            tools=[validar_arquivo_cef, gerar_relatorio],
            verbose=True,
            allow_delegation=False
        )
    return _compliance_officer

def get_autofix_engineer():
    """Cria e retorna o agente Auto-Fix Engineer (singleton) - OPÇÃO 2"""
    global _autofix_engineer
    if _autofix_engineer is None and CREWAI_DISPONIVEL:
        _autofix_engineer = Agent(
            role="Auto-Fix Engineer - Correção Inteligente",
            goal="Corrigir automaticamente problemas em arquivos CEF e aprender com padrões de erro para sugerir melhorias no código",
            backstory="""Você é um engenheiro especializado em auto-correção e machine learning aplicado.
            Sua missão é não apenas corrigir problemas detectados, mas também:
            1. Identificar padrões recorrentes de erros
            2. Sugerir melhorias no código gerador de arquivos
            3. Documentar correções para otimização futura
            4. Propor refatorações preventivas
            
            Você trabalha em conjunto com o QA Engineer: ele detecta, você corrige e aprende.""",
            tools=[gerar_relatorio],
            verbose=True,
            allow_delegation=False,
            max_iter=10  # Pode fazer até 10 iterações para encontrar a melhor correção
        )
    return _autofix_engineer


# ===== TAREFAS PRÉ-DEFINIDAS =====

def criar_tarefa_validacao_fh1(conteudo_arquivo: str) -> Task:
    """Cria tarefa de validação de arquivo FH1"""
    return Task(
        description=f"""
        Validar arquivo FH1 de habilitação ao FCVS:
        1. Verificar estrutura HEADER + REGISTRO I + TRAILER
        2. Validar comprimento de 430 bytes por linha
        3. Verificar posições dos campos críticos (UFS, Matrícula, FCVS)
        4. Gerar relatório de validação completo
        
        Conteúdo do arquivo:
        {conteudo_arquivo[:500]}...
        """,
        agent=get_qa_engineer(),
        expected_output="Relatório de validação com status APROVADO ou REPROVADO e lista de erros"
    )


def criar_tarefa_validacao_rcv(conteudo_arquivo: str) -> Task:
    """Cria tarefa de validação de arquivo RCV"""
    return Task(
        description=f"""
        Validar arquivo RCV de comprovação de valores:
        1. Verificar estrutura HEADER + N DETALHES + TRAILER
        2. Validar comprimento de 430 bytes em todas as linhas
        3. Verificar consistência entre quantidade de registros no HEADER/TRAILER
        4. Gerar relatório de validação detalhado
        
        Conteúdo do arquivo:
        {conteudo_arquivo[:500]}...
        """,
        agent=get_qa_engineer(),
        expected_output="Relatório de validação com aprovação ou lista de correções necessárias"
    )


def criar_tarefa_analise_contrato(contrato_id: int) -> Task:
    """Cria tarefa de análise de contrato"""
    return Task(
        description=f"""
        Analisar contrato ID {contrato_id}:
        1. Verificar situação de parcelas (pagas, em aberto)
        2. Identificar anomalias ou inconsistências
        3. Calcular indicadores de performance
        4. Gerar relatório de análise completo
        """,
        agent=get_data_analyst(),
        expected_output="Relatório de análise com métricas e recomendações"
    )


def criar_tarefa_correcao_bugs(descricao_problema: str) -> Task:
    """Cria tarefa de correção de problemas"""
    return Task(
        description=f"""
        Investigar e corrigir problema reportado:
        {descricao_problema}
        
        Ações esperadas:
        1. Analisar a causa raiz do problema
        2. Propor solução técnica
        3. Validar que a solução funciona
        4. Documentar a correção
        """,
        agent=get_backend_engineer(),
        expected_output="Relatório de correção com solução implementada ou proposta"
    )


# ===== CREWS PRÉ-CONFIGURADAS =====

def criar_crew_validacao_arquivo(conteudo: str, tipo_arquivo: str = "FH1") -> Crew:
    """
    Cria crew especializada em validação de arquivos CEF
    """
    if tipo_arquivo == "FH1":
        tarefa = criar_tarefa_validacao_fh1(conteudo)
    elif tipo_arquivo == "RCV":
        tarefa = criar_tarefa_validacao_rcv(conteudo)
    else:
        raise ValueError(f"Tipo de arquivo não suportado: {tipo_arquivo}")
    
    return Crew(
        agents=[get_qa_engineer(), get_compliance_officer()],
        tasks=[tarefa],
        verbose=True
    )


def criar_crew_analise_contratos(contratos_ids: list) -> Crew:
    """
    Cria crew para análise de múltiplos contratos
    """
    tarefas = [criar_tarefa_analise_contrato(cid) for cid in contratos_ids]
    
    return Crew(
        agents=[get_data_analyst(), get_backend_engineer()],
        tasks=tarefas,
        verbose=True
    )


def criar_crew_qa_completo(conteudo_arquivo: str, contratos_ids: list) -> Crew:
    """
    Cria crew completa com QA + Análise + Correção
    """
    tarefa_validacao = criar_tarefa_validacao_fh1(conteudo_arquivo)
    tarefas_analise = [criar_tarefa_analise_contrato(cid) for cid in contratos_ids[:3]]  # Limitar a 3
    
    return Crew(
        agents=[get_qa_engineer(), get_data_analyst(), get_backend_engineer(), get_compliance_officer()],
        tasks=[tarefa_validacao] + tarefas_analise,
        verbose=True
    )


# ===== EXEMPLO DE USO SIMPLES =====

def exemplo_validacao_simples():
    """
    Exemplo básico de validação de arquivo
    """
    if not CREWAI_DISPONIVEL:
        return "⚠️ CrewAI não está disponível"
    
    try:
        # QA e Backend trabalhando juntos
        qa = get_qa_engineer()
        dev = get_backend_engineer()
        
        if qa is None or dev is None:
            return "⚠️ Agentes não puderam ser criados. Verifique a configuração da OPENAI_API_KEY no arquivo .env"
        
        tarefa = Task(
            description="Review payment processing system and identify potential issues in transaction handling",
            agent=qa,
            expected_output="List of potential bugs and recommendations"
        )
        
        crew = Crew(
            agents=[qa, dev],
            tasks=[tarefa],
            verbose=True
        )
        
        resultado = crew.kickoff()
        return resultado
    except Exception as e:
        return f"❌ Erro ao executar agentes: {str(e)}"


# ===== FUNÇÕES DE INTEGRAÇÃO COM DJANGO =====

def validar_arquivo_com_ai(conteudo: str, tipo: str = "FH1") -> dict:
    """
    Valida arquivo usando AI agents e retorna resultado estruturado
    """
    try:
        crew = criar_crew_validacao_arquivo(conteudo, tipo)
        resultado = crew.kickoff()
        
        return {
            'sucesso': True,
            'resultado': str(resultado),
            'aprovado': '✅' in str(resultado) or 'APROVADO' in str(resultado).upper()
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'aprovado': False
        }


def analisar_padroes_erros_com_ai(historico_validacoes: list) -> dict:
    """
    OPÇÃO 2: Usa o Auto-Fix Engineer para analisar padrões de erro e sugerir melhorias no código.
    
    Args:
        historico_validacoes: Lista de dicts com {erros, correcoes, tipo_arquivo, data}
    
    Returns:
        dict com padroes_identificados, sugestoes_codigo, melhorias_preventivas
    """
    try:
        if not CREWAI_DISPONIVEL:
            return {'sucesso': False, 'erro': 'CrewAI não disponível'}
        
        autofix = get_autofix_engineer()
        
        # Preparar resumo do histórico
        resumo = f"Análise de {len(historico_validacoes)} validações:\n\n"
        erros_comuns = {}
        
        for val in historico_validacoes:
            erros = val.get('erros', '')
            if erros:
                # Contar erros semelhantes
                if 'HEADER' in erros:
                    erros_comuns['HEADER'] = erros_comuns.get('HEADER', 0) + 1
                if 'TRAILER' in erros:
                    erros_comuns['TRAILER'] = erros_comuns.get('TRAILER', 0) + 1
                if '431 bytes' in erros:
                    erros_comuns['HEADER_431'] = erros_comuns.get('HEADER_431', 0) + 1
                if '71 bytes' in erros:
                    erros_comuns['TRAILER_71'] = erros_comuns.get('TRAILER_71', 0) + 1
        
        resumo += "PADRÕES DETECTADOS:\n"
        for erro, count in sorted(erros_comuns.items(), key=lambda x: x[1], reverse=True):
            resumo += f"- {erro}: {count} ocorrências\n"
        
        # Criar tarefa de análise
        task = Task(
            description=f"""Analise os padrões de erro abaixo e sugira melhorias no código gerador:
            
            {resumo}
            
            Sua análise deve incluir:
            1. PADRÕES IDENTIFICADOS: Quais erros são mais comuns?
            2. CAUSA RAIZ: Por que esses erros estão acontecendo?
            3. SUGESTÕES DE CÓDIGO: Como corrigir o código gerador (views.py) para prevenir esses erros?
            4. MELHORIAS PREVENTIVAS: Que validações adicionar antes de gerar o arquivo?
            5. REFATORAÇÃO RECOMENDADA: Mudanças estruturais sugeridas
            
            Seja específico e técnico, citando nomes de funções e linhas de código quando possível.""",
            expected_output="Relatório detalhado com análise de padrões, causas raiz e sugestões de código específicas",
            agent=autofix
        )
        
        crew = Crew(
            agents=[autofix],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )
        
        resultado = crew.kickoff()
        
        return {
            'sucesso': True,
            'analise_completa': str(resultado),
            'total_validacoes': len(historico_validacoes),
            'erros_mais_comuns': erros_comuns
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e)
        }


def corrigir_com_agente_autofix(conteudo: str, erros_detectados: str, tipo_arquivo: str) -> dict:
    """
    OPÇÃO 2: Usa o Auto-Fix Engineer com IA para correção inteligente (não apenas regras).
    
    Args:
        conteudo: Conteúdo original do arquivo
        erros_detectados: String com os erros detectados pela AI
        tipo_arquivo: 'FH1' ou 'RCV'
    
    Returns:
        dict com conteudo_corrigido, correcoes_aplicadas, aprendizados, sucesso
    """
    try:
        if not CREWAI_DISPONIVEL:
            # Fallback para correção básica (Opção 1)
            return corrigir_arquivo_cef_automaticamente(conteudo, erros_detectados)
        
        autofix = get_autofix_engineer()
        
        # Preparar contexto para o agente
        task = Task(
            description=f"""Corrija o arquivo {tipo_arquivo} abaixo que apresenta os seguintes erros:

{erros_detectados}

CONTEÚDO DO ARQUIVO (primeiras 3 linhas):
{chr(10).join(conteudo.split(chr(10))[:3])}

REGRAS CEF:
- Cada linha deve ter EXATAMENTE 430 bytes
- HEADER: primeira linha, identifica o arquivo
- TRAILER: última linha, totalizadores
- Encoding: latin-1
- Line break: CRLF

Sua tarefa:
1. Identifique EXATAMENTE o que está errado
2. Sugira a correção específica (adicionar/remover bytes, onde)
3. Explique POR QUE esse erro ocorreu
4. Sugira como prevenir esse erro no código gerador

Formato da resposta:
CORREÇÃO: [descrição da correção]
CAUSA: [por que o erro ocorreu]
PREVENÇÃO: [como evitar no futuro]
APRENDIZADO: [lição para melhorar o sistema]""",
            expected_output="Análise detalhada com correção, causa, prevenção e aprendizado",
            agent=autofix
        )
        
        crew = Crew(
            agents=[autofix],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )
        
        resultado = crew.kickoff()
        resultado_str = str(resultado)
        
        # Aplicar correção básica (Opção 1) + análise do agente
        correcao_basica = corrigir_arquivo_cef_automaticamente(conteudo, erros_detectados)
        
        return {
            'sucesso': True,
            'conteudo_corrigido': correcao_basica['conteudo_corrigido'],
            'correcoes_aplicadas': correcao_basica['correcoes_aplicadas'],
            'analise_ia': resultado_str,  # Análise inteligente do agente
            'total_correcoes': correcao_basica['total_correcoes']
        }
    except Exception as e:
        # Fallback para Opção 1
        return corrigir_arquivo_cef_automaticamente(conteudo, erros_detectados)


def corrigir_arquivo_cef_automaticamente(conteudo: str, erros_detectados: str) -> dict:
    """
    Corrige automaticamente erros comuns em arquivos CEF baseado nos erros detectados pela AI.
    
    Args:
        conteudo: Conteúdo original do arquivo
        erros_detectados: String com os erros detectados pela AI
    
    Returns:
        dict com conteudo_corrigido, correcoes_aplicadas, sucesso
    """
    linhas = conteudo.split('\n')
    correcoes = []
    arquivo_corrigido = False
    
    # Processar cada linha
    linhas_corrigidas = []
    for i, linha in enumerate(linhas):
        linha_original = linha
        
        # Correção 1: HEADER com tamanho errado (deve ter 430 bytes)
        if i == 0 and 'HEADER' in erros_detectados.upper():
            if 'comprimento de 431' in erros_detectados or '431 bytes' in erros_detectados:
                # Remove 1 byte (geralmente \r ou espaço extra)
                linha = linha.rstrip('\r\n ')[:430]
                correcoes.append(f"✅ HEADER: Ajustado de {len(linha_original)} para 430 bytes")
                arquivo_corrigido = True
            elif len(linha) != 430:
                # Qualquer outro tamanho: ajustar com padding
                if len(linha) > 430:
                    linha = linha[:430]
                    correcoes.append(f"✅ HEADER: Cortado de {len(linha_original)} para 430 bytes")
                else:
                    linha = linha.ljust(430, ' ')
                    correcoes.append(f"✅ HEADER: Preenchido de {len(linha_original)} para 430 bytes")
                arquivo_corrigido = True
        
        # Correção 2: TRAILER com tamanho errado (deve ter 430 bytes)
        elif 'TRAILER' in linha_original.upper() or i == len(linhas) - 1:
            if 'TRAILER' in erros_detectados.upper():
                if '71 bytes' in erros_detectados or 'comprimento de 71' in erros_detectados:
                    # Adicionar padding para completar 430 bytes
                    linha = linha.ljust(430, ' ')
                    correcoes.append(f"✅ TRAILER: Expandido de 71 para 430 bytes (padding adicionado)")
                    arquivo_corrigido = True
                elif len(linha) != 430:
                    # Qualquer outro tamanho: ajustar
                    if len(linha) > 430:
                        linha = linha[:430]
                        correcoes.append(f"✅ TRAILER: Cortado de {len(linha_original)} para 430 bytes")
                    else:
                        linha = linha.ljust(430, ' ')
                        correcoes.append(f"✅ TRAILER: Preenchido de {len(linha_original)} para 430 bytes")
                    arquivo_corrigido = True
        
        # Correção 3: Registros do meio com tamanho errado
        elif len(linha) > 0 and len(linha) != 430:
            if len(linha) > 430:
                linha = linha[:430]
                correcoes.append(f"⚠️ Linha {i+1}: Cortada de {len(linha_original)} para 430 bytes")
            else:
                linha = linha.ljust(430, ' ')
                correcoes.append(f"⚠️ Linha {i+1}: Preenchida de {len(linha_original)} para 430 bytes")
            arquivo_corrigido = True
        
        linhas_corrigidas.append(linha)
    
    conteudo_final = '\n'.join(linhas_corrigidas)
    
    return {
        'sucesso': arquivo_corrigido,
        'conteudo_corrigido': conteudo_final if arquivo_corrigido else conteudo,
        'correcoes_aplicadas': correcoes,
        'total_correcoes': len(correcoes)
    }


def analisar_contratos_com_ai(contratos_ids: list) -> dict:
    """
    Analisa contratos usando AI agents
    """
    try:
        crew = criar_crew_analise_contratos(contratos_ids)
        resultado = crew.kickoff()
        
        return {
            'sucesso': True,
            'resultado': str(resultado),
            'contratos_analisados': len(contratos_ids)
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e)
        }
