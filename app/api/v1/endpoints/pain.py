from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.pain_report import (
    ReportPainRequest,
    PainReportResponse,
    PainReportCreatedResponse,
    RiskAssessmentResponse,
)
from app.services.pain_service import PainService

router = APIRouter()


@router.post("/report", response_model=PainReportCreatedResponse, status_code=201)
def reportar_molestia(
    data: ReportPainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reporta una molestia musculoesquelética.
    El sistema evalúa automáticamente si requiere atención profesional.
    """
    resultado = PainService.reportar_molestia(db, current_user, data)
    return resultado


@router.get("/active", response_model=List[PainReportResponse])
def molestias_activas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Molestias no resueltas de los últimos 7 días."""
    return PainService.obtener_molestias_activas(db, current_user)


@router.get("/history", response_model=List[PainReportResponse])
def historial_molestias(
    dias: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Historial de molestias reportadas."""
    return PainService.obtener_historial(db, current_user, dias)


@router.get("/risk-assessment", response_model=RiskAssessmentResponse)
def evaluacion_de_riesgo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluación de riesgo combinada: cruza molestias activas con ACWR.
    Innovación del sistema: prevención de lesiones basada en datos.
    """
    return PainService.evaluar_riesgo_combinado(db, current_user)


@router.patch("/{pain_id}/resolve", response_model=PainReportResponse)
def resolver_molestia(
    pain_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marca una molestia como resuelta."""
    return PainService.resolver_molestia(db, current_user, pain_id)