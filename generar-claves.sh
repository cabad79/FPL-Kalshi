#!/bin/bash
# ============================================================
# Generador de claves RSA para Kalshi API
# ============================================================
# Kalshi requiere un par de claves RSA 2048+ para firmar requests.
# Este script genera:
#   - private-key.pem  (clave privada, GUARDAR CON SEGURIDAD)
#   - public-key.pem   (certificado publico, subir a Kalshi)
# ============================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "========================================"
echo "  GENERADOR DE CLAVES RSA - KALSHI"
echo "========================================"
echo ""

# Verificar OpenSSL
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} OpenSSL no esta instalado."
    echo ""
    echo "Instalacion:"
    echo "  Ubuntu/Debian: sudo apt-get install openssl"
    echo "  macOS:         brew install openssl"
    echo "  Fedora:        sudo dnf install openssl"
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK]${NC} OpenSSL detectado."
echo ""

# Directorio de salida
OUTDIR="$HOME/.kalshi"
mkdir -p "$OUTDIR"

echo -e "${BLUE}[INFO]${NC} Los archivos se guardaran en: $OUTDIR"
echo ""

# Verificar si ya existen claves
if [ -f "$OUTDIR/private-key.pem" ]; then
    echo -e "${YELLOW}[ADVERTENCIA]${NC} Ya existe una clave privada en $OUTDIR/private-key.pem"
    read -p "¿Sobrescribir? (s/N): " overwrite
    if [[ ! $overwrite =~ ^[Ss]$ ]]; then
        echo "Cancelado."
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}[PASO 1/3]${NC} Generando clave privada RSA 2048..."
openssl genrsa -out "$OUTDIR/private-key.pem" 2048
echo -e "${GREEN}[OK]${NC} Clave privada generada."
echo ""

echo -e "${BLUE}[PASO 2/3]${NC} Extrayendo clave publica..."
openssl rsa -in "$OUTDIR/private-key.pem" -pubout -out "$OUTDIR/public-key.pem"
echo -e "${GREEN}[OK]${NC} Clave publica extraida."
echo ""

echo -e "${BLUE}[PASO 3/3]${NC} Configurando permisos seguros..."
chmod 700 "$OUTDIR"
chmod 600 "$OUTDIR/private-key.pem"
chmod 644 "$OUTDIR/public-key.pem"
echo -e "${GREEN}[OK]${NC} Permisos configurados."
echo ""

echo "========================================"
echo "  CLAVES GENERADAS EXITOSAMENTE"
echo "========================================"
echo ""
echo "Ubicacion:"
echo "  Clave PRIVADA: $OUTDIR/private-key.pem"
echo "  Clave PUBLICA: $OUTDIR/public-key.pem"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC}"
echo "  - La clave PRIVADA nunca debe compartirse ni subirse a internet"
echo "  - La clave PUBLICA debes subirla a Kalshi en:"
echo "    https://kalshi.com/account/api-keys"
echo "  - Guarda un backup de la clave privada en un lugar seguro"
echo ""
echo "Proximos pasos:"
echo "  1. Copia private-key.pem al proyecto:"
echo "     cp $OUTDIR/private-key.pem .kalshi/private-key.pem"
echo "  2. Sube public-key.pem a Kalshi y obtien tu KEY_ID"
echo "  3. Edita .env con tu KEY_ID"
echo "  4. Ejecuta: docker-compose up -d kalshi-mcp"
echo ""

# Mostrar fingerprint para verificacion
echo "Fingerprint (SHA-256) de la clave publica:"
openssl rsa -in "$OUTDIR/private-key.pem" -pubout -outform DER 2>/dev/null | openssl sha256

echo ""
