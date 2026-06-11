from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


TIPOS_COMIDA = ["desayuno", "almuerzo", "cena", "snack"]


class NutritionNeedsResponse(BaseModel):
    """Necesidades calóricas calculadas."""
    tmb: float  # Tasa Metabólica Basal
    get: float  # Gasto Energético Total
    objetivo_calorico: float  # ajustado según objetivo del usuario
    objetivo_usuario: str
    explicacion: str
    formula: str
    agua_recomendada_vasos: int


class RegisterMealRequest(BaseModel):
    tipo_comida: str
    descripcion: str = Field(..., min_length=2, max_length=300)
    calorias_estimadas: Optional[int] = Field(None, ge=0, le=5000)
    foto_base64: Optional[str] = None


class MealResponse(BaseModel):
    id: int
    fecha: date
    tipo_comida: str
    descripcion: str
    calorias_estimadas: Optional[int]
    validado: bool
    metodo_validacion: str
    detalle_validacion: Optional[str]
    puntos_otorgados: int
    tiene_foto: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MealCreatedResponse(BaseModel):
    meal: MealResponse
    puntos_ganados: int
    total_points: int
    mensaje_validacion: str


class RegisterWaterRequest(BaseModel):
    vasos: int = Field(..., ge=1, le=20)


class NutritionSummaryResponse(BaseModel):
    fecha: date
    objetivo_calorico: float
    calorias_consumidas: int
    calorias_restantes: float
    porcentaje_cumplido: float
    comidas_registradas: int
    vasos_agua: int
    agua_objetivo: int
    agua_cumplida: bool
    mensaje: str


class SimpleResponse(BaseModel):
    message: str