from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.training_load import (
    RegisterLoadRequest,
    SessionLoadResponse,
    ACWRResponse,
    LoadHistoryResponse,
    WeeklySummaryResponse,
)
from app.services.load_service import LoadService

router = APIRouter()


@router.post("/register", response_model=SessionLoadResponse, status_code=201)
def registrar_rpe(
    data: RegisterLoadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Registra el RPE después de una sesión.
    Foster et al. (2001): Carga interna = RPE × duración.
    """
    return LoadService.registrar_carga(db, current_user, data)


@router.get("/acwr", response_model=ACWRResponse)
def obtener_acwr(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calcula el Acute:Chronic Workload Ratio actual del usuario.
    Gabbett (2020): zona óptima entre 0.8 y 1.3.
    """
    return LoadService.calcular_acwr(db, current_user)


@router.get("/history", response_model=LoadHistoryResponse)
def historial_de_carga(
    dias: int = Query(30, ge=7, le=90, description="Cantidad de días a consultar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Historial de carga diaria para gráficas (RF-011)."""
    return LoadService.obtener_historial(db, current_user, dias)


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
def resumen_semanal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resumen de la semana actual."""
    return LoadService.resumen_semanal(db, current_user)