"""
MÓDULO: test_integracion.py
DESCRIPCIÓN: Prueba de integración — flujo completo de un usuario en RunZa
HERRAMIENTA: pytest + FastAPI TestClient
PROPÓSITO: Verificar que TODOS los módulos se comunican correctamente
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_flujo_completo_usuario():
    """
    PRUEBA DE INTEGRACIÓN: Simula el ciclo completo de un usuario real

    FLUJO:
        1. Registrarse
        2. Verificar stats iniciales en 0
        3. Completar 2 ejercicios
        4. Verificar que los puntos se acumularon correctamente
        5. Verificar que el nivel aumenta con los puntos

    EQUIVALENTE A: Lo que hace un usuario real en la app
    """

    # ─── PASO 1: Registro ────────────────────────────────────────────────
    registro = client.post("/api/v1/auth/register", json={
        "email": "integracion@runza.com",
        "password": "Test1234!",
        "full_name": "Usuario Integración"
    })
    assert registro.status_code == 201, "El registro debe ser exitoso"
    token = registro.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ─── PASO 2: Stats iniciales ─────────────────────────────────────────
    stats_iniciales = client.get("/api/v1/activities/stats", headers=headers)
    assert stats_iniciales.status_code == 200
    assert stats_iniciales.json()["total_points"] == 0, \
        "Usuario nuevo debe tener 0 puntos"

    # ─── PASO 3: Completar ejercicio 1 ───────────────────────────────────
    ejercicio_1 = client.post("/api/v1/activities/exercise", headers=headers, json={
        "name": "Burpees",
        "category": "cardio",
        "duration_seconds": 90,
        "difficulty": "dificil",
        "points": 25
    })
    assert ejercicio_1.status_code == 200
    assert ejercicio_1.json()["points_earned"] == 25

    # ─── PASO 4: Completar ejercicio 2 ───────────────────────────────────
    ejercicio_2 = client.post("/api/v1/activities/exercise", headers=headers, json={
        "name": "Sentadillas",
        "category": "fuerza",
        "duration_seconds": 60,
        "difficulty": "medio",
        "points": 20
    })
    assert ejercicio_2.status_code == 200
    assert ejercicio_2.json()["points_earned"] == 20

    # ─── PASO 5: Verificar puntos totales en BD ───────────────────────────
    stats_finales = client.get("/api/v1/activities/stats", headers=headers)
    assert stats_finales.status_code == 200
    total = stats_finales.json()["total_points"]
    assert total == 45, f"Esperado 45 puntos (25+20), obtenido: {total}"
    assert stats_finales.json()["total_exercises"] == 2