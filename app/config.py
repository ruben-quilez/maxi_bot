"""
Módulo de configuración del sistema RAG.
Gestiona variables de entorno y parámetros de configuración.
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Cargar variables de entorno desde .env si existe
load_dotenv()

class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Configuración de la API
    APP_NAME: str = "Sistema RAG con OpenAI y Qdrant"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL")
    OPENAI_COMPLETION_MODEL: str = os.getenv("OPENAI_COMPLETION_MODEL")
    
    # Configuración de Qdrant
    QDRANT_HOST: str = os.getenv("QDRANT_HOST")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT"))
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME")
    QDRANT_VECTOR_SIZE: int = 3072  # Tamaño de vectores 
    
    # Parámetros de búsqueda en Qdrant
    QDRANT_SEARCH_LIMIT: int = int(os.getenv("QDRANT_SEARCH_LIMIT"))
    QDRANT_SEARCH_SCORE_THRESHOLD: float = float(os.getenv("QDRANT_SEARCH_SCORE_THRESHOLD"))
    
    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

# Instancia global de configuración
settings = Settings()