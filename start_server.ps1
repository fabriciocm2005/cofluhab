Write-Host "============================================" -ForegroundColor Cyan
Write-Host " COFLUHAB - Servidor Django + CrewAI" -ForegroundColor Green
Write-Host " Python 3.12 + Django 6.0.1" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

Write-Host "Verificando Python 3.12..." -ForegroundColor Yellow
& .\venv_ai\Scripts\python.exe --version
Write-Host ""

Write-Host "Testando CrewAI..." -ForegroundColor Yellow
& .\venv_ai\Scripts\python.exe -c "from crewai import Agent; from crewai.tools import tool; print('✅ CrewAI OK')"
Write-Host ""

Write-Host "Iniciando servidor em http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host ""
Write-Host "Páginas disponíveis:" -ForegroundColor Cyan
Write-Host "  - http://127.0.0.1:8000/" -ForegroundColor White
Write-Host "  - http://127.0.0.1:8000/integracao-cef/" -ForegroundColor White
Write-Host "  - http://127.0.0.1:8000/ai-agents/test/" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANTE: MANTENHA ESTA JANELA ABERTA!" -ForegroundColor Yellow
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Inicia o servidor
& .\venv_ai\Scripts\python.exe manage.py runserver --noreload

Write-Host ""
Write-Host "============================================" -ForegroundColor Red
Write-Host "Servidor foi encerrado." -ForegroundColor Red
Write-Host "============================================" -ForegroundColor Red
Write-Host ""
Read-Host "Pressione Enter para fechar"
