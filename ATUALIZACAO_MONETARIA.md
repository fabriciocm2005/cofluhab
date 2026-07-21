# 💰 Sistema de Atualização Monetária Automática

## 📋 Visão Geral

Sistema completo para atualizar os saldos devedores mensalmente com base em índices oficiais de correção monetária (INPC, IPCA, TR, etc.).

## 🎯 Funcionalidades

### 1. Interface Web (Recomendado)
Acesse: **http://127.0.0.1:8000/atualizacao-monetaria/**

- ✅ Interface visual intuitiva
- ✅ Simulação antes de aplicar
- ✅ Histórico de todas as atualizações
- ✅ Confirmação antes de modificar dados
- ✅ Relatório de valores corrigidos

### 2. Linha de Comando (Avançado)

```bash
# Criar tabela de histórico (executar apenas uma vez)
py scripts\atualizar_saldo_monetario.py --acao criar-tabela

# Ver histórico de atualizações
py scripts\atualizar_saldo_monetario.py --acao historico

# Simular atualização para um mês específico
py scripts\atualizar_saldo_monetario.py --acao simular --mes 2024-11 --indice 0.39

# Aplicar atualização (modifica os dados!)
py scripts\atualizar_saldo_monetario.py --acao aplicar --mes 2024-11 --indice 0.39

# Atualizar mês atual (pede confirmação)
py scripts\atualizar_saldo_monetario.py --acao mes-atual
```

## 📊 Como Funciona

### Processo de Atualização:

1. **Simulação**:
   - Calcula quanto seria corrigido
   - Mostra exemplos dos primeiros 5 contratos
   - **NÃO modifica** nenhum dado
   - Gera relatório completo

2. **Aplicação**:
   - Atualiza todos os saldos devedores
   - Registra no histórico
   - **MODIFICA** os dados permanentemente
   - Recomenda-se fazer backup antes

### Fórmula de Correção:

```
Correção = Saldo Atual × (Índice ÷ 100)
Novo Saldo = Saldo Atual + Correção
```

**Exemplo:**
- Saldo Atual: R$ 10.000,00
- Índice: 0.39% (0.0039)
- Correção: R$ 10.000,00 × 0.0039 = R$ 39,00
- Novo Saldo: R$ 10.039,00

## 🔧 Configuração de Índices

Os índices mensais estão no arquivo `scripts/atualizar_saldo_monetario.py`:

```python
INDICES_MENSAIS = {
    '2024-11': Decimal('0.0039'),  # 0.39%
    '2024-12': Decimal('0.0052'),  # 0.52%
    '2025-01': Decimal('0.0042'),  # 0.42% (projeção)
}
```

### Onde obter os índices oficiais:

- **INPC**: https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9258-indice-nacional-de-precos-ao-consumidor.html
- **IPCA**: https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo.html
- **TR**: https://www.bcb.gov.br/estabilidadefinanceira/txreferenciais

## ⚠️ Avisos Importantes

### Antes de Aplicar:

1. ✅ **FAÇA BACKUP** do banco de dados:
   ```bash
   copy db.sqlite3 db.sqlite3.backup-AAAAMMDD
   ```

2. ✅ Execute **SIMULAÇÃO** primeiro:
   - Verifique os valores calculados
   - Confira se o índice está correto
   - Analise o relatório

3. ✅ Confirme o **índice oficial**:
   - Consulte fonte confiável (IBGE, Bacen)
   - Verifique se é o índice do mês correto
   - Confirme o percentual

### Após Aplicar:

- ❌ **NÃO é possível reverter automaticamente**
- ✅ Todas as alterações ficam registradas no histórico
- ✅ Use o backup para restaurar se necessário

## 📈 Histórico de Atualizações

O sistema mantém registro completo de:
- Data e hora da atualização
- Mês de referência
- Índice aplicado
- Quantidade de contratos atualizados
- Quantidade de parcelas modificadas
- Valor total corrigido

Tabela: `atualizacao_monetaria_historico`

## 🔄 Rotina Mensal Recomendada

### Dia 1 do mês:

1. Consultar índice oficial do mês anterior
2. Acessar interface web
3. Fazer backup do banco
4. Executar simulação
5. Conferir resultados
6. Aplicar atualização
7. Verificar histórico

## 📞 Exemplos de Uso

### Exemplo 1: Primeira atualização (Novembro/2024)
```bash
# 1. Criar tabela (primeira vez)
py scripts\atualizar_saldo_monetario.py --acao criar-tabela

# 2. Simular
py scripts\atualizar_saldo_monetario.py --acao simular --mes 2024-11 --indice 0.39

# 3. Se OK, aplicar
py scripts\atualizar_saldo_monetario.py --acao aplicar --mes 2024-11 --indice 0.39
```

### Exemplo 2: Via interface web
1. Acesse: http://127.0.0.1:8000/atualizacao-monetaria/
2. Selecione mês: **2024-11**
3. Informe índice: **0.39**
4. Clique em "Simular"
5. Se OK, clique em "Aplicar"

### Exemplo 3: Verificar histórico
```bash
py scripts\atualizar_saldo_monetario.py --acao historico
```

Resultado:
```
📜 HISTÓRICO DE ATUALIZAÇÕES MONETÁRIAS
  📅 2024-11-25 14:30 | Mês: 2024-11 | Índice: 0.3900%
     Contratos: 3129 | Valor Corrigido: R$ 1,234,567.89
```

## 🛠️ Solução de Problemas

### Erro: "Tabela não existe"
```bash
py scripts\atualizar_saldo_monetario.py --acao criar-tabela
```

### Erro: "Índice não disponível"
Adicione o índice em `INDICES_MENSAIS` no script

### Erro: Valores incorretos
1. Restaure backup
2. Verifique índice
3. Execute simulação novamente

## 📊 Relatório de Exemplo

```
🔄 APLICANDO ATUALIZAÇÃO MONETÁRIA
   Mês de Referência: 2024-11
   Índice de Correção: 0.3900%

  Contrato 006333:
    Saldo Anterior: R$ 18,318.46
    Correção: R$ 71.44
    Novo Saldo: R$ 18,389.90

📊 RESUMO DA ATUALIZAÇÃO:
   Total de Contratos Atualizados: 3,129
   Total de Parcelas Modificadas: 3,129
   Valor Total Corrigido: R$ 1,234,567.89

✅ ATUALIZAÇÃO APLICADA COM SUCESSO!
```

## 🔐 Segurança

- ✅ Interface requer confirmação para aplicar
- ✅ Histórico completo de todas as operações
- ✅ Simulação sempre disponível
- ✅ Backups recomendados
- ✅ Logs detalhados

## 💡 Dicas

1. **Sempre simule primeiro** - evita erros
2. **Faça backup regular** - segurança
3. **Documente índices** - auditoria
4. **Verifique histórico** - controle
5. **Use interface web** - mais seguro

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte este documento
2. Verifique o histórico de atualizações
3. Execute simulação para diagnóstico
4. Restaure backup se necessário
