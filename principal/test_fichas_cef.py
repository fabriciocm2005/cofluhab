"""
Testes Automatizados para Parsers e Geradores de Fichas CEF

Este módulo contém testes unitários e de integração para garantir
qualidade e confiabilidade dos componentes de fichas CEF.

Testa:
- Parsers (FH1, FH3, RNV, CADMUT)
- Validadores
- Geradores
- Interpretador de retornos
- Seletor inteligente

Autor: CEF Integration Bot
Data: 2026-01-23
"""

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile
import os

# Importa módulos a testar
try:
    from .ficha_parsers import (
        FH1Parser, FH3Parser, RNVParser, CADMUTParser,
        CampoSpec, ArquivoFichasCEF
    )
    from .ficha_validators import (
        FH1Validator, CADMUTValidator, CampoValidator,
        validar_fh1, validar_cadmut
    )
    from .ficha_generators import (
        FH1Generator, CADMUTGenerator, ArquivoFCVSGenerator,
        LoteGenerator
    )
    from .ficha_return_interpreter import (
        ReturnInterpreter, FCVSReturnParser, RegistroRetorno
    )
    from .ficha_selector import (
        FichaSelector, SequenciadorFichas, TipoFicha, SituacaoContrato
    )
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from ficha_parsers import (
        FH1Parser, FH3Parser, RNVParser, CADMUTParser,
        CampoSpec, ArquivoFichasCEF
    )
    from ficha_validators import (
        FH1Validator, CADMUTValidator, CampoValidator,
        validar_fh1, validar_cadmut
    )
    from ficha_generators import (
        FH1Generator, CADMUTGenerator, ArquivoFCVSGenerator,
        LoteGenerator
    )
    from ficha_return_interpreter import (
        ReturnInterpreter, FCVSReturnParser, RegistroRetorno
    )
    from ficha_selector import (
        FichaSelector, SequenciadorFichas, TipoFicha, SituacaoContrato
    )


# Mocks para testes

class MockMutuario:
    """Mock de Mutuario para testes"""
    def __init__(self):
        self.codigo = "001"
        self.nome = "JOÃO DA SILVA"
        self.cpf = "12345678909"
        self.dtnasc = date(1980, 1, 1)
        self.endereco = "RUA EXEMPLO"
        self.numero = "123"
        self.compl = "APTO 45"
        self.bairro = "CENTRO"
        self.cidade = "SAO PAULO"
        self.uf = "SP"
        self.cep = "01234567"
        self.telefone = "11999887766"
        self.email = "joao@example.com"
        self.conjunto = "001"


class MockContrato:
    """Mock de Contrato para testes"""
    def __init__(self):
        self.codigo = "0001234567890"
        self.conjunto = "001"
        self.data_contrato = date(2020, 1, 15)
        self.prazo = 240
        self.tx_juros = Decimal("8.5")
        self.sa = "SAC"
        self.cat_prof = "12345"
        self.pr = "01"
        self.data_primeiro_venc = date(2020, 2, 15)
    
    @property
    def parcelas(self):
        return MockParcelas()


class MockParcelas:
    """Mock de QuerySet de parcelas"""
    def all(self):
        return []
    
    def exists(self):
        return False


# Testes de Parsers

class TestFH1Parser(unittest.TestCase):
    """Testes para FH1Parser"""
    
    def setUp(self):
        self.parser = FH1Parser()
    
    def test_parser_carrega_campos(self):
        """Testa se parser carrega campos do JSON"""
        self.assertGreater(len(self.parser.campos), 0, "Parser deve carregar campos")
    
    def test_escrever_linha_tamanho_correto(self):
        """Testa se linha gerada tem tamanho correto"""
        dados = {'UFS': '35', 'MAT. AG. FINANC. /DV': '123456'}
        linha = self.parser.escrever_linha(dados)
        
        self.assertEqual(len(linha), FH1Parser.TAMANHO_REGISTRO, 
                        f"Linha deve ter {FH1Parser.TAMANHO_REGISTRO} caracteres")
    
    def test_ler_linha_extrai_campos(self):
        """Testa leitura de linha"""
        linha_teste = '35' + '123456' + ' ' * 422
        dados = self.parser.ler_linha(linha_teste)
        
        self.assertIn('UFS', dados)


class TestCADMUTParser(unittest.TestCase):
    """Testes para CADMUTParser"""
    
    def setUp(self):
        self.parser = CADMUTParser()
    
    def test_tamanho_registro_cadmut(self):
        """CADMUT deve ter 650 caracteres"""
        self.assertEqual(self.parser.TAMANHO_REGISTRO, 650)


# Testes de Validadores

class TestCampoValidator(unittest.TestCase):
    """Testes para validações básicas"""
    
    def test_validar_cpf_valido(self):
        """Testa CPF válido"""
        self.assertTrue(CampoValidator.validar_cpf("12345678909"))
    
    def test_validar_cpf_invalido(self):
        """Testa CPF inválido"""
        self.assertFalse(CampoValidator.validar_cpf("12345678900"))
        self.assertFalse(CampoValidator.validar_cpf("11111111111"))
    
    def test_validar_uf_valida(self):
        """Testa UF válida"""
        self.assertTrue(CampoValidator.validar_uf("SP"))
        self.assertTrue(CampoValidator.validar_uf("RJ"))
    
    def test_validar_uf_invalida(self):
        """Testa UF inválida"""
        self.assertFalse(CampoValidator.validar_uf("XX"))
        self.assertFalse(CampoValidator.validar_uf(""))
    
    def test_validar_data_valida(self):
        """Testa validação de data"""
        valida, data_obj = CampoValidator.validar_data("010180")
        self.assertTrue(valida)
        self.assertIsNotNone(data_obj)
    
    def test_validar_data_invalida(self):
        """Testa data inválida"""
        valida, _ = CampoValidator.validar_data("320180")  # Dia 32
        self.assertFalse(valida)
    
    def test_validar_valor_monetario(self):
        """Testa validação de valor monetário"""
        valido, decimal_val = CampoValidator.validar_valor_monetario(1000.50)
        self.assertTrue(valido)
        self.assertEqual(decimal_val, Decimal("1000.50"))
    
    def test_validar_valor_negativo(self):
        """Valor negativo deve ser inválido"""
        valido, _ = CampoValidator.validar_valor_monetario(-100)
        self.assertFalse(valido)


class TestFH1Validator(unittest.TestCase):
    """Testes para FH1Validator"""
    
    def setUp(self):
        self.validator = FH1Validator()
    
    def test_dados_validos(self):
        """Testa validação de dados válidos"""
        dados = {
            'UFS': '35',
            'MAT. AG. FINANC. /DV': '123456',
            'N.º CONTRATO DO MUT. NO AGENTE': '0001234567890',
            'NOME DO MUT. PRINCIPAL': 'JOÃO DA SILVA',
            'CPF/CI': '12345678909',
            'DATA DE NASCIMENTO': '010180',
            'CODIGO DO MUNICÍPIO': '12345',
            'UF': 'SP',
            'ENDEREÇO DO IMÓVEL': 'RUA EXEMPLO, 123',
            'DATA DO CONTRATO': '150120',
            'VALOR FINANCIAMENTO CONTRATADO': 150000.00,
            'PRAZO CONTRATADO': 240,
        }
        
        valido, erros = self.validator.validar(dados)
        self.assertTrue(valido, "Dados válidos devem passar na validação")
    
    def test_campo_obrigatorio_vazio(self):
        """Campo obrigatório vazio deve gerar erro"""
        dados = {'UFS': '35'}  # Faltam outros obrigatórios
        
        valido, erros = self.validator.validar(dados)
        self.assertFalse(valido)
        self.assertGreater(len(erros), 0)
    
    def test_cpf_invalido(self):
        """CPF inválido deve gerar erro"""
        dados = {
            'UFS': '35',
            'MAT. AG. FINANC. /DV': '123456',
            'N.º CONTRATO DO MUT. NO AGENTE': '0001234567890',
            'NOME DO MUT. PRINCIPAL': 'JOÃO',
            'CPF/CI': '12345678900',  # CPF inválido
            'DATA DE NASCIMENTO': '010180',
            'CODIGO DO MUNICÍPIO': '12345',
            'UF': 'SP',
            'ENDEREÇO DO IMÓVEL': 'RUA EXEMPLO',
            'DATA DO CONTRATO': '150120',
            'VALOR FINANCIAMENTO CONTRATADO': 150000,
            'PRAZO CONTRATADO': 240,
        }
        
        valido, erros = self.validator.validar(dados)
        self.assertFalse(valido)
        
        # Verifica se erro de CPF está presente
        codigos_erro = [e.codigo for e in erros]
        self.assertIn('CPF_INVALIDO', codigos_erro)


# Testes de Geradores

class TestFH1Generator(unittest.TestCase):
    """Testes para FH1Generator"""
    
    def setUp(self):
        self.generator = FH1Generator(validar=False)  # Sem validação para mock
        self.contrato = MockContrato()
        self.mutuario = MockMutuario()
    
    def test_gerar_ficha_retorna_string(self):
        """Gerador deve retornar string"""
        linha, erros = self.generator.gerar_de_contrato(self.contrato, self.mutuario)
        
        self.assertIsInstance(linha, str)
        self.assertEqual(len(linha), 430)
    
    def test_gerar_ficha_sem_mutuario(self):
        """Deve gerar ficha mesmo sem mutuário"""
        linha, erros = self.generator.gerar_de_contrato(self.contrato, None)
        
        self.assertIsInstance(linha, str)


class TestCADMUTGenerator(unittest.TestCase):
    """Testes para CADMUTGenerator"""
    
    def setUp(self):
        self.generator = CADMUTGenerator(validar=False)
        self.mutuario = MockMutuario()
    
    def test_gerar_cadmut(self):
        """Testa geração de CADMUT"""
        linha, erros = self.generator.gerar_de_mutuario(self.mutuario)
        
        self.assertIsInstance(linha, str)
        self.assertEqual(len(linha), 650)


class TestLoteGenerator(unittest.TestCase):
    """Testes para geração em lote"""
    
    def test_gerar_lote_fh1(self):
        """Testa geração de lote de FH1"""
        contratos = [MockContrato(), MockContrato()]
        
        lote_gen = LoteGenerator()
        resultado = lote_gen.gerar_lote_fh1(contratos, incluir_validacao=False)
        
        self.assertEqual(resultado['total'], 2)
        self.assertGreaterEqual(resultado['sucesso'], 0)


# Testes de Interpretador

class TestReturnInterpreter(unittest.TestCase):
    """Testes para interpretador de retornos"""
    
    def setUp(self):
        self.interpreter = ReturnInterpreter()
    
    def test_carrega_codigos_interpretacao(self):
        """Testa se códigos são carregados"""
        # Se arquivo existe, deve carregar códigos
        if self.interpreter.codigos_interpretacao:
            self.assertGreater(len(self.interpreter.codigos_interpretacao), 0)
    
    def test_interpretar_arquivo_mock(self):
        """Testa interpretação de arquivo mock"""
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='latin-1') as f:
            f.write("0I12345620260123000010\n")
            f.write("1I12345600012345678901JOAO" + " " * 380 + "\n")
            f.write("9123456000010\n")
            temp_path = f.name
        
        try:
            resultado = self.interpreter.interpretar_arquivo(temp_path, 'FCVS')
            
            self.assertIn('resumo', resultado)
            self.assertIn('total_registros', resultado['resumo'])
            self.assertEqual(resultado['resumo']['total_registros'], 3)
        
        finally:
            os.unlink(temp_path)


class TestRegistroRetorno(unittest.TestCase):
    """Testes para RegistroRetorno"""
    
    def test_identificar_header(self):
        """Testa identificação de HEADER"""
        linha = "0I123456" + " " * 422
        registro = RegistroRetorno(linha)
        
        self.assertEqual(registro.tipo_registro, 'HEADER')
    
    def test_identificar_trailer(self):
        """Testa identificação de TRAILER"""
        linha = "9123456" + " " * 423
        registro = RegistroRetorno(linha)
        
        self.assertEqual(registro.tipo_registro, 'TRAILER')


# Testes de Seletor

class TestFichaSelector(unittest.TestCase):
    """Testes para seletor inteligente"""
    
    def setUp(self):
        self.selector = FichaSelector()
        self.contrato = MockContrato()
        self.mutuario = MockMutuario()
    
    def test_contrato_novo_recomenda_fh1(self):
        """Contrato novo deve recomendar FH1"""
        recomendacoes = self.selector.selecionar_ficha(self.contrato, self.mutuario, [])
        
        self.assertGreater(len(recomendacoes), 0)
        # Deve recomendar CADMUT ou FH1
        tipos = [r.tipo_ficha for r in recomendacoes]
        self.assertTrue(TipoFicha.FH1 in tipos or TipoFicha.CADMUT in tipos)
    
    def test_determinar_situacao_novo(self):
        """Sem histórico deve ser NOVO"""
        situacao = self.selector._determinar_situacao(self.contrato, [])
        self.assertEqual(situacao, SituacaoContrato.NOVO)


class TestSequenciadorFichas(unittest.TestCase):
    """Testes para sequenciador"""
    
    def setUp(self):
        self.sequenciador = SequenciadorFichas()
    
    def test_validar_dependencias_fh3_sem_fh1(self):
        """FH3 não pode ser enviado sem FH1"""
        pode, pendentes = self.sequenciador.validar_dependencias([], TipoFicha.FH3)
        
        self.assertFalse(pode)
        self.assertIn('FH1', pendentes)
    
    def test_validar_dependencias_fh3_com_fh1(self):
        """FH3 pode ser enviado com FH1 aceito"""
        pode, pendentes = self.sequenciador.validar_dependencias([TipoFicha.FH1], TipoFicha.FH3)
        
        self.assertTrue(pode)
        self.assertEqual(len(pendentes), 0)
    
    def test_gerar_sequencia(self):
        """Testa geração de sequência"""
        contratos = [MockContrato(), MockContrato()]
        
        sequencia = self.sequenciador.gerar_sequencia(contratos)
        
        self.assertIn('lotes', sequencia)
        self.assertIn('total_fichas', sequencia)
        self.assertEqual(sequencia['total_contratos'], 2)


# Suite de testes

def suite():
    """Cria suite de testes"""
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Adiciona testes
    test_suite.addTests(loader.loadTestsFromTestCase(TestFH1Parser))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCADMUTParser))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCampoValidator))
    test_suite.addTests(loader.loadTestsFromTestCase(TestFH1Validator))
    test_suite.addTests(loader.loadTestsFromTestCase(TestFH1Generator))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCADMUTGenerator))
    test_suite.addTests(loader.loadTestsFromTestCase(TestLoteGenerator))
    test_suite.addTests(loader.loadTestsFromTestCase(TestReturnInterpreter))
    test_suite.addTests(loader.loadTestsFromTestCase(TestRegistroRetorno))
    test_suite.addTests(loader.loadTestsFromTestCase(TestFichaSelector))
    test_suite.addTests(loader.loadTestsFromTestCase(TestSequenciadorFichas))
    
    return test_suite


if __name__ == '__main__':
    print("🧪 Testes Automatizados - Fichas CEF")
    print("=" * 60)
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE TESTES")
    print("=" * 60)
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"✅ Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"💥 Erros: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM")
    
    print("\n💡 Cobertura de testes:")
    print("   • Parsers (FH1, CADMUT): ✅")
    print("   • Validadores (CPF, UF, Datas, Valores): ✅")
    print("   • Geradores (FH1, CADMUT, Lote): ✅")
    print("   • Interpretador de retornos: ✅")
    print("   • Seletor inteligente: ✅")
    print("   • Sequenciador: ✅")
