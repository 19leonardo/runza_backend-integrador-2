
# RunZa Backend 🏃⚽

Backend del ecosistema **RunZa**: aplicación móvil de entrenamiento personalizado para futbolistas con análisis biomecánico mediante visión por computadora.

Proyecto académico del programa Integrador 2 — Ingeniería en Sistemas — Universidad UNIFRANZ.

---

## 🚀 Stack Tecnológico

- **FastAPI** 0.136 — framework web async de alto rendimiento
- **PostgreSQL** 16 — base de datos relacional
- **SQLAlchemy** 2.0 + **Alembic** — ORM y migraciones
- **Pydantic v2** — validación de datos
- **JWT** (python-jose) — autenticación
- **bcrypt** — hashing de contraseñas
- **MediaPipe** — análisis de pose corporal con IA
- **OpenCV** — procesamiento de imágenes

---

## 📦 Módulos Implementados

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| Autenticación | ✅ | Registro, login, JWT con refresh tokens |
| Onboarding | ✅ | Perfil de usuario en 5 pasos + cálculo de IMC |
| Rutinas + IA Simbólica | ✅ | Generación de rutinas con reglas IF-THEN |
| Gamificación | ✅ | Sistema de puntos, niveles y rachas |
| Análisis de Pose | ✅ | Detección biomecánica con MediaPipe |
| RPE + ACWR | 🚧 | En desarrollo |
| Nutrición | 📋 | Planificado |
| Rol Entrenador | 📋 | Planificado |
| Chat | 📋 | Planificado |

---

## 🛠️ Instalación local

### Requisitos previos
- Python 3.11+
- PostgreSQL 16+
- Git

### Pasos

```bash
# 1. Clonar repositorio
git clone https://github.com/TU_USUARIO/runza-backend.git
cd runza-backend

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
copy .env.example .env
# Editar .env con tus credenciales reales

# 5. Crear base de datos en PostgreSQL
# Conectarse a postgres y ejecutar:
# CREATE DATABASE runza_db;

# 6. Ejecutar migraciones
alembic upgrade head

# 7. Sembrar ejercicios iniciales
python seed_exercises.py

# 8. Descargar modelo de pose (para análisis biomecánico)
curl -o pose_landmarker.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task

# 9. Iniciar servidor
uvicorn app.main:app --reload
```

El backend estará disponible en `http://localhost:8000`.
Documentación interactiva en `http://localhost:8000/docs`.

---

## 📐 Arquitectura