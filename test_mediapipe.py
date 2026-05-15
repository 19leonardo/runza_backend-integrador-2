"""
Test de detección de pose con MediaPipe API nueva (Tasks API).
Presiona 'q' para cerrar la ventana.
"""
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

# Configurar el detector de pose
base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_pose_presence_confidence=0.5,
    min_tracking_confidence=0.5,
)
detector = vision.PoseLandmarker.create_from_options(options)


def draw_landmarks_on_image(rgb_image, detection_result):
    """Dibuja los 33 puntos del cuerpo sobre la imagen."""
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)
    
    # Conexiones del cuerpo (qué punto se conecta con qué)
    connections = [
        # Cara
        (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
        # Brazos
        (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
        (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
        # Torso
        (11, 23), (12, 24), (23, 24),
        # Piernas
        (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
        (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
    ]

    for pose_landmarks in pose_landmarks_list:
        # Dibujar puntos
        for landmark in pose_landmarks:
            h, w, _ = annotated_image.shape
            x_px = int(landmark.x * w)
            y_px = int(landmark.y * h)
            cv2.circle(annotated_image, (x_px, y_px), 5, (0, 255, 0), -1)
        
        # Dibujar conexiones (líneas entre puntos)
        for start_idx, end_idx in connections:
            if start_idx < len(pose_landmarks) and end_idx < len(pose_landmarks):
                start = pose_landmarks[start_idx]
                end = pose_landmarks[end_idx]
                h, w, _ = annotated_image.shape
                start_point = (int(start.x * w), int(start.y * h))
                end_point = (int(end.x * w), int(end.y * h))
                cv2.line(annotated_image, start_point, end_point, (255, 255, 255), 2)
    
    return annotated_image


# Abrir cámara
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ No se pudo abrir la cámara")
    exit()

print("✅ Cámara abierta. Presiona 'q' para salir.")
print("   Párate lejos para que se vea todo tu cuerpo.")

frame_count = 0
while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    # Convertir BGR (OpenCV) a RGB (MediaPipe)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Crear objeto Image de MediaPipe
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    
    # Detectar pose (usar timestamp en ms)
    timestamp_ms = int(frame_count * (1000 / 30))  # asumiendo 30 fps
    detection_result = detector.detect_for_video(mp_image, timestamp_ms)
    frame_count += 1

    # Dibujar resultados sobre imagen original
    if detection_result.pose_landmarks:
        annotated = draw_landmarks_on_image(image_rgb, detection_result)
        # Convertir de vuelta a BGR para mostrar con OpenCV
        annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
        cv2.putText(annotated_bgr, "Cuerpo detectado", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow('RunZa - Test MediaPipe (q para salir)', annotated_bgr)
    else:
        cv2.putText(image, "Sin deteccion", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.imshow('RunZa - Test MediaPipe (q para salir)', image)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Cámara cerrada correctamente.")