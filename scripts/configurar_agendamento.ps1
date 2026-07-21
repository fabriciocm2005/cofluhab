# Script PowerShell para configurar Task Scheduler do Windows
# Executa automaticamente todo dia 30 às 08:00

$TaskName = "CoFluhab_Coleta_Indices_Bacen"
$ScriptPath = "$PWD\scripts\coletar_indices_bacen.py"
$PythonPath = (Get-Command py).Source
$WorkingDir = "$PWD"

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "🤖 CONFIGURANDO TAREFA AGENDADA NO WINDOWS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "   Nome da Tarefa: $TaskName"
Write-Host "   Script: $ScriptPath"
Write-Host "   Python: $PythonPath"
Write-Host "   Diretório: $WorkingDir"
Write-Host "   Agendamento: Todo dia 30 do mês às 08:00"
Write-Host "================================================================================`n" -ForegroundColor Cyan

# Remover tarefa existente se houver
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "⚠️  Tarefa existente encontrada. Removendo..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Criar ação (comando a executar)
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "scripts\coletar_indices_simples.py" `
    -WorkingDirectory $WorkingDir

# Criar gatilho (trigger) - Todo dia 30 às 08:00
$Trigger = New-ScheduledTaskTrigger -Daily -At 08:00AM

# Configurar para executar apenas no dia 30
# Nota: Infelizmente o Task Scheduler não tem trigger direto para "dia 30"
# Solução: Executar diariamente, mas o script verifica se é dia 30

# Criar principal (executar com usuário atual)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Configurações adicionais
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Registrar a tarefa
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Principal $Principal `
        -Settings $Settings `
        -Description "Coleta automática de índices econômicos do Banco Central (TR, IPCA, INPC) todo dia 30" `
        -ErrorAction Stop
    
    Write-Host "✅ Tarefa agendada criada com SUCESSO!" -ForegroundColor Green
    Write-Host "`n📋 Detalhes:" -ForegroundColor Cyan
    Get-ScheduledTask -TaskName $TaskName | Format-List TaskName, State, Description
    
    Write-Host "`n💡 Comandos úteis:" -ForegroundColor Cyan
    Write-Host "   Ver tarefa:         Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "   Executar agora:     Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "   Ver histórico:      Get-ScheduledTaskInfo -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "   Desabilitar:        Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "   Remover:            Unregister-ScheduledTask -TaskName '$TaskName'`n" -ForegroundColor White
    
} catch {
    Write-Host "❌ Erro ao criar tarefa: $_" -ForegroundColor Red
    Write-Host "`n⚠️  Execute o PowerShell como ADMINISTRADOR se necessário" -ForegroundColor Yellow
}

Write-Host "`n❓ Deseja TESTAR a coleta agora? (S/N): " -NoNewline -ForegroundColor Yellow
$resposta = Read-Host

if ($resposta -eq 'S' -or $resposta -eq 's') {
    Write-Host "`n🔄 Executando coleta de teste..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
    Get-ScheduledTaskInfo -TaskName $TaskName
}

Write-Host "`n================================================================================`n" -ForegroundColor Cyan
