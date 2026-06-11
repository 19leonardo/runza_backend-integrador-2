"""
Servicio de monitoreo de molestias musculoesqueléticas.
Prevención de lesiones (sección 5.2.5 del informe).
Cruza datos de dolor con ACWR (Gabbett, 2020) para evaluación de riesgo.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List
from fastapi import HTTPException, status

from app.models.user import User
from app.models.pain_report import PainReport
from app.schemas.pain_report import ReportPainRequest
from app.services.load_service import LoadService


class PainService:

    @staticmethod
    def _evaluar_nivel_alerta(intensidad: float, persistente: bool) -> dict:
        """Determina el nivel de alerta según la intensidad del dolor."""
        if intensidad >= 7:
            return {
                "requiere_atencion": True,
                "nivel_alerta": "urgente",
                "mensaje": "Dolor de alta intensidad detectado.",
                "recomendacion": (
                    "Te recomendamos consultar con un profesional de la salud "
                    "(médico deportivo o fisioterapeuta) antes de continuar entrenando "
                    "esa zona. No ignores un dolor intenso."
                ),
            }
        elif intensidad >= 4:
            if persistente:
                return {
                    "requiere_atencion": True,
                    "nivel_alerta": "alerta",
                    "mensaje": "Molestia moderada persistente (3+ días).",
                    "recomendacion": (
                        "Esta molestia lleva varios días. Considera reducir la carga "
                        "en esa zona y, si no mejora en 48-72h, consulta a un profesional."
                    ),
                }
            return {
                "requiere_atencion": False,
                "nivel_alerta": "precaucion",
                "mensaje": "Molestia moderada registrada.",
                "recomendacion": (
                    "Monitorea esta molestia. Si aumenta o persiste más de 3 días, "
                    "reduce la intensidad y considera consultar a un profesional."
                ),
            }
        else:
            return {
                "requiere_atencion": False,
                "nivel_alerta": "normal",
                "mensaje": "Molestia leve registrada.",
                "recomendacion": (
                    "Molestia leve. Continúa monitoreando. El descanso y una buena "
                    "técnica suelen resolver molestias leves."
                ),
            }

    @staticmethod
    def reportar_molestia(
        db: Session,
        user: User,
        data: ReportPainRequest
    ) -> dict:
        """Registra una molestia y evalúa si requiere atención."""
        hoy = date.today()

        # Verificar si es persistente (misma zona reportada en últimos 3 días)
        hace_3_dias = hoy - timedelta(days=3)
        reportes_previos = db.query(PainReport).filter(
            PainReport.user_id == user.id,
            PainReport.zona_cuerpo == data.zona_cuerpo,
            PainReport.fecha >= hace_3_dias,
            PainReport.resuelto == False,
        ).count()
        es_persistente = reportes_previos >= 2  # 2 previos + este = 3 días

        # Evaluar nivel de alerta
        evaluacion = PainService._evaluar_nivel_alerta(data.intensidad, es_persistente)

        # Crear el reporte
        reporte = PainReport(
            user_id=user.id,
            fecha=hoy,
            zona_cuerpo=data.zona_cuerpo,
            lado=data.lado,
            intensidad=data.intensidad,
            tipo_molestia=data.tipo_molestia,
            momento_dolor=data.momento_dolor,
            notas=data.notas,
            requiere_atencion=evaluacion["requiere_atencion"],
        )
        db.add(reporte)
        db.commit()
        db.refresh(reporte)

        return {
            "reporte": reporte,
            "requiere_atencion": evaluacion["requiere_atencion"],
            "nivel_alerta": evaluacion["nivel_alerta"],
            "mensaje": evaluacion["mensaje"],
            "recomendacion": evaluacion["recomendacion"],
        }

    @staticmethod
    def obtener_molestias_activas(db: Session, user: User) -> List[PainReport]:
        """Molestias no resueltas de los últimos 7 días."""
        hace_7_dias = date.today() - timedelta(days=7)
        return db.query(PainReport).filter(
            PainReport.user_id == user.id,
            PainReport.fecha >= hace_7_dias,
            PainReport.resuelto == False,
        ).order_by(PainReport.intensidad.desc()).all()

    @staticmethod
    def obtener_historial(db: Session, user: User, dias: int = 30) -> List[PainReport]:
        """Historial completo de molestias."""
        desde = date.today() - timedelta(days=dias)
        return db.query(PainReport).filter(
            PainReport.user_id == user.id,
            PainReport.fecha >= desde,
        ).order_by(PainReport.fecha.desc()).all()

    @staticmethod
    def resolver_molestia(db: Session, user: User, pain_id: int) -> PainReport:
        """Marca una molestia como resuelta."""
        reporte = db.query(PainReport).filter(
            PainReport.id == pain_id,
            PainReport.user_id == user.id,
        ).first()
        if not reporte:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporte de molestia no encontrado"
            )
        reporte.resuelto = True
        reporte.fecha_resolucion = date.today()
        db.commit()
        db.refresh(reporte)
        return reporte

    @staticmethod
    def evaluar_riesgo_combinado(db: Session, user: User) -> dict:
        """
        Evaluación de riesgo cruzando molestias activas con ACWR.
        Esta es la innovación del sistema: prevención basada en datos.
        """
        molestias = PainService.obtener_molestias_activas(db, user)
        tiene_molestias = len(molestias) > 0
        molestia_max = max([m.intensidad for m in molestias]) if molestias else 0

        # Obtener ACWR actual
        acwr_data = LoadService.calcular_acwr(db, user)
        acwr = acwr_data["acwr"]
        zona_acwr = acwr_data["zona"]

        # === Matriz de riesgo combinado ===
        # Cruza intensidad de dolor con zona de carga
        recomendaciones = []

        # Factor dolor
        dolor_alto = molestia_max >= 7
        dolor_moderado = 4 <= molestia_max < 7
        carga_alta = zona_acwr in ["alta", "sobrecarga"]

        if dolor_alto and carga_alta:
            nivel = "critico"
            color = "rojo"
            mensaje = "RIESGO CRÍTICO: Dolor intenso combinado con carga elevada."
            recomendaciones = [
                "Detén el entrenamiento de la zona afectada inmediatamente",
                "Consulta a un profesional de la salud lo antes posible",
                "Toma 2-3 días de descanso completo",
                "No regreses hasta que el dolor baje a menos de 3/10",
            ]
        elif dolor_alto:
            nivel = "alto"
            color = "naranja"
            mensaje = "RIESGO ALTO: Dolor intenso detectado."
            recomendaciones = [
                "Reduce o evita ejercicios que involucren la zona afectada",
                "Considera consultar a un profesional",
                "Aplica protocolo RICE (reposo, hielo, compresión, elevación)",
            ]
        elif dolor_moderado and carga_alta:
            nivel = "alto"
            color = "naranja"
            mensaje = "RIESGO ALTO: Molestia moderada + carga de entrenamiento elevada."
            recomendaciones = [
                "Reduce la intensidad general esta semana",
                "Incluye 1-2 días de recuperación activa",
                "Monitorea si la molestia aumenta",
            ]
        elif dolor_moderado:
            nivel = "moderado"
            color = "amarillo"
            mensaje = "RIESGO MODERADO: Molestia moderada en seguimiento."
            recomendaciones = [
                "Continúa entrenando con precaución",
                "Evita sobrecargar la zona afectada",
                "Si la molestia persiste 3+ días, consulta a un profesional",
            ]
        elif carga_alta:
            nivel = "moderado"
            color = "amarillo"
            mensaje = "RIESGO MODERADO: Carga elevada sin molestias reportadas."
            recomendaciones = [
                "Tu carga está alta. Considera un día de descanso preventivo",
                "Mantente atento a cualquier molestia que aparezca",
            ]
        else:
            nivel = "bajo"
            color = "verde"
            mensaje = "RIESGO BAJO: Todo en orden. Sigue así."
            recomendaciones = [
                "Mantén tu rutina actual",
                "Continúa registrando tu RPE y molestias para prevención",
            ]

        return {
            "tiene_molestias_activas": tiene_molestias,
            "cantidad_molestias_activas": len(molestias),
            "molestia_mas_intensa": molestia_max if tiene_molestias else None,
            "acwr_actual": acwr,
            "zona_acwr": zona_acwr,
            "nivel_riesgo_combinado": nivel,
            "color": color,
            "mensaje": mensaje,
            "recomendaciones": recomendaciones,
            "referencia": "Gabbett, T. J. (2020); Bahr & Holme (2003) - monitoreo preventivo",
        }