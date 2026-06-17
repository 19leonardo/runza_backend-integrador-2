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


# ===== Conexiones del esqueleto humano (para overlay visual) =====
# Cada par representa una "línea" del esqueleto. El frontend usa esto
# para dibujar el cuerpo con código de colores.
POSE_CONNECTIONS = [
    # Tronco
    (11, 12), (11, 23), (12, 24), (23, 24),
    # Brazo izquierdo
    (11, 13), (13, 15),
    # Brazo derecho
    (12, 14), (14, 16),
    # Pierna izquierda
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
    # Pierna derecha
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
]


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

        # === Detectar fase ===
        if angulo_rodilla >= 155:
            resultado["fase"] = "de_pie"
        elif angulo_rodilla >= 140:
            resultado["fase"] = "descendiendo"
        elif angulo_rodilla >= 100:
            resultado["fase"] = "sentadilla_parcial"
        else:
            resultado["fase"] = "sentadilla_profunda"

        # === REGLA 1: Profundidad ===
        if resultado["fase"] in ["sentadilla_parcial", "sentadilla_profunda"]:
            resultado["puntos_correctos"].append("Sentadilla completada")
            resultado["puntuacion"] += 40
        elif resultado["fase"] == "descendiendo" and angulo_rodilla < 150:
            resultado["puntos_correctos"].append("Buen descenso")
            resultado["puntuacion"] += 25

        # === REGLA 2: Rodilla en valgo ===
        x_rodilla_der = landmarks[Landmark.RIGHT_KNEE].x
        x_tobillo_der = landmarks[Landmark.RIGHT_ANKLE].x
        x_rodilla_izq = landmarks[Landmark.LEFT_KNEE].x
        x_tobillo_izq = landmarks[Landmark.LEFT_ANKLE].x

        diff_der = abs(x_rodilla_der - x_tobillo_der)
        diff_izq = abs(x_rodilla_izq - x_tobillo_izq)
        diff_max = max(diff_der, diff_izq)

        if resultado["fase"] != "de_pie":
            if diff_max > 0.10:
                resultado["errores"].append({
                    "tipo": "rodilla_en_valgo_grave",
                    "severidad": "alta",
                    "mensaje": "Tus rodillas están colapsando hacia adentro",
                    "correccion": "Empuja las rodillas hacia afuera, alineadas con los pies",
                    "consecuencia": "Riesgo elevado en LCA (Hewett et al., 2017)",
                    "referencia": "Hewett, T. E., Myer, G. D., & Ford, K. R. (2017)",
                })
            elif diff_max > 0.07:
                resultado["sugerencias"].append({
                    "tipo": "leve_desalineacion_rodillas",
                    "mensaje": "Intenta abrir un poco más las rodillas",
                })
                resultado["puntuacion"] += 20
            else:
                resultado["puntos_correctos"].append("Rodillas bien alineadas")
                resultado["puntuacion"] += 30

        # === REGLA 3: Espalda ===
        if resultado["fase"] in ["sentadilla_parcial", "sentadilla_profunda"]:
            if angulo_cadera < 60:
                resultado["errores"].append({
                    "tipo": "espalda_redondeada_grave",
                    "severidad": "alta",
                    "mensaje": "Tu espalda está demasiado inclinada",
                    "correccion": "Mantén el pecho arriba y la espalda recta",
                    "consecuencia": "Estrés lumbar elevado (Behm et al., 2017)",
                    "referencia": "Behm, D. G., et al. (2017)",
                })
            elif angulo_cadera < 75:
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

        # ============================================================
        # === DATOS NUEVOS PARA EL OVERLAY VISUAL DEL FRONTEND ===
        # ============================================================
        landmarks_norm = AnalizadorSentadilla.extraer_landmarks_normalizados(landmarks)
        conexiones = AnalizadorSentadilla.calcular_estado_conexiones(
            resultado["errores"], resultado["sugerencias"]
        )
        landmarks_norm = AnalizadorSentadilla.actualizar_estados_landmarks(
            landmarks_norm, conexiones
        )
        encuadre = AnalizadorSentadilla.validar_encuadre(landmarks)
        feedback_verbal = AnalizadorSentadilla.generar_feedback_verbal(
            resultado["fase"], resultado["errores"], resultado["sugerencias"]
        )

        resultado["landmarks"] = landmarks_norm
        resultado["conexiones"] = conexiones
        resultado["encuadre"] = encuadre
        resultado["feedback_verbal"] = feedback_verbal

        return resultado

    # ============================================================
    # === MÉTODOS AUXILIARES PARA EL OVERLAY VISUAL ===
    # ============================================================

    @staticmethod
    def extraer_landmarks_normalizados(landmarks) -> list:
        """
        Convierte los landmarks de MediaPipe en lista lista para el frontend.
        Las coordenadas vienen ya normalizadas (0 a 1) por MediaPipe.
        """
        resultado = []
        for idx, lm in enumerate(landmarks):
            resultado.append({
                "id": idx,
                "x": round(float(lm.x), 4),
                "y": round(float(lm.y), 4),
                "visibility": round(float(getattr(lm, 'visibility', 1.0)), 3),
                "estado": "ok",  # se actualiza después según los errores
            })
        return resultado

    @staticmethod
    def calcular_estado_conexiones(errores: list, sugerencias: list) -> list:
        """
        Asigna estado (ok/atencion/error) a cada conexión del esqueleto
        según los errores y sugerencias detectados.
        """
        # Mapeo: tipo de error/sugerencia → conexiones afectadas
        conexiones_afectadas = {
            "rodilla_en_valgo_grave": [(23, 25), (24, 26), (25, 27), (26, 28)],
            "leve_desalineacion_rodillas": [(23, 25), (24, 26), (25, 27), (26, 28)],
            "espalda_redondeada_grave": [(11, 23), (12, 24)],
            "leve_inclinacion": [(11, 23), (12, 24)],
        }

        # Por defecto todas las conexiones están "ok"
        estados = {par: "ok" for par in POSE_CONNECTIONS}

        # Aplicar errores graves → estado "error"
        for error in errores:
            tipo = error.get("tipo", "")
            for par in conexiones_afectadas.get(tipo, []):
                estados[par] = "error"

        # Aplicar sugerencias → estado "atencion" (sin sobrescribir errores)
        for sugerencia in sugerencias:
            tipo = sugerencia.get("tipo", "")
            for par in conexiones_afectadas.get(tipo, []):
                if estados.get(par) != "error":
                    estados[par] = "atencion"

        return [
            {"desde": d, "hasta": h, "estado": estados[(d, h)]}
            for (d, h) in POSE_CONNECTIONS
        ]

    @staticmethod
    def actualizar_estados_landmarks(landmarks_norm: list, conexiones: list) -> list:
        """
        Marca cada landmark con el peor estado de sus conexiones.
        Así los puntos también cambian de color, no solo las líneas.
        """
        prioridad = {"ok": 0, "atencion": 1, "error": 2}
        estado_por_id = {lm["id"]: "ok" for lm in landmarks_norm}

        for c in conexiones:
            for id_lm in (c["desde"], c["hasta"]):
                actual = estado_por_id.get(id_lm, "ok")
                if prioridad[c["estado"]] > prioridad[actual]:
                    estado_por_id[id_lm] = c["estado"]

        for lm in landmarks_norm:
            lm["estado"] = estado_por_id[lm["id"]]
        return landmarks_norm

    @staticmethod
    def validar_encuadre(landmarks) -> dict:
        """
        Verifica si el usuario está bien posicionado para entrenar.
        Devuelve sugerencias específicas si no lo está.
        """
        UMBRAL_VIS = 0.5

        cabeza_visible = landmarks[Landmark.NOSE].visibility > UMBRAL_VIS
        hombros_visibles = (
            landmarks[Landmark.LEFT_SHOULDER].visibility > UMBRAL_VIS
            and landmarks[Landmark.RIGHT_SHOULDER].visibility > UMBRAL_VIS
        )
        caderas_visibles = (
            landmarks[Landmark.LEFT_HIP].visibility > UMBRAL_VIS
            and landmarks[Landmark.RIGHT_HIP].visibility > UMBRAL_VIS
        )
        rodillas_visibles = (
            landmarks[Landmark.LEFT_KNEE].visibility > UMBRAL_VIS
            and landmarks[Landmark.RIGHT_KNEE].visibility > UMBRAL_VIS
        )
        pies_visibles = (
            landmarks[Landmark.LEFT_ANKLE].visibility > UMBRAL_VIS
            and landmarks[Landmark.RIGHT_ANKLE].visibility > UMBRAL_VIS
        )

        cuerpo_completo = (
            cabeza_visible and hombros_visibles
            and caderas_visibles and rodillas_visibles and pies_visibles
        )

        # ¿Está de perfil? Si los hombros están muy juntos en X, está de lado
        dx_hombros = abs(landmarks[Landmark.LEFT_SHOULDER].x - landmarks[Landmark.RIGHT_SHOULDER].x)
        vista_lateral = dx_hombros < 0.10

        # Decidir ajuste recomendado
        ajuste = None
        mensaje = "Posición correcta, puedes empezar."

        if not cabeza_visible and not pies_visibles:
            ajuste = "alejate"
            mensaje = "Aléjate de la cámara, debe verse tu cuerpo completo."
        elif not pies_visibles:
            ajuste = "alejate"
            mensaje = "Aléjate un poco, necesitamos ver tus pies."
        elif not cabeza_visible:
            ajuste = "centrate"
            mensaje = "Centra la cámara para verte completo."
        elif not vista_lateral:
            ajuste = "ponte_de_lado"
            mensaje = "Ponte de lado a la cámara para mejor análisis."
        elif not cuerpo_completo:
            ajuste = "centrate"
            mensaje = "Ajusta la posición para que se vea todo tu cuerpo."

        return {
            "valido": cuerpo_completo and vista_lateral,
            "cuerpo_completo": cuerpo_completo,
            "vista_lateral": vista_lateral,
            "pies_visibles": pies_visibles,
            "ajuste_recomendado": ajuste,
            "mensaje_encuadre": mensaje,
        }

    @staticmethod
    def generar_feedback_verbal(fase: str, errores: list, sugerencias: list) -> str:
        """
        Mensaje natural tipo entrenador, para mostrar/leer al usuario.
        Prioriza errores graves > sugerencias > mensajes positivos.
        """
        # Prioridad 1: errores graves
        if errores:
            return f"⚠ {errores[0]['mensaje']}"

        # Prioridad 2: sugerencias leves
        if sugerencias:
            return sugerencias[0]['mensaje']

        # Prioridad 3: mensajes positivos según fase
        if fase == "sentadilla_profunda":
            return "¡Excelente flexión! Espalda recta, muy bien."
        if fase == "sentadilla_parcial":
            return "Buena bajada, sigue así."
        if fase == "descendiendo":
            return "Vas bien, continúa bajando."
        if fase == "de_pie":
            return "Listo para la próxima repetición."
        return "Mantén el ritmo."


# ===== Validación de encuadre SIN análisis completo (rápido) =====
def solo_validar_encuadre(image_bytes_or_path) -> dict:
    """
    Versión rápida del análisis: solo verifica si el usuario está bien
    posicionado, sin analizar la técnica del ejercicio.
    Útil ANTES de empezar el entrenamiento (modo guía).
    """
    if isinstance(image_bytes_or_path, str):
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
            "valido": False,
            "mensaje_encuadre": "No se pudo cargar la imagen.",
            "ajuste_recomendado": "centrate",
        }

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    detector = get_detector()
    result = detector.detect(mp_image)

    if not result.pose_landmarks:
        return {
            "valido": False,
            "cuerpo_completo": False,
            "vista_lateral": False,
            "pies_visibles": False,
            "ajuste_recomendado": "centrate",
            "mensaje_encuadre": "No se detectó cuerpo. Asegúrate de estar visible.",
        }

    landmarks = result.pose_landmarks[0]
    return AnalizadorSentadilla.validar_encuadre(landmarks)


# ===== Función principal exportable =====
def analizar_imagen_sentadilla(image_bytes_or_path) -> dict:
    """
    Función principal. Recibe imagen y devuelve análisis completo
    incluyendo overlay visual (landmarks, conexiones, encuadre).
    Acepta: bytes, path a archivo, o array numpy.
    """
    if isinstance(image_bytes_or_path, str):
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

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    detector = get_detector()
    result = detector.detect(mp_image)

    if not result.pose_landmarks:
        return {
            "exito": False,
            "error": "No se detectó cuerpo en la imagen. Asegúrate de estar visible.",
        }

    landmarks = result.pose_landmarks[0]
    analisis = AnalizadorSentadilla.analizar(landmarks)
    analisis["exito"] = True

    return analisis


# ===== Filtro de suavizado =====
class SmoothingFilter:
    """
    Filtro de suavizado para eliminar el 'temblor' (jitter) de MediaPipe.
    Promedia las últimas N detecciones para dar fluidez.
    """
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.history = {}

    def smooth(self, landmarks):
        smoothed = []
        for i, lm in enumerate(landmarks):
            if i not in self.history:
                self.history[i] = deque(maxlen=self.window_size)
            self.history[i].append((lm.x, lm.y, lm.z))

            avg_x = sum(p[0] for p in self.history[i]) / len(self.history[i])
            avg_y = sum(p[1] for p in self.history[i]) / len(self.history[i])
            avg_z = sum(p[2] for p in self.history[i]) / len(self.history[i])

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
        self.estado = "esperando"
        self.reps_correctas = 0
        self.reps_incorrectas = 0
        self.rep_actual_tiene_error = False
        self.angulo_minimo_rep = 180

    def actualizar(self, analisis: dict) -> dict:
        fase = analisis["fase"]
        angulo_rodilla = analisis["angulos"]["rodilla_promedio"]
        tiene_error_ahora = len(analisis["errores"]) > 0

        if self.estado != "esperando":
            self.angulo_minimo_rep = min(self.angulo_minimo_rep, angulo_rodilla)

        if tiene_error_ahora and self.estado != "esperando":
            self.rep_actual_tiene_error = True

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
                if self.angulo_minimo_rep <= 140 and not self.rep_actual_tiene_error:
                    self.reps_correctas += 1
                else:
                    self.reps_incorrectas += 1

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
        self.__init__()