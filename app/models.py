"""
Módulo para definir los modelos de datos utilizando Pydantic.
Estos modelos definen las estructuras de datos para la API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4
from datetime import datetime

class QAItem(BaseModel):
    """Modelo para los items de preguntas y respuestas."""
    keyword: str = Field(..., description="Palabra clave o categoría para el Q&A")
    pregunta: str = Field(..., description="Pregunta original")
    respuesta: str = Field(..., description="Respuesta asociada a la pregunta")
    
    class Config:
        schema_extra = {
            "example": {
                "keyword": "planes",
                "pregunta": "¿Qué diferencia hay entre el Pack Completo y el Básico?",
                "respuesta": "El Pack Completo incluye todas las funcionalidades premium, mientras que el Pack Básico ofrece solo funciones esenciales a un precio más accesible."
            }
        }

class QueryInput(BaseModel):
    """Modelo para las consultas de búsqueda."""
    consulta: str = Field(..., description="Pregunta o consulta del usuario")
    contexto_previo: Optional[str] = Field(None, description="Contexto de conversaciones previas")
    contexto_actual: Optional[str] = Field(None, description="Contexto de la conversación actual")
    
    class Config:
        schema_extra = {
            "example": {
                "consulta": "¿Qué diferencia hay entre el Pack Completo y el Básico?",
                "contexto_previo": "Anteriormente hablamos sobre las opciones de suscripción.",
                "contexto_actual": "Estoy evaluando qué plan contratar."
            }
        }

class QAItemResponse(BaseModel):
    """Modelo para las respuestas retornadas tras buscar o insertar Q&A."""
    id: str = Field(..., description="Identificador único del Q&A")
    keyword: str = Field(..., description="Palabra clave o categoría")
    pregunta: str = Field(..., description="Pregunta original")
    respuesta: str = Field(..., description="Respuesta asociada")
    score: Optional[float] = Field(None, description="Puntuación de similitud (solo en búsquedas)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "keyword": "planes",
                "pregunta": "¿Qué diferencia hay entre el Pack Completo y el Básico?",
                "respuesta": "El Pack Completo incluye todas las funcionalidades premium, mientras que el Pack Básico ofrece solo funciones esenciales a un precio más accesible.",
                "score": 0.92
            }
        }

class QueryResponse(BaseModel):
    """Modelo para las respuestas a consultas."""
    resultados: List[QAItemResponse] = Field(..., description="Lista de resultados relevantes")
    respuesta_generada: Optional[str] = Field(None, description="Respuesta generada por el LLM (si está habilitado)")
    tiempo_respuesta: float = Field(..., description="Tiempo de respuesta en milisegundos")
    
    class Config:
        schema_extra = {
            "example": {
                "resultados": [
                    {
                        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        "keyword": "planes",
                        "pregunta": "¿Qué diferencia hay entre el Pack Completo y el Básico?",
                        "respuesta": "El Pack Completo incluye todas las funcionalidades premium, mientras que el Pack Básico ofrece solo funciones esenciales a un precio más accesible.",
                        "score": 0.92
                    }
                ],
                "respuesta_generada": "La principal diferencia entre ambos packs es que el Completo ofrece todas las funcionalidades premium, mientras que el Básico solo incluye las esenciales a un precio más económico.",
                "tiempo_respuesta": 120.45
            }
        }

class AddQAResponse(BaseModel):
    """Modelo para la respuesta al añadir un nuevo Q&A."""
    id: str = Field(..., description="Identificador único asignado al Q&A")
    status: str = Field("success", description="Estado de la operación")
    mensaje: str = Field("Q&A añadido correctamente", description="Mensaje descriptivo")
    item: QAItemResponse = Field(..., description="Item añadido")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "status": "success",
                "mensaje": "Q&A añadido correctamente",
                "item": {
                    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                    "keyword": "planes",
                    "pregunta": "¿Qué diferencia hay entre el Pack Completo y el Básico?",
                    "respuesta": "El Pack Completo incluye todas las funcionalidades premium, mientras que el Pack Básico ofrece solo funciones esenciales a un precio más accesible."
                }
            }
        }

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error."""
    status: str = Field("error", description="Estado de la operación")
    codigo: int = Field(..., description="Código de error HTTP")
    mensaje: str = Field(..., description="Mensaje de error descriptivo")
    detalle: Optional[str] = Field(None, description="Detalles adicionales del error")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "codigo": 400,
                "mensaje": "Error en el formato de la consulta",
                "detalle": "El campo 'consulta' es obligatorio"
            }
        }