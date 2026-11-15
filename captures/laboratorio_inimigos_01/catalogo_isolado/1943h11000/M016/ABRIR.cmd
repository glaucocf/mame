@echo off
cd /d "%~dp0..\..\..\..\.."
python capture_scripts\laboratorio_inimigo.py 1943h11000 --modelo M016 --abrir
if errorlevel 1 pause
