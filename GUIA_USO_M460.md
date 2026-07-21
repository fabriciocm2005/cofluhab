# Guia de Uso - Parsers M460xxx

## 🎯 Visão Geral

Os parsers M460xxx permitem processar arquivos CEF de irregularidades CADMUT:
- **M460301**: Contratos com irregularidade (acumulativo)
- **M460401**: Contratos com irregularidade (inclusões do mês)
- **M460801**: Contratos regularizados sem manifestação GIFUS

---

## 📦 Instalação

Os parsers estão no módulo `principal.ficha_m460_parsers`.

```python
from principal.ficha_m460_parsers import (
    ParserM460,
    RegistroM460301,
    RegistroM460401,
    RegistroM460801,
    TipoGIFUS,
    SituacaoMultiplicidadeSinistro,
    agrupar_por_gifus,
    agrupar_por_situacao,
    calcular_totais_vaf
)
```

---

## 🚀 Uso Básico

### 1. Processar arquivo M460301

```python
from principal.ficha_m460_parsers import ParserM460

# Parse do arquivo
registros, erros = ParserM460.parse_file_m460301('caminho/arquivo_m460301.txt')

# Verifica erros
if erros:
    print(f"Encontrados {len(erros)} erros:")
    for erro in erros:
        print(f"  - {erro}")

# Processa registros
print(f"Total de registros: {len(registros)}")
for reg in registros:
    print(f"Contrato: {reg.contrato}")
    print(f"  GIFUS: {reg.gifus_analise}")
    print(f"  Situação: {reg.situacao_mult_sinistro}")
    print(f"  Total VAFs: R$ {reg.total_todos_vafs:,.2f}")
```

### 2. Processar arquivo M460401

```python
# Mesmo uso, mas função diferente
registros, erros = ParserM460.parse_file_m460401('arquivo_m460401.txt')

# Registros têm mesma estrutura do M460301
for reg in registros:
    print(f"{reg.contrato}: R$ {reg.total_todos_vafs:,.2f}")
```

### 3. Processar arquivo M460801

```python
# M460801 tem apenas 9 campos (mais simples)
registros, erros = ParserM460.parse_file_m460801('arquivo_m460801.txt')

for reg in registros:
    print(f"Contrato {reg.contrato} regularizado em {reg.data_evento_cadmut}")
```

---

## 📊 Análises e Relatórios

### Agrupar por GIFUS

```python
from principal.ficha_m460_parsers import agrupar_por_gifus

registros, _ = ParserM460.parse_file_m460301('arquivo.txt')

por_gifus = agrupar_por_gifus(registros)

for gifus, contratos in por_gifus.items():
    print(f"GIFUS {gifus}: {len(contratos)} contratos")
    
    # Detalha contratos deste GIFUS
    for contrato in contratos:
        print(f"  - {contrato.contrato}")
```

### Agrupar por Situação

```python
from principal.ficha_m460_parsers import agrupar_por_situacao

registros, _ = ParserM460.parse_file_m460301('arquivo.txt')

por_situacao = agrupar_por_situacao(registros)

print("\nResumo por Situação:")
for situacao, contratos in por_situacao.items():
    print(f"  Situação {situacao}: {len(contratos)} contratos")
```

**Códigos de Situação**:
- `01`: Indício de Multiplicidade
- `02`: Indício de Sinistro SIT
- `03`: Multiplicidade Caracterizada
- `04`: Sinistro Caracterizado SIT
- `06`: Indício de Sinistro Parcial (SIP)
- `08`: Sinistro Parcial Caracterizado (SIP)
- `10`: Indício de Sinistro DFI
- `12`: Sinistro DFI Caracterizado

### Calcular Totais Financeiros

```python
from principal.ficha_m460_parsers import calcular_totais_vaf

registros, _ = ParserM460.parse_file_m460301('arquivo.txt')

totais = calcular_totais_vaf(registros)

print("\nTotais Financeiros:")
print(f"  Vencido: R$ {totais['total_vencido']:,.2f}")
print(f"  Vincendo: R$ {totais['total_vincendo']:,.2f}")
print(f"  VAF3: R$ {totais['total_vaf3']:,.2f}")
print(f"  VAF4: R$ {totais['total_vaf4']:,.2f}")
print(f"  TOTAL: R$ {totais['total_geral']:,.2f}")
```

---

## 🔍 Campos Disponíveis

### RegistroM460301 / RegistroM460401 (20 campos)

```python
reg = registros[0]

# Identificação
reg.gifus_analise           # str: Código GIFUS (ex: "21")
reg.agente_origem           # str: Agente origem
reg.agente_cessionario      # str: Agente cessionário
reg.agente_cedente          # str: Agente cedente
reg.contrato                # str: Número do contrato
reg.hipoteca                # int: Grau de hipoteca

# Datas
reg.data_contrato           # datetime: Data do contrato
reg.data_evento_cadmut      # datetime: Data do evento CADMUT
reg.data_pos_novacao_va1_vaf2   # datetime: Posicionamento VA1/VAF2
reg.data_pos_novacao_va3    # datetime: Posicionamento VA3
reg.data_pos_novacao_vaf4   # datetime: Posicionamento VAF4
reg.data_apresentacao_contestacao  # datetime | None: Data contestação
reg.data_prazo_final_contestacao   # datetime | None: Prazo final

# Localização
reg.municipio_cadmut        # str: Código município

# Valores Financeiros (Decimal)
reg.valor_saldo_vaf1_va2_vencido   # Decimal: Saldo vencido
reg.valor_saldo_vaf1_vaf2_vincendo # Decimal: Saldo vincendo
reg.valor_saldo_vaf3        # Decimal: Saldo VAF3
reg.valor_saldo_vaf4        # Decimal: Saldo VAF4

# Percentual
reg.percentual_cobertura    # Decimal: Percentual (ex: 85.00)

# Situação
reg.situacao_mult_sinistro  # str: Código situação (01-12)

# Properties calculadas
reg.total_saldo_vencido_vincendo  # Decimal: Vencido + Vincendo
reg.total_todos_vafs        # Decimal: Soma de todos os VAFs
reg.tem_contestacao         # bool: True se tem data de contestação
reg.contestacao_vencida     # bool: True se prazo venceu
```

### RegistroM460801 (9 campos)

```python
reg = registros[0]

# Identificação
reg.gifus_analise           # str: Código GIFUS
reg.agente_origem           # str: Agente origem
reg.agente_cessionario      # str: Agente cessionário
reg.agente_cedente          # str: Agente cedente
reg.contrato                # str: Número do contrato
reg.hipoteca                # int: Grau de hipoteca

# Datas
reg.data_contrato           # datetime: Data do contrato
reg.data_evento_cadmut      # datetime: Data do evento

# Localização
reg.municipio_cadmut        # str: Código município
```

---

## 🎨 Exemplos Práticos

### Exemplo 1: Contratos com Contestação Vencida

```python
registros, _ = ParserM460.parse_file_m460301('arquivo.txt')

contratos_vencidos = [r for r in registros if r.contestacao_vencida]

print(f"Contratos com contestação vencida: {len(contratos_vencidos)}")
for reg in contratos_vencidos:
    print(f"  {reg.contrato} - Prazo: {reg.data_prazo_final_contestacao}")
```

### Exemplo 2: Top 10 Maiores Saldos

```python
registros, _ = ParserM460.parse_file_m460301('arquivo.txt')

# Ordena por total de VAFs (decrescente)
top10 = sorted(registros, key=lambda r: r.total_todos_vafs, reverse=True)[:10]

print("Top 10 Maiores Saldos:")
for i, reg in enumerate(top10, 1):
    print(f"{i:2d}. {reg.contrato}: R$ {reg.total_todos_vafs:,.2f}")
```

### Exemplo 3: Contratos com Multiplicidade Caracterizada

```python
from principal.ficha_m460_parsers import SituacaoMultiplicidadeSinistro

registros, _ = ParserM460.parse_file_m460301('arquivo.txt')

mult_caracterizada = [
    r for r in registros 
    if r.situacao_mult_sinistro == SituacaoMultiplicidadeSinistro.MULTIPLICIDADE_CARACTERIZADA.value
]

print(f"Contratos com Multiplicidade Caracterizada: {len(mult_caracterizada)}")
for reg in mult_caracterizada:
    print(f"  {reg.contrato} - GIFUS {reg.gifus_analise}")
```

### Exemplo 4: Relatório por GIFUS com Totais

```python
from principal.ficha_m460_parsers import agrupar_por_gifus, TipoGIFUS

registros, _ = ParserM460.parse_file_m460301('arquivo.txt')

por_gifus = agrupar_por_gifus(registros)

print("\nRelatório por GIFUS")
print("=" * 60)

for gifus_code, contratos in sorted(por_gifus.items()):
    # Tenta pegar o nome do GIFUS
    try:
        gifus_enum = TipoGIFUS(gifus_code)
        gifus_nome = gifus_enum.name
    except:
        gifus_nome = gifus_code
    
    total = sum(c.total_todos_vafs for c in contratos)
    
    print(f"\nGIFUS {gifus_code} ({gifus_nome}):")
    print(f"  Contratos: {len(contratos)}")
    print(f"  Total VAFs: R$ {total:,.2f}")
    
    # Top 3 deste GIFUS
    top3 = sorted(contratos, key=lambda c: c.total_todos_vafs, reverse=True)[:3]
    print(f"  Top 3:")
    for c in top3:
        print(f"    {c.contrato}: R$ {c.total_todos_vafs:,.2f}")
```

### Exemplo 5: Comparar M460301 vs M460401

```python
# Carrega acumulativo e mensal
acumulativo, _ = ParserM460.parse_file_m460301('m460301.txt')
mensal, _ = ParserM460.parse_file_m460401('m460401.txt')

print(f"Total acumulativo: {len(acumulativo)} contratos")
print(f"Novos no mês: {len(mensal)} contratos")
print(f"Taxa de crescimento: {len(mensal)/len(acumulativo)*100:.2f}%")

# Verifica se todos os contratos mensais estão no acumulativo
contratos_acum = {r.contrato for r in acumulativo}
contratos_mens = {r.contrato for r in mensal}

novos_de_verdade = contratos_mens - contratos_acum
if novos_de_verdade:
    print(f"\nNovos contratos (não no acumulativo): {len(novos_de_verdade)}")
```

### Exemplo 6: Exportar para CSV

```python
import csv

registros, _ = ParserM460.parse_file_m460301('arquivo.txt')

with open('irregularidades.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # Cabeçalho
    writer.writerow([
        'Contrato', 'GIFUS', 'Data Contrato', 'Município', 
        'Situação', 'Total VAFs', 'Tem Contestação'
    ])
    
    # Dados
    for reg in registros:
        writer.writerow([
            reg.contrato,
            reg.gifus_analise,
            reg.data_contrato.strftime('%d/%m/%Y') if reg.data_contrato else '',
            reg.municipio_cadmut,
            reg.situacao_mult_sinistro,
            f"{reg.total_todos_vafs:.2f}",
            'Sim' if reg.tem_contestacao else 'Não'
        ])

print("CSV exportado: irregularidades.csv")
```

---

## ⚙️ Configurações

### Encoding

Por padrão, os arquivos são lidos com `latin-1`:

```python
registros, erros = ParserM460.parse_file_m460301(
    'arquivo.txt',
    encoding='latin-1'  # Padrão CEF
)

# Se necessário, altere para utf-8 ou outro
registros, erros = ParserM460.parse_file_m460301(
    'arquivo.txt',
    encoding='utf-8'
)
```

### Formato dos Dados

Os parsers atualmente esperam dados separados por pipe (`|`):

```
GIFUS|Agente1|Agente2|Agente3|Contrato|...
21|12345|12346|12347|1234567890123|...
```

**Importante**: Se os arquivos reais da CEF usarem formato posicional puro (sem delimitadores), será necessário ajustar os métodos `parse_*_line()`.

---

## ❌ Tratamento de Erros

### Erros de Parsing

```python
registros, erros = ParserM460.parse_file_m460301('arquivo.txt')

if erros:
    print(f"❌ Encontrados {len(erros)} erros:")
    for erro in erros:
        print(f"  {erro}")
    
    # Pode decidir parar ou continuar com registros válidos
    if len(erros) > len(registros) * 0.1:  # Mais de 10% de erro
        print("ATENÇÃO: Taxa de erro muito alta!")
        # Não processar
    else:
        # Processar registros válidos
        processar_registros(registros)
```

### Try/Except

```python
try:
    registros, erros = ParserM460.parse_file_m460301('arquivo.txt')
except FileNotFoundError:
    print("Arquivo não encontrado!")
except PermissionError:
    print("Sem permissão para ler arquivo!")
except Exception as e:
    print(f"Erro inesperado: {e}")
```

---

## 🔧 Dicas e Boas Práticas

### 1. Validar Dados Antes de Processar

```python
def validar_arquivo(caminho):
    """Valida se o arquivo existe e não está vazio"""
    from pathlib import Path
    
    arquivo = Path(caminho)
    if not arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    
    if arquivo.stat().st_size == 0:
        raise ValueError("Arquivo vazio")
    
    return True

# Uso
validar_arquivo('arquivo.txt')
registros, erros = ParserM460.parse_file_m460301('arquivo.txt')
```

### 2. Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

registros, erros = ParserM460.parse_file_m460301('arquivo.txt')

logger.info(f"Processados {len(registros)} registros")
if erros:
    logger.warning(f"Encontrados {len(erros)} erros")
    for erro in erros:
        logger.error(erro)
```

### 3. Cache de Resultados

```python
import pickle
from pathlib import Path

def carregar_com_cache(arquivo):
    """Carrega arquivo ou usa cache se disponível"""
    cache_file = Path(f"{arquivo}.cache")
    
    # Verifica se cache existe e é mais novo que arquivo
    if cache_file.exists():
        if cache_file.stat().st_mtime > Path(arquivo).stat().st_mtime:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    
    # Processa arquivo
    registros, erros = ParserM460.parse_file_m460301(arquivo)
    
    # Salva cache
    with open(cache_file, 'wb') as f:
        pickle.dump((registros, erros), f)
    
    return registros, erros
```

---

## 📚 Referências

- **Código Fonte**: [principal/ficha_m460_parsers.py](principal/ficha_m460_parsers.py)
- **Testes**: [testar_parsers_m460.py](testar_parsers_m460.py)
- **Validações**: [testar_validacoes_m460.py](testar_validacoes_m460.py)
- **Relatório**: [RELATORIO_TESTES_M460.md](RELATORIO_TESTES_M460.md)
- **Layouts**: [LAYOUTS_CEF_CONSOLIDADOS.md](LAYOUTS_CEF_CONSOLIDADOS.md)

---

## 🆘 Suporte

Se encontrar problemas:

1. Verifique se o formato do arquivo está correto (delimitado por `|`)
2. Verifique o encoding (padrão: `latin-1`)
3. Consulte a lista de erros retornada pelo parser
4. Execute os testes: `python testar_parsers_m460.py`

---

**Versão**: 1.0.0  
**Última Atualização**: 23/01/2026
