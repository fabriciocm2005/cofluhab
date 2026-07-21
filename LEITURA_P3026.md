# 📊 Sistema de Leitura e Visualização P3026

## Visão Geral

Sistema completo para leitura, interpretação e visualização de arquivos **P3026** - Arquivo de Posição da Carteira Homologada da CEF (Caixa Econômica Federal).

O arquivo P3026 vem **codificado em formato de posições fixas** (arquivo de texto com campos em posições específicas), e este sistema o converte em uma **visualização HTML amigável** com filtros e detalhes expandíveis.

## Estrutura de Arquivos

```
principal/
├── ficha_p3026_parser_v2.py          # Parser aprimorado com suporte a TR1-TR9
├── ficha_p3026_layout.json           # Especificação de layout extraída do Excel
├── templates/
│   └── cef_visualizar_p3026.html     # Template HTML amigável
└── views_cef.py                       # View para servir a página

externo/
├── extrair_layout_p3026.py           # Script para extrair layout do Excel
└── Leiaute_FCVS3026_TR1_a_TR9_270417 (1).xls  # Arquivo de layout original
```

## O Arquivo de Layout

O arquivo Excel **Leiaute_FCVS3026_TR1_a_TR9_270417.xls** contém a especificação técnica de todos os tipos de registro:

| Tipo | Descrição | Campos |
|------|-----------|--------|
| **TR1** | Contratos habilitados não homologados | 25 |
| **TR2** | Contratos com responsabilidade de replanejamento | 46 |
| **TR3** | Contratos com responsabilidade de alteração cadastral | 41 |
| **TR4** | Contratos com responsabilidade de outra natureza | 40 |
| **TR5** | Contratos com responsabilidade associada à cobertura | 35 |
| **TR6** | Contratos com responsabilidade por incidir evento | 39 |
| **TR7** | Contratos quitados | 40 |
| **TR8** | Contratos cancelados | 35 |
| **TR9** | Trailer/Rodapé | 33 |

## Como Usar

### 1. **Extrair Layout (Primeira Vez)**

Se precisar atualizar o layout a partir do arquivo Excel:

```bash
python extrair_layout_p3026.py
```

Isso gera `principal/ficha_p3026_layout.json` com todas as especificações.

### 2. **Acessar a Interface**

Acesse a URL no navegador:

```
http://127.0.0.1:8000/principal/cef/p3026/visualizar/
```

### 3. **Fazer Upload de um Arquivo P3026**

1. Clique em "Escolher arquivo"
2. Selecione um arquivo `.txt` recebido da CEF
3. Clique em "Carregar Arquivo"

### 4. **Visualizar Dados**

A interface mostra:

- **Painel Esquerdo**: Resumo e estatísticas
  - Total de registros
  - Data de geração
  - Código do agente
  - Distribuição por tipo (TR1-TR8)

- **Painel Direito**: Registros expandíveis
  - Cada registro mostra tipo, número do contrato e CPF
  - Clique para expandir e ver detalhes completos
  - Botões para "Expandir Tudo" / "Retrair Tudo"

## Estrutura do Parser

### ParserP3026

```python
from principal.ficha_p3026_parser_v2 import ParserP3026

# Usar parser
parser = ParserP3026()
arquivo, erros = parser.parse_arquivo('meu_arquivo_p3026.txt')

# Acessar dados
print(f"Total de registros: {len(arquivo.registros)}")
print(f"Resumo: {arquivo.resumo()}")

# Filtrar por tipo
registros_tr1 = arquivo.filtrar_por_tipo('1')
registros_tr4 = arquivo.filtrar_por_tipo('4')

# Filtrar por CPF
registros_cpf = arquivo.filtrar_por_cpf('12345678901')
```

### Dados de um Registro

```python
registro = arquivo.registros[0]

print(f"Tipo: {registro.tipo_registro}")
print(f"Contrato: {registro.numero_contrato}")
print(f"CPF: {registro.cpf_mutuario}")
print(f"Dados: {registro.dados}")  # Dicionário com todos os campos
```

## Formato do Arquivo JSON de Layout

```json
{
  "TR1": {
    "descricao": "Tipo de Registro 1",
    "total_campos": 25,
    "campos": [
      {
        "sequencia": "1",
        "nome": "TIPO DE REGISTRO = 1",
        "posicao": "001 A 001",
        "tamanho": "001",
        "formato": "9 (1)",
        "descricao": "NUMERICO"
      },
      ...
    ]
  },
  ...
}
```

## Integração com o Sistema

### URLs Disponíveis

```python
# Visualizador novo (amigável)
path('cef/p3026/visualizar/', views_cef.visualizar_p3026, name='visualizar_p3026')

# Processador original
path('cef/p3026/', views_cef.processar_p3026_view, name='processar_p3026')
```

### No Template

```django
<a href="{% url 'visualizar_p3026' %}" class="btn btn-primary">
    Ver Visualizador P3026
</a>
```

## Tratamento de Erros

O sistema captura e exibe:

- ❌ **Erros críticos**: Impede processamento
- ⚠️ **Avisos**: Arquivo processado parcialmente
- ✓ **Sucesso**: Todos os registros processados

## Campos Suportados

O parser extrai automaticamente todos os campos baseado no layout JSON:

### Exemplo: TR1 (Contrato Habilitado)
- Tipo de registro
- Matrícula do agente
- Agente cessionário
- Agente cedente
- Número do contrato
- Grau de hipoteca
- Nome do mutuário
- CPF
- Data de assinatura
- Endereço do imóvel
- Código/Nome do município
- Origem de recurso
- IM
- Taxa de juros
- Situação do contrato
- Tipo de evento
- Data do evento
- VAF (Valor de Avaliação Fiscal)
- Data de habilitação
- Documentação
- Datas de processamento
- Situação de análise
- Negociação/Transferência

## Próximas Funcionalidades

- [ ] Exportar para Excel com formatação
- [ ] Gráficos de distribuição
- [ ] Filtros avançados (por data, municipio, etc)
- [ ] Comparação com banco de dados
- [ ] Ações em lote
- [ ] API REST para integração

## Troubleshooting

### "Layout não encontrado"
```
python extrair_layout_p3026.py
```

### "Arquivo vazio"
Verifique se o arquivo P3026 foi baixado corretamente do SIWFC

### "Erro ao processar"
- Verifique encoding do arquivo (deve ser latin-1)
- Verifique se é um arquivo P3026 válido

## Referência Técnica

- **Arquivo**: P3026 - Posição da Carteira Homologada
- **Formato**: Texto com campos em posições fixas (fixed width)
- **Encoding**: Latin-1 (ISO-8859-1)
- **Agente**: CEF (Caixa Econômica Federal)
- **Sistema**: SIWFC (Sistema de Informação de Garantias - Fundo de Compensação)

---

**Última atualização**: 09/03/2026
