from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime


class RegisterLoadRequest(BaseModel):
    """Registrar RPE después de una sesión de entrenamiento."""
    rpe: float = Field(..., ge=0, le=10, description="Escala 0-10")
    duracion_minutos: int = Field(..., gt=0, le=300)
    routine_id: Optional[int] = None
    notas: Optional[str] = None

    @field_validator("rpe")
    @classmethod
    def rpe_valido(cls, v):
        if v < 0 or v > 10:
            raise ValueError("RPE debe estar entre 0 y 10")
        return round(v, 1)


class SessionLoadResponse(BaseModel):
    id: int
    user_id: int
    fecha: date
    rpe: float
    duracion_minutos: int
    carga_interna: float
    notas: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ACWRResponse(BaseModel):
    """Análisis de Acute:Chronic Workload Ratio."""
    carga_aguda: float  # promedio últimos 7 días
    carga_cronica: float  # promedio últimos 28 días
    acwr: float
    zona: str  # "sub_entrenamiento" | "optima" | "alta" | "sobrecarga"
    color: str  # "azul" | "verde" | "amarillo" | "rojo"
    recomendacion: str
    referencia: str
    dias_con_datos_agudos: int
    dias_con_datos_cronicos: int
    confianza: str  # "alta" | "media" | "baja"


class DailyLoadPoint(BaseModel):
    """Un punto de carga diaria para gráficas."""
    fecha: date
    carga_total: float
    rpe_promedio: float
    sesiones: int


class LoadHistoryResponse(BaseModel):
    """Historial de carga para visualización."""
    dias: int
    puntos: List[DailyLoadPoint]
    carga_total_periodo: float
    rpe_promedio_periodo: float


class WeeklySummaryResponse(BaseModel):
    """Resumen semanal del usuario."""
    semana_inicio: date
    semana_fin: date
    sesiones_completadas: int
    carga_total: float
    duracion_total_minutos: int
    rpe_promedio: float
    dia_mas_intenso: Optional[str]
    acwr_actual: float
    zona: str
    mensaje: str