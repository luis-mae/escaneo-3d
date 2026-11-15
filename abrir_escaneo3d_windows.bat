@echo off
setlocal
cd /d "%~dp0"
echo ESCANEO 3D - Servidor local
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)
%PY% -c "import sys; print(sys.version)" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Instala Python 3.11 y vuelve a ejecutar.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual...
  %PY% -m venv .venv
  if errorlevel 1 goto error
)
set "P=.venv\Scripts\python.exe"
echo Instalando dependencias de ESCANEO 3D...
"%P%" -m pip install -r requirements-web.txt
if errorlevel 1 goto error
echo.
echo La funcion Quitar fondo requiere IA adicional.
choice /C SN /N /M "Instalar motor de quitar fondo ahora? [S/N]: "
if errorlevel 2 goto ejecutar
"%P%" -m pip install -r requirements-fondo.txt
if errorlevel 1 echo AVISO: no se instalo el motor de quitar fondo.
:ejecutar
echo.
echo Abri http://127.0.0.1:8000 en esta PC.
echo Para detener, presiona Ctrl+C.
start "" "http://127.0.0.1:8000"
"%P%" -m uvicorn tools.servidor_web:app --host 127.0.0.1 --port 8000
exit /b %errorlevel%
:error
echo ERROR: no se pudo preparar el servidor.
pause
exit /b 1
