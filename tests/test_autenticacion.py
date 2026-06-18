"""
MÓDULO: test_autenticacion.py
DESCRIPCIÓN: Pruebas unitarias del sistema de autenticación de RunZa
HERRAMIENTA: pytest + FastAPI TestClient
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRegistro:
    """Pruebas del endpoint POST /api/v1/auth/register"""

    def test_registro_exitoso_retorna_201_y_token(self):
        """
        CASO: Usuario nuevo con datos válidos
        ESPERADO: Status 201 y access_token en respuesta
        """
        response = client.post("/api/v1/auth/register", json={
            "email": "nuevo@runza.com",
            "password": "Password123!",
            "full_name": "Nuevo Usuario"
        })
        assert response.status_code == 201
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert data["tokens"]["token_type"] == "bearer"

    def test_registro_email_duplicado_retorna_400(self):
        """
        CASO: Intentar registrar el mismo email dos veces
        ESPERADO: Status 400 con mensaje de error
        """
        datos = {
            "email": "duplicado@runza.com",
            "password": "Password123!",
            "full_name": "Usuario Duplicado"
        }
        client.post("/api/v1/auth/register", json=datos)
        response = client.post("/api/v1/auth/register", json=datos)

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_registro_sin_email_retorna_422(self):
        """
        CASO: Enviar datos incompletos (sin email)
        ESPERADO: Status 422 Unprocessable Entity (validación Pydantic)
        """
        response = client.post("/api/v1/auth/register", json={
            "password": "Password123!",
            "full_name": "Sin Email"
        })
        assert response.status_code == 422


class TestLogin:
    """Pruebas del endpoint POST /api/v1/auth/login"""

    def test_login_credenciales_validas_retorna_token(self, usuario_registrado):
        """
        CASO: Login con email y contraseña correctos
        ESPERADO: Status 200 y tokens de acceso
        """
        response = client.post("/api/v1/auth/login", json={
            "email": "test_runza@prueba.com",
            "password": "Test1234!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    def test_login_password_incorrecta_retorna_401(self, usuario_registrado):
        """
        CASO: Login con contraseña incorrecta
        ESPERADO: Status 401 Unauthorized
        """
        response = client.post("/api/v1/auth/login", json={
            "email": "test_runza@prueba.com",
            "password": "ContraseñaIncorrecta!"
        })
        assert response.status_code == 401

    def test_login_usuario_inexistente_retorna_401(self):
        """
        CASO: Login con email que no existe en la BD
        ESPERADO: Status 401 Unauthorized
        """
        response = client.post("/api/v1/auth/login", json={
            "email": "noexiste@runza.com",
            "password": "cualquier_cosa"
        })
        assert response.status_code == 401

    def test_endpoint_protegido_sin_token_retorna_403(self):
        """
        CASO: Acceder a endpoint protegido sin JWT
        ESPERADO: Status 403 - HTTPBearer de FastAPI responde 403 cuando
        no se envía NINGÚN header Authorization (reserva 401 para el caso
        en que el token sí se envía pero es inválido/expirado).
        """
        response = client.get("/api/v1/activities/stats")
        assert response.status_code == 403