from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.pose import (
    PoseAnalysisRequest,
    PoseAnalysisResponse,
    RepValidationRequest,
    RepValidationResponse,
)
from app.services.pose_service import (
    decode_base64_image,
    analizar_imagen_sentadilla,
)

router = APIRouter()


@router.post("/analyze", response_model=PoseAnalysisResponse)
def analizar_pose(
    data: PoseAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Recibe una imagen en base64 y devuelve análisis biomecánico.
    Por ahora solo soporta sentadilla. Próximamente: plancha, zancada, salto.
    """
    if data.ejercicio.lower() not in ["sentadilla", "squat"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ejercicio '{data.ejercicio}' aún no soportado. Disponible: sentadilla"
        )

    try:
        image = decode_base64_image(data.image_base64)
        if image is None:
            return PoseAnalysisResponse(
                exito=False,
                error="No se pudo decodificar la imagen. Verifica el formato base64."
            )

        resultado = analizar_imagen_sentadilla(image)
        return PoseAnalysisResponse(**resultado)

    except Exception as e:
        return PoseAnalysisResponse(
            exito=False,
            error=f"Error procesando imagen: {str(e)}"
        )


@router.post("/validate-rep", response_model=RepValidationResponse)
def validar_repeticion(
    data: RepValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Valida si una serie de frames analizados constituye una repetición válida.
    El frontend manda múltiples análisis (uno por frame) y este endpoint
    decide si la rep cuenta como correcta para otorgar puntos.
    """
    if not data.analisis_frames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron frames para validar"
        )

    total_frames = len(data.analisis_frames)
    frames_correctos = 0
    frames_con_errores_graves = 0
    alcanzo_profundidad = False
    fases_detectadas = set()

    for frame in data.analisis_frames:
        if frame.get("tecnica_correcta"):
            frames_correctos += 1

        errores = frame.get("errores", [])
        if any(e.get("severidad") == "alta" for e in errores):
            frames_con_errores_graves += 1

        fase = frame.get("fase", "")
        fases_detectadas.add(fase)

        if fase in ["sentadilla_parcial", "sentadilla_profunda"]:
            alcanzo_profundidad = True

    porcentaje_precision = round(
        (frames_correctos / total_frames) * 100, 1
    ) if total_frames > 0 else 0

    # Regla: rep válida si alcanzó profundidad Y al menos 60% de frames correctos
    rep_valida = alcanzo_profundidad and porcentaje_precision >= 60

    # Si tiene muchos frames con errores graves, no es válida aunque el % esté alto
    if frames_con_errores_graves >= (total_frames * 0.4):
        rep_valida = False

    # Mensaje motivacional
    if rep_valida:
        if porcentaje_precision >= 90:
            mensaje = "¡Repetición perfecta! Técnica impecable."
        elif porcentaje_precision >= 75:
            mensaje = "¡Excelente repetición!"
        else:
            mensaje = "Buena repetición, sigue mejorando."
    else:
        if not alcanzo_profundidad:
            mensaje = "Baja un poco más para que cuente la repetición."
        elif frames_con_errores_graves > 0:
            mensaje = "Cuida la técnica para evitar lesiones."
        else:
            mensaje = "Mantén la postura durante toda la repetición."

    # Por ahora puede completar ejercicio si tiene al menos 1 rep válida
    # (esto se va a refinar con el contador de reps por usuario después)
    puede_completar = rep_valida

    return RepValidationResponse(
        rep_valida=rep_valida,
        reps_correctas=1 if rep_valida else 0,
        reps_con_errores=0 if rep_valida else 1,
        porcentaje_precision=porcentaje_precision,
        puede_completar_ejercicio=puede_completar,
        mensaje=mensaje,
    )

@router.post("/check-position")
def verificar_posicion(
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Verifica solo el ENCUADRE del usuario, sin análisis biomecánico completo.
    Para usar cuando el usuario está ubicándose antes de empezar.
    Más rápido que /analyze.
    """
    image_base64 = data.get("image_base64", "")
    if not image_base64:
        raise HTTPException(400, "Falta image_base64")

    analizador = PoseService.get_analizador()
    img_bytes = base64.b64decode(image_base64)

    try:
        encuadre = analizador.solo_validar_encuadre(img_bytes)
        return encuadre
    except Exception as e:
        return {
            "valido": False,
            "mensaje_encuadre": f"No se detectó cuerpo: {str(e)}",
            "ajuste_recomendado": "centrate",
        }