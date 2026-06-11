from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base


class PainReport(Base):
    """
    Registro de molestias musculoesqueléticas reportadas por el usuario.
    Basado en monitoreo preventivo de lesiones (sección 5.2.5 del informe).
    Usa Escala Visual Analógica (EVA) 0-10 para intensidad.
    """
    __tablename__ = "pain_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    fecha = Column(Date, nullable=False, index=True)

    # Localización
    zona_cuerpo = Column(String(50), nullable=False)
    # rodilla, tobillo, isquiotibiales, cuadriceps, espalda_baja,
    # hombro, cadera, gemelo, aductor, otro
    lado = Column(String(20), default="no_aplica")  # izquierdo, derecho, ambos, no_aplica

    # Caracterización
    intensidad = Column(Float, nullable=False)  # 0-10 (EVA)
    tipo_molestia = Column(String(30), nullable=False)
    # muscular, articular, tendinosa, osea, otro
    momento_dolor = Column(String(30), nullable=False)
    # reposo, al_entrenar, despues_entrenar, todo_el_tiempo

    notas = Column(Text, nullable=True)

    # Estado
    requiere_atencion = Column(Boolean, default=False)
    resuelto = Column(Boolean, default=False)
    fecha_resolucion = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())