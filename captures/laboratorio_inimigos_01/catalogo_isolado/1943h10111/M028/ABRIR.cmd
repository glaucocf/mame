@echo off
cd /d "%~dp0..\..\..\..\.."
python capture_scripts\laboratorio_inimigo.py 1943h10111 --modelo M028 --abrir
if errorlevel 1 pause
