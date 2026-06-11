from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime


# Valores permitidos (validación)
ZONAS_VALIDAS = [
    "rodilla", "tobillo", "isquiotibiales", "cuadriceps", "espalda_baja",
    "hombro", "cadera", "gemelo", "aductor", "cuello", "muñeca", "otro"
]
LADOS_VALIDOS = ["izquierdo", "derecho", "ambos", "no_aplica"]
TIPOS_VALIDOS = ["muscular", "articular", "tendinosa", "osea", "otro"]
MOMENTOS_VALIDOS = ["reposo", "al_entrenar", "despues_entrenar", "todo_el_tiempo"]


class ReportPainRequest(BaseModel):
    """Reportar una molestia."""
    zona_cuerpo: str
    lado: str = "no_aplica"
    intensidad: float = Field(..., ge=0, le=10, description="Escala EVA 0-10")
    tipo_molestia: str
    momento_dolor: str
    notas: Optional[str] = None

    @field_validator("zona_cuerpo")
    @classmethod
    def zona_valida(cls, v):
        if v.lower() not in ZONAS_VALIDAS:
            raise ValueError(f"Zona debe ser una de: {ZONAS_VALIDAS}")
        return v.lower()

    @field_validator("lado")
    @classmethod
    def lado_valido(cls, v):
        if v.lower() not in LADOS_VALIDOS:
            raise ValueError(f"Lado debe ser uno de: {LADOS_VALIDOS}")
        return v.lower()

    @field_validator("tipo_molestia")
    @classmethod
    def tipo_valido(cls, v):
        if v.lower() not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo debe ser uno de: {TIPOS_VALIDOS}")
        return v.lower()

    @field_validator("momento_dolor")
    @classmethod
    def momento_valido(cls, v):
        if v.lower() not in MOMENTOS_VALIDOS:
            raise ValueError(f"Momento debe ser uno de: {MOMENTOS_VALIDOS}")
        return v.lower()


class PainReportResponse(BaseModel):
    id: int
    user_id: int
    fecha: date
    zona_cuerpo: str
    lado: str
    intensidad: float
    tipo_molestia: str
    momento_dolor: str
    notas: Optional[str]
    requiere_atencion: bool
    resuelto: bool
    fecha_resolucion: Optional[date]
    created_at: datetime

    model_config = {"from_attributes": True}


class PainReportCreatedResponse(BaseModel):
    """Respuesta al crear un reporte, con feedback."""
    reporte: PainReportResponse
    requiere_atencion: bool
    nivel_alerta: str  # "normal" | "precaucion" | "alerta" | "urgente"
    mensaje: str
    recomendacion: str


class RiskAssessmentResponse(BaseModel):
    """Evaluación de riesgo combinada: dolor + carga (ACWR)."""
    tiene_molestias_activas: bool
    cantidad_molestias_activas: int
    molestia_mas_intensa: Optional[float]
    acwr_actual: float
    zona_acwr: str
    nivel_riesgo_combinado: str  # "bajo" | "moderado" | "alto" | "critico"
    color: str
    mensaje: str
    recomendaciones: List[str]
    referencia: str