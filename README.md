# Sistema RAG con OpenAI y Qdrant

Este sistema implementa un motor de Retrieval Augmented Generation (RAG) utilizando OpenAI para la generación de embeddings y respuestas, y Qdrant como base de datos vectorial para almacenar y buscar información relevante.

## Estructura del Proyecto

```
.
├── app                      # Código principal de la aplicación
│   ├── config.py            # Configuración y variables de entorno
│   ├── Dockerfile           # Definición del contenedor para la API
│   ├── endpoints.py         # Definición de endpoints de la API
│   ├── main.py              # Punto de entrada principal de la API
│   ├── models.py            # Modelos de datos (Pydantic)
│   ├── requirements.txt     # Dependencias Python
│   ├── static               # Archivos estáticos
│   │   └── prompts          # Templates para prompts
│   │       ├── generate_response.txt   # Template para generar respuestas
│   │       └── system_prompt.txt       # Template para el prompt del sistema
│   └── utils.py             # Funciones de utilidad
├── dataset.json             # Dataset de preguntas y respuestas
├── docker-compose.yml       # Configuración de Docker Compose
├── env.example              # Ejemplo de archivo de variables de entorno
├── qdrant                   # Datos de Qdrant
│   ├── config               # Configuración de Qdrant
│   └── qdrant_data          # Datos persistentes de Qdrant
└── scripts
    └── load_dataset.py      # Script para cargar el dataset en Qdrant
```

## Requisitos Previos

- Docker y Docker Compose
- Python 3.9+ (para ejecución local)
- Una clave de API de OpenAI

## Configuración

1. **Variables de Entorno**

   Copia el archivo `env.example` a `.env` y configura las variables:

   ```bash
   cp env.example .env
   ```

   Edita `.env` con tu editor favorito:

   ```
   # OpenAI
   OPENAI_API_KEY=tu_api_key_de_openai
   OPENAI_EMBEDDING_MODEL=text-embedding-3-large
   OPENAI_COMPLETION_MODEL=gpt-4o-mini-2024-07-18

   # Qdrant
   QDRANT_HOST=maxi_qdrant   # Para Docker Compose
   # QDRANT_HOST=localhost   # Para ejecución local
   QDRANT_PORT=6333
   QDRANT_COLLECTION_NAME=qa_items

   # Parámetros de búsqueda
   QDRANT_SEARCH_LIMIT=10
   QDRANT_SEARCH_SCORE_THRESHOLD=0.3

   # Configuración general
   LOG_LEVEL=INFO
   ```

   > **IMPORTANTE**: El valor de `QDRANT_HOST` debe ser:
   > - `maxi_qdrant` cuando ejecutas la API dentro de Docker (usando Docker Compose)
   > - `localhost` cuando ejecutas la API localmente en tu máquina

2. **Crear directorios necesarios**

   ```bash
   mkdir -p logs qdrant/config qdrant/qdrant_data
   ```

## Ejecución

### Script de Inicialización (Recomendado)

El proyecto incluye un script `init_service.sh` que automatiza el proceso de inicialización:

1. **Dar permisos de ejecución al script**

   ```bash
   chmod +x init_service.sh
   ```

2. **Ejecutar el script**

   ```bash
   ./init_service.sh
   ```

   Este script realiza automáticamente las siguientes tareas:
   - Verifica la existencia de archivos necesarios (.env, dataset.json)
   - Crea y configura un entorno virtual de Python
   - Instala las dependencias necesarias
   - Verifica que Qdrant esté en ejecución (o lo inicia con Docker)
   - Carga el dataset en Qdrant
   - OJO No lo ejecutes dos veces porque meterás 2 veces los datos! Si quieres reejecutar borra la colección. 

3. **Para iniciar también la API**

   ```bash
   ./init_service.sh --start-api
   ```

   > El script detectará automáticamente si necesitas usar `localhost` o `maxi_qdrant` para conectar con Qdrant.

4. **Acceder a la documentación de la API**

   Abre en tu navegador:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Con Docker Compose (Manual)

1. **Iniciar los servicios**

   ```bash
   docker-compose up -d
   ```

   Esto iniciará:
   - Qdrant (disponible en http://localhost:6333)
   - La API FastAPI (disponible en http://localhost:8000)

2. **Cargar el dataset**

   ```bash
   # Primero entramos al contenedor
   docker exec -it maxi_api bash

   # Luego ejecutamos el script de carga
   python -m scripts.load_dataset dataset.json
   ```

## Uso de la API

### Endpoints Principales

#### Consulta

- **URL**: `/api/v1/query`
- **Método**: `POST`
- **Descripción**: Realiza una consulta al sistema RAG
- **Ejemplo de Request**:
  ```json
  {
      "consulta": "¿Qué diferencia hay entre el Pack Completo y el Básico?",
      "contexto_previo": "Anteriormente hablamos sobre las opciones de suscripción.",
      "contexto_actual": "Estoy evaluando qué plan contratar."
  }
  ```

#### Añadir Q&A

- **URL**: `/api/v1/add`
- **Método**: `POST`
- **Descripción**: Añade un nuevo par pregunta-respuesta al sistema
- **Ejemplo de Request**:
  ```json
  {
      "keyword": "planes.packs",
      "pregunta": "¿Qué diferencia hay entre el Pack Completo y el Básico?",
      "respuesta": "El Pack Completo incluye todas las funcionalidades premium, mientras que el Pack Básico ofrece solo funciones esenciales a un precio más accesible."
  }
  ```

#### Estado de Salud

- **URL**: `/health`
- **Método**: `GET`
- **Descripción**: Verifica el estado de la API

## Detalles de la Configuración

### OpenAI

- `OPENAI_API_KEY`: Tu clave de API de OpenAI
- `OPENAI_EMBEDDING_MODEL`: Modelo para generar embeddings (por defecto `text-embedding-3-large`)
- `OPENAI_COMPLETION_MODEL`: Modelo para generar respuestas (por defecto `gpt-4o-mini-2024-07-18`)

### Qdrant

- `QDRANT_HOST`: Hostname del servidor Qdrant
  - `maxi_qdrant` para ejecución con Docker Compose
  - `localhost` para ejecución local
- `QDRANT_PORT`: Puerto de Qdrant (por defecto `6333`)
- `QDRANT_COLLECTION_NAME`: Nombre de la colección en Qdrant (por defecto `qa_items`)

### Parámetros de Búsqueda

- `QDRANT_SEARCH_LIMIT`: Número máximo de resultados a devolver (por defecto `10`)
- `QDRANT_SEARCH_SCORE_THRESHOLD`: Umbral mínimo de similitud para considerar un resultado relevante (por defecto `0.3`)

## Logging

Los logs se guardan en:
- Contenedor: `/app/logs/`
- Host: `./logs/` (mapeado desde el contenedor)

## Script de Inicialización

El script `init_service.sh` automatiza la configuración y ejecución del sistema RAG. Realiza las siguientes tareas:

1. **Verificación de requisitos**:
   - Comprueba que exista el archivo `.env`
   - Verifica la existencia del dataset
   - Asegura que las dependencias necesarias estén instaladas

2. **Configuración del entorno**:
   - Crea un entorno virtual de Python si no existe
   - Instala todas las dependencias necesarias
   - Verifica la conectividad con Qdrant

3. **Carga de datos**:
   - Carga automáticamente el dataset en Qdrant
   - Gestiona la configuración correcta para la conexión (localhost vs maxi_qdrant)

4. **Opciones de ejecución**:
   - `./init_service.sh`: Solo configura el entorno y carga el dataset
   - `./init_service.sh --start-api`: Además, inicia la API

> **Nota**: El script detecta automáticamente si estás ejecutando Qdrant a través de Docker o localmente y ajusta la configuración según sea necesario.

## Solución de Problemas

### Error de conexión a Qdrant

Si obtienes errores como "Connection refused" al conectar con Qdrant, verifica:

1. **Desde Docker**: 
   - Asegúrate de que `QDRANT_HOST=maxi_qdrant` en el archivo `.env`
   - Verifica que el contenedor de Qdrant esté ejecutándose:
     ```bash
     docker ps | grep maxi_qdrant
     ```

2. **Desde local**:
   - Asegúrate de que `QDRANT_HOST=localhost` en el archivo `.env`
   - Verifica que el puerto 6333 esté expuesto correctamente:
     ```bash
     curl http://localhost:6333/health
     ```

3. **Usando el script de inicialización**:
   - El script `init_service.sh` debería manejar automáticamente esta configuración
   - Si encuentras problemas, verifica los logs generados por el script

### Error al cargar el dataset

Si tienes problemas al cargar el dataset:

1. Verifica que el archivo `dataset.json` existe y tiene el formato correcto
2. Asegúrate de tener configurada correctamente la API key de OpenAI
3. Revisa los logs para ver errores específicos:
   ```bash
   docker logs maxi_api
   ```

## Despliegue en Producción

Para un entorno de producción:

1. Modifica `docker-compose.yml` para añadir restricciones de recursos
2. Configura un proxy inverso como Nginx para gestionar las solicitudes
3. Implementa autenticación en la API
4. Ajusta los límites de búsqueda según tus necesidades
5. Considera usar una caché para respuestas frecuentes

## Mantenimiento

- **Actualizar el dataset**: Ejecuta nuevamente el script `load_dataset.py`
- **Limpiar los datos de Qdrant**: Elimina el directorio `qdrant/qdrant_data` y reinicia los contenedores
- **Ver logs**: 
  ```bash
  docker logs maxi_api
  docker logs maxi_qdrant
  ```