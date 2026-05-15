"""
Servicio de gamificación: puntos, niveles, rachas.
Implementa el sistema de motivación del informe (sección 5.3.2.2, Bourdon et al., 2017).
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.models.user import User
from app.models.exercise import ExerciseCompletion


class GamificationService:

    # Umbrales de niveles (puntos acumulados para subir)
    # Nivel 1: 0-99 | Nivel 2: 100-299 | Nivel 3: 300-599 | etc.
    @staticmethod
    def calcular_nivel(total_points: int) -> int:
        """Calcula el nivel del usuario según sus puntos totales."""
        if total_points < 100:
            return 1
        elif total_points < 300:
            return 2
        elif total_points < 600:
            return 3
        elif total_points < 1000:
            return 4
        elif total_points < 1500:
            return 5
        elif total_points < 2500:
            return 6
        elif total_points < 4000:
            return 7
        elif total_points < 6000:
            return 8
        elif total_points < 10000:
            return 9
        else:
            return 10

    @staticmethod
    def actualizar_racha(db: Session, user: User) -> None:
        """
        Actualiza la racha de días consecutivos del usuario.
        Lógica:
        - Si última actividad fue ayer → racha +1
        - Si última actividad fue hoy → no cambia
        - Si fue hace 2+ días → racha = 1 (reset)
        """
        hoy = date.today()

        # Buscar última completion antes de hoy
        ultima_completion = db.query(ExerciseCompletion).filter(
            ExerciseCompletion.user_id == user.id,
            func.date(ExerciseCompletion.completed_at) < hoy
        ).order_by(ExerciseCompletion.completed_at.desc()).first()

        if not ultima_completion:
            # Primera vez que entrena
            user.current_streak = 1
        else:
            fecha_ultima = ultima_completion.completed_at.date()
            dias_diferencia = (hoy - fecha_ultima).days

            if dias_diferencia == 1:
                # Entrenó ayer → racha continúa
                user.current_streak = (user.current_streak or 0) + 1
            elif dias_diferencia == 0:
                # Ya tenía completion hoy → no cambiar racha
                pass
            else:
                # Más de 1 día sin entrenar → reset
                user.current_streak = 1

        # Actualizar racha más larga histórica
        if user.current_streak > (user.longest_streak or 0):
            user.longest_streak = user.current_streak

    @staticmethod
    def aplicar_recompensa(
        db: Session,
        user: User,
        puntos: int
    ) -> dict:
        """
        Aplica los puntos al usuario y verifica si subió de nivel.
        Devuelve dict con info útil para el frontend.
        """
        nivel_anterior = user.level or 1
        user.total_points = (user.total_points or 0) + puntos
        user.total_exercises = (user.total_exercises or 0) + 1

        nuevo_nivel = GamificationService.calcular_nivel(user.total_points)
        leveled_up = nuevo_nivel > nivel_anterior
        user.level = nuevo_nivel

        # Actualizar racha
        GamificationService.actualizar_racha(db, user)

        db.commit()
        db.refresh(user)

        return {
            "points_earned": puntos,
            "total_points": user.total_points,
            "level": user.level,
            "leveled_up": leveled_up,
            "current_streak": user.current_streak,
        }