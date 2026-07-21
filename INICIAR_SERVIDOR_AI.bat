@echo off
cd /d "%~dp0"
title COFLUHAB Servidor Django + CrewAI
color 0A
echo ============================================
echo  COFLUHAB - Servidor Django + CrewAI
echo  Python 3.12 + Django 6.0.1
echo ============================================
echo.
echo Verificando Python 3.12...
venv_ai\Scripts\python.exe --version
echo.
echo Iniciando servidor em http://127.0.0.1:8000/
echo.
echo Paginas disponiveis:
echo   - http://127.0.0.1:8000/
echo   - http://127.0.0.1:8000/integracao-cef/
echo   - http://127.0.0.1:8000/ai-agents/test/
echo.
echo IMPORTANTE: NAO FECHE ESTA JANELA!
echo Pressione Ctrl+C para parar o servidor
echo ============================================
echo.

venv_ai\Scripts\python.exe manage.py runserver --noreload

echo.
echo ============================================
echo Servidor foi encerrado.
echo ============================================
pause
