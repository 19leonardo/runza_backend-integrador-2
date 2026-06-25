"""
conftest.py
Configuración compartida para toda la suite de pruebas de RunZa Backend.

Resuelve dos problemas reales encontrados al correr los tests contra una
base de datos limpia (como la que usa un pipeline de CI):

1. TestClient no dispara el evento "startup" de FastAPI por defecto, así
   que las tablas nunca se creaban automáticamente -> se fuerza la
   creación del esquema una vez por sesión de tests.
2. Sin limpieza entre tests, los datos de una prueba (emails, mensajes,
   contactos) interferían con las demás al correr la suite más de una
   vez -> se vacían las tablas antes de cada test para que cada caso
   empiece desde un estado conocido.
"""
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app  # al importar app.main ya se registran todos los modelos

client = TestClient(app)

# Tablas en orden seguro para TRUNCATE ... CASCADE
_TABLAS = (
    "messages, conversation_participants, conversations, user_contacts, "
    "exercise_tips, exercise_scoring_rules, exercise_angle_rules, "
    "exercise_detections, daily_stats, activities, users"
)


@pytest.fixture(scope="session", autouse=True)
def _crear_esquema_de_pruebas():
    """Crea el esquema completo antes de correr cualquier test."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _base_de_datos_limpia():
    """Vacía las tablas antes de cada test para garantizar aislamiento."""
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {_TABLAS} RESTART IDENTITY CASCADE"))
        conn.commit()
    yield


@pytest.fixture
def usuario_registrado():
    """Registra un usuario de prueba y retorna sus datos."""
    response = client.post("/api/v1/auth/register", json={
        "email": "test_runza@prueba.com",
        "password": "Test1234!",
        "full_name": "Usuario Test"
    })
    return response.json()


@pytest.fixture
def cliente_autenticado(usuario_registrado):
    """Retorna un TestClient con token JWT ya incluido."""
    token = usuario_registrado["tokens"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client
    client.headers.pop("Authorization", None)
