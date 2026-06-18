"""
MÓDULO: test_pose.py
DESCRIPCIÓN: Pruebas del módulo de análisis de poses (MediaPipe) de RunZa
HERRAMIENTA: pytest + FastAPI TestClient
NOTA: En el entorno de CI no se instala MediaPipe (es una dependencia pesada
de visión por computadora). El servicio está diseñado para degradar a un
"modo demo" en ese caso, así que estas pruebas validan ese contrato sin
necesitar la librería real ni una imagen de cuerpo entero de verdad.
"""

import base64

import pytest


class TestSaludDelServicio:
    """Pruebas del endpoint GET /api/v1/pose/health"""

    def test_health_retorna_200_y_campos_esperados(self, cliente_autenticado):
        """
        CASO: Consultar el estado del servicio de poses
        ESPERADO: Status 200 con los campos de diagnóstico esperados
        """
        response = cliente_autenticado.get("/api/v1/pose/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "mediapipe_available" in data
        assert "exercises_loaded" in data
        assert isinstance(data["exercises_loaded"], int)


class TestListaDeEjercicios:
    """Pruebas del endpoint GET /api/v1/pose/exercises"""

    def test_exercises_retorna_200_con_estructura_correcta(self, cliente_autenticado):
        """
        CASO: Consultar la lista de ejercicios disponibles para detección
        ESPERADO: Status 200, success=True y una lista (puede estar vacía
        si la base de datos de pruebas no fue poblada con el seed)
        """
        response = cliente_autenticado.get("/api/v1/pose/exercises")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["exercises"], list)
        assert data["count"] == len(data["exercises"])


class TestAnalizarPose:
    """Pruebas del endpoint POST /api/v1/pose/analyze"""

    def test_analyze_sin_imagen_retorna_400(self, cliente_autenticado):
        """
        CASO: Enviar image_base64 vacío
        ESPERADO: Status 400 - el endpoint exige una imagen
        """
        response = cliente_autenticado.post("/api/v1/pose/analyze", json={
            "image_base64": ""
        })
        assert response.status_code == 400

    def test_analyze_sin_campo_image_base64_retorna_422(self, cliente_autenticado):
        """
        CASO: No enviar el campo image_base64 en absoluto
        ESPERADO: Status 422 - validación de Pydantic
        """
        response = cliente_autenticado.post("/api/v1/pose/analyze", json={})
        assert response.status_code == 422

    def test_analyze_modo_demo_sin_mediapipe(self, cliente_autenticado):
        """
        CASO: Enviar una imagen válida en un entorno sin MediaPipe instalado
        ESPERADO: Status 200 en "modo demo" (success=True, landmarks=None),
        en vez de un error 500. Este es el comportamiento de degradación
        elegante que el equipo implementó a propósito.
        """
        # Imagen mínima 1x1 PNG válida en base64, solo para pasar el chequeo
        # de "no vacío"; el contenido real no importa en modo demo.
        pixel_png_base64 = base64.b64encode(
            bytes.fromhex(
                "89504e470d0a1a0a0000000d4948445200000001000000010802000000"
                "907724de0000000c4944415478da6360606060000000050001a5f645"
                "400000000049454e44ae426082"
            )
        ).decode()

        response = cliente_autenticado.post("/api/v1/pose/analyze", json={
            "image_base64": pixel_png_base64
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
