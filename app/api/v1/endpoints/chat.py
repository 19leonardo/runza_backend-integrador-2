from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.chat import (
    CreateIndividualChatRequest, CreateGroupChatRequest,
    SendMessageRequest, MessageResponse, ConversationListItem,
    ConversationDetailResponse, MessagesPageResponse,
    UnreadCountResponse, SimpleMessageResponse,
    AddMembersRequest, RemoveMemberRequest, RenameGroupRequest, MakeAdminRequest,
)
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/conversations/individual", status_code=201)
def crear_chat_individual(
    data: CreateIndividualChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea (o recupera) un chat individual con otro usuario."""
    conv = ChatService.crear_chat_individual(db, current_user, data.other_user_id)
    return {"conversation_id": conv.id, "es_grupo": conv.es_grupo}


@router.post("/conversations/group", status_code=201)
def crear_chat_grupal(
    data: CreateGroupChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea un chat grupal con varios participantes."""
    conv = ChatService.crear_chat_grupal(
        db, current_user, data.nombre, data.descripcion, data.participant_ids
    )
    return {"conversation_id": conv.id, "es_grupo": conv.es_grupo, "nombre": conv.nombre}


@router.get("/conversations", response_model=List[ConversationListItem])
def listar_conversaciones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todas mis conversaciones ordenadas por último mensaje."""
    return ChatService.listar_conversaciones(db, current_user)


@router.get("/conversations/{conv_id}", response_model=ConversationDetailResponse)
def detalle_conversacion(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalle de una conversación (participantes, si soy admin, etc.)."""
    return ChatService.detalle_conversacion(db, current_user, conv_id)


@router.post("/conversations/{conv_id}/messages", response_model=MessageResponse, status_code=201)
def enviar_mensaje(
    conv_id: int,
    data: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Envía un mensaje a una conversación."""
    msg = ChatService.enviar_mensaje(db, current_user, conv_id, data.content)
    sender = current_user
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "sender_id": msg.sender_id,
        "sender_name": sender.full_name,
        "content": msg.content,
        "tipo": msg.tipo,
        "created_at": msg.created_at,
        "es_mio": True,
    }


@router.get("/conversations/{conv_id}/messages", response_model=MessagesPageResponse)
def obtener_mensajes(
    conv_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene los mensajes de una conversación."""
    return ChatService.obtener_mensajes(db, current_user, conv_id, limit)


@router.post("/conversations/{conv_id}/read", response_model=SimpleMessageResponse)
def marcar_leido(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marca una conversación como leída."""
    return ChatService.marcar_como_leido(db, current_user, conv_id)


@router.get("/unread-count", response_model=UnreadCountResponse)
def contar_no_leidos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Total de mensajes no leídos (para el badge de notificación)."""
    return ChatService.contar_no_leidos(db, current_user)

# ===== GESTIÓN AVANZADA DE GRUPOS =====

@router.post("/conversations/{conv_id}/members", response_model=SimpleMessageResponse)
def agregar_miembros(
    conv_id: int,
    data: AddMembersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agrega miembros a un grupo (solo admin)."""
    return ChatService.agregar_miembros(db, current_user, conv_id, data.user_ids)


@router.delete("/conversations/{conv_id}/members", response_model=SimpleMessageResponse)
def quitar_miembro(
    conv_id: int,
    data: RemoveMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Quita un miembro de un grupo (solo admin)."""
    return ChatService.quitar_miembro(db, current_user, conv_id, data.user_id)


@router.post("/conversations/{conv_id}/leave", response_model=SimpleMessageResponse)
def salir_del_grupo(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Salir de un grupo."""
    return ChatService.salir_del_grupo(db, current_user, conv_id)


@router.patch("/conversations/{conv_id}/rename", response_model=SimpleMessageResponse)
def renombrar_grupo(
    conv_id: int,
    data: RenameGroupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Renombra un grupo (solo admin)."""
    return ChatService.renombrar_grupo(
        db, current_user, conv_id, data.nombre, data.descripcion
    )


@router.post("/conversations/{conv_id}/make-admin", response_model=SimpleMessageResponse)
def hacer_admin(
    conv_id: int,
    data: MakeAdminRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Promueve a un miembro a administrador (solo admin)."""
    return ChatService.hacer_admin(db, current_user, conv_id, data.user_id)