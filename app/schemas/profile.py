from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    weight_kg: Optional[float] = Field(None, ge=20, le=300)
    height_cm: Optional[float] = Field(None, ge=100, le=250)
    objetivo: Optional[str] = None
    dias_semana: Optional[int] = Field(None, ge=1, le=7)
    duracion_sesion: Optional[int] = None
    nivel_actividad: Optional[str] = None


class UpdatePhotoRequest(BaseModel):
    foto_base64: str


class ProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    genero: Optional[str]
    birth_date: Optional[str]
    weight_kg: Optional[float]
    height_cm: Optional[float]
    avatar_url: Optional[str]
    deporte: Optional[str]
    posicion: Optional[str]
    objetivo: Optional[str]
    nivel_actividad: Optional[str]
    dias_semana: Optional[int]
    duracion_sesion: Optional[int]
    onboarding_completed: bool
    total_points: int
    level: int
    current_streak: int
    longest_streak: int
    total_exercises: int

    model_config = {"from_attributes": True}


class FullDashboardResponse(BaseModel):
    """Dashboard personal completo del jugador."""
    # Identidad
    full_name: str
    nivel: int
    total_points: int

    # Progreso de entrenamiento
    current_streak: int
    longest_streak: int
    total_exercises: int
    puntos_para_siguiente_nivel: int

    # Carga (ACWR)
    acwr: float
    zona_acwr: str
    color_acwr: str

    # Salud / molestias
    molestias_activas: int
    nivel_riesgo: str

    # Nutrición hoy
    calorias_consumidas_hoy: int
    objetivo_calorico: float
    vasos_agua_hoy: int

    # Mensaje motivacional global
    mensaje: str