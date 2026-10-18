@echo off
cd /d "%~dp0"
echo ===================================================
echo   INICIANDO CHROMA APP - MVP COLORIMETRIA ^& MAKEUP
echo ===================================================
echo.
echo 1. Verificando e instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo 2. Inicializando Base de Datos...
python database.py
if errorlevel 1 goto error
echo.
echo 3. Iniciando Servidor Flask en http://localhost:3020 ...
set CHROMA_HOST=127.0.0.1
set CHROMA_PORT=3020
python app.py
:error
pause
