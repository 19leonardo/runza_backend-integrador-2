from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ===== Crear conversaciones =====
class CreateIndividualChatRequest(BaseModel):
    other_user_id: int


class CreateGroupChatRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: Optional[str] = None
    participant_ids: List[int] = Field(..., min_length=1)


# ===== Enviar mensaje =====
class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


# ===== Respuestas =====
class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: str
    content: str
    tipo: str
    created_at: datetime
    es_mio: bool

    model_config = {"from_attributes": True}


class ParticipantInfo(BaseModel):
    user_id: int
    full_name: str
    email: str
    es_admin: bool
    is_online: bool
    activo: bool


class ConversationListItem(BaseModel):
    id: int
    es_grupo: bool
    nombre: str  # nombre del grupo o del otro usuario si es individual
    ultimo_mensaje: Optional[str]
    ultimo_mensaje_fecha: Optional[datetime]
    mensajes_no_leidos: int
    total_participantes: int
    otro_usuario_online: Optional[bool]  # solo para individual


class ConversationDetailResponse(BaseModel):
    id: int
    es_grupo: bool
    nombre: Optional[str]
    descripcion: Optional[str]
    participantes: List[ParticipantInfo]
    soy_admin: bool


class MessagesPageResponse(BaseModel):
    conversation_id: int
    mensajes: List[MessageResponse]
    total: int


class UnreadCountResponse(BaseModel):
    total_no_leidos: int
    conversaciones_con_no_leidos: int


class SimpleMessageResponse(BaseModel):
    message: str

# ===== Gestión avanzada de grupos =====
class AddMembersRequest(BaseModel):
    user_ids: List[int] = Field(..., min_length=1)


class RemoveMemberRequest(BaseModel):
    user_id: int


class RenameGroupRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: Optional[str] = None


class MakeAdminRequest(BaseModel):
    user_id: int