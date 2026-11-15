@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo No existe el entorno local. Ejecuta primero abrir_escaneo3d_windows.bat
  pause
  exit /b 1
)
set "SESION=A:\escaneo3d"
if not exist "%SESION%\" (
  echo No se encontro A:\escaneo3d
  set /p "SESION=Ruta completa de la sesion COLMAP: "
)
if not exist "%SESION%\" (
  echo ERROR: la carpeta no existe.
  pause
  exit /b 1
)
echo.
echo Diagnostico de la sesion existente, sin repetir COLMAP:
"%PY%" -m tools.diagnosticar_entorno_mvp --sesion "%SESION%"
if errorlevel 1 (
  echo.
  echo No se detecto una nube utilizable o faltan dependencias.
  echo No se generara una malla ficticia.
  pause
  exit /b 1
)
echo.
choice /C SN /N /M "Procesar nube existente sin repetir COLMAP? [S/N]: "
if errorlevel 2 exit /b 0
set "SALIDA=%~dp0resultados_reanudados"
set /a NUM=1
:buscar
if exist "%SALIDA%_%NUM%" (
  set /a NUM+=1
  goto buscar
)
set "DESTINO=%SALIDA%_%NUM%"
echo Exportando a "%DESTINO%"
"%PY%" -m tools.escanear_fotos_mvp "%SESION%" --reanudar --filtrar-ruido --salida "%DESTINO%"
if errorlevel 1 (
  echo ERROR: no se pudo completar la exportacion.
  pause
  exit /b 1
)
echo.
echo Archivos generados en "%DESTINO%\modelo_3d\exportados"
echo IMPORTANTE: comprobar visualmente el modelo; no asumir escala ni imprimibilidad.
start "" explorer "%DESTINO%"
pause
