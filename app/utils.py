"""
Utilidades para el sistema RAG.
Contiene funciones para generar embeddings, interactuar con OpenAI y Qdrant,
y funciones para manejar templates de prompts.
"""

import time
import uuid
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Union
import openai
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from loguru import logger
from jinja2 import Template

from config import settings

# Configuración de OpenAI
openai.api_key = settings.OPENAI_API_KEY

def setup_qdrant_collection() -> QdrantClient:
    """
    Configura y devuelve un cliente Qdrant, asegurando que la colección exista.
    
    Returns:
        QdrantClient: Cliente Qdrant configurado
    """
    try:
        # Inicializar cliente Qdrant
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        
        # Verificar si la colección existe, y crearla si no
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
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
            logger.info(f"Usando colección existente: {settings.QDRANT_COLLECTION_NAME}")
            
        return client
    
    except Exception as e:
        logger.error(f"Error al configurar Qdrant: {str(e)}")
        raise

def generar_embedding(texto: str) -> List[float]:
    """
    Genera un embedding para el texto dado utilizando la API de OpenAI.
    
    Args:
        texto (str): Texto para generar el embedding
        
    Returns:
        List[float]: Vector de embedding generado
        
    Raises:
        Exception: Si hay un error al generar el embedding
    """
    try:
        inicio = time.time()
        
        # Llamar a OpenAI para generar el embedding
        response = openai.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=texto
        )
        
        # Extraer y retornar el vector
        vector = response.data[0].embedding
        
        fin = time.time()
        logger.info(f"Embedding generado en {(fin - inicio)*1000:.2f}ms")
        return vector
    
    except Exception as e:
        logger.error(f"Error al generar embedding: {str(e)}")
        raise

def insertar_qa_en_qdrant(
    client: QdrantClient, 
    qa_item: Dict[str, Any], 
    vector: List[float]
) -> str:
    """
    Inserta un nuevo elemento Q&A en Qdrant.
    
    Args:
        client (QdrantClient): Cliente Qdrant
        qa_item (Dict[str, Any]): Datos del Q&A
        vector (List[float]): Vector de embedding
        
    Returns:
        str: ID del punto insertado
        
    Raises:
        Exception: Si hay un error al insertar en Qdrant
    """
    try:
        # Generar ID único
        point_id = str(uuid.uuid4())
        
        # Insertar en Qdrant
        client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=qa_item
                )
            ]
        )
        
        logger.info(f"Q&A insertado en Qdrant con ID: {point_id}")
        return point_id
    
    except Exception as e:
        logger.error(f"Error al insertar en Qdrant: {str(e)}")
        raise

def buscar_similares(
    client: QdrantClient, 
    vector: List[float], 
    limit: int = settings.QDRANT_SEARCH_LIMIT
) -> List[Dict[str, Any]]:
    """
    Busca elementos Q&A similares en Qdrant.
    
    Args:
        client (QdrantClient): Cliente Qdrant
        vector (List[float]): Vector de embedding para buscar
        limit (int): Número máximo de resultados
        
    Returns:
        List[Dict[str, Any]]: Lista de resultados con sus metadatos y scores
        
    Raises:
        Exception: Si hay un error al buscar en Qdrant
    """
    try:
        inicio = time.time()
        
        # Realizar búsqueda por similitud
        results = client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=vector,
            limit=limit,
            score_threshold=settings.QDRANT_SEARCH_SCORE_THRESHOLD
        )
        
        # Procesar resultados
        processed_results = []
        for res in results:
            processed_results.append({
                "id": res.id,
                "score": res.score,
                **res.payload
            })
        
        fin = time.time()
        logger.info(f"Búsqueda en Qdrant completada en {(fin - inicio)*1000:.2f}ms. Encontrados {len(processed_results)} resultados")
        return processed_results
    
    except Exception as e:
        logger.error(f"Error al buscar en Qdrant: {str(e)}")
        raise

def cargar_template(nombre_template: str) -> Template:
    """
    Carga un template de prompt desde un archivo.
    
    Args:
        nombre_template (str): Nombre del archivo de template (sin ruta)
        
    Returns:
        Template: Objeto Template de Jinja2
        
    Raises:
        FileNotFoundError: Si el archivo de template no existe
    """
    try:
        # Construir la ruta al template
        prompt_path = os.path.join('static', 'prompts', nombre_template)
        
        # Verificar que el archivo existe
        if not os.path.exists(prompt_path):
            logger.error(f"Template no encontrado: {prompt_path}")
            raise FileNotFoundError(f"Template no encontrado: {prompt_path}")
        
        # Leer el contenido del template
        with open(prompt_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        
        # Crear y retornar el objeto Template
        template = Template(template_content)
        logger.info(f"Template cargado: {nombre_template}")
        return template
    
    except Exception as e:
        logger.error(f"Error al cargar template {nombre_template}: {str(e)}")
        raise

def generar_respuesta_llm(
    consulta: str, 
    resultados: List[Dict[str, Any]],
    contexto_previo: Optional[str] = None,
    contexto_actual: Optional[str] = None
) -> Optional[str]:
    """
    Genera una respuesta usando el LLM de OpenAI basada en los resultados encontrados.
    
    Args:
        consulta (str): Consulta original
        resultados (List[Dict[str, Any]]): Resultados relevantes encontrados
        contexto_previo (Optional[str]): Contexto de conversaciones previas
        contexto_actual (Optional[str]): Contexto de la conversación actual
        
    Returns:
        Optional[str]: Respuesta generada por el LLM o None si no hay información suficiente
        
    Raises:
        Exception: Si hay un error al generar la respuesta
    """
    try:
        inicio = time.time()
        
        # Si no hay resultados, indicarlo
        if not resultados:
            logger.info("No se encontraron resultados relevantes para generar respuesta")
        
        # Preparar el contexto con los resultados
        documentos_contexto = []
        for i, res in enumerate(resultados):
            documentos_contexto.append({
                "numero": i+1,
                "pregunta": res['pregunta'],
                "respuesta": res['respuesta']
            })
        
        # Cargar el template para generar respuestas
        template = cargar_template('generate_response.txt')

        # Renderizar el template con los datos
        prompt = template.render(
                consulta=consulta,
                documentos=documentos_contexto,
                contexto_previo=contexto_previo,
                contexto_actual=contexto_actual
            )
        
        # Cargar template del system prompt
        system_template = cargar_template('system_prompt.txt')
        system_prompt = system_template.render(
                instrucciones_adicionales=None
            )

        # Llamar a OpenAI para generar respuesta con clasificación
        response = openai.chat.completions.create(
            model=settings.OPENAI_COMPLETION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"}
        )                
        
        # Parsear la respuesta JSON
        try:
            respuesta_json = json.loads(response.choices[0].message.content.strip())
            puede_responder = respuesta_json.get("puede_responder", False)
            respuesta_texto = respuesta_json.get("respuesta", "")
            
            # Devolver la respuesta del LLM tanto si puede responder como si no
            fin = time.time()
            logger.info(f"Respuesta generada por LLM en {(fin - inicio)*1000:.2f}ms")
            
            if not puede_responder:
                logger.info("El LLM indica que no hay información suficiente para responder")
                # Devolver el mensaje en lugar de None
                return respuesta_texto
                
            return respuesta_texto
            
        except json.JSONDecodeError:
            logger.warning("No se pudo parsear la respuesta como JSON, usando la respuesta completa")
            respuesta = response.choices[0].message.content.strip()
            fin = time.time()
            logger.info(f"Respuesta generada por LLM en {(fin - inicio)*1000:.2f}ms")
            return respuesta
    
    except Exception as e:
        logger.error(f"Error al generar respuesta con LLM: {str(e)}")
        raise