"""
Análisis de sentadilla mejorado:
- Suavizado temporal (sin jitter)
- Contador de repeticiones
- Sistema de 3 colores (verde/naranja/rojo)
- Mensajes motivacionales

Controles:
  q = salir
  r = reiniciar contador de reps
"""
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from app.services.pose_service import AnalizadorSentadilla, SmoothingFilter, RepCounter

# Configurar detector
base_options = mp_python.BaseOptions(model_asset_path='pose_landmarker.task')
options = mp_vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=mp_vision.RunningMode.VIDEO,
    num_poses=1,
    min_pose_detection_confidence=0.5,
)
detector = mp_vision.PoseLandmarker.create_from_options(options)

# Inicializar herramientas
smoother = SmoothingFilter(window_size=5)
rep_counter = RepCounter()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ No se pudo abrir la cámara")
    exit()

print("✅ Análisis avanzado de sentadilla activo.")
print("   Controles: 'q' = salir | 'r' = reiniciar reps\n")


def get_color_estado(puntuacion: int, tiene_errores_graves: bool):
    """Devuelve color BGR según puntuación y errores graves."""
    if tiene_errores_graves:
        return (0, 0, 255)  # rojo
    if puntuacion >= 50:
        return (0, 255, 0)  # verde
    if puntuacion >= 30:
        return (0, 165, 255)  # naranja
    return (0, 255, 255)  # amarillo

def get_mensaje_motivacional(reps_correctas: int, reps_incorrectas: int) -> str:
    """Mensaje según rendimiento."""
    total = reps_correctas + reps_incorrectas
    if total == 0:
        return "Listo para empezar! Haz una sentadilla."
    if total < 5:
        precision = (reps_correctas / total) * 100
        if precision == 100:
            return "Tecnica perfecta! Sigue asi"
        elif precision >= 70:
            return "Vas muy bien, cuida la tecnica"
        else:
            return "Concentrate en la tecnica antes de la velocidad"
    else:
        precision = (reps_correctas / total) * 100
        if precision >= 90:
            return f"EXCELENTE! {precision:.0f}% de precision"
        elif precision >= 70:
            return f"Buen trabajo - {precision:.0f}% de precision"
        else:
            return f"Sigue practicando - {precision:.0f}% de precision"


frame_count = 0
while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

    timestamp_ms = int(frame_count * (1000 / 30))
    result = detector.detect_for_video(mp_image, timestamp_ms)
    frame_count += 1

    h, w, _ = image.shape

    if result.pose_landmarks:
        # Aplicar suavizado para eliminar jitter
        landmarks_suavizados = smoother.smooth(result.pose_landmarks[0])

        # Analizar con landmarks suavizados
        analisis = AnalizadorSentadilla.analizar(landmarks_suavizados)
        rep_info = rep_counter.actualizar(analisis)

        # Color según estado
        color = get_color_estado(analisis["puntuacion"], len(analisis["errores"]) > 0)

        # Dibujar landmarks suavizados (puntos más pequeños y limpios)
        for lm in landmarks_suavizados:
            x_px, y_px = int(lm.x * w), int(lm.y * h)
            cv2.circle(image, (x_px, y_px), 3, color, -1)

        # === Panel superior izquierdo: datos técnicos ===
        cv2.rectangle(image, (5, 5), (300, 150), (0, 0, 0), -1)
        cv2.rectangle(image, (5, 5), (300, 150), color, 2)
        cv2.putText(image, f"Fase: {analisis['fase']}", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(image, f"Rodilla: {analisis['angulos']['rodilla_promedio']:.0f} deg",
                    (15, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(image, f"Cadera:  {analisis['angulos']['cadera_promedio']:.0f} deg",
                    (15, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(image, f"Puntuacion: {analisis['puntuacion']}/100", (15, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.putText(image, f"Estado: {rep_info['estado_rep']}", (15, 135),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # === Panel superior derecho: contador de reps ===
        panel_x = w - 220
        cv2.rectangle(image, (panel_x, 5), (w - 5, 130), (0, 0, 0), -1)
        cv2.rectangle(image, (panel_x, 5), (w - 5, 130), (255, 255, 255), 2)
        cv2.putText(image, "REPETICIONES", (panel_x + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        cv2.putText(image, f"Correctas: {rep_info['reps_correctas']}",
                    (panel_x + 10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(image, f"Con error: {rep_info['reps_incorrectas']}",
                    (panel_x + 10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(image, f"Total: {rep_info['total_reps']}",
                    (panel_x + 10, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1)

        # === Errores en pantalla ===
        y_pos = 180
        for error in analisis["errores"]:
            cv2.rectangle(image, (5, y_pos - 20), (w - 5, y_pos + 10), (0, 0, 100), -1)
            cv2.putText(image, f">> {error['mensaje']}", (15, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            y_pos += 35

        # === Mensaje motivacional inferior ===
        msg = get_mensaje_motivacional(rep_info["reps_correctas"], rep_info["reps_incorrectas"])
        cv2.rectangle(image, (5, h - 50), (w - 5, h - 10), (40, 40, 40), -1)
        cv2.putText(image, msg, (15, h - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    else:
        cv2.putText(image, "No se detecta cuerpo - acercate a la camara", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imshow('RunZa - Analisis Avanzado (q=salir, r=reset)', image)

    key = cv2.waitKey(5) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        rep_counter.reset()
        print("🔄 Contador de reps reiniciado")

cap.release()
cv2.destroyAllWindows()
print("✅ Sesión finalizada.")