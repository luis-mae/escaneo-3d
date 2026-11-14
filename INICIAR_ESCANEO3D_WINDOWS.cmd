@echo off
setlocal
cd /d "%~dp0"
echo.
echo ESCANEO 3D - inicio local
echo.
where docker >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Desktop no esta instalado o no esta en PATH.
  echo Instala Docker Desktop, reinicia Windows y vuelve a abrir este archivo.
  pause
  exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Desktop no esta iniciado.
  echo Abre Docker Desktop y espera hasta que el motor este listo.
  pause
  exit /b 1
)
docker compose version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Compose no esta disponible.
  pause
  exit /b 1
)
echo Preparando motor 3D. La primera instalacion puede tardar varios minutos...
docker compose up --build -d
if errorlevel 1 (
  echo ERROR: No se pudo iniciar el motor 3D.
  echo Ejecuta: docker compose logs --tail 100
  pause
  exit /b 1
)
echo Esperando respuesta del servidor...
powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 60;$i++){try{$r=Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/salud' -TimeoutSec 3;if($r.colmap_detectado){$ok=$true;break}}catch{};Start-Sleep -Seconds 2};if(-not $ok){exit 1}"
if errorlevel 1 (
  echo ERROR: El servidor no respondio o no detecto COLMAP.
  echo Ejecuta: docker compose logs --tail 100
  pause
  exit /b 1
)
start "" "http://127.0.0.1:8000"
echo ESCANEO 3D listo. La aplicacion se abrio en el navegador.
echo Para detenerla: docker compose down
pause
