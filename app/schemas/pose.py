from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PoseAnalysisRequest(BaseModel):
    """Petición para analizar una imagen."""
    image_base64: str = Field(
        ...,
        description="Imagen codificada en base64 (con o sin prefijo data:image)"
    )
    ejercicio: str = Field(
        default="sentadilla",
        description="Nombre del ejercicio a analizar"
    )


class ErrorDetectado(BaseModel):
    tipo: str
    severidad: str
    mensaje: str
    correccion: str
    consecuencia: str
    referencia: str


class SugerenciaMenor(BaseModel):
    tipo: str
    mensaje: str


class PoseAnalysisResponse(BaseModel):
    """Respuesta del análisis biomecánico."""
    exito: bool
    ejercicio: str = ""
    fase: str = ""
    angulos: Dict[str, float] = {}
    errores: List[ErrorDetectado] = []
    sugerencias: List[SugerenciaMenor] = []
    puntos_correctos: List[str] = []
    tecnica_correcta: bool = False
    puntuacion: int = 0
    mensaje: str = ""
    error: Optional[str] = None  # presente solo si exito=False


class RepValidationRequest(BaseModel):
    """Validar si una serie de análisis cuenta como rep válida."""
    routine_exercise_id: int
    analisis_frames: List[Dict[str, Any]] = Field(
        ...,
        description="Lista de análisis de frames de la serie"
    )


class RepValidationResponse(BaseModel):
    """Respuesta a validación de rep."""
    rep_valida: bool
    reps_correctas: int
    reps_con_errores: int
    porcentaje_precision: float
    puede_completar_ejercicio: bool
    mensaje: str

class Landmark(BaseModel):
    """Punto del cuerpo con coordenadas normalizadas (0 a 1)."""
    id: int            # 0 a 32 (33 puntos de MediaPipe)
    x: float           # 0 a 1 (izquierda → derecha)
    y: float           # 0 a 1 (arriba → abajo)
    visibility: float  # 0 a 1 (qué tan visible está el punto)
    estado: str        # "ok" | "atencion" | "error"


class Conexion(BaseModel):
    """Línea entre dos landmarks (segmento del esqueleto)."""
    desde: int   # id del landmark origen
    hasta: int   # id del landmark destino
    estado: str  # "ok" | "atencion" | "error"


class EncuadreInfo(BaseModel):
    """Información sobre la posición del usuario frente a la cámara."""
    valido: bool                         # si está listo para entrenar
    cuerpo_completo: bool                # se ve de pies a cabeza
    vista_lateral: bool                  # está de perfil (recomendado)
    pies_visibles: bool
    ajuste_recomendado: Optional[str]    # "alejate" | "acercate" | "ponte_de_lado" | "centrate" | null
    mensaje_encuadre: str                # mensaje para mostrar al usuario