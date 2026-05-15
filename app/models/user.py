from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # nullable para OAuth
    full_name = Column(String(255), nullable=False)
    birth_date = Column(String(20), nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Estado
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_online = Column(Boolean, default=False)

    # Gamificación
    total_points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    level = Column(Integer, default=1)
    total_exercises = Column(Integer, default=0)

    # Onboarding
    onboarding_completed = Column(Boolean, default=False)
    deporte = Column(String(100), nullable=True)
    posicion = Column(String(100), nullable=True)
    objetivo = Column(String(100), nullable=True)
    nivel_actividad = Column(String(50), nullable=True)
    dias_semana = Column(Integer, nullable=True)
    duracion_sesion = Column(Integer, nullable=True)
    equipamiento = Column(Text, nullable=True)
    lesiones = Column(Text, nullable=True)
    genero = Column(String(20), nullable=True)
    role = Column(String(20), default="jugador", nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)