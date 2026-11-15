@echo off
cd /d "%~dp0..\..\.."
python capture_scripts\laboratorio_inimigo.py 1943h01111 --abrir
if errorlevel 1 pause
