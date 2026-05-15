from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Exercise(Base):
    """Catálogo maestro de ejercicios disponibles en RunZa."""
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # CRÍTICO: category siempre obligatorio (Error 1 del proyecto anterior)
    category = Column(String(50), nullable=False, index=True)
    # categorías: "calentamiento", "fuerza", "cardio", "tecnica", "estiramiento", "agilidad"
    
    # Filtros
    deporte = Column(String(50), nullable=True, index=True)  # null = válido para todos
    objetivo = Column(String(50), nullable=True, index=True)
    nivel_dificultad = Column(String(20), default="medio")  # "facil", "medio", "dificil"
    
    # Parámetros del ejercicio
    duracion_segundos = Column(Integer, default=60)
    sets = Column(Integer, default=3)
    repeticiones = Column(Integer, default=10)
    descanso_segundos = Column(Integer, default=30)
    
    # Gamificación
    points_value = Column(Integer, default=10)
    
    # Metadata
    requiere_equipamiento = Column(Boolean, default=False)
    equipamiento_necesario = Column(String(200), nullable=True)
    video_url = Column(String(500), nullable=True)
    imagen_url = Column(String(500), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Routine(Base):
    """Rutina personalizada generada para un usuario en una fecha."""
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    duracion_estimada_minutos = Column(Integer, default=30)
    total_puntos_disponibles = Column(Integer, default=0)
    
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    exercises = relationship("RoutineExercise", back_populates="routine", cascade="all, delete-orphan")


class RoutineExercise(Base):
    """Relación entre rutina y ejercicios (con orden y estado)."""
    __tablename__ = "routine_exercises"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    
    orden = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    routine = relationship("Routine", back_populates="exercises")
    exercise = relationship("Exercise")


class ExerciseCompletion(Base):
    """Historial de ejercicios completados (para estadísticas y racha)."""
    __tablename__ = "exercise_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=True)
    
    points_earned = Column(Integer, default=0)
    duration_seconds = Column(Integer, nullable=True)
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)