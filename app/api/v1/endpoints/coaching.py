from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.coaching import (
    GenerateCodeRequest, InviteCodeResponse,
    JoinByCodeRequest, SearchPlayerRequest, PlayerSearchResult,
    PlayerListItem, PlayerDashboard, CoachAlert, MyCoachResponse,
)
from app.services.coaching_service import CoachingService

router = APIRouter()


def get_current_coach(current_user: User = Depends(get_current_user)) -> User:
    """Dependencia: verifica que el usuario sea entrenador o especialista."""
    if current_user.role not in ["entrenador", "especialista", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta función es solo para entrenadores"
        )
    return current_user


# ========== ENDPOINTS DEL ENTRENADOR ==========

@router.post("/generate-code", response_model=InviteCodeResponse, status_code=201)
def generar_codigo(
    data: GenerateCodeRequest,
    db: Session = Depends(get_db),
    coach: User = Depends(get_current_coach),
):
    """Genera un código de invitación para compartir por WhatsApp."""
    return CoachingService.generar_codigo_invitacion(
        db, coach, data.especialidad, data.max_usos
    )


@router.post("/search-players", response_model=List[PlayerSearchResult])
def buscar_jugadores(
    data: SearchPlayerRequest,
    db: Session = Depends(get_db),
    coach: User = Depends(get_current_coach),
):
    """Busca jugadores por email o nombre."""
    return CoachingService.buscar_jugadores(db, data.query)


@router.get("/players", response_model=List[PlayerListItem])
def listar_mis_jugadores(
    db: Session = Depends(get_db),
    coach: User = Depends(get_current_coach),
):
    """Lista todos los jugadores vinculados al entrenador."""
    return CoachingService.listar_jugadores(db, coach)


@router.get("/players/{player_id}/dashboard", response_model=PlayerDashboard)
def dashboard_de_jugador(
    player_id: int,
    db: Session = Depends(get_db),
    coach: User = Depends(get_current_coach),
):
    """Dashboard completo de un jugador (puntos, ACWR, molestias, riesgo)."""
    return CoachingService.dashboard_jugador(db, coach, player_id)


@router.get("/alerts", response_model=List[CoachAlert])
def alertas_de_jugadores(
    db: Session = Depends(get_db),
    coach: User = Depends(get_current_coach),
):
    """Lista jugadores en riesgo alto o crítico."""
    return CoachingService.obtener_alertas(db, coach)


# ========== ENDPOINTS DEL JUGADOR ==========

@router.post("/join-by-code")
def unirse_con_codigo(
    data: JoinByCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """El jugador ingresa un código para vincularse con un entrenador."""
    return CoachingService.unirse_por_codigo(db, current_user, data.codigo)


@router.get("/my-coaches", response_model=List[MyCoachResponse])
def mis_entrenadores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """El jugador ve quiénes son sus entrenadores."""
    return CoachingService.mi_entrenador(db, current_user)