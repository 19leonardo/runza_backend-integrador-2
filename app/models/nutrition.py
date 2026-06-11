from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class MealLog(Base):
    """Registro de una comida del usuario."""
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)

    tipo_comida = Column(String(20), nullable=False)  # desayuno, almuerzo, cena, snack
    descripcion = Column(String(300), nullable=False)
    calorias_estimadas = Column(Integer, nullable=True)  # opcional, el usuario lo pone

    # Foto como evidencia
    foto_path = Column(String(500), nullable=True)

    # Resultado de la validación (escalable a futuro)
    validado = Column(Boolean, default=False)
    metodo_validacion = Column(String(50), default="ninguno")
    # ninguno | deteccion_objetos | modelo_ia (futuro)
    detalle_validacion = Column(Text, nullable=True)

    # Gamificación
    puntos_otorgados = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WaterLog(Base):
    """Registro de hidratación diaria."""
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    vasos = Column(Integer, default=0)  # cada vaso = 250 ml
    puntos_otorgados = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())