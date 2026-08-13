#!/bin/bash
# ============================================================
# MCP Kalshi + FPL - Docker Launcher para Linux/macOS/Git Bash
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
echo "  MCP KALSHI + FPL - Docker Launcher"
echo "========================================"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker no esta instalado."
    echo "Descargalo desde: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker Compose no esta disponible."
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Docker detectado."
echo ""

# Crear directorios
mkdir -p .kalshi logs

# Verificar clave privada (solo para Kalshi)
if [ ! -f .kalshi/private-key.pem ]; then
    echo -e "${YELLOW}[ADVERTENCIA]${NC} No se encontro .kalshi/private-key.pem"
    echo "Para usar Kalshi, necesitas una clave privada:"
    echo "  1. Ve a https://kalshi.com/account/api-keys (demo)"
    echo "  2. Genera un par de claves RSA"
    echo "  3. Guarda la clave privada en .kalshi/private-key.pem"
    echo ""
fi

# Verificar .env
if [ ! -f .env ]; then
    echo -e "${BLUE}[INFO]${NC} Creando .env con valores por defecto..."
    cat > .env <<EOF
KALSHI_ENV=demo
KALSHI_KEY_ID=tu_key_id_aqui
EOF
    echo -e "${YELLOW}[IMPORTANTE]${NC} Edita .env con tus credenciales reales de Kalshi."
    echo "El FPL MCP no requiere credenciales."
    echo ""
fi

# Menu
while true; do
    echo ""
    echo "========================================"
    echo "  MENU PRINCIPAL"
    echo "========================================"
    echo ""
    echo " [1]  Iniciar AMBOS MCPs (Kalshi + FPL)"
    echo " [2]  Iniciar solo KALSHI MCP"
    echo " [3]  Iniciar solo FPL MCP"
    echo " [4]  Construir imagenes"
    echo " [5]  Ver logs de Kalshi"
    echo " [6]  Ver logs de FPL"
    echo " [7]  Detener todos los contenedores"
    echo " [8]  Shell en Kalshi"
    echo " [9]  Shell en FPL"
    echo " [10] Limpiar todo"
    echo " [11] Salir"
    echo ""
    read -p "Selecciona una opcion (1-11): " option

    case $option in
        1)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Iniciando AMBOS MCPs..."
            echo -e "${GREEN}[INFO]${NC} Kalshi: DEMO (requiere clave privada)"
            echo -e "${GREEN}[INFO]${NC} FPL: Public API (no requiere credenciales)"
            echo ""
            docker-compose up --build -d kalshi-mcp fpl-mcp
            echo ""
            echo -e "${GREEN}[OK]${NC} Contenedores iniciados."
            echo "Para ver logs:"
            echo "  docker logs -f kalshi-mcp-demo"
            echo "  docker logs -f fpl-mcp-demo"
            read -p "Presiona Enter para continuar..."
            ;;
        2)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Iniciando KALSHI MCP (DEMO)..."
            docker-compose up --build -d kalshi-mcp
            echo -e "${GREEN}[OK]${NC} Kalshi MCP iniciado."
            read -p "Presiona Enter para continuar..."
            ;;
        3)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Iniciando FPL MCP..."
            docker-compose up --build -d fpl-mcp
            echo -e "${GREEN}[OK]${NC} FPL MCP iniciado."
            echo "Para probar: docker logs -f fpl-mcp-demo"
            read -p "Presiona Enter para continuar..."
            ;;
        4)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Construyendo imagenes..."
            docker-compose build --no-cache
            echo -e "${GREEN}[OK]${NC} Imagenes construidas."
            read -p "Presiona Enter para continuar..."
            ;;
        5)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Logs de Kalshi..."
            docker logs -f kalshi-mcp-demo 2>/dev/null || echo -e "${YELLOW}No esta corriendo.${NC}"
            read -p "Presiona Enter para continuar..."
            ;;
        6)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Logs de FPL..."
            docker logs -f fpl-mcp-demo 2>/dev/null || echo -e "${YELLOW}No esta corriendo.${NC}"
            read -p "Presiona Enter para continuar..."
            ;;
        7)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Deteniendo contenedores..."
            docker-compose down
            echo -e "${GREEN}[OK]${NC} Detenidos."
            read -p "Presiona Enter para continuar..."
            ;;
        8)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Shell en Kalshi..."
            docker exec -it kalshi-mcp-demo /bin/bash 2>/dev/null || echo -e "${YELLOW}No esta corriendo.${NC}"
            read -p "Presiona Enter para continuar..."
            ;;
        9)
            echo ""
            echo -e "${BLUE}[INFO]${NC} Shell en FPL..."
            docker exec -it fpl-mcp-demo /bin/sh 2>/dev/null || echo -e "${YELLOW}No esta corriendo.${NC}"
            read -p "Presiona Enter para continuar..."
            ;;
        10)
            echo ""
            echo -e "${YELLOW}[ADVERTENCIA]${NC} Esto eliminara todo."
            read -p "¿Estas seguro? (s/N): " confirm
            if [[ $confirm =~ ^[Ss]$ ]]; then
                docker-compose down -v --rmi all
                docker system prune -f
                echo -e "${GREEN}[OK]${NC} Limpieza completada."
            else
                echo "Cancelado."
            fi
            read -p "Presiona Enter para continuar..."
            ;;
        11)
            echo ""
            echo "Hasta luego."
            exit 0
            ;;
        *)
            echo -e "${RED}Opcion invalida.${NC}"
            ;;
    esac
done
