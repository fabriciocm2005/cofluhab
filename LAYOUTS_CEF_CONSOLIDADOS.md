# Layouts CEF Consolidados - Documentação Completa

## 📚 Visão Geral

Esta documentação consolida **TODOS** os layouts CEF extraídos dos manuais oficiais.

### Arquivos de Origem
1. `Leiaute_M460301.pdf` - Contratos com Irregularidade (Acumulativo)
2. `Leiaute_M460401.pdf` - Contratos com Irregularidade (Inclusões Mês)
3. `Leiaute_M460801.pdf` - Contratos Regularizados
4. `Leiaute_FCVS3026_TR1_a_TR9_270417.xls` - Arquivo P3026 (9 tipos)
5. `Leiautes_Movim_CADMUT - 2025.pdf` - Movimentações CADMUT 2025
6. `Leiautes_Movim_FCVS - 2025 - V2.pdf` - Movimentações FCVS 2025 V2
7. `Leiaute_CADMUT_Espelho.pdf` - Espelho CADMUT

---

## 1. ARQUIVOS M460xxx - IRREGULARIDADES CADMUT

### M460301 - Contratos com Irregularidade (Acumulativo)

**Descrição**: Relação **acumulativa** de todos os contratos novados que apresentam irregularidades no sistema CADMUT.

**Total de Campos**: 20  
**Tamanho Estimado**: 176 caracteres por linha  
**Formato**: Posicional ou delimitado (a confirmar com arquivo real)

#### Campos

| Seq | Nome | Tipo | Tam | Decimais | Obrigatório | Descrição |
|-----|------|------|-----|----------|-------------|-----------|
| 01 | GIFUS_ANALISE | Cha | 2 | - | ✅ | Código do GIFUS responsável pela análise |
| 02 | AGENTE_ORIGEM | Num | 5 | - | ✅ | Código do agente de origem |
| 03 | AGENTE_CESSIONARIO | Num | 5 | - | ✅ | Código do agente cessionário |
| 04 | AGENTE_CEDENTE | Num | 5 | - | ✅ | Código do agente cedente |
| 05 | CONTRATO | Cha | 13 | - | ✅ | Número do contrato |
| 06 | HIPOTECA | Num | 1 | - | ✅ | Grau de hipoteca (1=primeira, 2=segunda, etc) |
| 07 | DATA_CONTRATO | Date | 10 | - | ✅ | Data de assinatura do contrato (DD-MM-AAAA) |
| 08 | MUNICIPIO_CADMUT | Num | 4 | - | ✅ | Código do município no CADMUT |
| 09 | DATA_EVENTO_CADMUT | Date | 10 | - | ✅ | Data do evento no CADMUT (DD-MM-AAAA) |
| 10 | DATA_POS_NOVACAO_VA1_VAF2 | Date | 10 | - | ✅ | Data de posicionamento da novação VA1/VAF2 |
| 11 | VALOR_SALDO_VAF1_VA2_VENCIDO | Num | 13 | 2 | ✅ | Valor do saldo vencido (99999999999,99) |
| 12 | VALOR_SALDO_VAF1_VAF2_VINCENDO | Num | 13 | 2 | ✅ | Valor do saldo a vencer (99999999999,99) |
| 13 | DATA_POS_NOVACAO_VA3 | Date | 10 | - | ✅ | Data de posicionamento da novação VA3 |
| 14 | VALOR_SALDO_VAF3 | Num | 13 | 2 | ✅ | Valor do saldo VAF3 (99999999999,99) |
| 15 | DATA_POS_NOVACAO_VAF4 | Date | 10 | - | ✅ | Data de posicionamento da novação VAF4 |
| 16 | VALOR_SALDO_VAF4 | Num | 13 | 2 | ✅ | Valor do saldo VAF4 (99999999999,99) |
| 17 | PERCENTUAL_COBERTURA | Num | 5 | 2 | ✅ | Percentual de cobertura (999,99) |
| 18 | SITUACAO_MULT_SINISTRO | Cha | 2 | - | ✅ | Código da situação de multiplicidade/sinistro |
| 19 | DATA_APRESENTACAO_CONTESTACAO | Date | 10 | - | ❌ | Data de apresentação da contestação |
| 20 | DATA_PRAZO_FINAL_CONTESTACAO | Date | 10 | - | ❌ | Prazo final para contestação |

#### Códigos GIFUS (Campo 01)

| Código | Descrição |
|--------|-----------|
| 03 | GIFUS/SA - Salvador |
| 04 | GIFUS/BR - Brasília |
| 05 | GIFUS/FO - Fortaleza |
| 08 | GIFUS/GO - Goiânia |
| 11 | GIFUS/BH - Belo Horizonte |
| 12 | GIFUS/BE - Belém |
| 14 | GIFUS/CT - Curitiba |
| 15 | GIFUS/RE - Recife |
| 18 | GIFUS/PO - Porto Alegre |
| 19 | GIFUS/RJ - Rio de Janeiro |
| 20 | GIFUS/FL - Florianópolis |
| 21 | GIFUS/SP - São Paulo |

#### Códigos de Situação Multiplicidade/Sinistro (Campo 18)

| Código | Descrição |
|--------|-----------|
| 01 | Indício de Multiplicidade |
| 02 | Indício de Sinistro SIT |
| 03 | Multiplicidade Caracterizada |
| 04 | Sinistro Caracterizado SIT |
| 06 | Indício de Sinistro Parcial (SIP) |
| 08 | Sinistro Parcial Caracterizado (SIP) |
| 10 | Indício de Sinistro DFI |
| 12 | Sinistro DFI Caracterizado |

---

### M460401 - Contratos com Irregularidade (Inclusões no Mês)

**Descrição**: Relação dos contratos novados com irregularidades CADMUT **adicionados no mês corrente**.

**Estrutura**: **IDÊNTICA ao M460301**  
**Diferença**: Contém apenas novos registros do mês, não o acumulado  
**Total de Campos**: 20  
**Tamanho Estimado**: 176 caracteres por linha

#### Uso
- **M460301**: Visão completa de TODAS as irregularidades (histórico completo)
- **M460401**: Visão incremental de NOVAS irregularidades (apenas mês corrente)

---

### M460801 - Contratos Regularizados sem Manifestação GIFUS

**Descrição**: Contratos que estavam com irregularidades no CADMUT mas foram **regularizados automaticamente** sem necessidade de manifestação da GIFUS.

**Total de Campos**: 9 (layout simplificado)  
**Tamanho Estimado**: 56 caracteres por linha

#### Campos

| Seq | Nome | Tipo | Tam | Obrigatório | Descrição |
|-----|------|------|-----|-------------|-----------|
| 01 | GIFUS_ANALISE | Cha | 2 | ✅ | Código do GIFUS responsável |
| 02 | AGENTE_ORIGEM | Num | 5 | ✅ | Código do agente de origem |
| 03 | AGENTE_CESSIONARIO | Num | 5 | ✅ | Código do agente cessionário |
| 04 | AGENTE_CEDENTE | Num | 5 | ✅ | Código do agente cedente |
| 05 | CONTRATO | Cha | 13 | ✅ | Número do contrato |
| 06 | HIPOTECA | Num | 1 | ✅ | Grau de hipoteca |
| 07 | DATA_CONTRATO | Date | 10 | ✅ | Data do contrato (DD-MM-AAAA) |
| 08 | MUNICIPIO_CADMUT | Num | 4 | ✅ | Código do município |
| 09 | DATA_EVENTO_CADMUT | Date | 10 | ✅ | Data do evento (DD-MM-AAAA) |

**Observação**: Este arquivo **NÃO contém** informações de valores VAF, percentual de cobertura ou contestações, pois os contratos já foram regularizados.

---

## 2. ARQUIVO P3026 - POSIÇÃO DA CARTEIRA

### Visão Geral

O arquivo P3026 (FCVS3026) é o arquivo de **posição da carteira homologada** enviado pela CEF.

**Complexidade**: ALTA - Contém **9 tipos diferentes de registro** (TR1 a TR9)  
**Arquivo Origem**: Leiaute_FCVS3026_TR1_a_TR9_270417.xls  
**Data Especificação**: 27/04/2017

### Estatísticas

| Tipo Registro | Campos | Descrição | Complexidade |
|---------------|--------|-----------|--------------|
| **TR1** | 37 | Contratos Habilitados Não Homologados | Básica |
| **TR2** | 76 | Contratos com Responsabilidade Parcial | Alta |
| **TR3** | 71 | (A confirmar descrição completa) | Alta |
| **TR4** | 90 | (A confirmar descrição completa) | **Máxima** |
| **TR5** | 50 | (A confirmar descrição completa) | Média |
| **TR6** | 46 | (A confirmar descrição completa) | Média |
| **TR7** | 66 | (A confirmar descrição completa) | Alta |
| **TR8** | 62 | (A confirmar descrição completa) | Alta |
| **TR9** | 47 | (A confirmar descrição completa) | Média |
| **TOTAL** | **545** | - | - |

### TR1 - Contratos Habilitados Não Homologados (37 campos)

Layout de 500 posições. Principais campos:

| Seq | Posições | Descrição | Tamanho | Formato | Tipo |
|-----|----------|-----------|---------|---------|------|
| 01 | 001-001 | Tipo de Registro = 1 | 1 | 9(1) | Numérico |
| 02 | 002-006 | Matrícula do Agente | 5 | 9(5) | Numérico |
| 03 | 007-011 | Agente Cessionário | 5 | 9(5) | Numérico |
| 04 | 012-016 | Agente Cedente | 5 | 9(5) | Numérico |
| 05 | 017-029 | Número do Contrato | 13 | X(13) | Alfanumérico |
| 06 | 030-030 | Grau de Hipoteca | 1 | 9(1) | Numérico |
| 07 | 031-070 | Nome do Mutuário | 40 | X(40) | Alfanumérico |
| 08 | 071-081 | CPF | 11 | X(11) | Alfanumérico |
| 09 | 082-089 | Data Assinatura (DDMMAAAA) | 8 | X(8) | Alfanumérico |
| 10 | 090-129 | Endereço do Imóvel | 40 | X(40) | Alfanumérico |
| 11 | 130-134 | Código do Município | 5 | X(5) | Alfanumérico |
| 12 | 135-144 | Nome do Município | 10 | X(10) | Alfanumérico |
| 13 | 145-146 | Origem de Recurso | 2 | X(2) | Alfanumérico |
| 14 | 147-148 | IM | 2 | X(2) | Alfanumérico |
| 15 | 149-154 | Taxa de Juros Contratual | 6 | X(6) | Alfanumérico |
| 16 | 155-160 | Taxa de Juros no Evento | 6 | X(6) | Alfanumérico |
| 17 | 161-162 | Código Situação Contrato | 2 | 9(2) | Numérico |
| 18 | 163-232 | Descrição Situação Contrato | 70 | X(70) | Alfanumérico |
| 19 | 233-235 | Tipo de Evento | 3 | X(3) | Alfanumérico |
| 20 | 236-243 | Data do Evento (DDMMAAAA) | 8 | X(8) | Alfanumérico |
| 21 | 244-257 | VAF 1 Informado pelo Agente | 14 | X(14) | Alfanumérico |
| 22 | 258-271 | VAF 2 Informado pelo Agente | 14 | X(14) | Alfanumérico |
| 23 | 272-285 | VAF 3 Informado pelo Agente | 14 | X(14) | Alfanumérico |
| 24 | 286-299 | VAF 4 Informado pelo Agente | 14 | X(14) | Alfanumérico |
| 25 | 300-313 | VAF 1 Calculado pela CEF | 14 | X(14) | Alfanumérico |
| 26 | 314-327 | VAF 2 Calculado pela CEF | 14 | X(14) | Alfanumérico |
| 27 | 328-341 | VAF 3 Calculado pela CEF | 14 | X(14) | Alfanumérico |
| 28 | 342-355 | VAF 4 Calculado pela CEF | 14 | X(14) | Alfanumérico |
| 29 | 356-359 | Qtd Parcelas Contratadas | 4 | X(4) | Alfanumérico |
| 30 | 360-363 | Qtd Parcelas Antecipadas | 4 | X(4) | Alfanumérico |
| 31 | 364-377 | Valor Parcela Contratada | 14 | X(14) | Alfanumérico |
| 32 | 378-391 | Valor Primeira Parcela Antecipada | 14 | X(14) | Alfanumérico |
| 33 | 392-405 | Valor Última Parcela Antecipada | 14 | X(14) | Alfanumérico |
| 34 | 406-425 | Protocolo | 20 | X(20) | Alfanumérico |
| 35 | 426-430 | Cód Retorno Cadastro Preliminar | 5 | X(5) | Alfanumérico |
| 36 | 431-435 | Cód Retorno Cadastro Definitivo | 5 | X(5) | Alfanumérico |
| 37 | 436-500 | FILLER (reservado) | 65 | X(65) | Alfanumérico |

### Implementação Atual vs Especificação Excel

**Status**: ⚠️ **Implementação Parcial**

A implementação atual em [ficha_p3026_parser.py](ficha_p3026_parser.py) possui:
- ✅ Estrutura básica (HEADER/REGISTRO/TRAILER)
- ✅ 20 campos principais do TR1
- ❌ **Faltam 17 campos** do TR1
- ❌ **Faltam TR2 a TR9 completos**

Ver [ANALISE_P3026_COMPLETA.md](ANALISE_P3026_COMPLETA.md) para detalhes.

---

## 3. MOVIMENTAÇÕES CADMUT 2025

**Arquivo**: `Leiautes_Movim_CADMUT - 2025.pdf` (232 KB)  
**Status**: ⏳ **Extração Pendente**

Este arquivo contém as especificações **2025 atualizadas** para todos os tipos de movimentação CADMUT.

### Importância
- Especificação oficial mais recente (2025)
- Pode conter alterações em relação a versões anteriores
- Necessário para atualizar parsers existentes

---

## 4. MOVIMENTAÇÕES FCVS 2025 V2

**Arquivo**: `Leiautes_Movim_FCVS - 2025 - V2.pdf` (529 KB)  
**Status**: ⏳ **Extração Pendente**

Especificações **2025 V2** para movimentações FCVS, incluindo:
- FH1 (Ficha de Habilitação tipo 1)
- FH3 (Ficha de Habilitação tipo 3)
- RNV (Registro de Novação)
- Outros tipos de ficha

---

## 5. ESPELHO CADMUT

**Arquivo**: `Leiaute_CADMUT_Espelho.pdf` (8 KB)  
**Status**: ⏳ **Extração Pendente**

Layout do arquivo de **espelho** (mirror/report) do CADMUT.

**Propósito**: Relatório consolidado das informações CADMUT para conferência.

---

## 📊 Status de Implementação

### ✅ Completo
- M460301 Parser (estrutura definida)
- M460401 Parser (estrutura definida)
- M460801 Parser (estrutura definida)
- P3026 Parser básico (TR1 parcial)

### ⏳ Em Progresso
- P3026 TR1 completo (37 campos)
- P3026 TR2-TR9 (545 campos total)

### ❌ Pendente
- Movimentações CADMUT 2025 (extração PDF)
- Movimentações FCVS 2025 V2 (extração PDF)
- Espelho CADMUT (extração PDF)
- Testes com arquivos reais
- Validações de campos
- Django views para M460xxx

---

## 📂 Arquivos Gerados

1. **p3026_layouts_estruturado.json** - Layouts TR1-TR9 em JSON (4620 linhas)
2. **principal/ficha_m460_parsers.py** - Parser M460xxx (422 linhas)
3. **ANALISE_P3026_COMPLETA.md** - Análise detalhada do P3026
4. **LAYOUTS_CEF_CONSOLIDADOS.md** - Este documento

---

## 🔧 Próximos Passos

### Alta Prioridade
1. ✅ Extrair P3026 Excel (TR1-TR9) - **CONCLUÍDO**
2. ⏳ Atualizar P3026 parser com 37 campos TR1
3. ⏳ Implementar parsers TR2-TR9
4. ⏳ Testar M460xxx parsers com dados reais

### Média Prioridade
5. ⏳ Extrair PDFs grandes (CADMUT 2025, FCVS 2025)
6. ⏳ Comparar com parsers existentes
7. ⏳ Criar Django views para M460xxx
8. ⏳ Atualizar ficha_parsers.py com specs 2025

### Baixa Prioridade
9. ⏳ Extrair Espelho CADMUT
10. ⏳ Documentação de uso completa
11. ⏳ Testes unitários
12. ⏳ Integração com sistema existente

---

## 📖 Referências

- **Manuais CEF**: `C:\Users\fabri\cofluhab\dados_antigos\manuais\`
- **Parser P3026**: [principal/ficha_p3026_parser.py](principal/ficha_p3026_parser.py)
- **Parser M460xxx**: [principal/ficha_m460_parsers.py](principal/ficha_m460_parsers.py)
- **Análise P3026**: [ANALISE_P3026_COMPLETA.md](ANALISE_P3026_COMPLETA.md)

---

**Última Atualização**: 24/01/2026  
**Total de Layouts Documentados**: 13 (M460301, M460401, M460801, TR1-TR9, CADMUT 2025, FCVS 2025, Espelho)
