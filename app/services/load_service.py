"""
Servicio de cálculo de carga interna de entrenamiento.
Implementa RPE (Foster et al., 2001) y ACWR (Gabbett, 2020).
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, timedelta
from typing import List
from fastapi import HTTPException, status

from app.models.user import User
from app.models.training_load import SessionLoad
from app.schemas.training_load import RegisterLoadRequest


class LoadService:

    # ===== Zonas ACWR según Gabbett (2020) =====
    @staticmethod
    def clasificar_acwr(acwr: float) -> dict:
        """Clasifica el ACWR en zonas de riesgo."""
        if acwr < 0.8:
            return {
                "zona": "sub_entrenamiento",
                "color": "azul",
                "recomendacion": (
                    "Tu carga ha sido baja últimamente. Puedes aumentar "
                    "gradualmente la intensidad para mejorar tu rendimiento."
                ),
            }
        elif acwr <= 1.3:
            return {
                "zona": "optima",
                "color": "verde",
                "recomendacion": (
                    "¡Excelente! Estás en la zona óptima de carga. "
                    "Mantén este ritmo para minimizar el riesgo de lesión."
                ),
            }
        elif acwr <= 1.5:
            return {
                "zona": "alta",
                "color": "amarillo",
                "recomendacion": (
                    "Tu carga es alta. Considera incluir un día de "
                    "recuperación activa en los próximos 2-3 días."
                ),
            }
        else:
            return {
                "zona": "sobrecarga",
                "color": "rojo",
                "recomendacion": (
                    "⚠️ ALERTA: Riesgo elevado de lesión por sobrecarga. "
                    "Reduce la intensidad y considera 1-2 días de descanso completo. "
                    "Escucha a tu cuerpo."
                ),
            }

    # ===== Registrar carga de una sesión =====
    @staticmethod
    def registrar_carga(
        db: Session,
        user: User,
        data: RegisterLoadRequest
    ) -> SessionLoad:
        """
        Registra el RPE y duración de una sesión.
        Carga interna = RPE × duración (Foster et al., 2001).
        """
        carga_interna = data.rpe * data.duracion_minutos

        nueva_carga = SessionLoad(
            user_id=user.id,
            routine_id=data.routine_id,
            fecha=date.today(),
            rpe=data.rpe,
            duracion_minutos=data.duracion_minutos,
            carga_interna=carga_interna,
            notas=data.notas,
        )
        db.add(nueva_carga)
        db.commit()
        db.refresh(nueva_carga)
        return nueva_carga

    # ===== Calcular ACWR =====
    @staticmethod
    def calcular_acwr(db: Session, user: User) -> dict:
        """
        Calcula el ACWR del usuario:
        - Carga Aguda: promedio diario últimos 7 días
        - Carga Crónica: promedio diario últimos 28 días
        - ACWR = Aguda / Crónica
        """
        hoy = date.today()
        hace_7_dias = hoy - timedelta(days=7)
        hace_28_dias = hoy - timedelta(days=28)

        # Carga aguda (últimos 7 días)
        cargas_agudas = db.query(
            func.coalesce(func.sum(SessionLoad.carga_interna), 0).label("total")
        ).filter(
            SessionLoad.user_id == user.id,
            SessionLoad.fecha >= hace_7_dias,
            SessionLoad.fecha <= hoy,
        ).scalar() or 0

        # Carga crónica (últimos 28 días)
        cargas_cronicas = db.query(
            func.coalesce(func.sum(SessionLoad.carga_interna), 0).label("total")
        ).filter(
            SessionLoad.user_id == user.id,
            SessionLoad.fecha >= hace_28_dias,
            SessionLoad.fecha <= hoy,
        ).scalar() or 0

        # Promedios diarios
        promedio_agudo = float(cargas_agudas) / 7
        promedio_cronico = float(cargas_cronicas) / 28

        # ACWR (evitar división por cero)
        if promedio_cronico == 0:
            acwr = 0.0
        else:
            acwr = round(promedio_agudo / promedio_cronico, 2)

        # Días con datos (para evaluar confianza del cálculo)
        dias_agudos = db.query(func.count(func.distinct(SessionLoad.fecha))).filter(
            SessionLoad.user_id == user.id,
            SessionLoad.fecha >= hace_7_dias,
        ).scalar() or 0

        dias_cronicos = db.query(func.count(func.distinct(SessionLoad.fecha))).filter(
            SessionLoad.user_id == user.id,
            SessionLoad.fecha >= hace_28_dias,
        ).scalar() or 0

        # Nivel de confianza
        if dias_cronicos >= 14 and dias_agudos >= 3:
            confianza = "alta"
        elif dias_cronicos >= 7:
            confianza = "media"
        else:
            confianza = "baja"

        clasificacion = LoadService.clasificar_acwr(acwr) if acwr > 0 else {
            "zona": "datos_insuficientes",
            "color": "gris",
            "recomendacion": (
                "Necesitas registrar más sesiones para calcular tu ACWR de forma confiable. "
                "Sigue entrenando y registrando tu RPE."
            ),
        }

        return {
            "carga_aguda": round(promedio_agudo, 2),
            "carga_cronica": round(promedio_cronico, 2),
            "acwr": acwr,
            "zona": clasificacion["zona"],
            "color": clasificacion["color"],
            "recomendacion": clasificacion["recomendacion"],
            "referencia": "Gabbett, T. J. (2020). Debunking the myths about training load.",
            "dias_con_datos_agudos": dias_agudos,
            "dias_con_datos_cronicos": dias_cronicos,
            "confianza": confianza,
        }

    # ===== Historial de carga (para gráficas) =====
    @staticmethod
    def obtener_historial(db: Session, user: User, dias: int = 30) -> dict:
        """Devuelve carga diaria de los últimos N días."""
        hoy = date.today()
        desde = hoy - timedelta(days=dias)

        # Agrupar por fecha
        resultados = db.query(
            SessionLoad.fecha,
            func.sum(SessionLoad.carga_interna).label("carga_total"),
            func.avg(SessionLoad.rpe).label("rpe_promedio"),
            func.count(SessionLoad.id).label("sesiones"),
        ).filter(
            SessionLoad.user_id == user.id,
            SessionLoad.fecha >= desde,
        ).group_by(SessionLoad.fecha).order_by(SessionLoad.fecha.asc()).all()

        puntos = [
            {
                "fecha": r.fecha,
                "carga_total": round(float(r.carga_total), 2),
                "rpe_promedio": round(float(r.rpe_promedio), 2),
                "sesiones": r.sesiones,
            }
            for r in resultados
        ]

        carga_total_periodo = sum(p["carga_total"] for p in puntos)
        rpe_promedio_periodo = (
            sum(p["rpe_promedio"] for p in puntos) / len(puntos)
            if puntos else 0
        )

        return {
            "dias": dias,
            "puntos": puntos,
            "carga_total_periodo": round(carga_total_periodo, 2),
            "rpe_promedio_periodo": round(rpe_promedio_periodo, 2),
        }

    # ===== Resumen semanal =====
    @staticmethod
    def resumen_semanal(db: Session, user: User) -> dict:
        """Resumen de la semana actual (lunes a domingo)."""
        hoy = date.today()
        dia_semana = hoy.weekday()  # lunes=0, domingo=6
        semana_inicio = hoy - timedelta(days=dia_semana)
        semana_fin = semana_inicio + timedelta(days=6)

        sesiones = db.query(SessionLoad).filter(
            SessionLoad.user_id == user.id,
            SessionLoad.fecha >= semana_inicio,
            SessionLoad.fecha <= semana_fin,
        ).all()

        if not sesiones:
            return {
                "semana_inicio": semana_inicio,
                "semana_fin": semana_fin,
                "sesiones_completadas": 0,
                "carga_total": 0,
                "duracion_total_minutos": 0,
                "rpe_promedio": 0,
                "dia_mas_intenso": None,
                "acwr_actual": 0,
                "zona": "sin_datos",
                "mensaje": "Aún no tienes sesiones registradas esta semana. ¡Vamos!"
            }

        carga_total = sum(s.carga_interna for s in sesiones)
        duracion_total = sum(s.duracion_minutos for s in sesiones)
        rpe_promedio = sum(s.rpe for s in sesiones) / len(sesiones)

        # Día más intenso
        sesion_mas_intensa = max(sesiones, key=lambda s: s.carga_interna)
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_mas_intenso = dias_semana[sesion_mas_intensa.fecha.weekday()]

        # ACWR actual
        acwr_data = LoadService.calcular_acwr(db, user)

        # Mensaje motivacional
        if len(sesiones) >= 4:
            mensaje = f"¡Gran semana! {len(sesiones)} sesiones completadas."
        elif len(sesiones) >= 2:
            mensaje = f"Vas bien con {len(sesiones)} sesiones. Sigue así."
        else:
            mensaje = f"Solo {len(sesiones)} sesión esta semana. Intenta sumar más."

        return {
            "semana_inicio": semana_inicio,
            "semana_fin": semana_fin,
            "sesiones_completadas": len(sesiones),
            "carga_total": round(carga_total, 2),
            "duracion_total_minutos": duracion_total,
            "rpe_promedio": round(rpe_promedio, 2),
            "dia_mas_intenso": dia_mas_intenso,
            "acwr_actual": acwr_data["acwr"],
            "zona": acwr_data["zona"],
            "mensaje": mensaje,
        }