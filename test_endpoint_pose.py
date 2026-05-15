"""
Test del endpoint REST de análisis de pose.
Toma una foto con tu cámara, la manda al backend y muestra el análisis.

Controles:
  SPACE = tomar foto y enviar al backend
  q = salir
"""
import cv2
import base64
import requests
import json

# CONFIGURACIÓN
API_URL = "http://localhost:8000/api/v1"
EMAIL = "jay@runza.com"
PASSWORD = "runza123"


def login() -> str:
    """Obtiene un token JWT haciendo login."""
    print("🔑 Haciendo login...")
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    if response.status_code != 200:
        print(f"❌ Login falló: {response.text}")
        exit()
    token = response.json()["access_token"]
    print("✅ Login exitoso\n")
    return token


def analizar_foto(image_bgr, token: str):
    """Convierte imagen a base64 y la envía al endpoint."""
    # Codificar imagen a JPEG
    _, buffer = cv2.imencode('.jpg', image_bgr)
    image_base64 = base64.b64encode(buffer).decode('utf-8')

    # Enviar al endpoint
    print("📤 Enviando imagen al backend...")
    response = requests.post(
        f"{API_URL}/pose/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "image_base64": image_base64,
            "ejercicio": "sentadilla"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None

    return response.json()


def mostrar_resultado(resultado: dict):
    """Muestra el análisis en consola de forma clara."""
    print("\n" + "=" * 60)
    print("📊 ANÁLISIS DE LA SENTADILLA")
    print("=" * 60)

    if not resultado.get("exito"):
        print(f"❌ {resultado.get('error', 'Error desconocido')}")
        return

    print(f"Ejercicio: {resultado['ejercicio']}")
    print(f"Fase: {resultado['fase']}")
    print(f"Puntuación: {resultado['puntuacion']}/100")
    print(f"Técnica correcta: {'✅ SÍ' if resultado['tecnica_correcta'] else '❌ NO'}")

    print("\n📐 Ángulos detectados:")
    for nombre, valor in resultado['angulos'].items():
        print(f"   • {nombre}: {valor}°")

    if resultado['puntos_correctos']:
        print("\n✅ Puntos correctos:")
        for p in resultado['puntos_correctos']:
            print(f"   • {p}")

    if resultado['errores']:
        print("\n🚨 Errores detectados:")
        for e in resultado['errores']:
            print(f"   • [{e['severidad'].upper()}] {e['mensaje']}")
            print(f"     → Corrección: {e['correccion']}")
            print(f"     → Referencia: {e['referencia']}")

    if resultado['sugerencias']:
        print("\n💡 Sugerencias menores:")
        for s in resultado['sugerencias']:
            print(f"   • {s['mensaje']}")

    print(f"\n💬 {resultado['mensaje']}")
    print("=" * 60 + "\n")


# === Programa principal ===
def main():
    token = login()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    print("📸 Cámara abierta")
    print("   Párate frente a la cámara haciendo sentadilla")
    print("   Presiona ESPACIO cuando estés en la posición a analizar")
    print("   Presiona 'q' para salir\n")

    while True:
        success, frame = cap.read()
        if not success:
            continue

        # Mostrar instrucciones en pantalla
        display = frame.copy()
        cv2.putText(display, "ESPACIO = analizar | Q = salir",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow('RunZa - Captura para analisis (ESPACIO=enviar, Q=salir)', display)

        key = cv2.waitKey(5) & 0xFF
        if key == ord('q'):
            break
        elif key == 32:  # SPACE
            print("\n📸 Foto capturada, enviando...")
            resultado = analizar_foto(frame, token)
            if resultado:
                mostrar_resultado(resultado)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()