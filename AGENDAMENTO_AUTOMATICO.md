# 🤖 Agendamento Automático de Coleta de Índices

## ✅ Sistema Instalado e Funcionando!

O sistema de coleta automática de índices do Banco Central do Brasil está **pronto para uso**.

---

## 📊 O que foi instalado?

### 1️⃣ **Coletor de Índices** (`scripts/coletar_indices_bacen.py`)
- Busca TR, IPCA e INPC direto da API do Banco Central
- Salva histórico no banco de dados
- Permite coleta manual ou automática

### 2️⃣ **Agendador Python** (`scripts/agendador_indices.py`)
- Executa automaticamente todo dia 30 às 08:00
- Pode rodar em loop contínuo (desenvolvimento)
- Integra com Windows Task Scheduler (produção)

### 3️⃣ **Configurador Task Scheduler** (`scripts/configurar_agendamento.ps1`)
- Script PowerShell para configurar agendamento no Windows
- Cria tarefa que roda automaticamente

---

## 🚀 Como usar?

### **Opção 1: Coleta Manual (Uso Imediato)**

```powershell
# Coletar índices do mês atual
py scripts\coletar_indices_bacen.py --acao coletar

# Ver índices salvos
py scripts\coletar_indices_bacen.py --acao listar

# Coletar últimos 12 meses
py scripts\coletar_indices_bacen.py --acao ultimos-meses --quantidade 12

# Aplicar índice coletado ao saldo devedor
py scripts\coletar_indices_bacen.py --acao atualizar-saldos --mes 2024-11 --indice ipca
```

### **Opção 2: Agendamento Python (Desenvolvimento/Teste)**

```powershell
# Iniciar agendador em loop contínuo
py scripts\agendador_indices.py --modo iniciar

# Executar coleta imediatamente (teste)
py scripts\agendador_indices.py --modo executar-agora
```

⚠️ **Atenção**: O processo precisa ficar rodando. Se fechar o terminal, o agendador para.

### **Opção 3: Windows Task Scheduler (RECOMENDADO para Produção)** ⭐

```powershell
# 1. Abrir PowerShell como ADMINISTRADOR

# 2. Navegar até a pasta do projeto
cd C:\Users\fabri\cofluhab\cofluhab

# 3. Executar script de configuração
.\scripts\configurar_agendamento.ps1

# 4. Confirmar quando perguntar se quer testar (S/N)
```

**Vantagens**:
- ✅ Roda automaticamente mesmo com PC reiniciado
- ✅ Não precisa deixar terminal aberto
- ✅ Sistema nativo do Windows (mais confiável)
- ✅ Histórico de execuções no Event Viewer

**Comandos úteis após configurar**:
```powershell
# Ver status da tarefa
Get-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"

# Executar manualmente
Start-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"

# Ver histórico de execuções
Get-ScheduledTaskInfo -TaskName "CoFluhab_Coleta_Indices_Bacen"

# Desabilitar temporariamente
Disable-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"

# Habilitar novamente
Enable-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"

# Remover tarefa
Unregister-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"
```

---

## 📅 Quando o sistema executa?

- **Dia**: Todo dia **30 de cada mês**
- **Horário**: **08:00** da manhã
- **Ação**: Busca índices do mês **anterior** automaticamente

**Exemplo**:
- No dia **30/12/2024**, busca índices de **novembro/2024**
- No dia **30/01/2025**, busca índices de **dezembro/2024**

---

## 🔍 Como verificar se está funcionando?

### 1. **Verificar Task Scheduler (se usou Opção 3)**
```powershell
Get-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen" | Format-List
```

### 2. **Ver índices coletados**
```powershell
py scripts\coletar_indices_bacen.py --acao listar
```

### 3. **Testar coleta manual**
```powershell
py scripts\coletar_indices_bacen.py --acao coletar
```

### 4. **Acessar interface web**
```
http://127.0.0.1:8000/atualizacao-monetaria/
```
- Ver histórico de atualizações
- Simular aplicação de índice
- Aplicar correção monetária

---

## 🎯 Fluxo Automático Completo

### **Processo Automático (DIA 30)**:

1️⃣ **08:00** - Task Scheduler acorda  
2️⃣ **08:00:05** - Script `coletar_indices_bacen.py` executa  
3️⃣ **08:00:10** - Busca TR, IPCA, INPC na API do Banco Central  
4️⃣ **08:00:15** - Salva índices no banco de dados (`indices_economicos`)  
5️⃣ **Fim** - Aguarda próximo mês  

### **Processo Manual (Quando você quiser)**:

1️⃣ Acessa: `http://127.0.0.1:8000/atualizacao-monetaria/`  
2️⃣ Escolhe: Mês de referência (ex: 2024-11)  
3️⃣ Digita: Percentual do índice (ex: 0.56 para IPCA de novembro)  
4️⃣ Clica: "**Simular**" para ver prévia OU "**Aplicar**" para efetivar  

---

## 🛡️ Segurança e Backups

### **Antes de aplicar correção monetária**:

1. **SEMPRE fazer backup do banco**:
```powershell
copy db.sqlite3 db.sqlite3.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')
```

2. **SEMPRE usar modo SIMULAÇÃO primeiro**:
```powershell
py scripts\atualizar_saldo_monetario.py --acao simulacao --mes 2024-11 --indice 0.56
```

3. **Conferir resultados** antes de aplicar

4. **Só depois aplicar de verdade**:
```powershell
py scripts\atualizar_saldo_monetario.py --acao aplicar --mes 2024-11 --indice 0.56
```

---

## 📚 Fontes Oficiais dos Índices

### **TR - Taxa Referencial**
- 🌐 **API Bacen**: Série 226
- 📊 **URL Manual**: https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries

### **IPCA - Inflação (Índice Nacional de Preços ao Consumidor Amplo)**
- 🌐 **API Bacen**: Série 433
- 📊 **IBGE**: https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo.html

### **INPC - Inflação (Índice Nacional de Preços ao Consumidor)**
- 🌐 **API Bacen**: Série 188
- 📊 **IBGE**: https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9258-indice-nacional-de-precos-ao-consumidor.html

---

## 🔧 Troubleshooting (Problemas Comuns)

### **Problema**: Task Scheduler não executa

**Solução**:
1. Verificar se está habilitada:
```powershell
Get-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"
```

2. Ver último erro:
```powershell
Get-ScheduledTaskInfo -TaskName "CoFluhab_Coleta_Indices_Bacen"
```

3. Testar execução manual:
```powershell
Start-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"
```

### **Problema**: API do Banco Central não responde

**Solução**:
1. Testar conexão:
```powershell
curl https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json
```

2. Verificar internet

3. Tentar novamente mais tarde (API pode estar fora do ar)

### **Problema**: Índice não encontrado para o mês

**Solução**:
- Índices são divulgados **depois** do mês de referência
- Exemplo: Índice de **novembro/2024** só está disponível em **dezembro/2024**
- Aguardar divulgação oficial do IBGE/Bacen

---

## 📞 Comandos Rápidos (Cheat Sheet)

```powershell
# COLETA MANUAL
py scripts\coletar_indices_bacen.py --acao coletar
py scripts\coletar_indices_bacen.py --acao listar

# TESTE DO AGENDADOR
py scripts\agendador_indices.py --modo executar-agora

# CONFIGURAR WINDOWS TASK SCHEDULER
.\scripts\configurar_agendamento.ps1

# VER STATUS DA TAREFA AGENDADA
Get-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"

# EXECUTAR TAREFA MANUALMENTE
Start-ScheduledTask -TaskName "CoFluhab_Coleta_Indices_Bacen"

# BACKUP DO BANCO
copy db.sqlite3 db.sqlite3.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')

# SIMULAÇÃO DE ATUALIZAÇÃO
py scripts\atualizar_saldo_monetario.py --acao simulacao --mes 2024-11 --indice 0.56

# APLICAR ATUALIZAÇÃO (CUIDADO!)
py scripts\atualizar_saldo_monetario.py --acao aplicar --mes 2024-11 --indice 0.56

# INTERFACE WEB
py manage.py runserver
# Acessar: http://127.0.0.1:8000/atualizacao-monetaria/
```

---

## ✨ Pronto!

Seu sistema de **coleta automática de índices** está funcionando! 🎉

**Recomendação**: Configure o **Windows Task Scheduler** (Opção 3) para automação completa e confiável.

**Dúvidas?** Consulte os arquivos:
- `ATUALIZACAO_MONETARIA.md` - Documentação completa do sistema de correção
- `scripts/coletar_indices_bacen.py` - Código fonte do coletor
- `scripts/agendador_indices.py` - Código fonte do agendador

---

**Desenvolvido com ❤️ para CoFluhab**  
**Sistema de Gestão de Contratos Habitacionais**
