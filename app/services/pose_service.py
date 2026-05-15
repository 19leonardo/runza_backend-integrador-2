"""
Servicio de análisis biomecánico con MediaPipe.
Implementa la detección de errores técnicos mediante visión por computadora.
Basado en literatura: Hewett et al. (2017), Behm et al. (2017), Myer et al. (2020).
"""
import math
import base64
from typing import Optional
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from collections import deque



# ===== Constantes de Landmarks (MediaPipe Pose) =====
# Mapeo de los 33 puntos del cuerpo. Solo usamos los relevantes para sentadilla.
class Landmark:
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


# ===== Detector global (se carga una sola vez) =====
_detector = None

def get_detector():
    """Inicializa MediaPipe una vez y reutiliza la instancia."""
    global _detector
    if _detector is None:
        base_options = mp_python.BaseOptions(model_asset_path='pose_landmarker.task')
        options = mp_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
        )
        _detector = mp_vision.PoseLandmarker.create_from_options(options)
    return _detector


# ===== Utilidades matemáticas =====
def calcular_angulo(a, b, c) -> float:
    """
    Calcula el ángulo formado por tres puntos (a, b, c) con vértice en b.
    Cada punto es un landmark con atributos .x, .y
    Devuelve ángulo en grados (0-180).
    """
    angulo_rad = math.atan2(c.y - b.y, c.x - b.x) - math.atan2(a.y - b.y, a.x - b.x)
    angulo_deg = abs(angulo_rad * 180.0 / math.pi)
    if angulo_deg > 180.0:
        angulo_deg = 360.0 - angulo_deg
    return round(angulo_deg, 2)


def decode_base64_image(base64_string: str) -> np.ndarray:
    """Convierte string base64 (que envía el frontend) a array de imagen."""
    # Si viene con prefijo "data:image/jpeg;base64,", lo quitamos
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    img_data = base64.b64decode(base64_string)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img


# ===== Análisis específico de sentadilla =====
class AnalizadorSentadilla:
    """
    Analiza una sentadilla con enfoque motivador.
    Premia el esfuerzo y progreso, penaliza SOLO errores que generen riesgo real de lesión.
    Basado en Hewett et al. (2017), Behm et al. (2017).
    """

    @staticmethod
    def analizar(landmarks) -> dict:
        resultado = {
            "ejercicio": "sentadilla",
            "fase": "desconocida",
            "angulos": {},
            "errores": [],
            "sugerencias": [],
            "puntos_correctos": [],
            "tecnica_correcta": False,
            "puntuacion": 0,
            "mensaje": "",
            "feedback_visual": [],
        }

        # === Calcular ángulos ===
        angulo_rodilla_der = calcular_angulo(
            landmarks[Landmark.RIGHT_HIP],
            landmarks[Landmark.RIGHT_KNEE],
            landmarks[Landmark.RIGHT_ANKLE],
        )
        angulo_rodilla_izq = calcular_angulo(
            landmarks[Landmark.LEFT_HIP],
            landmarks[Landmark.LEFT_KNEE],
            landmarks[Landmark.LEFT_ANKLE],
        )
        angulo_rodilla = (angulo_rodilla_der + angulo_rodilla_izq) / 2

        angulo_cadera_der = calcular_angulo(
            landmarks[Landmark.RIGHT_SHOULDER],
            landmarks[Landmark.RIGHT_HIP],
            landmarks[Landmark.RIGHT_KNEE],
        )
        angulo_cadera_izq = calcular_angulo(
            landmarks[Landmark.LEFT_SHOULDER],
            landmarks[Landmark.LEFT_HIP],
            landmarks[Landmark.LEFT_KNEE],
        )
        angulo_cadera = (angulo_cadera_der + angulo_cadera_izq) / 2

        resultado["angulos"] = {
            "rodilla_derecha": angulo_rodilla_der,
            "rodilla_izquierda": angulo_rodilla_izq,
            "rodilla_promedio": round(angulo_rodilla, 2),
            "cadera_promedio": round(angulo_cadera, 2),
        }

        # === Detectar fase (umbrales más permisivos) ===
        if angulo_rodilla >= 155:
            resultado["fase"] = "de_pie"
        elif angulo_rodilla >= 140:
            resultado["fase"] = "descendiendo"
        elif angulo_rodilla >= 100:
            resultado["fase"] = "sentadilla_parcial"
        else:
            resultado["fase"] = "sentadilla_profunda"

        # === REGLA 1: Profundidad — más permisiva ===
        # Antes 130°, ahora 140° = ya cuenta como sentadilla
        if resultado["fase"] in ["sentadilla_parcial", "sentadilla_profunda"]:
            resultado["puntos_correctos"].append("Sentadilla completada")
            resultado["puntuacion"] += 40
        elif resultado["fase"] == "descendiendo" and angulo_rodilla < 150:
            # Está bajando bien, dar puntos parciales
            resultado["puntos_correctos"].append("Buen descenso")
            resultado["puntuacion"] += 25

        # === REGLA 2: Rodilla en valgo — solo penalizar si es GRAVE ===
        # Umbral más permisivo: antes 5%, ahora 10%
        x_rodilla_der = landmarks[Landmark.RIGHT_KNEE].x
        x_tobillo_der = landmarks[Landmark.RIGHT_ANKLE].x
        x_rodilla_izq = landmarks[Landmark.LEFT_KNEE].x
        x_tobillo_izq = landmarks[Landmark.LEFT_ANKLE].x

        diff_der = abs(x_rodilla_der - x_tobillo_der)
        diff_izq = abs(x_rodilla_izq - x_tobillo_izq)
        diff_max = max(diff_der, diff_izq)

        if resultado["fase"] != "de_pie":
            if diff_max > 0.10:  # GRAVE: rodilla muy colapsada
                resultado["errores"].append({
                    "tipo": "rodilla_en_valgo_grave",
                    "severidad": "alta",
                    "mensaje": "Tus rodillas están colapsando hacia adentro",
                    "correccion": "Empuja las rodillas hacia afuera, alineadas con los pies",
                    "consecuencia": "Riesgo elevado en LCA (Hewett et al., 2017)",
                    "referencia": "Hewett, T. E., Myer, G. D., & Ford, K. R. (2017)",
                })
            elif diff_max > 0.07:  # LEVE: pequeña desalineación
                resultado["sugerencias"].append({
                    "tipo": "leve_desalineacion_rodillas",
                    "mensaje": "Intenta abrir un poco más las rodillas",
                })
                resultado["puntuacion"] += 20
            else:
                resultado["puntos_correctos"].append("Rodillas bien alineadas")
                resultado["puntuacion"] += 30

        # === REGLA 3: Espalda — solo penalizar si está muy mal ===
        # Antes <70°, ahora <60° (más tolerante)
        if resultado["fase"] in ["sentadilla_parcial", "sentadilla_profunda"]:
            if angulo_cadera < 60:  # GRAVE
                resultado["errores"].append({
                    "tipo": "espalda_redondeada_grave",
                    "severidad": "alta",
                    "mensaje": "Tu espalda está demasiado inclinada",
                    "correccion": "Mantén el pecho arriba y la espalda recta",
                    "consecuencia": "Estrés lumbar elevado (Behm et al., 2017)",
                    "referencia": "Behm, D. G., et al. (2017)",
                })
            elif angulo_cadera < 75:  # LEVE
                resultado["sugerencias"].append({
                    "tipo": "leve_inclinacion",
                    "mensaje": "Intenta mantener el pecho un poco más arriba",
                })
                resultado["puntuacion"] += 20
            else:
                resultado["puntos_correctos"].append("Postura de espalda correcta")
                resultado["puntuacion"] += 30

        # === Decisión final: filosofía motivacional ===
        tiene_error_grave = len(resultado["errores"]) > 0
        
        if not tiene_error_grave and resultado["puntuacion"] >= 50:
            resultado["tecnica_correcta"] = True
            if resultado["puntuacion"] >= 80:
                resultado["mensaje"] = "¡Técnica excelente! Sigue así."
            else:
                resultado["mensaje"] = "¡Buen trabajo! Vas por buen camino."
        elif tiene_error_grave:
            resultado["tecnica_correcta"] = False
            resultado["mensaje"] = "Cuida la técnica para evitar lesiones."
        else:
            resultado["mensaje"] = "Continúa el movimiento..."

        return resultado

# ===== Función principal exportable =====
def analizar_imagen_sentadilla(image_bytes_or_path) -> dict:
    """
    Función principal. Recibe imagen y devuelve análisis completo.
    Acepta: bytes, path a archivo, o array numpy.
    """
    # Cargar imagen
    if isinstance(image_bytes_or_path, str):
        # Es un path
        image = cv2.imread(image_bytes_or_path)
    elif isinstance(image_bytes_or_path, bytes):
        np_arr = np.frombuffer(image_bytes_or_path, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    elif isinstance(image_bytes_or_path, np.ndarray):
        image = image_bytes_or_path
    else:
        raise ValueError("Tipo de imagen no soportado")

    if image is None:
        return {
            "exito": False,
            "error": "No se pudo cargar la imagen",
        }

    # Convertir BGR → RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Detectar pose
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    detector = get_detector()
    result = detector.detect(mp_image)

    if not result.pose_landmarks:
        return {
            "exito": False,
            "error": "No se detectó cuerpo en la imagen. Asegúrate de estar visible.",
        }

    # Analizar primera persona detectada
    landmarks = result.pose_landmarks[0]
    analisis = AnalizadorSentadilla.analizar(landmarks)
    analisis["exito"] = True

    return analisis

class SmoothingFilter:
    """
    Filtro de suavizado para eliminar el 'temblor' (jitter) de MediaPipe.
    Promedia las últimas N detecciones para dar fluidez.
    """
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.history = {}  # un deque por cada landmark index

    def smooth(self, landmarks):
        """Recibe los 33 landmarks y devuelve versión suavizada."""
        smoothed = []
        for i, lm in enumerate(landmarks):
            if i not in self.history:
                self.history[i] = deque(maxlen=self.window_size)
            self.history[i].append((lm.x, lm.y, lm.z))

            # Promedio
            avg_x = sum(p[0] for p in self.history[i]) / len(self.history[i])
            avg_y = sum(p[1] for p in self.history[i]) / len(self.history[i])
            avg_z = sum(p[2] for p in self.history[i]) / len(self.history[i])

            # Crear objeto landmark suavizado
            smoothed.append(type('SmoothedLandmark', (), {
                'x': avg_x, 'y': avg_y, 'z': avg_z,
                'visibility': getattr(lm, 'visibility', 1.0),
            })())
        return smoothed


# ===== Contador de repeticiones =====
class RepCounter:
    """
    Cuenta repeticiones completas de sentadillas analizando el ciclo:
    de_pie → bajando → fondo → subiendo → de_pie = 1 rep
    """
    def __init__(self):
        self.estado = "esperando"  # esperando | bajando | fondo | subiendo
        self.reps_correctas = 0
        self.reps_incorrectas = 0
        self.rep_actual_tiene_error = False
        self.angulo_minimo_rep = 180  # menor ángulo alcanzado en la rep actual

    def actualizar(self, analisis: dict) -> dict:
        """Actualiza el estado del contador según el análisis actual."""
        fase = analisis["fase"]
        angulo_rodilla = analisis["angulos"]["rodilla_promedio"]
        tiene_error_ahora = len(analisis["errores"]) > 0

        # Trackear ángulo mínimo de la rep actual
        if self.estado != "esperando":
            self.angulo_minimo_rep = min(self.angulo_minimo_rep, angulo_rodilla)

        # Si en cualquier momento hubo error, marcar la rep como incorrecta
        if tiene_error_ahora and self.estado != "esperando":
            self.rep_actual_tiene_error = True

        # Máquina de estados
        if self.estado == "esperando" and fase == "descendiendo":
            self.estado = "bajando"
            self.angulo_minimo_rep = angulo_rodilla
            self.rep_actual_tiene_error = tiene_error_ahora

        elif self.estado == "bajando":
            if fase in ["sentadilla_parcial", "sentadilla_profunda"]:
                self.estado = "fondo"

        elif self.estado == "fondo":
            if fase == "descendiendo" and angulo_rodilla > self.angulo_minimo_rep + 10:
                self.estado = "subiendo"

        elif self.estado == "subiendo":
            if fase == "de_pie":
                # ¡Rep completa!
                if self.angulo_minimo_rep <= 140 and not self.rep_actual_tiene_error:
                    self.reps_correctas += 1
                else:
                    self.reps_incorrectas += 1

                # Reset para próxima rep
                self.estado = "esperando"
                self.rep_actual_tiene_error = False
                self.angulo_minimo_rep = 180

        return {
            "estado_rep": self.estado,
            "reps_correctas": self.reps_correctas,
            "reps_incorrectas": self.reps_incorrectas,
            "total_reps": self.reps_correctas + self.reps_incorrectas,
        }

    def reset(self):
        """Reinicia el contador."""
        self.__init__()