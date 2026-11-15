@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto usage
if "%~2"=="" goto usage
set "SESSION=%~1"
set "OUTPUT=%~2"
set "FILTER=%~3"
where py >nul 2>nul
if not errorlevel 1 (
  set "PYTHON=py -3"
) else (
  set "PYTHON=python"
)
echo Comprobando Python y dependencias...
%PYTHON% -c "import numpy, scipy; import tools.escanear_fotos_mvp" 
if errorlevel 1 (
  echo ERROR: Python o dependencias no disponibles. Instalar requirements.txt.
  exit /b 1
)
echo [1/3] Revisando reconstruccion existente...
%PYTHON% -m tools.verificar_sesion_mvp "%SESSION%"
if errorlevel 1 goto fail
echo [2/3] Creando OBJ, STL y GLB sin repetir COLMAP...
if /I "%FILTER%"=="filtrar" (
  %PYTHON% -m tools.escanear_fotos_mvp "%SESSION%" --reanudar --salida "%OUTPUT%" --max-puntos 2500 --filtrar-ruido
) else (
  %PYTHON% -m tools.escanear_fotos_mvp "%SESSION%" --reanudar --salida "%OUTPUT%" --max-puntos 2500
)
if errorlevel 1 goto fail
echo [3/3] Verificando los tres formatos exportados...
if not exist "%OUTPUT%\modelo_3d\exportados\modelo.obj" goto fail
if not exist "%OUTPUT%\modelo_3d\exportados\modelo.stl" goto fail
if not exist "%OUTPUT%\modelo_3d\exportados\modelo.glb" goto fail
%PYTHON% -m tools.auditar_exportaciones_mvp "%OUTPUT%\modelo_3d\exportados"
if errorlevel 1 goto fail
echo Resultado guardado en "%OUTPUT%\modelo_3d\exportados"
echo ATENCION: modelo preliminar; escala y calidad no verificadas.
exit /b 0
:usage
echo Uso: reanudar_escaneo_windows.bat "A:\escaneo3d" "A:\escaneo3d_resultado" [filtrar]
echo La carpeta de salida debe ser nueva y estar fuera de la sesion original.
exit /b 2
:fail
echo ERROR: Revisar ERROR_MALLA.txt o resultado del comando anterior.
exit /b 1
