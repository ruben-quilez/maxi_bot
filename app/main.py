"""
Punto de entrada principal para la aplicación FastAPI del sistema RAG.
Configura la aplicación, middleware, logging y monta los endpoints.
"""

import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
import json

from config import settings
from endpoints import router

# Configurar el logger
logger.remove()  # Remover el handler por defecto
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)


# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para sistema de Retrieval Augmented Generation (RAG) con OpenAI y Qdrant",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, limitar a orígenes específicos
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Middleware para logging de peticiones
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para registrar información sobre las peticiones."""
    start_time = time.time()
    
    # Generar ID único para la petición
    request_id = f"{time.time():.0f}"
    
    # Registrar detalles iniciales
    logger.info(f"Inicio de petición [{request_id}] {request.method} {request.url.path}")
    
    # Intentar leer el cuerpo de la petición
    try:
        body = await request.body()
        if body:
            try:
                # Intentar parsear como JSON
                body_str = body.decode("utf-8")
                if len(body_str) > 0:
                    logger.debug(f"Request body [{request_id}]: {body_str}")
            except Exception as e:
                logger.warning(f"No se pudo decodificar el cuerpo de la petición: {str(e)}")
    except Exception:
        pass
    
    # Procesar la petición
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Registrar detalles finales
        logger.info(f"Fin de petición [{request_id}] {request.method} {request.url.path} - Status: {response.status_code} - Tiempo: {process_time:.2f}ms")
        
        # Añadir cabecera con tiempo de procesamiento
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
    
    except Exception as e:
        # Registrar errores no manejados
        logger.error(f"Error no manejado en petición [{request_id}]: {str(e)}")
        
        # Generar respuesta de error
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "codigo": 500,
                "mensaje": "Error interno del servidor",
                "detalle": str(e)
            }
        )

# Incluir los routers definidos
app.include_router(router)

# Endpoint de verificación de estado
@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado de la API."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Mensaje informativo de inicio
@app.on_event("startup")
async def startup_event():
    """Evento ejecutado al iniciar la aplicación."""
    logger.info(f"=== Iniciando {settings.APP_NAME} v{settings.APP_VERSION} ===")
    logger.info(f"Docs disponibles en: /docs")
    logger.info(f"API configurada con prefijo: {settings.API_PREFIX}")

# Si se ejecuta este archivo directamente
if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor con Uvicorn...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)