# Análise de Conformidade: Leiaute FH1 vs Geração Atual

## TIPOS DE MOVIMENTO = I - FH1 (Fichas para Habilitação ao FCVS)

### DADOS (Registro Type 1 - Ficha do Mutuário)
```
SEQ  NOME DO CAMPO                      POSIÇÃO    TAMANHO  TIPO    OBS
01 . UFS                                01 a 02    2        NUM
02 . MAT. AG. FINANC. /DV              03 a 08    6        NUM     ← IMPORTANTE
03 . N.º CONTRATO DO MUT. NO AGENTE    09 a 21    13       ALFA
04 . HIPOTECA                          22         1        NUM
05   TIPO DE REGISTRO                  23         1        NUM     (Deve ser 1)
06   SEQUENCIAL                        24 a 25    2        NUM     (Zeros)
07   CONSTANTE                         26         1        NUM     (0)
... [campos 08-63 - dados do mutuário] ...
64 . UFS                                406 a 407  2        NUM     ← LOTE
65 . MAT. AG. FINANC.                  408 a 413  6        NUM     ← LOTE
66 . DATA GERAÇÃO                      414 a 419  6        NUM     ← LOTE (DDMMAA)
67 . NÚMERO                            420 a 422  3        NUM     ← LOTE
68 . FORMA DE ENVIO                    423        1        ALFA    ← LOTE (S)
69 . TIPO MOVIMENTO                    424        1        ALFA    ← LOTE (I)
70   FILLER                            425 a 430  6        -       ← LOTE (BRANCOS)
```

### HEADER (Registro Type 0)
```
SEQ  NOME DO CAMPO                      POSIÇÃO    TAMANHO  TIPO    OBS
01   UFS                                01 a 02    2        NUM
02   MAT.AG.FINANC                      03 a 08    6        NUM     ← IMPORTANTE
03   CONSTANTE                          09 a 22    14       NUM     (ZEROS)
04   TIPO DE REGISTRO                   23         1        NUM     (Deve ser 0)
05   CONSTANTE                          24 a 32    9        NUM     (ZEROS)
06   QTD DOCTOS                         33 a 37    5        NUM
... [campos 07] FILLER]                38 a 405   368      -       (BRANCOS)
08   UFS                                406 a 407  2        NUM     ← LOTE
09   MAT. AG. FINANC.                  408 a 413  6        NUM     ← LOTE
10   DATA GERAÇÃO                      414 a 419  6        NUM     ← LOTE (DDMMAA)
11   NÚMERO                            420 a 422  3        NUM     ← LOTE
12   FORMA DE ENVIO                    423        1        ALFA    ← LOTE (S)
13   TIPO MOVIMENTO                    424        1        ALFA    ← LOTE (I)
14   FILLER                            425 a 430  6        -       ← LOTE (BRANCOS)
```

## CRÍTICO: IDENTIFICAÇÃO DO LOTE

A especificação diz: **"IDENTIFICAÇÃO DO LOTE Duplicar do HEADER"**

Isso significa que as posições 406-430 (25 caracteres) DEVEM SER IDÊNTICAS:
- HEADER posições 406-430
- DADOS posições 406-430

### Composição da IDENTIFICAÇÃO DO LOTE (25 chars):
```
POS    CAMPO              TAMANHO  CONTEÚDO
406-407  UFS              2        "19" (São Paulo - códigos por estado)
408-413  MAT. AG. FINANC  6        "000049" (Matrícula 000044 + DV 9)
414-419  DATA GERAÇÃO     6        "DDMMAA" (ex: 030226)
420-422  NÚMERO           3        "001" (número do lote)
423      FORMA DE ENVIO   1        "S" (FCVS 2000)
424      TIPO MOVIMENTO   1        "I" (FH1)
425-430  FILLER           6        "      " (6 BRANCOS)
```

## ERROS DETECTADOS NA CEF (Códigos 100512-100522)

CEF está reportando:
- **100512**: DIA diferente entre HEADER e DADOS
- **100513**: MÊS diferente entre HEADER e DADOS
- **100514**: ANO diferente entre HEADER e DADOS
- **100515**: NUMERO LOTE diferente entre HEADER e DADOS
- **100516**: FORMA DE ENVIO diferente entre HEADER e DADOS
- **100517**: TIPO MOVIMENTO diferente entre HEADER e DADOS
- **100520**: IDENTIFICAÇÃO DO LOTE diferente entre HEADER e DADOS
- **100522**: Outros campos da IDENTIFICAÇÃO DO LOTE

## ERRO PRINCIPAL: DV (Código 100820/100821)

```
"O DÍGITO VERIFICADOR (DV) do agente financeiro está diferente do DV cadastrado 
para o agente financeiro cadastrado no SICVS"
```

### Possíveis Causas:
1. **Matrícula 44 não cadastrada na CEF/SICVS** - Mais provável
2. **Algoritmo DV diferente** - Possível, mas CEF usaria também módulo 11
3. **Formato da matrícula diferente** - CEF talvez espere formato diferente
4. **Código da UFS (19) incorreto** - SP tem código 19, mas pode ser outro

## PRÓXIMAS AÇÕES

1. **AGUARDANDO CEF**: Email foi enviado para clarificar DV correto para matrícula 44
2. **VERIFICAR CÓDIGO UFS**: Confirmar se UFS 19 é correto (provavelmente São Paulo)
3. **VALIDAR ALGORITMO**: Se CEF responder, comparar seu DV com nosso cálculo
4. **TESTAR FORMATO**: Talvez a matrícula precise de prefixo ou sufixo especial

## Curiosidade do Teste

O script `gerar_lotes_teste_dv.py` gerou 10 lotes (DV 0-9), todos com:
```
HEADER posição 406-430: "19000049030226001SI      " (com DV9)
DADOS  posição 406-430: "19000049030226001SI      " (com DV9)
```

Ou seja: Apesar de tentar gerar DVs 0-9 diferentes, o algoritmo `normalizar_matricula_com_dv()` 
SEMPRE calcula o mesmo DV (9) para matrícula 00004, pois o algoritmo é determinístico.

**Conclusão**: Se CEF responder com DV diferente de 9, significa que:
- O algoritmo de cálculo está errado, OU
- A matrícula base (44) está incorreta, OU
- A matrícula não existe cadastrada no sistema CEF
