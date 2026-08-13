@echo off
REM ============================================================
REM MCP Kalshi + FPL - Docker Launcher para Windows
REM ============================================================

echo.
echo ========================================
echo   MCP KALSHI + FPL - Docker Launcher
echo ========================================
echo.

REM Verificar que Docker esta instalado
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no esta instalado o no esta en el PATH.
    echo Descargalo desde: https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe
    pause
    exit /b 1
)

REM Verificar que Docker Compose esta disponible
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose no esta disponible.
    echo Actualiza Docker Desktop a la ultima version.
    pause
    exit /b 1
)

echo [OK] Docker detectado.
echo.

REM Crear directorios necesarios
if not exist .kalshi mkdir .kalshi
if not exist logs mkdir logs

REM Verificar que la clave privada existe (solo para Kalshi)
if not exist .kalshi\private-key.pem (
    echo [ADVERTENCIA] No se encontro .kalshi\private-key.pem
    echo.
    echo Para usar Kalshi, necesitas una clave privada:
    echo 1. Ve a https://kalshi.com/account/api-keys (demo)
    echo 2. Genera un par de claves RSA
    echo 3. Guarda la clave privada en .kalshi\private-key.pem
    echo.
)

REM Verificar que el .env existe
if not exist .env (
    echo [INFO] Creando .env con valores por defecto...
    echo KALSHI_ENV=demo > .env
    echo KALSHI_KEY_ID=tu_key_id_aqui >> .env
    echo.
    echo [IMPORTANTE] Edita el archivo .env con tus credenciales reales de Kalshi.
    echo El FPL MCP no requiere credenciales.
    echo.
)

echo.
echo ========================================
echo   MENU PRINCIPAL
echo ========================================
echo.
echo [1]  Iniciar AMBOS MCPs (Kalshi + FPL)
echo [2]  Iniciar solo KALSHI MCP
echo [3]  Iniciar solo FPL MCP
echo [4]  Construir imagenes
echo [5]  Ver logs de Kalshi
echo [6]  Ver logs de FPL
echo [7]  Detener todos los contenedores
echo [8]  Shell en contenedor Kalshi
echo [9]  Shell en contenedor FPL
echo [10] Limpiar todo (volumenes + imagenes)
echo [11] Salir
echo.

set /p option="Selecciona una opcion (1-11): "

if "%option%"=="1" goto start_both
if "%option%"=="2" goto start_kalshi
if "%option%"=="3" goto start_fpl
if "%option%"=="4" goto build
if "%option%"=="5" goto logs_kalshi
if "%option%"=="6" goto logs_fpl
if "%option%"=="7" goto stop
if "%option%"=="8" goto shell_kalshi
if "%option%"=="9" goto shell_fpl
if "%option%"=="10" goto clean
if "%option%"=="11" goto end

echo Opcion invalida.
pause
exit /b 1

:start_both
echo.
echo [INFO] Iniciando AMBOS MCPs...
echo [INFO] Kalshi: DEMO (requiere clave privada)
echo [INFO] FPL: Public API (no requiere credenciales)
echo.
docker-compose up --build -d kalshi-mcp fpl-mcp
echo.
echo [OK] Contenedores iniciados.
echo.
echo Para ver logs en tiempo real:
echo   docker logs -f kalshi-mcp-demo
echo   docker logs -f fpl-mcp-demo
echo.
pause
goto end

:start_kalshi
echo.
echo [INFO] Iniciando KALSHI MCP (DEMO)...
docker-compose up --build -d kalshi-mcp
echo.
echo [OK] Kalshi MCP iniciado.
echo Para ver logs: docker logs -f kalshi-mcp-demo
echo.
pause
goto end

:start_fpl
echo.
echo [INFO] Iniciando FPL MCP...
docker-compose up --build -d fpl-mcp
echo.
echo [OK] FPL MCP iniciado.
echo Para ver logs: docker logs -f fpl-mcp-demo
echo.
echo Puedes probarlo ahora:
echo   docker exec -it fpl-mcp-demo python -c "import fpl_mcp_server; print('OK')"
echo.
pause
goto end

:build
echo.
echo [INFO] Construyendo imagenes Docker...
docker-compose build --no-cache
echo.
echo [OK] Imagenes construidas.
pause
goto end

:logs_kalshi
echo.
echo [INFO] Logs de Kalshi MCP...
docker logs -f kalshi-mcp-demo 2>nul || echo [ERROR] Contenedor no esta corriendo.
pause
goto end

:logs_fpl
echo.
echo [INFO] Logs de FPL MCP...
docker logs -f fpl-mcp-demo 2>nul || echo [ERROR] Contenedor no esta corriendo.
pause
goto end

:stop
echo.
echo [INFO] Deteniendo todos los contenedores...
docker-compose down
echo [OK] Contenedores detenidos.
pause
goto end

:shell_kalshi
echo.
echo [INFO] Shell en Kalshi MCP...
docker exec -it kalshi-mcp-demo /bin/bash 2>nul || echo [ERROR] Contenedor no esta corriendo.
pause
goto end

:shell_fpl
echo.
echo [INFO] Shell en FPL MCP...
docker exec -it fpl-mcp-demo /bin/sh 2>nul || echo [ERROR] Contenedor no esta corriendo.
pause
goto end

:clean
echo.
echo [ADVERTENCIA] Esto eliminara todos los contenedores, volumenes e imagenes.
set /p confirm="Estas seguro? (s/N): "
if /i "%confirm%"=="s" (
    docker-compose down -v --rmi all
    docker system prune -f
    echo [OK] Limpieza completada.
) else (
    echo Cancelado.
)
pause
goto end

:end
echo.
echo Hasta luego.
