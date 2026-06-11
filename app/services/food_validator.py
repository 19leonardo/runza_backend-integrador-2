"""
Validador de comida con arquitectura escalable (patrón Strategy).

HOY: validación básica por detección de objetos (MediaPipe).
FUTURO (1+ año): se puede agregar un modelo propio de clasificación
de alimentos SIN modificar el resto del código.

Para cambiar de validador, solo se cambia la línea:
    validador_activo = ValidadorBasicoObjetos()
por:
    validador_activo = ValidadorModeloIA()
"""
from abc import ABC, abstractmethod
import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


class ResultadoValidacion:
    """Resultado estándar que devuelve cualquier validador."""
    def __init__(self, es_valido: bool, metodo: str, detalle: str, confianza: float = 0.0):
        self.es_valido = es_valido
        self.metodo = metodo
        self.detalle = detalle
        self.confianza = confianza


class FoodValidator(ABC):
    """
    Interfaz abstracta. Cualquier validador (hoy o futuro)
    debe implementar el método validar().
    """
    @abstractmethod
    def validar(self, image_bgr) -> ResultadoValidacion:
        pass


class ValidadorBasicoObjetos(FoodValidator):
    """
    Validador ACTUAL: verifica que la imagen contenga objetos reales
    (no pantalla negra, no imagen vacía) usando detección básica.

    No afirma que sea comida (eso requeriría un modelo entrenado).
    Solo verifica presencia de contenido visual significativo.
    """

    def validar(self, image_bgr) -> ResultadoValidacion:
        if image_bgr is None:
            return ResultadoValidacion(
                False, "deteccion_objetos",
                "No se pudo leer la imagen", 0.0
            )

        # 1. Verificar que no sea imagen vacía/negra/uniforme
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        desviacion = float(np.std(gray))

        if desviacion < 15:
            # Muy poca variación = imagen vacía, negra o pantalla uniforme
            return ResultadoValidacion(
                False, "deteccion_objetos",
                "La imagen parece vacía o sin contenido real", 0.1
            )

        # 2. Verificar que tenga bordes/detalles (comida tiene texturas)
        bordes = cv2.Canny(gray, 50, 150)
        densidad_bordes = float(np.sum(bordes > 0)) / bordes.size

        if densidad_bordes < 0.02:
            return ResultadoValidacion(
                False, "deteccion_objetos",
                "La imagen no tiene suficiente detalle visual", 0.3
            )

        # 3. Verificar variedad de color (la comida suele tener colores variados)
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        saturacion_promedio = float(np.mean(hsv[:, :, 1]))

        confianza = min(0.95, (desviacion / 80) + densidad_bordes + (saturacion_promedio / 255))

        return ResultadoValidacion(
            True, "deteccion_objetos",
            f"Contenido visual válido detectado (variación: {desviacion:.0f}, "
            f"detalle: {densidad_bordes:.2%})",
            round(confianza, 2)
        )


class ValidadorModeloIA(FoodValidator):
    """
    Validador FUTURO (placeholder, NO implementado aún).

    Cuando tengas tu dataset y modelo entrenado (1+ año),
    implementas este método y cambias la configuración.
    El resto del sistema NO se entera del cambio.
    """
    def validar(self, image_bgr) -> ResultadoValidacion:
        raise NotImplementedError(
            "El modelo de IA propio aún no está implementado. "
            "Planificado para versión futura. Usa ValidadorBasicoObjetos."
        )


# ===== CONFIGURACIÓN: cambiar aquí cuando tengas el modelo nuevo =====
validador_activo: FoodValidator = ValidadorBasicoObjetos()


def validar_foto_comida(image_bytes: bytes) -> ResultadoValidacion:
    """
    Función pública que usa el validador configurado.
    El endpoint llama a esto sin saber qué validador hay detrás.
    """
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return validador_activo.validar(image)