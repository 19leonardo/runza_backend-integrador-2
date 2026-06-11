from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Conversation(Base):
    """Una conversación: individual (2 personas) o grupal (N personas)."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    es_grupo = Column(Boolean, default=False, nullable=False)
    nombre = Column(String(150), nullable=True)  # solo para grupos
    descripcion = Column(String(300), nullable=True)  # solo para grupos
    
    creado_por = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    participants = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class ConversationParticipant(Base):
    """Quién participa en una conversación y hasta cuándo leyó."""
    __tablename__ = "conversation_participants"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Para grupos: rol del participante
    es_admin = Column(Boolean, default=False)

    # Para contador de no leídos (clave para evitar el error histórico)
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Si el usuario salió del grupo
    activo = Column(Boolean, default=True)

    conversation = relationship("Conversation", back_populates="participants")


class Message(Base):
    """Un mensaje dentro de una conversación."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    content = Column(Text, nullable=False)
    
    # Tipo de mensaje (para futuro: imágenes, etc.)
    tipo = Column(String(20), default="texto")  # texto | sistema

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    conversation = relationship("Conversation", back_populates="messages")