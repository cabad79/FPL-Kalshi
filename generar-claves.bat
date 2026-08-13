@echo off
REM ============================================================
REM Generador de claves RSA para Kalshi API
REM ============================================================
REM Kalshi requiere un par de claves RSA 2048+ para firmar requests.
REM Este script genera:
REM   - private-key.pem  (clave privada, GUARDAR CON SEGURIDAD)
REM   - public-key.pem   (certificado publico, subir a Kalshi)
REM ============================================================

echo.
echo ========================================
echo   GENERADOR DE CLAVES RSA - KALSHI
echo ========================================
echo.

REM Verificar que OpenSSL esta instalado
openssl version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] OpenSSL no esta instalado o no esta en el PATH.
    echo.
    echo Opciones de instalacion:
    echo   1. Git for Windows incluye OpenSSL:
    echo      https://git-scm.com/download/win
    echo   2. OpenSSL oficial:
    echo      https://slproweb.com/products/Win32OpenSSL.html
    echo   3. Chocolatey: choco install openssl
    echo.
    pause
    exit /b 1
)

echo [OK] OpenSSL detectado.
echo.

REM Directorio de salida
set OUTDIR=%USERPROFILE%\.kalshi
if not exist %OUTDIR% mkdir %OUTDIR%

echo Los archivos se guardaran en: %OUTDIR%
echo.

REM Verificar si ya existen claves
if exist %OUTDIR%\private-key.pem (
    echo [ADVERTENCIA] Ya existe una clave privada en %OUTDIR%\private-key.pem
    set /p overwrite="¿Sobrescribir? (s/N): "
    if /i not "!overwrite!"=="s" (
        echo Cancelado.
        pause
        exit /b 0
    )
)

echo.
echo [PASO 1/3] Generando clave privada RSA 2048...
openssl genrsa -out %OUTDIR%\private-key.pem 2048
if errorlevel 1 (
    echo [ERROR] Fallo al generar la clave privada.
    pause
    exit /b 1
)

echo [OK] Clave privada generada.
echo.

echo [PASO 2/3] Extrayendo clave publica...
openssl rsa -in %OUTDIR%\private-key.pem -pubout -out %OUTDIR%\public-key.pem
if errorlevel 1 (
    echo [ERROR] Fallo al extraer la clave publica.
    pause
    exit /b 1
)

echo [OK] Clave publica extraida.
echo.

echo [PASO 3/3] Configurando permisos seguros...
icacls %OUTDIR%\private-key.pem /inheritance:r >nul 2>&1
icacls %OUTDIR%\private-key.pem /grant:r "%USERNAME%:R" >nul 2>&1

echo [OK] Permisos configurados (solo lectura para tu usuario).
echo.

echo ========================================
echo   CLAVES GENERADAS EXITOSAMENTE
echo ========================================
echo.
echo Ubicacion:
echo   Clave PRIVADA: %OUTDIR%\private-key.pem
echo   Clave PUBLICA: %OUTDIR%\public-key.pem
echo.
echo IMPORTANTE:
echo   - La clave PRIVADA nunca debe compartirse ni subirse a internet
echo   - La clave PUBLICA debes subirla a Kalshi en:
echo     https://kalshi.com/account/api-keys
echo   - Guarda un backup de la clave privada en un lugar seguro
echo.
echo Proximos pasos:
echo   1. Copia private-key.pem al proyecto:
echo      copy %OUTDIR%\private-key.pem .kalshi\private-key.pem
echo   2. Sube public-key.pem a Kalshi y obtien tu KEY_ID
echo   3. Edita .env con tu KEY_ID
echo   4. Ejecuta: docker-compose up -d kalshi-mcp
echo.

REM Mostrar fingerprint para verificacion
openssl rsa -in %OUTDIR%\private-key.pem -pubout -outform DER 2>nul | openssl sha256

echo.
pause
