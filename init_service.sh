#!/bin/bash

# Script para inicializar el servicio RAG y cargar el dataset
# Autor: Claude
# Fecha: 10/03/2025

# Colores para los mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio base del proyecto
PROJECT_DIR="$(pwd)"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
DATASET_FILE="$PROJECT_DIR/dataset.json"

# Función para imprimir mensajes con formato
log_message() {
    local level=$1
    local message=$2
    local color=$NC

    case "$level" in
        "INFO") color=$GREEN ;;
        "WARN") color=$YELLOW ;;
        "ERROR") color=$RED ;;
    esac

    echo -e "${color}[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $message${NC}"
}

# Verificar si existe el archivo .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    log_message "ERROR" "No se encontró el archivo .env. Por favor, crea este archivo basado en env.example."
    exit 1
fi

# Verificar si el dataset existe
if [ ! -f "$DATASET_FILE" ]; then
    log_message "ERROR" "No se encontró el archivo dataset.json en $DATASET_FILE"
    exit 1
fi

# Crear y activar entorno virtual
VENV_DIR="$PROJECT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    log_message "INFO" "Creando entorno virtual en $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Error al crear el entorno virtual. Asegúrate de tener instalado python3-venv."
        log_message "INFO" "Puedes instalarlo con: sudo apt install python3-venv python3-full"
        exit 1
    fi
    log_message "INFO" "Entorno virtual creado correctamente."
else
    log_message "INFO" "Usando entorno virtual existente en $VENV_DIR"
fi

# Activar el entorno virtual
log_message "INFO" "Activando entorno virtual..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    log_message "ERROR" "Error al activar el entorno virtual."
    exit 1
fi

# Instalar dependencias de Python en el entorno virtual
log_message "INFO" "Instalando dependencias de Python en el entorno virtual..."
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/app/requirements.txt"
if [ $? -ne 0 ]; then
    log_message "ERROR" "Error al instalar las dependencias de Python."
    exit 1
fi
log_message "INFO" "Dependencias instaladas correctamente."

# Verificar si los contenedores Docker están en ejecución
if command -v docker &> /dev/null; then
    log_message "INFO" "Verificando si los contenedores Docker están en ejecución..."
    
    # Verificar si los contenedores ya están en ejecución
    QDRANT_RUNNING=$(docker ps | grep maxi_qdrant | wc -l)
    
    if [ "$QDRANT_RUNNING" -eq 0 ]; then
        log_message "INFO" "Iniciando contenedores con docker-compose..."
        docker-compose up -d maxi_qdrant
        
        # Esperar a que Qdrant esté listo
        log_message "INFO" "Esperando a que Qdrant esté listo..."
        sleep 10
    else
        log_message "INFO" "El contenedor de Qdrant ya está en ejecución."
    fi
else
    log_message "WARN" "Docker no está instalado o no está en el PATH. Asegúrate de que Qdrant esté en ejecución manualmente."
    
    # Esperar a que el usuario confirme que Qdrant está en ejecución
    read -p "¿Está Qdrant en ejecución? (s/n): " qdrant_running
    if [[ "$qdrant_running" != "s" && "$qdrant_running" != "S" ]]; then
        log_message "ERROR" "Por favor, inicia Qdrant antes de continuar."
        exit 1
    fi
fi

# Verificar la conectividad con Qdrant
log_message "INFO" "Verificando la conectividad con Qdrant..."
# Extraer el host y puerto de Qdrant del archivo .env
QDRANT_HOST=$(grep QDRANT_HOST "$PROJECT_DIR/.env" | cut -d '=' -f2 | cut -d '#' -f1 | tr -d ' ')
QDRANT_PORT=$(grep QDRANT_PORT "$PROJECT_DIR/.env" | cut -d '=' -f2 | cut -d '#' -f1 | tr -d ' ')

# Si QDRANT_HOST es "maxi_qdrant" (nombre del contenedor), cambiarlo a localhost para la verificación
if [ "$QDRANT_HOST" = "maxi_qdrant" ]; then
    QDRANT_HOST="localhost"
fi

# Intentar conectarse a Qdrant
timeout 5 bash -c "cat < /dev/null > /dev/tcp/$QDRANT_HOST/$QDRANT_PORT"
if [ $? -ne 0 ]; then
    log_message "ERROR" "No se puede conectar a Qdrant en $QDRANT_HOST:$QDRANT_PORT"
    exit 1
fi
log_message "INFO" "Conectividad con Qdrant verificada."

# Ejecutar el script de carga del dataset
log_message "INFO" "Iniciando la carga del dataset..."
cd "$PROJECT_DIR"
"$VENV_DIR/bin/python" "$SCRIPTS_DIR/load_dataset.py" "$DATASET_FILE"

if [ $? -ne 0 ]; then
    log_message "ERROR" "Error durante la carga del dataset."
    exit 1
fi

log_message "INFO" "Dataset cargado correctamente."

# Iniciar la API si se especifica
if [ "$1" = "--start-api" ]; then
    log_message "INFO" "Iniciando la API..."
    
    # Verificar si la API ya está en ejecución en docker
    API_RUNNING=$(docker ps | grep maxi_api | wc -l)
    
    if [ "$API_RUNNING" -eq 0 ]; then
        docker-compose up -d maxi_api
        log_message "INFO" "API iniciada. Accede a la documentación en http://localhost:8000/docs"
    else
        log_message "INFO" "La API ya está en ejecución."
    fi
fi

log_message "INFO" "Inicialización completada con éxito."
exit 0