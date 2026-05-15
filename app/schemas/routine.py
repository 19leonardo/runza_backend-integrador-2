from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ExerciseInRoutine(BaseModel):
    """Ejercicio dentro de una rutina."""
    id: int
    exercise_id: int
    orden: int
    is_completed: bool
    nombre: str
    descripcion: Optional[str]
    category: str
    nivel_dificultad: str
    duracion_segundos: int
    sets: int
    repeticiones: int
    descanso_segundos: int
    points_value: int

    model_config = {"from_attributes": True}


class RoutineResponse(BaseModel):
    """Rutina completa con sus ejercicios."""
    id: int
    user_id: int
    fecha: date
    nombre: str
    descripcion: Optional[str]
    duracion_estimada_minutos: int
    total_puntos_disponibles: int
    is_completed: bool
    created_at: datetime
    exercises: List[ExerciseInRoutine]

    model_config = {"from_attributes": True}


class ExerciseCatalogResponse(BaseModel):
    """Ejercicio del catálogo (sin estado de completado)."""
    id: int
    nombre: str
    descripcion: Optional[str]
    category: str
    deporte: Optional[str]
    objetivo: Optional[str]
    nivel_dificultad: str
    duracion_segundos: int
    sets: int
    repeticiones: int
    descanso_segundos: int
    points_value: int
    requiere_equipamiento: bool
    equipamiento_necesario: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class CompleteExerciseRequest(BaseModel):
    """Marcar un ejercicio como completado."""
    duration_seconds: Optional[int] = None


class CompleteExerciseResponse(BaseModel):
    """Respuesta al completar un ejercicio."""
    message: str
    points_earned: int
    total_points: int
    level: int
    leveled_up: bool
    routine_progress_percentage: float