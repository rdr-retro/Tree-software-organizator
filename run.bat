@echo off
setlocal

echo === Tree Software Organization ===
echo.

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

:: Crear entorno virtual si no existe
if not exist "%VENV_DIR%" (
    echo Creando entorno virtual...
    python -m venv "%VENV_DIR%"
    echo.
)

:: Activar entorno virtual
call "%VENV_DIR%\Scripts\activate.bat"

:: Verificar si PySide6 está instalado
python -c "import PySide6" 2>nul
if errorlevel 1 (
    echo Instalando PySide6...
    pip install PySide6
    echo.
)

:: Ejecutar el programa
echo Ejecutando Tree Software Organization...
echo.
python "%SCRIPT_DIR%src\main.py"

:: Desactivar entorno virtual
call deactivate

endlocal
pause
