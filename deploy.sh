#!/usr/bin/env bash
# ==============================================================================
# Script de Despliegue Automatizado (1-Click) para E-Commerce Bersaj
# Entorno: AWS Academy EC2 (Ubuntu 22.04 / 24.04 LTS) o Linux Local
# ==============================================================================

set -e

# Colores para la terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

echo -e "${BLUE}"
echo "=================================================================="
echo "    🚀 DESPLIEGUE AUTOMATIZADO - E-COMMERCE BERSAJ 2026-I       "
echo "    Arquitectura de Software - Entrega No. 2 (Prof. Nicolás R.)  "
echo "=================================================================="
echo -e "${NC}"

# 1. Comprobar permisos y sistema
echo -e "${YELLOW}[1/6] Verificando dependencias del sistema...${NC}"

if ! command -v git &> /dev/null; then
    echo "Instalando git..."
    sudo apt-get update && sudo apt-get install -y git
fi

if ! command -v curl &> /dev/null; then
    echo "Instalando curl..."
    sudo apt-get update && sudo apt-get install -y curl
fi

# 2. Instalar Docker y Docker Compose si no están presentes
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}[2/6] Docker no detectado. Instalando Docker Engine y Plugins...${NC}"
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose-v2
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER" || true
    echo -e "${GREEN}Docker instalado correctamente.${NC}"
else
    echo -e "${GREEN}[2/6] Docker ya se encuentra instalado.${NC}"
fi

# Determinar comando de Docker Compose (docker compose o docker-compose)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${YELLOW}Instalando plugin docker-compose-v2...${NC}"
    sudo apt-get update && sudo apt-get install -y docker-compose-v2
    DOCKER_COMPOSE="docker compose"
fi

# Asegurar que el servicio Docker esté activo
sudo systemctl start docker || true

# 3. Preparar archivo de variables de entorno (.env)
echo -e "${YELLOW}[3/6] Verificando variables de entorno (.env)...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Archivo .env creado a partir de .env.example.${NC}"
    else
        cat << 'EOF' > .env
DEBUG=True
SECRET_KEY=bersaj-secret-key-aws-2026-production
EMAIL_MODE=CELERY
USE_CATALOG_MICROSERVICE=true
CATALOG_SERVICE_URL=http://flask_catalog:5001
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EXCHANGE_API_MODE=REAL
ALLY_SERVICE_URL=http://fake-ally-service
EOF
        echo -e "${GREEN}Archivo .env generado con valores por defecto.${NC}"
    fi
else
    echo -e "${GREEN}Archivo .env detectado.${NC}"
fi

# 4. Construir y levantar los 5 contenedores
echo -e "${YELLOW}[4/6] Construyendo y orquestando contenedores con Docker Compose...${NC}"
$DOCKER_COMPOSE down --remove-orphans || true
$DOCKER_COMPOSE up -d --build

# 5. Esperar inicialización y verificar estado de contenedores
echo -e "${YELLOW}[5/6] Esperando inicialización de servicios (migraciones y seed data)...${NC}"
for i in {1..20}; do
    if curl -s http://localhost:80/health &> /dev/null; then
        echo -e "${GREEN}API Gateway (Nginx) respondiendo correctamente.${NC}"
        break
    fi
    sleep 1
done

echo ""
$DOCKER_COMPOSE ps

# 6. Detección de IP y URLs públicas
echo -e "${YELLOW}[6/6] Realizando verificaciones de salud y endpoints...${NC}"

# Obtener IP Pública (soporta AWS EC2 metadata y fallback a internet)
PUBLIC_IP=$(curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)
if [ -z "$PUBLIC_IP" ]; then
    PUBLIC_IP=$(curl -s --connect-timeout 2 https://ifconfig.me 2>/dev/null || echo "localhost")
fi

GATEWAY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/health || echo "000")
CATALOG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/health/catalog || echo "000")
PUBLIC_API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/api/v1/public/catalog || echo "000")
UI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ || echo "000")

echo ""
echo -e "${GREEN}==================================================================${NC}"
echo -e "${GREEN}       🎉 ¡DESPLIEGUE COMPLETADO Y OPERACIONAL CON ÉXITO!        ${NC}"
echo -e "${GREEN}==================================================================${NC}"
echo ""
echo -e "📍 ${BLUE}IP Pública Detectada:${NC} http://${PUBLIC_IP}"
echo ""
echo -e "🔗 ${YELLOW}Endpoints para Revisión y Sustentación:${NC}"
echo -e "   • Tienda Web (Django Core):           http://${PUBLIC_IP}/"
echo -e "   • Formulario de Checkout:             http://${PUBLIC_IP}/tienda/checkout/"
echo -e "   • Catálogo del Aliado:                http://${PUBLIC_IP}/tienda/aliado/"
echo -e "   • Servicio a Proveer (Aliados):       http://${PUBLIC_IP}/api/v1/public/catalog"
echo -e "   • Microservicio Catálogo (Flask):     http://${PUBLIC_IP}/api/v1/products"
echo -e "   • Healthcheck Nginx API Gateway:      http://${PUBLIC_IP}/health"
echo ""
echo -e "🩺 ${YELLOW}Estado de Salud de los Servicios:${NC}"
echo -e "   • Nginx Gateway:       HTTP ${GATEWAY_STATUS}"
echo -e "   • Flask Catalog Svc:   HTTP ${CATALOG_STATUS}"
echo -e "   • Servicio Aliados:    HTTP ${PUBLIC_API_STATUS}"
echo -e "   • Django Frontend:     HTTP ${UI_STATUS}"
echo ""
echo -e "🛠️  ${BLUE}Comandos Útiles de Administración:${NC}"
echo -e "   • Ver logs en tiempo real:    ${YELLOW}${DOCKER_COMPOSE} logs -f${NC}"
echo -e "   • Ver logs de Celery Worker:  ${YELLOW}${DOCKER_COMPOSE} logs -f celery_worker${NC}"
echo -e "   • Reiniciar todos:            ${YELLOW}${DOCKER_COMPOSE} restart${NC}"
echo -e "   • Detener contenedores:       ${YELLOW}${DOCKER_COMPOSE} down${NC}"
echo ""
echo -e "${GREEN}¡Todo listo para la entrega y sustentación!${NC}"
