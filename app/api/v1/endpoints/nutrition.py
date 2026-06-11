from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.nutrition import (
    NutritionNeedsResponse, RegisterMealRequest, MealResponse,
    MealCreatedResponse, RegisterWaterRequest, NutritionSummaryResponse,
    SimpleResponse,
)
from app.services.nutrition_service import NutritionService

router = APIRouter()


@router.get("/needs", response_model=NutritionNeedsResponse)
def calcular_necesidades(
    current_user: User = Depends(get_current_user),
):
    """Calcula TMB y necesidades calóricas (Mifflin-St Jeor, 1990)."""
    return NutritionService.calcular_necesidades(current_user)


@router.post("/meals", response_model=MealCreatedResponse, status_code=201)
def registrar_comida(
    data: RegisterMealRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registra una comida. Si incluye foto, se valida y se guarda como evidencia."""
    return NutritionService.registrar_comida(db, current_user, data)


@router.get("/meals/today", response_model=List[MealResponse])
def comidas_de_hoy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista las comidas registradas hoy."""
    return NutritionService.comidas_de_hoy(db, current_user)


@router.delete("/meals/{meal_id}", response_model=SimpleResponse)
def borrar_comida(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Elimina una comida y ajusta los puntos."""
    return NutritionService.borrar_comida(db, current_user, meal_id)


@router.post("/water", response_model=SimpleResponse)
def registrar_agua(
    data: RegisterWaterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registra vasos de agua consumidos (cada vaso = 250ml)."""
    return NutritionService.registrar_agua(db, current_user, data.vasos)


@router.get("/summary", response_model=NutritionSummaryResponse)
def resumen_del_dia(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resumen nutricional del día: consumido vs objetivo, agua."""
    return NutritionService.resumen_dia(db, current_user)