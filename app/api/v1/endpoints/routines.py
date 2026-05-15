from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List
from app.core.database import get_db
from app.schemas.routine import (
    RoutineResponse, ExerciseCatalogResponse,
    CompleteExerciseRequest, CompleteExerciseResponse
)
from app.services.routine_service import RoutineService
from app.services.gamification_service import GamificationService
from app.deps import get_current_user
from app.models.user import User
from app.models.exercise import Exercise, Routine, RoutineExercise, ExerciseCompletion

router = APIRouter()


@router.get("/today", response_model=RoutineResponse)
def obtener_rutina_de_hoy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la rutina del día, generándola automáticamente si no existe."""
    rutina = RoutineService.obtener_rutina_hoy(db, current_user)
    return RoutineService.formatear_rutina(rutina)


@router.post("/generate", response_model=RoutineResponse, status_code=201)
def generar_nueva_rutina(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fuerza la generación de la rutina del día."""
    rutina = RoutineService.generar_rutina_diaria(db, current_user)
    return RoutineService.formatear_rutina(rutina)


@router.get("/exercises", response_model=List[ExerciseCatalogResponse])
def listar_catalogo_ejercicios(
    category: Optional[str] = Query(None),
    deporte: Optional[str] = Query(None),
    objetivo: Optional[str] = Query(None),
    nivel_dificultad: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista el catálogo completo de ejercicios con filtros opcionales."""
    query = db.query(Exercise).filter(Exercise.is_active == True)
    if category:
        query = query.filter(Exercise.category == category)
    if deporte:
        query = query.filter(Exercise.deporte == deporte)
    if objetivo:
        query = query.filter(Exercise.objetivo == objetivo)
    if nivel_dificultad:
        query = query.filter(Exercise.nivel_dificultad == nivel_dificultad)
    return query.all()


@router.post(
    "/{routine_id}/exercises/{routine_exercise_id}/complete",
    response_model=CompleteExerciseResponse
)
def completar_ejercicio(
    routine_id: int,
    routine_exercise_id: int,
    data: CompleteExerciseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marca un ejercicio de la rutina como completado y otorga puntos.
    Sistema de gamificación basado en Bourdon et al. (2017).
    """
    # Validar rutina
    rutina = db.query(Routine).filter(
        Routine.id == routine_id,
        Routine.user_id == current_user.id
    ).first()
    if not rutina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rutina no encontrada"
        )

    # Validar ejercicio dentro de la rutina
    routine_exercise = db.query(RoutineExercise).filter(
        RoutineExercise.id == routine_exercise_id,
        RoutineExercise.routine_id == routine_id
    ).first()
    if not routine_exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejercicio no encontrado en esta rutina"
        )

    # Si ya está completado, error
    if routine_exercise.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este ejercicio ya fue completado"
        )

    # Marcar como completado
    routine_exercise.is_completed = True
    routine_exercise.completed_at = datetime.now(timezone.utc)

    # Obtener puntos del ejercicio
    ejercicio = routine_exercise.exercise
    puntos = ejercicio.points_value

    # Registrar en historial de completions
    completion = ExerciseCompletion(
        user_id=current_user.id,
        exercise_id=ejercicio.id,
        routine_id=routine_id,
        points_earned=puntos,
        duration_seconds=data.duration_seconds or ejercicio.duracion_segundos,
    )
    db.add(completion)

    # Aplicar gamificación (puntos, nivel, racha)
    recompensa = GamificationService.aplicar_recompensa(db, current_user, puntos)

    # Verificar si la rutina completa quedó terminada
    total_ejercicios = db.query(RoutineExercise).filter(
        RoutineExercise.routine_id == routine_id
    ).count()
    completados = db.query(RoutineExercise).filter(
        RoutineExercise.routine_id == routine_id,
        RoutineExercise.is_completed == True
    ).count()

    progreso = round((completados / total_ejercicios) * 100, 1) if total_ejercicios > 0 else 0

    # Si todos los ejercicios están hechos, marcar rutina completa
    if completados == total_ejercicios:
        rutina.is_completed = True

    db.commit()

    return CompleteExerciseResponse(
        message=f"¡Ejercicio completado! Ganaste {puntos} puntos.",
        points_earned=recompensa["points_earned"],
        total_points=recompensa["total_points"],
        level=recompensa["level"],
        leveled_up=recompensa["leveled_up"],
        routine_progress_percentage=progreso,
    )


@router.get("/progress")
def progreso_del_dia(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Devuelve el progreso del usuario en la rutina de hoy."""
    from datetime import date
    rutina = db.query(Routine).filter(
        Routine.user_id == current_user.id,
        Routine.fecha == date.today()
    ).first()

    if not rutina:
        return {
            "has_routine_today": False,
            "message": "No tienes rutina generada para hoy"
        }

    total = len(rutina.exercises)
    completados = sum(1 for e in rutina.exercises if e.is_completed)
    progreso = round((completados / total) * 100, 1) if total > 0 else 0

    return {
        "has_routine_today": True,
        "routine_id": rutina.id,
        "routine_name": rutina.nombre,
        "total_exercises": total,
        "completed_exercises": completados,
        "progress_percentage": progreso,
        "is_completed": rutina.is_completed,
        "user_stats": {
            "total_points": current_user.total_points,
            "level": current_user.level,
            "current_streak": current_user.current_streak,
            "longest_streak": current_user.longest_streak,
            "total_exercises_completed": current_user.total_exercises,
        }
    }