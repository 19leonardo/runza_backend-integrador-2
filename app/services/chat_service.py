"""
Servicio de chat individual y grupal.
IMPORTANTE: incluye _normalize_datetime() para evitar el error histórico
'TypeError: can't compare offset-naive and offset-aware datetimes'.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.user import User
from app.models.chat import Conversation, ConversationParticipant, Message


def _normalize_datetime(dt: Optional[datetime]) -> datetime:
    """
    Normaliza un datetime para evitar el error de comparación
    offset-naive vs offset-aware.
    Si el datetime no tiene timezone, le asigna UTC.
    Si es None, devuelve una fecha muy antigua (para ordenamiento).
    """
    if dt is None:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class ChatService:

    # ===== Crear conversación individual =====
    @staticmethod
    def crear_chat_individual(db: Session, user: User, other_user_id: int) -> Conversation:
        if other_user_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes crear un chat contigo mismo"
            )

        other = db.query(User).filter(User.id == other_user_id).first()
        if not other:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Buscar si ya existe un chat individual entre ambos
        # (conversación no-grupo donde ambos son participantes)
        subq = db.query(ConversationParticipant.conversation_id).filter(
            ConversationParticipant.user_id == user.id
        ).subquery()

        existente = db.query(Conversation).join(ConversationParticipant).filter(
            Conversation.es_grupo == False,
            Conversation.id.in_(subq),
            ConversationParticipant.user_id == other_user_id,
        ).first()

        if existente:
            return existente

        # Crear nueva conversación individual
        conv = Conversation(es_grupo=False, creado_por=user.id)
        db.add(conv)
        db.flush()

        db.add(ConversationParticipant(conversation_id=conv.id, user_id=user.id))
        db.add(ConversationParticipant(conversation_id=conv.id, user_id=other_user_id))
        db.commit()
        db.refresh(conv)
        return conv

    # ===== Crear conversación grupal =====
    @staticmethod
    def crear_chat_grupal(
        db: Session, user: User, nombre: str,
        descripcion: Optional[str], participant_ids: List[int]
    ) -> Conversation:
        # Validar que los participantes existan
        ids_unicos = list(set(participant_ids))
        if user.id in ids_unicos:
            ids_unicos.remove(user.id)

        usuarios = db.query(User).filter(User.id.in_(ids_unicos)).all()
        if len(usuarios) != len(ids_unicos):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uno o más participantes no existen"
            )

        conv = Conversation(
            es_grupo=True,
            nombre=nombre,
            descripcion=descripcion,
            creado_por=user.id,
        )
        db.add(conv)
        db.flush()

        # El creador es admin
        db.add(ConversationParticipant(
            conversation_id=conv.id, user_id=user.id, es_admin=True
        ))
        # Los demás son miembros normales
        for uid in ids_unicos:
            db.add(ConversationParticipant(
                conversation_id=conv.id, user_id=uid, es_admin=False
            ))

        # Mensaje de sistema
        db.add(Message(
            conversation_id=conv.id,
            sender_id=user.id,
            content=f"{user.full_name} creó el grupo '{nombre}'",
            tipo="sistema",
        ))

        db.commit()
        db.refresh(conv)
        return conv

    # ===== Verificar que el usuario participa en la conversación =====
    @staticmethod
    def _get_participacion(db: Session, conv_id: int, user_id: int) -> ConversationParticipant:
        part = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conv_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.activo == True,
        ).first()
        if not part:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No participas en esta conversación"
            )
        return part

    # ===== Enviar mensaje =====
    @staticmethod
    def enviar_mensaje(db: Session, user: User, conv_id: int, content: str) -> Message:
        ChatService._get_participacion(db, conv_id, user.id)

        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversación no encontrada"
            )

        mensaje = Message(
            conversation_id=conv_id,
            sender_id=user.id,
            content=content,
            tipo="texto",
        )
        db.add(mensaje)
        # Actualizar timestamp de la conversación
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(mensaje)
        return mensaje

    # ===== Listar conversaciones del usuario =====
    @staticmethod
    def listar_conversaciones(db: Session, user: User) -> List[dict]:
        participaciones = db.query(ConversationParticipant).filter(
            ConversationParticipant.user_id == user.id,
            ConversationParticipant.activo == True,
        ).all()

        resultado = []
        for part in participaciones:
            conv = db.query(Conversation).filter(
                Conversation.id == part.conversation_id
            ).first()
            if not conv:
                continue

            # Último mensaje
            ultimo_msg = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at.desc()).first()

            # Contar no leídos (mensajes después de last_read_at, no míos)
            last_read = _normalize_datetime(part.last_read_at)
            todos_mensajes = db.query(Message).filter(
                Message.conversation_id == conv.id,
                Message.sender_id != user.id,
            ).all()
            no_leidos = sum(
                1 for m in todos_mensajes
                if _normalize_datetime(m.created_at) > last_read
            )

            # Nombre a mostrar
            if conv.es_grupo:
                nombre_mostrar = conv.nombre
                otro_online = None
            else:
                # Buscar al otro participante
                otro_part = db.query(ConversationParticipant).filter(
                    ConversationParticipant.conversation_id == conv.id,
                    ConversationParticipant.user_id != user.id,
                ).first()
                if otro_part:
                    otro_user = db.query(User).filter(
                        User.id == otro_part.user_id
                    ).first()
                    nombre_mostrar = otro_user.full_name if otro_user else "Usuario"
                    otro_online = otro_user.is_online if otro_user else False
                else:
                    nombre_mostrar = "Usuario"
                    otro_online = False

            total_participantes = db.query(ConversationParticipant).filter(
                ConversationParticipant.conversation_id == conv.id,
                ConversationParticipant.activo == True,
            ).count()

            resultado.append({
                "id": conv.id,
                "es_grupo": conv.es_grupo,
                "nombre": nombre_mostrar,
                "ultimo_mensaje": ultimo_msg.content if ultimo_msg else None,
                "ultimo_mensaje_fecha": ultimo_msg.created_at if ultimo_msg else None,
                "mensajes_no_leidos": no_leidos,
                "total_participantes": total_participantes,
                "otro_usuario_online": otro_online,
            })

        # Ordenar por último mensaje (usando normalizador para evitar el error)
        resultado.sort(
            key=lambda c: _normalize_datetime(c["ultimo_mensaje_fecha"]),
            reverse=True
        )
        return resultado

    # ===== Obtener mensajes de una conversación =====
    @staticmethod
    def obtener_mensajes(
        db: Session, user: User, conv_id: int, limit: int = 50
    ) -> dict:
        ChatService._get_participacion(db, conv_id, user.id)

        mensajes = db.query(Message).filter(
            Message.conversation_id == conv_id
        ).order_by(Message.created_at.asc()).limit(limit).all()

        total = db.query(Message).filter(
            Message.conversation_id == conv_id
        ).count()

        mensajes_data = []
        for m in mensajes:
            sender = db.query(User).filter(User.id == m.sender_id).first()
            mensajes_data.append({
                "id": m.id,
                "conversation_id": m.conversation_id,
                "sender_id": m.sender_id,
                "sender_name": sender.full_name if sender else "Usuario",
                "content": m.content,
                "tipo": m.tipo,
                "created_at": m.created_at,
                "es_mio": m.sender_id == user.id,
            })

        return {
            "conversation_id": conv_id,
            "mensajes": mensajes_data,
            "total": total,
        }

    # ===== Marcar conversación como leída =====
    @staticmethod
    def marcar_como_leido(db: Session, user: User, conv_id: int) -> dict:
        part = ChatService._get_participacion(db, conv_id, user.id)
        part.last_read_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Conversación marcada como leída"}

    # ===== Contador total de no leídos =====
    @staticmethod
    def contar_no_leidos(db: Session, user: User) -> dict:
        participaciones = db.query(ConversationParticipant).filter(
            ConversationParticipant.user_id == user.id,
            ConversationParticipant.activo == True,
        ).all()

        total_no_leidos = 0
        convs_con_no_leidos = 0

        for part in participaciones:
            last_read = _normalize_datetime(part.last_read_at)
            mensajes = db.query(Message).filter(
                Message.conversation_id == part.conversation_id,
                Message.sender_id != user.id,
            ).all()
            no_leidos = sum(
                1 for m in mensajes
                if _normalize_datetime(m.created_at) > last_read
            )
            if no_leidos > 0:
                total_no_leidos += no_leidos
                convs_con_no_leidos += 1

        return {
            "total_no_leidos": total_no_leidos,
            "conversaciones_con_no_leidos": convs_con_no_leidos,
        }

    # ===== Detalle de conversación =====
    @staticmethod
    def detalle_conversacion(db: Session, user: User, conv_id: int) -> dict:
        mi_part = ChatService._get_participacion(db, conv_id, user.id)
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversación no encontrada"
            )

        participantes = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conv_id,
            ConversationParticipant.activo == True,
        ).all()

        parts_data = []
        for p in participantes:
            u = db.query(User).filter(User.id == p.user_id).first()
            if not u:
                continue
            parts_data.append({
                "user_id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "es_admin": p.es_admin,
                "is_online": u.is_online or False,
                "activo": p.activo,
            })

        return {
            "id": conv.id,
            "es_grupo": conv.es_grupo,
            "nombre": conv.nombre,
            "descripcion": conv.descripcion,
            "participantes": parts_data,
            "soy_admin": mi_part.es_admin,
        }
    
    # ===== GESTIÓN AVANZADA DE GRUPOS =====

    @staticmethod
    def _verificar_grupo_y_admin(db: Session, conv_id: int, user_id: int):
        """Verifica que sea un grupo y que el usuario sea admin."""
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        if not conv.es_grupo:
            raise HTTPException(
                status_code=400,
                detail="Esta operación solo aplica a grupos"
            )
        part = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conv_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.activo == True,
        ).first()
        if not part:
            raise HTTPException(status_code=403, detail="No participas en este grupo")
        if not part.es_admin:
            raise HTTPException(
                status_code=403,
                detail="Solo los administradores pueden hacer esto"
            )
        return conv

    @staticmethod
    def agregar_miembros(db: Session, user: User, conv_id: int, user_ids: List[int]) -> dict:
        conv = ChatService._verificar_grupo_y_admin(db, conv_id, user.id)
        agregados = []

        for uid in set(user_ids):
            nuevo_user = db.query(User).filter(User.id == uid).first()
            if not nuevo_user:
                continue

            # Ver si ya está (activo o inactivo)
            existente = db.query(ConversationParticipant).filter(
                ConversationParticipant.conversation_id == conv_id,
                ConversationParticipant.user_id == uid,
            ).first()

            if existente:
                if existente.activo:
                    continue  # ya está activo
                existente.activo = True  # reactivar si había salido
            else:
                db.add(ConversationParticipant(
                    conversation_id=conv_id, user_id=uid, es_admin=False
                ))
            agregados.append(nuevo_user.full_name)

        # Mensaje de sistema
        if agregados:
            db.add(Message(
                conversation_id=conv_id,
                sender_id=user.id,
                content=f"{user.full_name} agregó a: {', '.join(agregados)}",
                tipo="sistema",
            ))
        db.commit()
        return {"message": f"Agregados: {', '.join(agregados) if agregados else 'ninguno'}"}

    @staticmethod
    def quitar_miembro(db: Session, user: User, conv_id: int, user_id: int) -> dict:
        ChatService._verificar_grupo_y_admin(db, conv_id, user.id)

        if user_id == user.id:
            raise HTTPException(
                status_code=400,
                detail="Para salir del grupo usa la opción 'salir', no 'quitar'"
            )

        part = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conv_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.activo == True,
        ).first()
        if not part:
            raise HTTPException(status_code=404, detail="Ese usuario no está en el grupo")

        part.activo = False
        quitado = db.query(User).filter(User.id == user_id).first()
        db.add(Message(
            conversation_id=conv_id,
            sender_id=user.id,
            content=f"{user.full_name} quitó a {quitado.full_name if quitado else 'un usuario'}",
            tipo="sistema",
        ))
        db.commit()
        return {"message": "Miembro quitado del grupo"}

    @staticmethod
    def salir_del_grupo(db: Session, user: User, conv_id: int) -> dict:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv or not conv.es_grupo:
            raise HTTPException(status_code=400, detail="Esto solo aplica a grupos")

        part = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conv_id,
            ConversationParticipant.user_id == user.id,
            ConversationParticipant.activo == True,
        ).first()
        if not part:
            raise HTTPException(status_code=404, detail="No estás en este grupo")

        part.activo = False
        db.add(Message(
            conversation_id=conv_id,
            sender_id=user.id,
            content=f"{user.full_name} salió del grupo",
            tipo="sistema",
        ))
        db.commit()
        return {"message": "Saliste del grupo"}

    @staticmethod
    def renombrar_grupo(
        db: Session, user: User, conv_id: int, nombre: str, descripcion: Optional[str]
    ) -> dict:
        conv = ChatService._verificar_grupo_y_admin(db, conv_id, user.id)
        nombre_anterior = conv.nombre
        conv.nombre = nombre
        if descripcion is not None:
            conv.descripcion = descripcion
        db.add(Message(
            conversation_id=conv_id,
            sender_id=user.id,
            content=f"{user.full_name} cambió el nombre de '{nombre_anterior}' a '{nombre}'",
            tipo="sistema",
        ))
        db.commit()
        return {"message": f"Grupo renombrado a '{nombre}'"}

    @staticmethod
    def hacer_admin(db: Session, user: User, conv_id: int, user_id: int) -> dict:
        ChatService._verificar_grupo_y_admin(db, conv_id, user.id)

        part = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conv_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.activo == True,
        ).first()
        if not part:
            raise HTTPException(status_code=404, detail="Ese usuario no está en el grupo")

        part.es_admin = True
        nuevo_admin = db.query(User).filter(User.id == user_id).first()
        db.add(Message(
            conversation_id=conv_id,
            sender_id=user.id,
            content=f"{nuevo_admin.full_name if nuevo_admin else 'Un usuario'} ahora es administrador",
            tipo="sistema",
        ))
        db.commit()
        return {"message": "Usuario promovido a administrador"}