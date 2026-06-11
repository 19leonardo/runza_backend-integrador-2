"""
Test del endpoint de registro de comida con foto.
Toma una foto con tu cámara (apunta a cualquier objeto/comida) y la registra.
"""
import cv2
import base64
import requests

API_URL = "http://localhost:8000/api/v1"

# Login
r = requests.post(f"{API_URL}/auth/login",
                  json={"email": "jay@runza.com", "password": "runza123"})
token = r.json()["access_token"]
print("Login OK")

# Capturar foto
cap = cv2.VideoCapture(0)
print("Apunta a algo con detalle (comida, objeto). ESPACIO=capturar, Q=salir")

while True:
    ok, frame = cap.read()
    if not ok:
        continue
    cv2.imshow("Captura comida (ESPACIO=enviar)", frame)
    key = cv2.waitKey(5) & 0xFF
    if key == ord('q'):
        break
    elif key == 32:  # ESPACIO
        _, buf = cv2.imencode('.jpg', frame)
        b64 = base64.b64encode(buf).decode('utf-8')
        resp = requests.post(
            f"{API_URL}/nutrition/meals",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "tipo_comida": "almuerzo",
                "descripcion": "Pollo con arroz y ensalada",
                "calorias_estimadas": 650,
                "foto_base64": b64
            }
        )
        print("\n=== RESPUESTA ===")
        print(resp.json())
        print("=================\n")

cap.release()
cv2.destroyAllWindows()