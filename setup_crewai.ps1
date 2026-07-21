# Script para instalar e testar CrewAI
Write-Host "Instalando CrewAI no Python 3.12..." -ForegroundColor Yellow

.\venv_ai\Scripts\pip.exe install crewai crewai-tools --quiet --no-warn-script-location

Write-Host "`nTestando CrewAI..." -ForegroundColor Yellow
.\venv_ai\Scripts\python.exe -c "from crewai import Agent, Task, Crew; print('✅ CrewAI instalado com sucesso!')"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Instalação completa! Python 3.12 com CrewAI funcionando." -ForegroundColor Green
    Write-Host "`nAgora vamos iniciar o servidor Django com Python 3.12:" -ForegroundColor Cyan
    Write-Host ".\venv_ai\Scripts\python.exe manage.py runserver" -ForegroundColor White
} else {
    Write-Host "`n❌ Erro na instalação" -ForegroundColor Red
}
