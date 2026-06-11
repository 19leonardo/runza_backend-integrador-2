from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CoachInviteCode(Base):
    """
    Código de invitación generado por un entrenador.
    Se comparte por WhatsApp. El jugador lo ingresa para vincularse.
    """
    __tablename__ = "coach_invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    
    # Especialidad del entrenador en este código
    especialidad = Column(String(50), default="entrenador")
    # entrenador, preparador_fisico, nutricionista, fisioterapeuta, medico

    activo = Column(String(10), default="si")  # si | no
    usos = Column(Integer, default=0)  # cuántos jugadores lo usaron
    max_usos = Column(Integer, default=100)  # límite de usos

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CoachPlayer(Base):
    """
    Relación entre un entrenador y un jugador.
    Many-to-many: un jugador puede tener varios entrenadores.
    """
    __tablename__ = "coach_player"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    especialidad = Column(String(50), default="entrenador")
    estado = Column(String(20), default="activo")  # pendiente | activo | rechazado

    fecha_vinculacion = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())