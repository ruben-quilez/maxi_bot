"""
Script para cargar dataset.json en Qdrant.
Procesa cada entrada, genera embeddings e inserta registros en Qdrant.
"""

import json
import time
import uuid
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger
import openai
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from dotenv import load_dotenv

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings

# Cargar variables de entorno
load_dotenv()

# Configurar OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)

# Configurar el logger
logger.remove()  # Remover el handler por defecto
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

def generar_embedding(texto: str) -> List[float]:
    """
    Genera un embedding para el texto utilizando OpenAI.
    
    Args:
        texto (str): Texto para el cual generar embedding
        
    Returns:
        List[float]: Vector de embedding
    """
    try:
        response = openai.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=texto
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error al generar embedding: {str(e)}")
        raise

def setup_qdrant_collection() -> QdrantClient:
    """
    Configura la conexión con Qdrant y asegura que exista la colección.
    
    Returns:
        QdrantClient: Cliente de Qdrant
    """
    try:
        # Inicializar el cliente
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        
        # Obtener colecciones existentes
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        # Crear la colección si no existe
        if settings.QDRANT_COLLECTION_NAME not in collection_names:
            logger.info(f"Creando colección {settings.QDRANT_COLLECTION_NAME} en Qdrant")
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=qdrant_models.VectorParams(
                    size=settings.QDRANT_VECTOR_SIZE,
                    distance=qdrant_models.Distance.COSINE
                )
            )
            logger.info(f"Colección {settings.QDRANT_COLLECTION_NAME} creada con éxito")
        else:
            logger.info(f"Utilizando colección existente: {settings.QDRANT_COLLECTION_NAME}")
        
        return client
    except Exception as e:
        logger.error(f"Error al configurar Qdrant: {str(e)}")
        raise

def cargar_dataset(filepath: str) -> None:
    """
    Carga el dataset desde un archivo JSON y lo procesa.
    
    Args:
        filepath (str): Ruta al archivo dataset.json
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(filepath):
            logger.error(f"El archivo {filepath} no existe")
            return
        
        # Leer el archivo
        with open(filepath, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        logger.info(f"Archivo {filepath} cargado. Contiene {len(dataset)} elementos")
        
        # Inicializar el cliente Qdrant
        client = setup_qdrant_collection()
        
        # Procesar cada elemento
        items_procesados = 0
        items_fallidos = 0
        
        for i, item in enumerate(dataset):
            try:
                logger.info(f"Procesando item {i+1}/{len(dataset)}: {item.get('keyword', 'sin keyword')}")
                
                # Verificar campos obligatorios
                if not all(key in item for key in ['keyword', 'pregunta', 'respuesta']):
                    logger.warning(f"Item {i+1} no tiene todos los campos requeridos, saltando")
                    items_fallidos += 1
                    continue
                
                # Preparar texto para el embedding
                texto_completo = f"{item['pregunta']} {item['respuesta']}"
                
                # Generar embedding
                vector = generar_embedding(texto_completo)
                
                # Generar ID único
                point_id = str(uuid.uuid4())
                
                # Insertar en Qdrant
                client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points=[
                        qdrant_models.PointStruct(
                            id=point_id,
                            vector=vector,
                            payload={
                                "keyword": item["keyword"],
                                "pregunta": item["pregunta"],
                                "respuesta": item["respuesta"]
                            }
                        )
                    ]
                )
                
                logger.info(f"Item {i+1} insertado con ID: {point_id}")
                items_procesados += 1
                
                # Pausa breve para no sobrecargar la API de OpenAI
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error al procesar item {i+1}: {str(e)}")
                items_fallidos += 1
        
        # Resumen final
        logger.info("=== Resumen de la carga ===")
        logger.info(f"Total de items: {len(dataset)}")
        logger.info(f"Items procesados correctamente: {items_procesados}")
        logger.info(f"Items fallidos: {items_fallidos}")
        
    except Exception as e:
        logger.error(f"Error al cargar el dataset: {str(e)}")

if __name__ == "__main__":
    # Obtener la ruta del archivo desde los argumentos o usar un valor por defecto
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = "dataset.json"
    
    logger.info(f"Iniciando carga del dataset desde: {dataset_path}")
    cargar_dataset(dataset_path)
    logger.info("Proceso finalizado")