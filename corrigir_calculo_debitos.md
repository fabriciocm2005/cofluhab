# Correção do Cálculo de Débitos de Prestações

## Problema Identificado

O contrato 6080 mostra débito de **R$ 61.006.652,38** quando deveria ser menos de R$ 500.000,00.

### Análise Realizada

1. **332 parcelas em aberto** para contrato 6080
2. **Componentes somam R$ 12.311.335,22** - valores em MOEDA ANTIGA não convertidos
3. **Mora calculada gera R$ 48.695.317,16** - calculada sobre valores inflados
4. **sddev soma R$ 1.983.584.210,52** - é saldo devedor acumulado, não valor de parcela

### Causa Raiz

As parcelas foram importadas do arquivo **MOVMUT.DBF** com valores em **moeda antiga** (Cruzados de 1987), mas o campo `conversor` foi gravado como **1.0**, fazendo com que valores como:

- Parcela 29 (venc: 30/03/1987): juros=R$ 712,68 (são Cruzados!)
- Parcela 30 (venc: 30/04/1987): juros=R$ 817,99 (são Cruzados!)

Sejam tratados como se fossem Reais modernos.

## Solução

Aplicar conversão monetária baseada na **data de vencimento** de cada parcela:

### Tabela de Conversões (Cascata)

| Período | Moeda | Conversão para próxima |
|---------|-------|------------------------|
| Até 27/02/1986 | Cruzeiro (Cr$) | ÷ 1.000 → Cruzado |
| 28/02/1986 - 15/01/1989 | Cruzado (Cz$) | ÷ 1.000 → Cruzado Novo |
| 16/01/1989 - 15/03/1990 | Cruzado Novo (NCz$) | = Cruzeiro (sem mudança) |
| 16/03/1990 - 31/07/1993 | Cruzeiro (Cr$) | ÷ 1.000 → Cruzeiro Real |
| 01/08/1993 - 30/06/1994 | Cruzeiro Real (CR$) | ÷ 2.750 → Real |
| A partir de 01/07/1994 | Real (R$) | - |

### Conversão Completa

Para uma parcela de **30/03/1987** (Cruzado):
```
Valor original: 712,68 Cruzados
÷ 1.000 → 0,71268 Cruzado Novo
÷ 1.000 → 0,00071268 Cruzeiro Real  
÷ 2.750 → 0,000000259 Reais
= R$ 0,00 (centavos)
```

## Implementação

Modificar a view `debito_prestacoes()` em `principal/views.py` para:

1. Aplicar conversão baseada em `p.dtvenc` ANTES de calcular mora
2. Usar apenas `vlautent` se disponível e > 0
3. Se `vlautent` vazio, somar componentes E converter
4. Nunca usar `sddev` (é saldo acumulado)

### Código de Conversão

```python
def converter_valor_para_real(valor, data_vencimento):
    """Converte valor da moeda histórica para Real baseado na data"""
    from decimal import Decimal
    from datetime import date
    
    if valor is None or valor == 0:
        return Decimal('0')
    
    valor_convertido = Decimal(str(valor))
    
    # Se data é None ou já é Real (após 01/07/1994), retornar direto
    if data_vencimento is None or data_vencimento >= date(1994, 7, 1):
        return valor_convertido
    
    # Aplicar conversões em cascata
    # Até 27/02/1986: Cruzeiro antigo
    if data_vencimento < date(1986, 2, 28):
        valor_convertido = valor_convertido / Decimal('1000')  # Cr$ → Cz$
        valor_convertido = valor_convertido / Decimal('1000')  # Cz$ → NCz$
        valor_convertido = valor_convertido / Decimal('1000')  # NCz$ → CR$
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
        
    # 28/02/1986 - 15/01/1989: Cruzado
    elif data_vencimento < date(1989, 1, 16):
        valor_convertido = valor_convertido / Decimal('1000')  # Cz$ → NCz$
        valor_convertido = valor_convertido / Decimal('1000')  # NCz$ → CR$
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
        
    # 16/01/1989 - 15/03/1990: Cruzado Novo
    elif data_vencimento < date(1990, 3, 16):
        valor_convertido = valor_convertido / Decimal('1000')  # NCz$ → CR$
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
        
    # 16/03/1990 - 31/07/1993: Cruzeiro
    elif data_vencimento < date(1993, 8, 1):
        valor_convertido = valor_convertido / Decimal('1000')  # Cr$ → CR$
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
        
    # 01/08/1993 - 30/06/1994: Cruzeiro Real
    elif data_vencimento < date(1994, 7, 1):
        valor_convertido = valor_convertido / Decimal('2750')  # CR$ → R$
    
    return valor_convertido
```

## Resultado Esperado

Após a correção, o contrato 6080 deve mostrar:
- Débito de Prestação: **< R$ 500.000,00** (valor realista)
- Mora calculada sobre valores convertidos corretos
- Total compatível com débitos reais de contratos habitacionais

## Arquivos a Modificar

- `principal/views.py` - Função `debito_prestacoes()` (linha 1088)
- `principal/views.py` - Função `relatorio_debitos()` (linha 1445)

Ambas usam a mesma lógica de cálculo que precisa ser corrigida.
