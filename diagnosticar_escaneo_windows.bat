@echo off
setlocal
cd /d "%~dp0"
set "SESSION=%~1"
set "OUTPUT=%~2"
if "%SESSION%"=="" set "SESSION=A:\escaneo3d"
if "%OUTPUT%"=="" set "OUTPUT=A:\diagnostico_escaneo3d.zip"
where py >nul 2>nul
if not errorlevel 1 (
  set "PYTHON=py -3"
) else (
  set "PYTHON=python"
)
echo Generando diagnostico seguro de COLMAP...
echo Sesion: "%SESSION%"
echo ZIP: "%OUTPUT%"
%PYTHON% -m tools.paquete_diagnostico_mvp "%SESSION%" --salida "%OUTPUT%"
if errorlevel 1 (
  echo ERROR: no se pudo generar el diagnostico. Revisar Python y la ruta de sesion.
  pause
  exit /b 1
)
echo Diagnostico generado. Adjuntar el ZIP a ChatGPT.
for %%F in ("%OUTPUT%") do explorer "%%~dpF"
pause
