"""
CEF Integration Bot - Agente especializado em integração com sistemas CEF
Lê manuais, entende procedimentos e automatiza interações com o portal web
"""

import os
import json
from datetime import datetime
from pathlib import Path

try:
    # from crewai import Agent, Task, Crew
    # from crewai.tools import tool
    CREWAI_DISPONIVEL = True
except:
    CREWAI_DISPONIVEL = False
    print("⚠️ CrewAI não disponível - funcionalidades limitadas")
    def tool(name_or_func):
        """Fallback decorator para quando CrewAI não está disponível"""
        if callable(name_or_func):
            return name_or_func
        def decorator(func):
            return func
        return decorator
    class Agent: 
        def __init__(self, **kwargs): self.config = kwargs
    class Task: 
        def __init__(self, **kwargs): self.config = kwargs
    class Crew: 
        def __init__(self, **kwargs): self.config = kwargs
        def kickoff(self): return "CrewAI indisponível"


# ===== CONFIGURAÇÕES =====
MANUAIS_PATH = r"C:\Users\fabri\cofluhab\dados_antigos\manuais"
KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), 'cef_knowledge_base.json')


# ===== FERRAMENTAS DE LEITURA DE MANUAIS =====

@tool("Leitor de PDFs")
def ler_pdf(caminho_pdf: str) -> str:
    """
    Lê conteúdo de arquivo PDF e retorna texto extraído.
    Suporta PDFs de documentação técnica e manuais.
    """
    try:
        import PyPDF2
        
        with open(caminho_pdf, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            
            # Limitar a 50 páginas iniciais para análise rápida
            max_pages = min(50, total_pages)
            texto = []
            
            for i in range(max_pages):
                page = reader.pages[i]
                texto.append(page.extract_text())
            
            conteudo = "\n".join(texto)
            
            return f"""
📄 PDF: {os.path.basename(caminho_pdf)}
📊 Total de páginas: {total_pages}
📖 Páginas analisadas: {max_pages}

{conteudo[:5000]}...

[Truncado para análise inicial]
"""
    except ImportError:
        return "❌ PyPDF2 não instalado. Execute: pip install PyPDF2"
    except Exception as e:
        return f"❌ Erro ao ler PDF: {str(e)}"


@tool("Analisador de Manuais CEF")
def analisar_manuais_cef() -> str:
    """
    Analisa todos os manuais CEF disponíveis e retorna resumo estruturado.
    Identifica: layouts, processos, endpoints, formatos de arquivo.
    """
    manuais_info = []
    
    if not os.path.exists(MANUAIS_PATH):
        return f"❌ Pasta de manuais não encontrada: {MANUAIS_PATH}"
    
    for arquivo in os.listdir(MANUAIS_PATH):
        if arquivo.endswith('.pdf'):
            caminho = os.path.join(MANUAIS_PATH, arquivo)
            tamanho_mb = os.path.getsize(caminho) / (1024 * 1024)
            
            # Identificar tipo de manual pelo nome
            tipo = "Desconhecido"
            if "FCVS" in arquivo and "Leiautes" in arquivo:
                tipo = "📋 Layouts de Movimentação FCVS"
            elif "CADMUT" in arquivo:
                tipo = "👤 Layouts de Cadastro de Mutuários"
            elif "SIWFC" in arquivo:
                tipo = "🌐 Manual do Sistema Web (SIWFC)"
            elif "Anexos" in arquivo and "Roteiro" in arquivo:
                tipo = "📎 Anexos e Roteiros de Análise"
            
            manuais_info.append({
                'arquivo': arquivo,
                'tipo': tipo,
                'tamanho_mb': round(tamanho_mb, 2),
                'caminho': caminho
            })
    
    resumo = "📚 MANUAIS CEF DISPONÍVEIS:\n\n"
    for i, manual in enumerate(manuais_info, 1):
        resumo += f"{i}. {manual['tipo']}\n"
        resumo += f"   📁 {manual['arquivo']}\n"
        resumo += f"   💾 {manual['tamanho_mb']} MB\n\n"
    
    return resumo


@tool("Extrator de Informações Técnicas")
def extrair_info_tecnica(manual: str, topico: str) -> str:
    """
    Extrai informações técnicas específicas de um manual.
    Tópicos: 'login', 'upload', 'download', 'layouts', 'endpoints', 'autenticacao'
    """
    # Mapeamento de arquivos
    manuais_map = {
        'fcvs': 'Leiautes_Movim_FCVS - 2025 - V2.pdf',
        'cadmut': 'Leiautes_Movim_CADMUT - 2025.pdf',
        'web': 'Manual_SIWFC_MAR_2025.pdf',
        'roteiro': 'Anexos-do-Roteiro-de-Analise-do-FCVS.pdf'
    }
    
    if manual.lower() not in manuais_map:
        return f"❌ Manual não reconhecido. Opções: {', '.join(manuais_map.keys())}"
    
    caminho = os.path.join(MANUAIS_PATH, manuais_map[manual.lower()])
    
    if not os.path.exists(caminho):
        return f"❌ Manual não encontrado: {caminho}"
    
    # Ler PDF e buscar por tópico
    conteudo = ler_pdf(caminho)
    
    # Filtrar por tópico (busca simples)
    topico_lower = topico.lower()
    linhas_relevantes = []
    
    for linha in conteudo.split('\n'):
        if topico_lower in linha.lower():
            linhas_relevantes.append(linha)
    
    if linhas_relevantes:
        return f"🔍 Informações sobre '{topico}' no manual {manual}:\n\n" + "\n".join(linhas_relevantes[:20])
    else:
        return f"⚠️ Tópico '{topico}' não encontrado no manual {manual}"


@tool("Construtor de Knowledge Base")
def construir_knowledge_base() -> str:
    """
    Constrói base de conhecimento a partir dos manuais CEF.
    Cria índice estruturado para consulta rápida.
    """
    knowledge = {
        'criado_em': datetime.now().isoformat(),
        'manuais': [],
        'topicos': {
            'autenticacao': [],
            'layouts': [],
            'endpoints': [],
            'processos': [],
            'erros_comuns': []
        }
    }
    
    # Analisar cada manual
    for arquivo in os.listdir(MANUAIS_PATH):
        if arquivo.endswith('.pdf'):
            caminho = os.path.join(MANUAIS_PATH, arquivo)
            
            manual_info = {
                'nome': arquivo,
                'tipo': None,
                'topicos_encontrados': []
            }
            
            # Identificar tipo
            if 'SIWFC' in arquivo:
                manual_info['tipo'] = 'web'
                manual_info['descricao'] = 'Manual do Sistema Web de Integração'
            elif 'FCVS' in arquivo and 'Leiautes' in arquivo:
                manual_info['tipo'] = 'fcvs_layouts'
                manual_info['descricao'] = 'Layouts de Movimentação FCVS'
            elif 'CADMUT' in arquivo:
                manual_info['tipo'] = 'cadmut_layouts'
                manual_info['descricao'] = 'Layouts de Cadastro de Mutuários'
            elif 'Anexos' in arquivo:
                manual_info['tipo'] = 'roteiro'
                manual_info['descricao'] = 'Roteiro de Análise e Anexos'
            
            knowledge['manuais'].append(manual_info)
    
    # Salvar knowledge base
    try:
        with open(KNOWLEDGE_BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, indent=2, ensure_ascii=False)
        
        return f"✅ Knowledge Base criada com sucesso!\n📍 {KNOWLEDGE_BASE_PATH}\n📚 {len(knowledge['manuais'])} manuais indexados"
    except Exception as e:
        return f"❌ Erro ao salvar knowledge base: {str(e)}"


# ===== AGENTE CEF INTEGRATION BOT =====

_cef_integration_bot = None

def get_cef_integration_bot():
    """Retorna agente CEF Integration Bot (singleton)"""
    global _cef_integration_bot
    
    if _cef_integration_bot is None and CREWAI_DISPONIVEL:
        _cef_integration_bot = Agent(
            role="CEF Integration Bot - Especialista em Integração Bancária",
            goal="""Dominar todos os procedimentos de integração com sistemas CEF, 
            incluindo: autenticação web, envio de fichas, processamento de retornos, 
            upload de dossiês e interpretação de layouts de arquivo.""",
            backstory="""Você é um especialista sênior em integração bancária com a Caixa 
            Econômica Federal (CEF). Possui conhecimento profundo dos sistemas SIWFC, 
            layouts de FCVS e CADMUT, e procedimentos operacionais. Sua missão é automatizar 
            toda a interação com o portal web da CEF, tornando o processo seguro, rápido e 
            confiável. Você lê manuais técnicos, interpreta especificações e implementa 
            soluções robustas.""",
            tools=[
                analisar_manuais_cef,
                ler_pdf,
                extrair_info_tecnica,
                construir_knowledge_base
            ],
            verbose=True,
            allow_delegation=True,
            max_iter=15
        )
    
    return _cef_integration_bot


# ===== FUNÇÕES AUXILIARES =====

def inicializar_knowledge_base():
    """Inicializa a knowledge base lendo todos os manuais"""
    print("\n" + "="*80)
    print("🤖 CEF INTEGRATION BOT - INICIANDO...")
    print("="*80 + "\n")
    
    if not CREWAI_DISPONIVEL:
        print("⚠️ CrewAI não disponível. Criando knowledge base manualmente...\n")
        resultado = construir_knowledge_base()
        print(resultado)
        return
    
    bot = get_cef_integration_bot()
    
    task = Task(
        description="""Analise todos os manuais CEF disponíveis e construa uma knowledge base 
        estruturada. Identifique:
        1. Procedimentos de autenticação no portal web
        2. URLs e endpoints do sistema
        3. Formatos de arquivo (FH1, RCV, FCVS)
        4. Processo de envio de fichas
        5. Formato de retornos e como processá-los
        6. Requisitos para upload de dossiês
        
        Crie um índice completo para consulta rápida.""",
        agent=bot,
        expected_output="Knowledge base estruturada com índice de todos os procedimentos CEF"
    )
    
    crew = Crew(
        agents=[bot],
        tasks=[task],
        verbose=True
    )
    
    print("\n🚀 Iniciando análise dos manuais...\n")
    resultado = crew.kickoff()
    print("\n" + "="*80)
    print("✅ ANÁLISE CONCLUÍDA")
    print("="*80)
    print(resultado)


def consultar_procedimento(procedimento: str) -> str:
    """
    Consulta knowledge base sobre procedimento específico.
    Ex: 'login', 'envio_fh1', 'download_retorno'
    """
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        return "❌ Knowledge base não encontrada. Execute inicializar_knowledge_base() primeiro."
    
    try:
        with open(KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        
        # Buscar procedimento
        resultados = []
        for topico, conteudo in kb.get('topicos', {}).items():
            if procedimento.lower() in topico.lower():
                resultados.append(f"📌 {topico.upper()}:\n" + "\n".join(conteudo))
        
        if resultados:
            return "\n\n".join(resultados)
        else:
            return f"⚠️ Procedimento '{procedimento}' não encontrado na knowledge base."
    
    except Exception as e:
        return f"❌ Erro ao consultar knowledge base: {str(e)}"


if __name__ == "__main__":
    # Testar inicialização
    print("🧪 TESTE DO CEF INTEGRATION BOT\n")
    
    # Listar manuais
    print(analisar_manuais_cef())
    
    # Construir knowledge base
    print("\n" + construir_knowledge_base())
