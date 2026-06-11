"""
Servicio de gestión entrenador-jugador.
Implementa RF-015 del informe: rol entrenador/especialista.
"""
import random
import string
from sqlalchemy.orm import Session
from datetime import date
from typing import List
from fastapi import HTTPException, status

from app.models.user import User
from app.models.coaching import CoachInviteCode, CoachPlayer
from app.services.load_service import LoadService
from app.services.pain_service import PainService


class CoachingService:

    @staticmethod
    def _generar_codigo() -> str:
        """Genera un código tipo RUNZA-X7K2."""
        chars = string.ascii_uppercase + string.digits
        sufijo = "".join(random.choices(chars, k=4))
        return f"RUNZA-{sufijo}"

    @staticmethod
    def generar_codigo_invitacion(
        db: Session, coach: User, especialidad: str, max_usos: int
    ) -> dict:
        """El entrenador genera un código para compartir por WhatsApp."""
        # Generar código único
        codigo = CoachingService._generar_codigo()
        while db.query(CoachInviteCode).filter(CoachInviteCode.codigo == codigo).first():
            codigo = CoachingService._generar_codigo()

        invite = CoachInviteCode(
            coach_id=coach.id,
            codigo=codigo,
            especialidad=especialidad,
            max_usos=max_usos,
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)

        link = f"https://runza.app/join/{codigo}"
        mensaje_wpp = (
            f"¡Hola! Te invito a entrenar conmigo en RunZa 🏃⚽\n\n"
            f"Soy tu {especialidad}. Usa este código en la app: *{codigo}*\n\n"
            f"O entra a: {link}"
        )

        return {
            "id": invite.id,
            "codigo": invite.codigo,
            "especialidad": invite.especialidad,
            "usos": invite.usos,
            "max_usos": invite.max_usos,
            "link_compartible": link,
            "mensaje_whatsapp": mensaje_wpp,
        }

    @staticmethod
    def unirse_por_codigo(db: Session, player: User, codigo: str) -> dict:
        """El jugador ingresa un código para vincularse a un entrenador."""
        invite = db.query(CoachInviteCode).filter(
            CoachInviteCode.codigo == codigo.upper().strip(),
            CoachInviteCode.activo == "si",
        ).first()

        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código inválido o inactivo"
            )

        if invite.usos >= invite.max_usos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este código alcanzó su límite de usos"
            )

        if invite.coach_id == player.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes vincularte contigo mismo"
            )

        # Verificar si ya existe el vínculo con esa especialidad
        existe = db.query(CoachPlayer).filter(
            CoachPlayer.coach_id == invite.coach_id,
            CoachPlayer.player_id == player.id,
            CoachPlayer.especialidad == invite.especialidad,
        ).first()

        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya estás vinculado con este entrenador en esa especialidad"
            )

        # Crear vínculo
        vinculo = CoachPlayer(
            coach_id=invite.coach_id,
            player_id=player.id,
            especialidad=invite.especialidad,
            estado="activo",
            fecha_vinculacion=date.today(),
        )
        db.add(vinculo)
        invite.usos += 1
        db.commit()

        coach = db.query(User).filter(User.id == invite.coach_id).first()

        return {
            "message": f"¡Vinculado correctamente con {coach.full_name}!",
            "coach_name": coach.full_name,
            "especialidad": invite.especialidad,
            "estado": "activo",
        }

    @staticmethod
    def buscar_jugadores(db: Session, query: str) -> List[User]:
        """El entrenador busca jugadores por email o nombre."""
        q = f"%{query.lower()}%"
        return db.query(User).filter(
            User.role == "jugador",
            (User.email.ilike(q)) | (User.full_name.ilike(q)),
        ).limit(10).all()

    @staticmethod
    def invitar_jugador_directo(
        db: Session, coach: User, player_id: int, especialidad: str
    ) -> dict:
        """El entrenador agrega directamente a un jugador (estado pendiente)."""
        player = db.query(User).filter(
            User.id == player_id, User.role == "jugador"
        ).first()
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jugador no encontrado"
            )

        existe = db.query(CoachPlayer).filter(
            CoachPlayer.coach_id == coach.id,
            CoachPlayer.player_id == player_id,
            CoachPlayer.especialidad == especialidad,
        ).first()
        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una invitación o vínculo con este jugador"
            )

        vinculo = CoachPlayer(
            coach_id=coach.id,
            player_id=player_id,
            especialidad=especialidad,
            estado="pendiente",
        )
        db.add(vinculo)
        db.commit()

        return {
            "message": f"Invitación enviada a {player.full_name}",
            "estado": "pendiente",
        }

    @staticmethod
    def listar_jugadores(db: Session, coach: User) -> List[dict]:
        """Lista todos los jugadores vinculados al entrenador."""
        vinculos = db.query(CoachPlayer).filter(
            CoachPlayer.coach_id == coach.id,
        ).all()

        resultado = []
        for v in vinculos:
            player = db.query(User).filter(User.id == v.player_id).first()
            if not player:
                continue
            resultado.append({
                "player_id": player.id,
                "full_name": player.full_name,
                "email": player.email,
                "deporte": player.deporte,
                "posicion": player.posicion,
                "especialidad": v.especialidad,
                "estado": v.estado,
                "total_points": player.total_points or 0,
                "level": player.level or 1,
                "current_streak": player.current_streak or 0,
                "fecha_vinculacion": v.fecha_vinculacion,
            })
        return resultado

    @staticmethod
    def _verificar_acceso(db: Session, coach: User, player_id: int) -> User:
        """Verifica que el entrenador tenga acceso a ese jugador."""
        vinculo = db.query(CoachPlayer).filter(
            CoachPlayer.coach_id == coach.id,
            CoachPlayer.player_id == player_id,
            CoachPlayer.estado == "activo",
        ).first()
        if not vinculo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a este jugador o no está vinculado contigo"
            )
        player = db.query(User).filter(User.id == player_id).first()
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jugador no encontrado"
            )
        return player

    @staticmethod
    def dashboard_jugador(db: Session, coach: User, player_id: int) -> dict:
        """Dashboard completo de un jugador (solo si está vinculado)."""
        player = CoachingService._verificar_acceso(db, coach, player_id)

        # Datos de carga (ACWR)
        acwr_data = LoadService.calcular_acwr(db, player)

        # Datos de molestias y riesgo
        riesgo = PainService.evaluar_riesgo_combinado(db, player)

        return {
            "player_id": player.id,
            "full_name": player.full_name,
            "email": player.email,
            "deporte": player.deporte,
            "posicion": player.posicion,
            "objetivo": player.objetivo,
            "total_points": player.total_points or 0,
            "level": player.level or 1,
            "current_streak": player.current_streak or 0,
            "longest_streak": player.longest_streak or 0,
            "total_exercises": player.total_exercises or 0,
            "acwr_actual": acwr_data["acwr"],
            "zona_acwr": acwr_data["zona"],
            "color_acwr": acwr_data["color"],
            "molestias_activas": riesgo["cantidad_molestias_activas"],
            "molestia_mas_intensa": riesgo["molestia_mas_intensa"],
            "nivel_riesgo": riesgo["nivel_riesgo_combinado"],
            "color_riesgo": riesgo["color"],
            "mensaje_riesgo": riesgo["mensaje"],
        }

    @staticmethod
    def obtener_alertas(db: Session, coach: User) -> List[dict]:
        """Lista jugadores en riesgo (sobrecarga o dolor intenso)."""
        vinculos = db.query(CoachPlayer).filter(
            CoachPlayer.coach_id == coach.id,
            CoachPlayer.estado == "activo",
        ).all()

        alertas = []
        for v in vinculos:
            player = db.query(User).filter(User.id == v.player_id).first()
            if not player:
                continue

            riesgo = PainService.evaluar_riesgo_combinado(db, player)

            if riesgo["nivel_riesgo_combinado"] in ["alto", "critico"]:
                alertas.append({
                    "player_id": player.id,
                    "full_name": player.full_name,
                    "tipo_alerta": "riesgo_combinado",
                    "nivel": riesgo["nivel_riesgo_combinado"],
                    "mensaje": riesgo["mensaje"],
                    "detalle": " | ".join(riesgo["recomendaciones"][:2]),
                })

        return alertas

    @staticmethod
    def mi_entrenador(db: Session, player: User) -> List[dict]:
        """El jugador ve quiénes son sus entrenadores."""
        vinculos = db.query(CoachPlayer).filter(
            CoachPlayer.player_id == player.id,
        ).all()

        resultado = []
        for v in vinculos:
            coach = db.query(User).filter(User.id == v.coach_id).first()
            if not coach:
                continue
            resultado.append({
                "coach_id": coach.id,
                "coach_name": coach.full_name,
                "coach_email": coach.email,
                "especialidad": v.especialidad,
                "estado": v.estado,
                "fecha_vinculacion": v.fecha_vinculacion,
            })
        return resultado