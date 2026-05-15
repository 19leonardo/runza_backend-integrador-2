from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.onboarding import (
    IMCRequest, IMCResponse,
    OnboardingRequest, OnboardingResponse
)
from app.services.onboarding_service import OnboardingService
from app.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/imc", response_model=IMCResponse)
def calcular_imc(data: IMCRequest):
    """Calcula IMC sin guardar. Usado en el Paso 1 del onboarding."""
    return OnboardingService.calcular_imc(data.weight_kg, data.height_cm)


@router.post("/complete", response_model=OnboardingResponse)
def completar_onboarding(
    data: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Guarda todo el perfil del onboarding (los 5 pasos)."""
    return OnboardingService.completar_onboarding(db, current_user, data)


@router.get("/status")
def estado_onboarding(current_user: User = Depends(get_current_user)):
    """Verifica si el usuario ya completó el onboarding."""
    return {
        "onboarding_completed": current_user.onboarding_completed,
        "user_id": current_user.id,
        "email": current_user.email,
    }