"""
Seletor Inteligente de Fichas CEF

Este módulo implementa lógica de decisão automática para determinar qual tipo
de ficha CEF deve ser enviada baseado no contexto, situação do contrato e histórico.

Funcionalidades:
- Análise de situação do contrato
- Decisão automática de tipo de ficha (FH1, FH2, FH3, RCV, RNV, CADMUT)
- Regras baseadas em:
  * Estado do contrato (novo, alterado, quitado)
  * Histórico de envios anteriores
  * Tipo de operação (inclusão, alteração, exclusão)
  * Documentação pendente
  * Situação cadastral do mutuário
- Sugestões de fichas complementares
- Validação de pré-requisitos
- Sequência automática de envios

Autor: CEF Integration Bot
Data: 2026-01-23
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class TipoFicha(Enum):
    """Tipos de fichas disponíveis"""
    FH1 = "FH1"  # Habilitação ao FCVS
    FH2 = "FH2"  # Complemento de habilitação
    FH3 = "FH3"  # Alterações contratuais
    RCV = "RCV"  # Receita
    RNV = "RNV"  # Registro
    CADMUT = "CADMUT"  # Cadastro de mutuário
    DOSSIE = "DOSSIE"  # Dossiê completo


class SituacaoContrato(Enum):
    """Situações possíveis de contrato"""
    NOVO = "NOVO"  # Nunca enviado
    ATIVO = "ATIVO"  # Já enviado e aceito
    ALTERADO = "ALTERADO"  # Com alterações não enviadas
    CRITICA = "CRITICA"  # Rejeitado com críticas
    QUITADO = "QUITADO"  # Contrato quitado
    SUSPENSO = "SUSPENSO"  # Temporariamente suspenso


class TipoOperacao(Enum):
    """Tipos de operação"""
    INCLUSAO = "I"  # Inclusão
    ALTERACAO = "A"  # Alteração
    EXCLUSAO = "E"  # Exclusão


class Recomendacao:
    """Representa uma recomendação de ficha"""
    
    def __init__(self, tipo_ficha: TipoFicha, prioridade: int = 1,
                 motivo: str = "", pre_requisitos: List[str] = None,
                 fichas_complementares: List[TipoFicha] = None):
        self.tipo_ficha = tipo_ficha
        self.prioridade = prioridade  # 1=alta, 2=média, 3=baixa
        self.motivo = motivo
        self.pre_requisitos = pre_requisitos or []
        self.fichas_complementares = fichas_complementares or []
        self.validacoes_pendentes = []
    
    def adicionar_validacao(self, validacao: str):
        """Adiciona validação pendente"""
        self.validacoes_pendentes.append(validacao)
    
    def to_dict(self):
        return {
            'tipo_ficha': self.tipo_ficha.value,
            'prioridade': self.prioridade,
            'motivo': self.motivo,
            'pre_requisitos': self.pre_requisitos,
            'fichas_complementares': [f.value for f in self.fichas_complementares],
            'validacoes_pendentes': self.validacoes_pendentes
        }


class FichaSelector:
    """
    Seletor inteligente de fichas
    
    Analisa contexto e decide qual ficha enviar
    """
    
    def __init__(self):
        self.regras = self._carregar_regras()
    
    def _carregar_regras(self) -> Dict:
        """Carrega regras de decisão"""
        return {
            'novo_contrato': {
                'situacao': SituacaoContrato.NOVO,
                'fichas': [TipoFicha.CADMUT, TipoFicha.FH1],
                'sequencia': True
            },
            'alteracao_contrato': {
                'situacao': SituacaoContrato.ALTERADO,
                'fichas': [TipoFicha.FH3],
                'pre_requisito': 'FH1_ACEITO'
            },
            'correcao_critica': {
                'situacao': SituacaoContrato.CRITICA,
                'fichas': [TipoFicha.FH1],  # Reenvia com correções
                'tipo_operacao': TipoOperacao.ALTERACAO
            },
            'cadastro_mutuario': {
                'condicao': 'mutuario_sem_cadastro',
                'fichas': [TipoFicha.CADMUT],
                'prioridade': 1
            }
        }
    
    def selecionar_ficha(self, contrato, mutuario=None, 
                        historico_envios: List = None) -> List[Recomendacao]:
        """
        Seleciona ficha(s) apropriada(s) para o contrato
        
        Args:
            contrato: Instância de Contrato Django
            mutuario: Instância de Mutuario (opcional)
            historico_envios: Lista de envios anteriores
        
        Returns:
            Lista de recomendações ordenadas por prioridade
        """
        recomendacoes = []
        
        # Determina situação atual
        situacao = self._determinar_situacao(contrato, historico_envios)
        
        # Verifica se mutuário precisa cadastro
        if mutuario and self._precisa_cadastro_mutuario(mutuario, historico_envios):
            rec = Recomendacao(
                tipo_ficha=TipoFicha.CADMUT,
                prioridade=1,
                motivo="Mutuário não possui cadastro válido na CEF",
                pre_requisitos=["CPF válido", "Dados cadastrais completos"]
            )
            recomendacoes.append(rec)
        
        # Aplica regras baseadas na situação
        if situacao == SituacaoContrato.NOVO:
            recomendacoes.extend(self._regras_novo_contrato(contrato, mutuario))
        
        elif situacao == SituacaoContrato.ALTERADO:
            recomendacoes.extend(self._regras_alteracao(contrato, historico_envios))
        
        elif situacao == SituacaoContrato.CRITICA:
            recomendacoes.extend(self._regras_correcao(contrato, historico_envios))
        
        elif situacao == SituacaoContrato.ATIVO:
            # Contrato ativo, verifica se há alterações pendentes
            if self._tem_alteracoes_pendentes(contrato, historico_envios):
                recomendacoes.extend(self._regras_alteracao(contrato, historico_envios))
        
        # Ordena por prioridade
        recomendacoes.sort(key=lambda x: x.prioridade)
        
        return recomendacoes
    
    def _determinar_situacao(self, contrato, historico_envios: List) -> SituacaoContrato:
        """Determina situação atual do contrato"""
        
        if not historico_envios:
            return SituacaoContrato.NOVO
        
        # Pega último envio
        ultimo_envio = historico_envios[-1] if historico_envios else None
        
        if ultimo_envio:
            status = getattr(ultimo_envio, 'status', None)
            
            if status == 'REJEITADO' or status == 'CRITICA':
                return SituacaoContrato.CRITICA
            
            elif status == 'ACEITO':
                # Verifica se houve alterações depois
                data_envio = getattr(ultimo_envio, 'data_envio', None)
                if data_envio and hasattr(contrato, 'data_alteracao'):
                    if contrato.data_alteracao and contrato.data_alteracao > data_envio:
                        return SituacaoContrato.ALTERADO
                
                return SituacaoContrato.ATIVO
        
        return SituacaoContrato.NOVO
    
    def _precisa_cadastro_mutuario(self, mutuario, historico_envios: List) -> bool:
        """Verifica se mutuário precisa de cadastro CEF"""
        
        if not mutuario:
            return False
        
        # Verifica se já foi enviado CADMUT aceito
        if historico_envios:
            for envio in historico_envios:
                if getattr(envio, 'tipo_envio', '') == 'CADMUT' and \
                   getattr(envio, 'status', '') == 'ACEITO':
                    return False
        
        return True
    
    def _regras_novo_contrato(self, contrato, mutuario) -> List[Recomendacao]:
        """Regras para novo contrato"""
        recomendacoes = []
        
        # FH1 obrigatório para habilitação
        rec_fh1 = Recomendacao(
            tipo_ficha=TipoFicha.FH1,
            prioridade=1,
            motivo="Contrato novo precisa ser habilitado ao FCVS",
            pre_requisitos=[
                "Dados contratuais completos",
                "Mutuário cadastrado",
                "Parcelas importadas"
            ]
        )
        
        # Verifica dados mínimos
        if not contrato.codigo:
            rec_fh1.adicionar_validacao("Número do contrato não informado")
        
        if not contrato.data_contrato:
            rec_fh1.adicionar_validacao("Data do contrato não informada")
        
        if not mutuario:
            rec_fh1.adicionar_validacao("Mutuário não vinculado")
        
        recomendacoes.append(rec_fh1)
        
        # FH2 pode ser necessário para dados complementares
        if self._precisa_fh2(contrato):
            rec_fh2 = Recomendacao(
                tipo_ficha=TipoFicha.FH2,
                prioridade=2,
                motivo="Dados complementares de habilitação",
                pre_requisitos=["FH1 enviado e aceito"]
            )
            recomendacoes.append(rec_fh2)
        
        return recomendacoes
    
    def _regras_alteracao(self, contrato, historico_envios: List) -> List[Recomendacao]:
        """Regras para alteração de contrato"""
        recomendacoes = []
        
        # Verifica se FH1 foi aceito
        fh1_aceito = self._verifica_ficha_aceita(historico_envios, 'FH1')
        
        if not fh1_aceito:
            rec = Recomendacao(
                tipo_ficha=TipoFicha.FH1,
                prioridade=1,
                motivo="Necessário enviar FH1 antes de registrar alterações",
                pre_requisitos=[]
            )
            recomendacoes.append(rec)
        else:
            # FH3 para registrar alterações
            rec = Recomendacao(
                tipo_ficha=TipoFicha.FH3,
                prioridade=1,
                motivo="Registrar alterações contratuais",
                pre_requisitos=["FH1 aceito"]
            )
            recomendacoes.append(rec)
        
        return recomendacoes
    
    def _regras_correcao(self, contrato, historico_envios: List) -> List[Recomendacao]:
        """Regras para correção de críticas"""
        recomendacoes = []
        
        # Pega último envio com crítica
        ultimo_critica = None
        if historico_envios:
            for envio in reversed(historico_envios):
                if getattr(envio, 'status', '') in ['REJEITADO', 'CRITICA']:
                    ultimo_critica = envio
                    break
        
        if ultimo_critica:
            tipo_original = getattr(ultimo_critica, 'tipo_envio', 'FH1')
            
            # Mapeia tipo de ficha
            tipo_ficha = TipoFicha.FH1  # Padrão
            if tipo_original == 'FH3':
                tipo_ficha = TipoFicha.FH3
            elif tipo_original == 'CADMUT':
                tipo_ficha = TipoFicha.CADMUT
            
            rec = Recomendacao(
                tipo_ficha=tipo_ficha,
                prioridade=1,
                motivo=f"Reenviar {tipo_original} com correções das críticas",
                pre_requisitos=["Críticas corrigidas"]
            )
            
            # Adiciona códigos de crítica
            if hasattr(ultimo_critica, 'codigos_critica'):
                rec.adicionar_validacao(f"Corrigir códigos: {ultimo_critica.codigos_critica}")
            
            recomendacoes.append(rec)
        
        return recomendacoes
    
    def _tem_alteracoes_pendentes(self, contrato, historico_envios: List) -> bool:
        """Verifica se há alterações não enviadas"""
        
        if not historico_envios:
            return False
        
        # Verifica se data de alteração é posterior ao último envio
        ultimo_envio = historico_envios[-1]
        data_ultimo = getattr(ultimo_envio, 'data_envio', None)
        
        if hasattr(contrato, 'data_alteracao') and contrato.data_alteracao and data_ultimo:
            return contrato.data_alteracao > data_ultimo
        
        return False
    
    def _precisa_fh2(self, contrato) -> bool:
        """Verifica se precisa FH2 (dados complementares)"""
        # FH2 necessário para casos específicos (implementar lógica conforme manual)
        return False
    
    def _verifica_ficha_aceita(self, historico_envios: List, tipo: str) -> bool:
        """Verifica se ficha do tipo foi aceita"""
        if not historico_envios:
            return False
        
        for envio in historico_envios:
            if getattr(envio, 'tipo_envio', '') == tipo and \
               getattr(envio, 'status', '') == 'ACEITO':
                return True
        
        return False


class SequenciadorFichas:
    """
    Sequenciador automático de envio de fichas
    
    Gerencia ordem e dependências entre múltiplas fichas
    """
    
    def __init__(self):
        self.selector = FichaSelector()
        self.dependencias = self._definir_dependencias()
    
    def _definir_dependencias(self) -> Dict:
        """Define dependências entre fichas"""
        return {
            TipoFicha.FH1: [],  # Sem dependências
            TipoFicha.FH2: [TipoFicha.FH1],  # Depende de FH1
            TipoFicha.FH3: [TipoFicha.FH1],  # Depende de FH1
            TipoFicha.RCV: [TipoFicha.FH1],  # Depende de FH1
            TipoFicha.RNV: [],  # Sem dependências
            TipoFicha.CADMUT: [],  # Sem dependências
        }
    
    def gerar_sequencia(self, contratos: List, mutuarios: List = None) -> Dict[str, Any]:
        """
        Gera sequência automática de envios para múltiplos contratos
        
        Args:
            contratos: Lista de contratos
            mutuarios: Lista de mutuários (opcional)
        
        Returns:
            Dicionário com sequência organizada
        """
        sequencia = {
            'lotes': [],
            'total_fichas': 0,
            'total_contratos': len(contratos),
            'estimativa_tempo': None
        }
        
        # Agrupa por tipo de ficha
        por_tipo = {tipo: [] for tipo in TipoFicha}
        
        for i, contrato in enumerate(contratos):
            mutuario = mutuarios[i] if mutuarios and i < len(mutuarios) else None
            
            # Pega recomendações
            recomendacoes = self.selector.selecionar_ficha(contrato, mutuario, [])
            
            for rec in recomendacoes:
                por_tipo[rec.tipo_ficha].append({
                    'contrato': contrato,
                    'mutuario': mutuario,
                    'recomendacao': rec
                })
        
        # Organiza em lotes respeitando dependências
        lote_num = 1
        
        # Lote 1: Fichas sem dependências (CADMUT, RNV)
        lote1 = []
        for tipo in [TipoFicha.CADMUT, TipoFicha.RNV]:
            if por_tipo[tipo]:
                lote1.extend(por_tipo[tipo])
        
        if lote1:
            sequencia['lotes'].append({
                'numero': lote_num,
                'descricao': 'Cadastros e registros base',
                'fichas': lote1,
                'pode_executar': True
            })
            lote_num += 1
        
        # Lote 2: FH1 (habilitações)
        if por_tipo[TipoFicha.FH1]:
            sequencia['lotes'].append({
                'numero': lote_num,
                'descricao': 'Habilitações ao FCVS (FH1)',
                'fichas': por_tipo[TipoFicha.FH1],
                'pode_executar': len(lote1) == 0,  # Só executa se lote 1 estiver vazio ou concluído
                'aguarda_lote': 1 if lote1 else None
            })
            lote_num += 1
        
        # Lote 3: Complementares (FH2, FH3, RCV)
        lote3 = []
        for tipo in [TipoFicha.FH2, TipoFicha.FH3, TipoFicha.RCV]:
            if por_tipo[tipo]:
                lote3.extend(por_tipo[tipo])
        
        if lote3:
            sequencia['lotes'].append({
                'numero': lote_num,
                'descricao': 'Complementos e alterações',
                'fichas': lote3,
                'pode_executar': False,
                'aguarda_lote': 2  # Aguarda FH1
            })
        
        # Calcula totais
        sequencia['total_fichas'] = sum(len(lote['fichas']) for lote in sequencia['lotes'])
        
        # Estima tempo (2 minutos por ficha, em média)
        sequencia['estimativa_tempo'] = sequencia['total_fichas'] * 2
        
        return sequencia
    
    def validar_dependencias(self, fichas_enviadas: List[TipoFicha], 
                            ficha_desejada: TipoFicha) -> Tuple[bool, List[str]]:
        """
        Valida se dependências foram satisfeitas
        
        Args:
            fichas_enviadas: Fichas já enviadas e aceitas
            ficha_desejada: Ficha que se deseja enviar
        
        Returns:
            Tupla (pode_enviar, fichas_pendentes)
        """
        dependencias = self.dependencias.get(ficha_desejada, [])
        
        fichas_pendentes = []
        for dep in dependencias:
            if dep not in fichas_enviadas:
                fichas_pendentes.append(dep.value)
        
        pode_enviar = len(fichas_pendentes) == 0
        
        return (pode_enviar, fichas_pendentes)


# Funções auxiliares de alto nível

def selecionar_ficha_automatica(contrato, mutuario=None, historico_envios=None) -> Dict:
    """
    Seleciona ficha automaticamente para um contrato
    
    Args:
        contrato: Instância de Contrato
        mutuario: Instância de Mutuario
        historico_envios: Lista de EnvioCEF
    
    Returns:
        Dicionário com recomendação principal
    """
    selector = FichaSelector()
    recomendacoes = selector.selecionar_ficha(contrato, mutuario, historico_envios or [])
    
    if recomendacoes:
        principal = recomendacoes[0]
        return {
            'ficha_recomendada': principal.tipo_ficha.value,
            'prioridade': principal.prioridade,
            'motivo': principal.motivo,
            'pre_requisitos': principal.pre_requisitos,
            'pode_enviar': len(principal.validacoes_pendentes) == 0,
            'validacoes_pendentes': principal.validacoes_pendentes
        }
    
    return {
        'ficha_recomendada': None,
        'motivo': 'Nenhuma ficha necessária no momento'
    }


def gerar_plano_envio(contratos: List) -> Dict:
    """
    Gera plano de envio para múltiplos contratos
    
    Args:
        contratos: Lista de contratos
    
    Returns:
        Plano de envio sequenciado
    """
    sequenciador = SequenciadorFichas()
    return sequenciador.gerar_sequencia(contratos)


# Exemplo de uso
if __name__ == '__main__':
    print("🧠 Seletor Inteligente de Fichas CEF")
    print("=" * 60)
    
    # Mock de contrato
    class MockContrato:
        def __init__(self, codigo, situacao='novo'):
            self.codigo = codigo
            self.data_contrato = date(2020, 1, 15)
            self.situacao = situacao
    
    class MockMutuario:
        def __init__(self):
            self.cpf = "12345678909"
            self.nome = "JOÃO DA SILVA"
    
    # Teste 1: Contrato novo
    print("\n📄 Teste 1: Contrato novo")
    contrato1 = MockContrato("0001", "novo")
    mutuario1 = MockMutuario()
    
    resultado = selecionar_ficha_automatica(contrato1, mutuario1, [])
    print(f"   Ficha recomendada: {resultado['ficha_recomendada']}")
    print(f"   Motivo: {resultado['motivo']}")
    print(f"   Pode enviar: {resultado['pode_enviar']}")
    
    if resultado['pre_requisitos']:
        print(f"   Pré-requisitos:")
        for pre in resultado['pre_requisitos']:
            print(f"      • {pre}")
    
    # Teste 2: Múltiplos contratos (sequenciamento)
    print("\n📦 Teste 2: Plano de envio para 3 contratos")
    contratos = [
        MockContrato("0001", "novo"),
        MockContrato("0002", "novo"),
        MockContrato("0003", "novo")
    ]
    
    plano = gerar_plano_envio(contratos)
    print(f"   Total de contratos: {plano['total_contratos']}")
    print(f"   Total de fichas: {plano['total_fichas']}")
    print(f"   Estimativa de tempo: {plano['estimativa_tempo']} minutos")
    print(f"   Lotes organizados: {len(plano['lotes'])}")
    
    for lote in plano['lotes']:
        print(f"\n   Lote {lote['numero']}: {lote['descricao']}")
        print(f"      Fichas: {len(lote['fichas'])}")
        print(f"      Pode executar: {'✅ Sim' if lote['pode_executar'] else '⏳ Aguardando'}")
    
    # Teste 3: Validação de dependências
    print("\n🔗 Teste 3: Validação de dependências")
    sequenciador = SequenciadorFichas()
    
    # Tenta enviar FH3 sem ter FH1
    pode, pendentes = sequenciador.validar_dependencias([], TipoFicha.FH3)
    print(f"   Pode enviar FH3 sem FH1? {pode}")
    if pendentes:
        print(f"   Fichas pendentes: {', '.join(pendentes)}")
    
    # Com FH1 aceito
    pode, pendentes = sequenciador.validar_dependencias([TipoFicha.FH1], TipoFicha.FH3)
    print(f"   Pode enviar FH3 com FH1 aceito? {pode}")
    
    print("\n✅ Testes de seleção inteligente concluídos!")
    print("\n💡 Próximos passos:")
    print("   1. Integrar com views Django")
    print("   2. Adicionar regras mais complexas")
    print("   3. Machine learning para otimizar seleção")
    print("   4. Dashboard de planejamento de envios")
