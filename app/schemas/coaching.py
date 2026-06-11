from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime


ESPECIALIDADES = [
    "entrenador", "preparador_fisico", "nutricionista",
    "fisioterapeuta", "medico"
]


class GenerateCodeRequest(BaseModel):
    especialidad: str = "entrenador"
    max_usos: int = Field(default=100, gt=0, le=1000)


class InviteCodeResponse(BaseModel):
    id: int
    codigo: str
    especialidad: str
    usos: int
    max_usos: int
    link_compartible: str
    mensaje_whatsapp: str

    model_config = {"from_attributes": True}


class JoinByCodeRequest(BaseModel):
    codigo: str


class SearchPlayerRequest(BaseModel):
    query: str  # email o nombre


class PlayerSearchResult(BaseModel):
    id: int
    full_name: str
    email: str
    deporte: Optional[str]
    posicion: Optional[str]

    model_config = {"from_attributes": True}


class PlayerListItem(BaseModel):
    player_id: int
    full_name: str
    email: str
    deporte: Optional[str]
    posicion: Optional[str]
    especialidad: str
    estado: str
    total_points: int
    level: int
    current_streak: int
    fecha_vinculacion: Optional[date]


class PlayerDashboard(BaseModel):
    """Dashboard completo de un jugador (visto por su entrenador)."""
    player_id: int
    full_name: str
    email: str
    deporte: Optional[str]
    posicion: Optional[str]
    objetivo: Optional[str]

    # Gamificación
    total_points: int
    level: int
    current_streak: int
    longest_streak: int
    total_exercises: int

    # Carga (ACWR)
    acwr_actual: float
    zona_acwr: str
    color_acwr: str

    # Molestias
    molestias_activas: int
    molestia_mas_intensa: Optional[float]

    # Riesgo combinado
    nivel_riesgo: str
    color_riesgo: str
    mensaje_riesgo: str


class CoachAlert(BaseModel):
    """Alerta de un jugador en riesgo."""
    player_id: int
    full_name: str
    tipo_alerta: str  # "sobrecarga" | "dolor_intenso" | "riesgo_combinado"
    nivel: str
    mensaje: str
    detalle: str


class MyCoachResponse(BaseModel):
    coach_id: int
    coach_name: str
    coach_email: str
    especialidad: str
    estado: str
    fecha_vinculacion: Optional[date]