"""
MÓDULO: test_google_auth.py
DESCRIPCIÓN: Pruebas del endpoint de autenticación con Google de RunZa
HERRAMIENTA: pytest + FastAPI TestClient + unittest.mock
NOTA: Se simula (mock) la llamada externa a la API de Google para que las
pruebas sean rápidas, deterministas y no dependan de un token real ni de
que el servicio de Google esté disponible al correr en CI.

IMPORTANTE: el endpoint real registrado en la API es
POST /api/v1/auth/google (definido en app/api/v1/endpoints/auth.py).
Existe un archivo separado app/api/v1/endpoints/google_auth.py con una
implementación equivalente, pero su router NUNCA se registra en
app/api/v1/api.py, así que ese código está muerto y no es alcanzable.
Estas pruebas validan el endpoint real, no el archivo huérfano.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_google_client(status_code: int, json_data: dict):
    """Construye un AsyncClient de httpx simulado para las pruebas."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    return mock_client_instance


class TestGoogleAuth:
    """Pruebas del endpoint POST /api/v1/auth/google"""

    @patch("app.api.v1.endpoints.auth.httpx.AsyncClient")
    def test_token_invalido_retorna_401(self, mock_async_client, cliente_autenticado):
        """
        CASO: Google rechaza el token (inválido o expirado)
        ESPERADO: Status 401 Unauthorized
        """
        mock_async_client.return_value = _mock_google_client(401, {})

        response = cliente_autenticado.post("/api/v1/auth/google", json={
            "token": "token-invalido"
        })
        assert response.status_code == 401

    @patch("app.api.v1.endpoints.auth.httpx.AsyncClient")
    def test_usuario_nuevo_se_crea_automaticamente(self, mock_async_client, cliente_autenticado):
        """
        CASO: Token válido de un usuario que no existe todavía en la BD
        ESPERADO: Status 200, se crea el usuario y se devuelven tokens JWT
        """
        mock_async_client.return_value = _mock_google_client(200, {
            "email": "nuevo_google@runza.com",
            "name": "Usuario Google",
            "picture": "https://example.com/avatar.png"
        })

        response = cliente_autenticado.post("/api/v1/auth/google", json={
            "token": "token-valido"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "nuevo_google@runza.com"
        assert "access_token" in data["tokens"]

    @patch("app.api.v1.endpoints.auth.httpx.AsyncClient")
    def test_usuario_existente_no_se_duplica(self, mock_async_client, cliente_autenticado, usuario_registrado):
        """
        CASO: El email de Google ya pertenece a un usuario registrado
        ESPERADO: Status 200, se reutiliza el usuario existente (no se
        crea un registro duplicado)
        """
        email_existente = usuario_registrado["user"]["email"]

        mock_async_client.return_value = _mock_google_client(200, {
            "email": email_existente,
            "name": "Usuario Existente",
            "picture": ""
        })

        response = cliente_autenticado.post("/api/v1/auth/google", json={
            "token": "token-valido"
        })
        assert response.status_code == 200
        assert response.json()["user"]["email"] == email_existente

    def test_sin_token_retorna_422(self, cliente_autenticado):
        """
        CASO: Enviar la solicitud sin el campo 'token'
        ESPERADO: Status 422 - validación de Pydantic
        """
        response = cliente_autenticado.post("/api/v1/auth/google", json={})
        assert response.status_code == 422
