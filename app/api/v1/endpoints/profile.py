from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.profile import (
    UpdateProfileRequest, UpdatePhotoRequest,
    ProfileResponse, FullDashboardResponse,
)
from app.services.profile_service import ProfileService

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
def ver_mi_perfil(
    current_user: User = Depends(get_current_user),
):
    """Ver mi perfil completo."""
    return ProfileService.obtener_perfil(current_user)


@router.patch("/me", response_model=ProfileResponse)
def actualizar_mi_perfil(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualizar datos del perfil."""
    return ProfileService.actualizar_perfil(db, current_user, data)


@router.post("/me/photo")
def actualizar_foto(
    data: UpdatePhotoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Subir/actualizar foto de perfil."""
    return ProfileService.actualizar_foto(db, current_user, data.foto_base64)


@router.get("/dashboard", response_model=FullDashboardResponse)
def mi_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard personal completo: todas las métricas en un solo lugar."""
    return ProfileService.dashboard_completo(db, current_user)