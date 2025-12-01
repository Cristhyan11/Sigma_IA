@echo off

Title Calificador de Imágenes Médicas
echo.
echo ⚡ Iniciando GUI para uso médico...
echo.
REM ejecutando
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error ejecutando el GUI
    echo 💡 Verificar dependencias: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo 👋 GUI cerrado correctamente.
pause