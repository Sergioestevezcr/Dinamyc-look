#!/bin/bash
# deploy.sh - Script de despliegue automatizado para VPS con Webuzo

echo "🚀 Iniciando despliegue de Dinamyc Look..."

# Variables - AJUSTA ESTOS VALORES
SERVER_USER="tu_usuario"
SERVER_IP="tu_ip_del_servidor"
REMOTE_PATH="/home/$SERVER_USER/public_html/dinamyclook.com"
LOCAL_PATH="."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    log_error "Archivo .env no encontrado. Copia .env.example a .env y configúralo."
    exit 1
fi

log_info "Archivo .env encontrado ✓"

# Crear archivo temporal excluyendo archivos innecesarios
log_info "Creando archivo temporal para subir..."
tar -czf dinamyc-look-deploy.tar.gz \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.gitignore' \
    --exclude='deploy.sh' \
    --exclude='*.tar.gz' \
    .

log_info "Archivo comprimido creado ✓"

# Subir archivos al servidor
log_info "Subiendo archivos al servidor..."
scp dinamyc-look-deploy.tar.gz $SERVER_USER@$SERVER_IP:~/

if [ $? -ne 0 ]; then
    log_error "Error al subir archivos"
    rm dinamyc-look-deploy.tar.gz
    exit 1
fi

log_info "Archivos subidos ✓"

# Ejecutar comandos en el servidor
log_info "Configurando en el servidor..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
    # Crear directorio si no existe
    mkdir -p ~/public_html/dinamyclook.com
    
    # Descomprimir archivos
    tar -xzf ~/dinamyc-look-deploy.tar.gz -C ~/public_html/dinamyclook.com/
    
    # Navegar al directorio
    cd ~/public_html/dinamyclook.com
    
    # Crear entorno virtual si no existe
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    
    # Activar entorno virtual
    source .venv/bin/activate
    
    # Instalar/actualizar dependencias
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Crear directorio tmp si no existe (para Passenger)
    mkdir -p tmp
    
    # Configurar permisos
    chmod +x wsgi.py
    chmod -R 755 static
    
    # Reiniciar aplicación (Passenger)
    touch tmp/restart.txt
    
    # Limpiar archivo temporal
    rm ~/dinamyc-look-deploy.tar.gz
    
    echo "✅ Despliegue completado en el servidor"
ENDSSH

# Limpiar archivo local
rm dinamyc-look-deploy.tar.gz

log_info "🎉 ¡Despliegue completado exitosamente!"
log_info "Visita tu sitio en: https://dinamyclook.com"
