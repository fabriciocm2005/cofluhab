# Especificação Completa do Arquivo P3026 - FCVS CEF

## Origem
- **Arquivo**: Leiaute_FCVS3026_TR1_a_TR9_270417.xls
- **Data do documento**: 27/04/2017
- **Tipo**: Arquivo de Posição da Carteira Homologada
- **Fonte**: CEF (Caixa Econômica Federal)

## Estrutura do Arquivo

O arquivo P3026 contém **9 tipos de registro diferentes** (TR1 a TR9), cada um com sua estrutura específica:

### TR1 - CONTRATOS HABILITADOS NÃO HOMOLOGADOS (37 campos)
Contratos que foram aprovados/habilitados mas ainda não homologados pela CEF.

**Principais campos**:
- Tipo de Registro = 1
- Matrícula do Agente
- Agente Cessionário/Cedente
- Número do Contrato
- Nome do Mutuário e CPF
- Data Assinatura Contrato
- Endereço do Imóvel
- Código e Nome do Município
- Origem de Recurso e IM
- Taxas de Juros (contratual e no evento)
- Código e Descrição da Situação do Contrato
- Tipo e Data do Evento
- Valores VAF 1, 2, 3 e 4 (informado pelo agente)
- Valores VAF 1, 2, 3 e 4 (calculado pela CEF)
- Quantidade e Valor de Parcelas
- Protocolo e Código de Retorno

### TR2 - CONTRATOS COM RESPONSABILIDADE PARCIAL (76 campos)
Contratos onde o agente tem responsabilidade parcial no pagamento.

**Complexidade**: 76 campos - layout mais extenso que TR1

### TR3 - [Descrição baseada em análise] (71 campos)
**Complexidade**: 71 campos

### TR4 - [Descrição baseada em análise] (90 campos)
**Complexidade**: 90 campos - **MAIOR LAYOUT DO P3026**

### TR5 - [Descrição baseada em análise] (50 campos)
**Complexidade**: 50 campos

### TR6 - [Descrição baseada em análise] (46 campos)
**Complexidade**: 46 campos

### TR7 - [Descrição baseada em análise] (66 campos)
**Complexidade**: 66 campos

### TR8 - [Descrição baseada em análise] (62 campos)
**Complexidade**: 62 campos

### TR9 - [Descrição baseada em análise] (47 campos)
**Complexidade**: 47 campos

## Comparação com Implementação Atual

### Parser Atual (ficha_p3026_parser.py)

O parser atualmente implementado considera apenas **3 tipos de registro**:
- **Tipo 0**: HEADER
- **Tipo 1**: REGISTRO (contrato)
- **Tipo 9**: TRAILER

**⚠️ ATENÇÃO**: O arquivo Excel mostra que existem **9 tipos diferentes de TR** (TR1 a TR9), sugerindo que:
1. O arquivo P3026 pode ter múltiplos formatos de registro tipo '1'
2. Cada TR representa uma categoria diferente de contrato ou situação
3. Nossa implementação atual pode estar simplificada demais

### Diferenças Identificadas

#### Campos do TR1 (Excel) vs RegistroContratoP3026 (Implementado)

**TR1 - 37 campos no total**:
```
01. TIPO DE REGISTRO = 1                     (001-001) - Numérico
02. MATRICULA DO AGENTE                      (002-006) - Numérico
03. AGENTE CESSIONÁRIO                       (007-011) - Numérico
04. AGENTE CEDENTE                           (012-016) - Numérico
05. NÚMERO DO CONTRATO                       (017-029) - Alfanumérico (13)
06. GRAU DE HIPOTECA DO CONTRATO             (030-030) - Numérico
07. NOME DO MUTUÁRIO                         (031-070) - Alfanumérico (40)
08. CPF                                      (071-081) - Alfanumérico (11)
09. DATA ASSINATURA CONTRATO (DDMMAAAA)      (082-089) - Alfanumérico (8)
10. ENDEREÇO DO IMOVEL                       (090-129) - Alfanumérico (40)
11. CODIGO DO MUNICIPIO                      (130-134) - Alfanumérico (5)
12. NOME DO MUNICIPIO                        (135-144) - Alfanumérico (10)
13. ORIGEM DE RECURSO                        (145-146) - Alfanumérico (2)
14. IM                                       (147-148) - Alfanumérico (2)
15. TAXA DE JUROS CONTRATUAL                 (149-154) - Alfanumérico (6)
16. TAXA DE JUROS NO EVENTO                  (155-160) - Alfanumérico (6)
17. CODIGO SITUACAO DO CONTRATO              (161-162) - Numérico (2)
18. DESCRICAO SITUACAO DO CONTRATO           (163-232) - Alfanumérico (70)
19. TIPO DE EVENTO                           (233-235) - Alfanumérico (3)
20. DATA DO EVENTO (DDMMAAAA)                (236-243) - Alfanumérico (8)
21. VAF 1 INFORMADO PELO AGENTE              (244-257) - Alfanumérico (14)
22. VAF 2 INFORMADO PELO AGENTE              (258-271) - Alfanumérico (14)
23. VAF 3 INFORMADO PELO AGENTE              (272-285) - Alfanumérico (14)
24. VAF 4 INFORMADO PELO AGENTE              (286-299) - Alfanumérico (14)
25. VAF 1 CALCULADO PELA CEF                 (300-313) - Alfanumérico (14)
26. VAF 2 CALCULADO PELA CEF                 (314-327) - Alfanumérico (14)
27. VAF 3 CALCULADO PELA CEF                 (328-341) - Alfanumérico (14)
28. VAF 4 CALCULADO PELA CEF                 (342-355) - Alfanumérico (14)
29. QUANTIDADE DE PARCELAS CONTRATADAS       (356-359) - Alfanumérico (4)
30. QUANTIDADE DE PARCELAS ANTECIPADAS       (360-363) - Alfanumérico (4)
31. VALOR DA PARCELA CONTRATADA              (364-377) - Alfanumérico (14)
32. VALOR DA PRIMEIRA PARCELA ANTECIPADA     (378-391) - Alfanumérico (14)
33. VALOR DA ÚLTIMA PARCELA ANTECIPADA       (392-405) - Alfanumérico (14)
34. PROTOCOLO                                (406-425) - Alfanumérico (20)
35. COD. RETORNO CADASTRO PRELIMINAR         (426-430) - Alfanumérico (5)
36. COD. RETORNO CADASTRO DEFINITIVO         (431-435) - Alfanumérico (5)
37. FILLER                                   (436-500) - Alfanumérico (65)
```

**Tamanho total do registro TR1**: 500 posições

#### Campos PRESENTES no Excel mas AUSENTES na implementação:
1. `ORIGEM_DE_RECURSO` (pos 145-146)
2. `IM` (pos 147-148)
3. `TAXA_JUROS_CONTRATUAL` (pos 149-154)
4. `TAXA_JUROS_EVENTO` (pos 155-160)
5. `CODIGO_SITUACAO_CONTRATO` (pos 161-162) - **existe descrição mas não código**
6. `TIPO_EVENTO` (pos 233-235)
7. `VAF1_CALCULADO_CEF` (pos 300-313)
8. `VAF2_CALCULADO_CEF` (pos 314-327)
9. `VAF3_CALCULADO_CEF` (pos 328-341)
10. `VAF4_CALCULADO_CEF` (pos 342-355)
11. `QTD_PARCELAS_CONTRATADAS` (pos 356-359)
12. `QTD_PARCELAS_ANTECIPADAS` (pos 360-363)
13. `VALOR_PARCELA_CONTRATADA` (pos 364-377)
14. `VALOR_PRIMEIRA_PARCELA_ANTECIPADA` (pos 378-391)
15. `VALOR_ULTIMA_PARCELA_ANTECIPADA` (pos 392-405)
16. `COD_RETORNO_CADASTRO_PRELIMINAR` (pos 426-430)
17. `COD_RETORNO_CADASTRO_DEFINITIVO` (pos 431-435)
18. `FILLER` (pos 436-500) - Espaço reservado

## Recomendações

### 1. Atualizar RegistroContratoP3026
Adicionar os **18 campos ausentes** identificados acima.

### 2. Implementar Classes para TR2-TR9
Criar classes específicas para cada tipo de registro:
```python
class RegistroTR2P3026:  # 76 campos
class RegistroTR3P3026:  # 71 campos
class RegistroTR4P3026:  # 90 campos - MAIS COMPLEXO
class RegistroTR5P3026:  # 50 campos
class RegistroTR6P3026:  # 46 campos
class RegistroTR7P3026:  # 66 campos
class RegistroTR8P3026:  # 62 campos
class RegistroTR9P3026:  # 47 campos
```

### 3. Lógica de Parsing Adaptativa
Modificar o parser para:
1. Detectar qual TR está sendo processado
2. Usar a classe apropriada para cada TR
3. Validar campos específicos de cada TR

### 4. Documentação das Descrições
O arquivo Excel contém as **descrições completas de cada TR** na primeira linha de cada aba.
É necessário:
1. Extrair essas descrições
2. Documentar o propósito de cada TR
3. Criar exemplos de uso para cada tipo

## Arquivo JSON Gerado

O processamento gerou o arquivo `p3026_layouts_estruturado.json` contendo:
- 9 tipos de registro (TR1-TR9)
- Total de 545 campos mapeados
- Especificação completa de cada campo:
  - Sequência
  - Posições (início-fim)
  - Descrição
  - Tamanho
  - Formato
  - Tipo (Numérico/Alfanumérico)

## Estatísticas

| TR | Campos | Complexidade |
|----|--------|--------------|
| TR1 | 37 | Básica |
| TR2 | 76 | Alta |
| TR3 | 71 | Alta |
| TR4 | 90 | **Máxima** |
| TR5 | 50 | Média |
| TR6 | 46 | Média |
| TR7 | 66 | Alta |
| TR8 | 62 | Alta |
| TR9 | 47 | Média |
| **TOTAL** | **545** | - |

## Próximos Passos

1. ✅ Extração dos layouts Excel - **CONCLUÍDO**
2. ⏳ Comparação detalhada campo a campo
3. ⏳ Atualização do parser com campos ausentes
4. ⏳ Implementação de parsers para TR2-TR9
5. ⏳ Testes com arquivos reais
6. ⏳ Documentação das descrições de cada TR
7. ⏳ Integração com Django (views para cada TR)

## Observações Importantes

- O arquivo P3026 é **muito mais complexo** do que a implementação atual sugere
- Existem **9 formatos diferentes** de registro de contrato (não apenas 1)
- A documentação oficial da CEF (Excel 27/04/2017) deve ser a referência definitiva
- Nossa implementação atual é funcional mas **incompleta** para uso pleno do arquivo P3026
