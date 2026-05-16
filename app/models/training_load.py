from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SessionLoad(Base):
    """
    Registro de carga interna por sesión de entrenamiento.
    Basado en RPE (Foster et al., 2001) y ACWR (Gabbett, 2020).
    """
    __tablename__ = "session_loads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=True)
    
    fecha = Column(Date, nullable=False, index=True)
    
    # Datos del usuario
    rpe = Column(Float, nullable=False)  # 0-10 escala CR-10
    duracion_minutos = Column(Integer, nullable=False)
    
    # Calculado automáticamente
    carga_interna = Column(Float, nullable=False)  # rpe × duracion
    
    # Metadata opcional
    notas = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())