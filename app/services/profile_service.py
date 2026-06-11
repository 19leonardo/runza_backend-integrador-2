"""
Servicio de perfil y dashboard personal del jugador.
Agrupa métricas de todos los módulos en un solo lugar.
"""
import os
import base64
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.nutrition import MealLog, WaterLog
from app.services.load_service import LoadService
from app.services.pain_service import PainService
from app.services.gamification_service import GamificationService
from app.services.nutrition_service import NutritionService

AVATAR_DIR = "uploads/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)


class ProfileService:

    # Umbrales de nivel (mismos que gamification_service)
    UMBRALES = [0, 100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000]

    @staticmethod
    def obtener_perfil(user: User) -> User:
        return user

    @staticmethod
    def actualizar_perfil(db: Session, user: User, data) -> User:
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.weight_kg is not None:
            user.weight_kg = data.weight_kg
        if data.height_cm is not None:
            user.height_cm = data.height_cm
        if data.objetivo is not None:
            user.objetivo = data.objetivo
        if data.dias_semana is not None:
            user.dias_semana = data.dias_semana
        if data.duracion_sesion is not None:
            user.duracion_sesion = data.duracion_sesion
        if data.nivel_actividad is not None:
            user.nivel_actividad = data.nivel_actividad
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def actualizar_foto(db: Session, user: User, foto_base64: str) -> dict:
        try:
            b64 = foto_base64
            if "," in b64:
                b64 = b64.split(",")[1]
            img_bytes = base64.b64decode(b64)

            filename = f"avatar_{user.id}.jpg"
            path = os.path.join(AVATAR_DIR, filename)
            with open(path, "wb") as f:
                f.write(img_bytes)

            user.avatar_url = path
            db.commit()
            db.refresh(user)
            return {"message": "Foto de perfil actualizada", "avatar_url": path}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error procesando la foto: {str(e)}"
            )

    @staticmethod
    def _puntos_siguiente_nivel(total_points: int) -> int:
        """Cuántos puntos faltan para el siguiente nivel."""
        for umbral in ProfileService.UMBRALES:
            if total_points < umbral:
                return umbral - total_points
        return 0  # ya está en nivel máximo

    @staticmethod
    def dashboard_completo(db: Session, user: User) -> dict:
        # ACWR
        acwr_data = LoadService.calcular_acwr(db, user)

        # Riesgo / molestias
        riesgo = PainService.evaluar_riesgo_combinado(db, user)

        # Nutrición hoy
        hoy = date.today()
        comidas = db.query(MealLog).filter(
            MealLog.user_id == user.id,
            MealLog.fecha == hoy,
        ).all()
        calorias_hoy = sum(c.calorias_estimadas or 0 for c in comidas)

        agua = db.query(WaterLog).filter(
            WaterLog.user_id == user.id,
            WaterLog.fecha == hoy,
        ).first()
        vasos_hoy = agua.vasos if agua else 0

        necesidades = NutritionService.calcular_necesidades(user)

        # Mensaje motivacional global
        puntos = user.total_points or 0
        racha = user.current_streak or 0
        if racha >= 7:
            mensaje = f"¡{racha} días seguidos! Eres imparable 🔥"
        elif racha >= 3:
            mensaje = f"Llevas {racha} días de racha. ¡Sigue así!"
        elif puntos > 0:
            mensaje = "Buen progreso. La constancia es la clave del éxito."
        else:
            mensaje = "¡Empieza hoy tu camino al siguiente nivel!"

        return {
            "full_name": user.full_name,
            "nivel": user.level or 1,
            "total_points": puntos,
            "current_streak": racha,
            "longest_streak": user.longest_streak or 0,
            "total_exercises": user.total_exercises or 0,
            "puntos_para_siguiente_nivel": ProfileService._puntos_siguiente_nivel(puntos),
            "acwr": acwr_data["acwr"],
            "zona_acwr": acwr_data["zona"],
            "color_acwr": acwr_data["color"],
            "molestias_activas": riesgo["cantidad_molestias_activas"],
            "nivel_riesgo": riesgo["nivel_riesgo_combinado"],
            "calorias_consumidas_hoy": calorias_hoy,
            "objetivo_calorico": necesidades["objetivo_calorico"],
            "vasos_agua_hoy": vasos_hoy,
            "mensaje": mensaje,
        }