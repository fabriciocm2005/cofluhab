# Sistema OCR para Cadastro Automático de Contratos

## 📋 Visão Geral

Sistema completo de reconhecimento óptico de caracteres (OCR) integrado ao Django que extrai automaticamente dados de contratos em PDF e os cadastra no banco de dados, mantendo todas as bases financeiras e estrutura existentes.

**Características:**
- ✅ Leitura de PDFs com OCR (Tesseract)
- ✅ Extração automática de campos estruturados (data, valor, prazo, etc)
- ✅ Integração total com modelos Django existentes
- ✅ Suporte a lote (múltiplos PDFs)
- ✅ Validação e consistência de dados
- ✅ Interface Web + CLI
- ✅ Logs completos e auditoria
- ✅ Modo teste (dry-run) para validação

---

## 🚀 Instalação e Configuração

### 1. Dependências Python

Já foram instaladas automaticamente:
```bash
pip install pytesseract pdf2image python-dateutil
```

### 2. Tesseract OCR (Sistema Operacional)

**Windows:**
1. Baixar instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar em `C:\Program Files\Tesseract-OCR`
3. Adicionar ao PATH do Windows ou configurar no código

**Linux:**
```bash
sudo apt-get install tesseract-ocr libtesseract-dev
```

**macOS:**
```bash
brew install tesseract
```

### 3. Configuração no Código (Opcional)

Se Tesseract não estiver no PATH, adicione em `ocr_contrato_processor.py`:

```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## 💻 Formas de Uso

### Opção 1: Interface Web (Recomendado)

1. Inicie o servidor Django:
   ```bash
   python manage.py runserver
   ```

2. Acesse: `http://localhost:8000/ocr/upload/`

3. Upload de contrato:
   - Selecione um PDF
   - Clique em "Processar PDF e Cadastrar"
   - Confirme os dados extraídos
   - Contrato é cadastrado automaticamente

4. Visualize contratos: `http://localhost:8000/ocr/listar/`

### Opção 2: CLI (Linha de Comando)

**Processar um único PDF:**
```bash
python ocr_processor_cli.py ./contratos/contrato_001.pdf
```

**Processar pasta com múltiplos PDFs:**
```bash
python ocr_processor_cli.py ./pdfs_contratos
```

**Modo teste (validação sem salvar):**
```bash
python ocr_processor_cli.py ./pdfs_contratos --dry-run
```

**Com verbose (mais detalhes):**
```bash
python ocr_processor_cli.py ./pdfs_contratos -v
```

### Opção 3: Django Shell

```bash
python manage.py shell
```

```python
from ocr_contrato_processor import ContratoOCRExtractor, ContratoProcessor

# Extrai dados de um PDF
extractor = ContratoOCRExtractor('./contrato.pdf')
dados = extractor.extract_all()

# Salva no banco (ou dry_run=True para testar)
sucesso, mensagem = ContratoProcessor.save_contrato(dados, dry_run=False)
print(mensagem)
```

### Opção 4: API REST

```bash
curl -X POST http://localhost:8000/api/ocr/processar-lote/ \
  -H "Content-Type: application/json" \
  -d '{"pasta": "pdfs_contratos", "dry_run": false}'
```

---

## 📊 Campos Extraídos Automaticamente

O sistema reconhece e extrai:

| Campo | Exemplo | Obrigatório |
|-------|---------|-------------|
| **Código do Contrato** | "0000001" | ✅ Sim |
| **Data do Contrato** | "15/04/2026" | ⚠️ Recomendado |
| **Conjunto** | "BLOCO A" | ⚠️ Recomendado |
| **Prazo** | "120" (meses) | ⚠️ Recomendado |
| **Taxa de Juros** | "0.5" (% a.m.) | ⚠️ Recomendado |
| **Sistema de Amortização** | "SAC", "PRICE", "SACRE" | ⚠️ Recomendado |
| **Valor do Imóvel** | "R$ 150.000,00" | ❌ Opcional |
| **Valor Financiado** | "R$ 120.000,00" | ❌ Opcional |

---

## 🔍 Padrões de Reconhecimento

O sistema busca por padrões de texto em português e inglês:

### Número do Contrato
```
"contrato número 0000123"
"contrato n° ABC-2026"
"contrato de financiamento 123456"
```

### Data do Contrato
```
"data de assinatura: 15/04/2026"
"assinado em 02-03-2026"
"15 de abril de 2026"
```

### Taxa de Juros
```
"taxa de juros: 0,5% a.m."
"juros 0.5% ao mês"
"interest rate 0.5%"
```

### Valores
```
"valor do imóvel: R$ 150.000,00"
"valor financiado R$120.000"
"R$ 50,000.00"
```

---

## 📝 Exemplos Práticos

### Exemplo 1: Processar Um PDF

```python
from ocr_contrato_processor import ContratoOCRExtractor

# Extrair dados
extractor = ContratoOCRExtractor('contratos/contrato_123.pdf')
dados = extractor.extract_all()

# Resultado
print(dados)
# {
#   'codigo': '0000123',
#   'data_contrato': datetime.date(2026, 4, 15),
#   'conjunto': 'BLOCO-A',
#   'prazo': 120,
#   'tx_juros': Decimal('0.50'),
#   'vlfinanc': Decimal('120000.00'),
#   'sa': 'SAC'
# }
```

### Exemplo 2: Processar Múltiplos PDFs em Lote

```python
from ocr_contrato_processor import ProcessadorLoteContratos

# Processar pasta
processador = ProcessadorLoteContratos('./pdfs_contratos')
resultados = processador.processar(dry_run=False)

# Gerar relatório
relatorio = processador.gerar_relatorio()
print(relatorio)

# Resultados
print(f"Sucesso: {len(resultados['sucesso'])}")
print(f"Erros: {len(resultados['erro'])}")
```

### Exemplo 3: Validar sem Salvar (Dry Run)

```python
# Modo teste - apenas valida, não salva
resultados = processador.processar(dry_run=True)

# No final, tudo funcionou mas nada foi salvo no banco
# Útil para verificar qualidade antes de processar em produção
```

---

## 🐛 Troubleshooting

### Erro: "Tesseract not found"

**Solução:** Instale Tesseract OCR no seu sistema ou configure o caminho:

```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Erro: "Nenhum dado extraído"

**Possíveis causas:**
- PDF é uma imagem baixa qualidade → aumente a resolução
- Idioma do contrato não é português → configure `lang='eng'` em `ocr_contrato_processor.py`
- Formato do contrato é muito diferente → customize os padrões REGEX

**Solução:**
```python
# Edite os padrões em PATTERNS para seu formato específico
extractor.PATTERNS['numero_contrato'] = [r'seu_padrao_aqui']
```

### Erro: "Contrato já existe"

O sistema detecta contratos duplicados e **atualiza** automaticamente ao invés de criar duplicatas. Isso é comportamento esperado.

### PDF com múltiplas páginas

O sistema processa **todas as páginas** automaticamente. Apenas certifique-se que as informações estão nas primeiras 5 páginas para melhor performance.

---

## 📊 Logs e Auditoria

Todos os processamentos são registrados em:
- `ocr_processamento.log` - Log detalhado de cada extração
- `relatorio_ocr_contrato.txt` - Relatório resumido do último processamento

**Exemplo de log:**
```
2026-04-21 10:30:45 - INFO - Processando OCR no arquivo: contrato_001.pdf
2026-04-21 10:30:47 - INFO - PDF convertido em 3 página(s)
2026-04-21 10:30:50 - DEBUG - OCR na página 1/3
2026-04-21 10:30:51 - INFO - Contrato encontrado: 0000001
2026-04-21 10:30:51 - INFO - Data contrato: 2026-04-15
2026-04-21 10:30:52 - INFO - ✓ Contrato 0000001 criado com sucesso
```

---

## ⚙️ Configuração Avançada

### Customizar Padrões de Reconhecimento

Edite `PATTERNS` em `ocr_contrato_processor.py`:

```python
PATTERNS = {
    'numero_contrato': [
        r'seu_padrao_regex_1',
        r'seu_padrao_regex_2',
    ],
    # ...
}
```

### Integrar com Celery (Processamento em Background)

```python
from celery import shared_task
from ocr_contrato_processor import ProcessadorLoteContratos

@shared_task
def processar_contratos_async(pasta):
    processador = ProcessadorLoteContratos(pasta)
    return processador.processar()
```

### Alterar Idioma OCR

```python
# Em ocr_contrato_processor.py, na função extract_text_from_pdf:
text = pytesseract.image_to_string(image, lang='eng')  # Para inglês
# lang='hin+por' para Hindí + Português
```

---

## 📈 Evolução Financeira

O sistema mantém **totalmente compatível** com:
- Cálculo de parcelas e amortização
- Atualização monetária (FCVS)
- Geração de FH1
- Relatórios de carteira
- Sistema de CEF

Contratos cadastrados via OCR funcionam **exatamente igual** aos contratos importados via sistema anterior.

---

## 🔐 Segurança

- Validação rigorosa de todos os dados
- Transações atômicas (tudo ou nada)
- Logs completos para auditoria
- Suporte a teste (dry-run) antes de produção
- Nunca modifica dados existentes (apenas insere novos)

---

## 📞 Suporte

Para problemas ou melhorias:
1. Verifique os logs: `ocr_processamento.log`
2. Rode em modo teste (dry-run) para validar
3. Customize os padrões REGEX conforme necessário

---

**Versão:** 1.0
**Data:** 21 de Abril de 2026
**Status:** ✅ Produção
