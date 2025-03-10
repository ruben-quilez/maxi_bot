"""
Endpoints de la API FastAPI para el sistema RAG.
Define las rutas y la lógica de los endpoints.
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from models import QAItem, QueryInput, QueryResponse, AddQAResponse
from utils import (
    generar_embedding, 
    insertar_qa_en_qdrant, 
    buscar_similares, 
    generar_respuesta_llm,
    setup_qdrant_collection
)
from config import settings

# Router para los endpoints de la API
router = APIRouter(prefix=settings.API_PREFIX)

# Dependencia para obtener el cliente Qdrant
def get_qdrant_client():
    """Dependencia para obtener un cliente Qdrant configurado."""
    return setup_qdrant_collection()

@router.post("/query", response_model=QueryResponse, tags=["consultas"])
async def consultar(
    query_input: QueryInput,
    qdrant_client = Depends(get_qdrant_client)
):
    try:
        inicio = time.time()
        logger.info(f"Recibida consulta: {query_input.consulta}")
        
        # Generar embedding para la consulta
        vector = generar_embedding(query_input.consulta)
        
        # Buscar Q&As similares en Qdrant
        resultados = buscar_similares(
            client=qdrant_client,
            vector=vector,
            limit=settings.QDRANT_SEARCH_LIMIT
        )
        
        # Generar respuesta con LLM solo si hay resultados
        respuesta_generada = None
        # if resultados:
        respuesta_generada = generar_respuesta_llm(
                consulta=query_input.consulta,
                resultados=resultados,
                contexto_previo=query_input.contexto_previo,
                contexto_actual=query_input.contexto_actual
            )
        
        fin = time.time()
        tiempo_total = (fin - inicio) * 1000  # Convertir a milisegundos
        
        # Construir respuesta
        response = QueryResponse(
            resultados=resultados,
            respuesta_generada=respuesta_generada,
            tiempo_respuesta=tiempo_total
        )
        
        logger.info(f"Consulta procesada en {tiempo_total:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error en endpoint /query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/add", response_model=AddQAResponse, tags=["administración"])
async def añadir_qa(
    qa_item: QAItem,
    qdrant_client = Depends(get_qdrant_client)
):
    """
    Endpoint para añadir un nuevo Q&A al sistema.
    
    Recibe un objeto Q&A, genera su embedding y lo almacena en Qdrant.
    
    Args:
        qa_item (QAItem): Nuevo ítem de pregunta y respuesta
        
    Returns:
        AddQAResponse: Confirmación de la operación con detalles
    """
    try:
        logger.info(f"Recibida solicitud para añadir Q&A con keyword: {qa_item.keyword}")
        
        # Preparar texto para embedding (concatenando pregunta y respuesta)
        texto_completo = f"{qa_item.pregunta} {qa_item.respuesta}"
        
        # Generar embedding
        vector = generar_embedding(texto_completo)
        
        # Preparar payload para Qdrant
        qa_payload = {
            "keyword": qa_item.keyword,
            "pregunta": qa_item.pregunta,
            "respuesta": qa_item.respuesta
        }
        
        # Insertar en Qdrant
        point_id = insertar_qa_en_qdrant(
            client=qdrant_client,
            qa_item=qa_payload,
            vector=vector
        )
        
        # Construir respuesta
        response = AddQAResponse(
            id=point_id,
            status="success",
            mensaje="Q&A añadido correctamente",
            item={
                "id": point_id,
                **qa_payload
            }
        )
        
        logger.info(f"Q&A añadido con ID: {point_id}")
        return response
    
    except Exception as e:
        logger.error(f"Error en endpoint /add: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al añadir Q&A: {str(e)}")