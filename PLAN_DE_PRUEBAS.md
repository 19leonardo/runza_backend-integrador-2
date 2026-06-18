# Plan de Pruebas — RunZa Backend

## 1. Alcance

Este plan cubre la API del backend de RunZa (FastAPI + PostgreSQL), tal
como está desplegada hoy en el repositorio `runza-backend`. Los módulos
con endpoints activos son:

| Módulo | Prefijo | Endpoints |
|---|---|---|
| Autenticación | `/api/v1/auth` | register, login, google, refresh, me |
| Actividades / Puntos | `/api/v1/activities` | exercise, meal, water, mood, sleep, wellness, stats, progress, recent |
| Chat | `/api/v1/chat` | search, contacts (GET/POST), conversations, online/offline |
| Análisis de poses | `/api/v1/pose` | analyze, health, exercises |

No se incluyen módulos que existen en versiones más completas del
proyecto (onboarding, rutinas, RPE/ACWR, diario de molestias, entrenador,
nutrición, perfil) porque **no están presentes en este repositorio** —
quedan fuera de alcance hasta que se suban.

## 2. Estrategia de pruebas

- **Pruebas unitarias/de integración (pytest + FastAPI TestClient)**: cada
  endpoint se prueba contra una base de datos PostgreSQL real y efímera,
  no una simulada, para validar el comportamiento real del ORM.
- **Técnicas de diseño de casos aplicadas**: partición de equivalencia
  (ej. credenciales válidas vs. inválidas vs. inexistentes), valores
  límite/casos negativos (campos faltantes → 422, recursos inexistentes →
  404), y pruebas de flujo de extremo a extremo (registro → ejercicio →
  estadísticas).
- **Mocking de dependencias externas**: la llamada real a la API de
  Google en `/auth/google` se simula con `unittest.mock`, para que las
  pruebas sean deterministas y no dependan de un token real ni de que
  Google esté disponible.
- **Aislamiento entre pruebas**: cada test corre contra una base de datos
  con las tablas vaciadas (fixture `_base_de_datos_limpia`), así el orden
  de ejecución y las corridas repetidas no afectan el resultado.
- **Integración continua (CI)**: GitHub Actions ejecuta toda la suite
  automáticamente en cada `push` y `pull request`, contra un contenedor
  de PostgreSQL 16 real, más un job de análisis estático (`flake8`).

## 3. Herramientas

| Capa | Herramienta |
|---|---|
| Test runner | pytest 8.x |
| Cliente HTTP de pruebas | FastAPI TestClient (httpx) |
| Cobertura | pytest-cov |
| Mocking | unittest.mock (AsyncMock/MagicMock) |
| CI/CD | GitHub Actions |
| Análisis estático | flake8 |
| Base de datos de pruebas | PostgreSQL 16 (contenedor de servicio en CI) |

## 4. Resultado actual

**28 casos de prueba, 100% pasando**, cobriendo los 4 módulos activos.
Cobertura de código (`pytest-cov`): **65% del paquete `app/`**, con el
detalle completo disponible en el reporte de cobertura que sube el
pipeline como artefacto.

| Archivo | Casos | Qué cubre |
|---|---|---|
| `test_autenticacion.py` | 7 | Registro, login, validaciones, acceso sin token |
| `test_chat.py` | 6 | Contactos, búsqueda de usuarios |
| `test_ejercicios.py` | 5 | Registro de ejercicios, acumulación de puntos, stats |
| `test_pose.py` | 5 | Salud del servicio, lista de ejercicios, validación y modo demo de `/analyze` |
| `test_google_auth.py` | 4 | Login con Google (token inválido, usuario nuevo, usuario existente, validación) |
| `test_integracion.py` | 1 | Flujo completo: registro → 2 ejercicios → verificación de puntos |

## 5. Defectos reales encontrados durante este trabajo

Correr la suite contra un entorno limpio (como hace CI) sacó a la luz
varios problemas que **no se notaban en desarrollo local**, porque la
base de datos local ya tenía las tablas creadas de antes:

1. **Los tests nunca creaban el esquema en un entorno limpio.**
   `TestClient(app)` no dispara el evento `startup` de FastAPI por
   defecto, así que `Base.metadata.create_all()` nunca se ejecutaba.
   Resultado: en una base de datos nueva (como la de CI), *todos* los
   tests fallaban con `relation "users" does not exist`.
   → Corregido con una fixture de sesión que crea el esquema antes de
   correr la suite (`tests/conftest.py`).

2. **Los tests no eran repetibles.** Sin limpieza entre corridas, volver
   a correr la suite fallaba por emails duplicados.
   → Corregido con una fixture que vacía las tablas antes de cada test.

3. **Desfase entre el contrato esperado y la respuesta real de la API.**
   Los tests de autenticación esperaban `access_token` en la raíz de la
   respuesta (`{"access_token": "..."}`), pero el endpoint real devuelve
   los tokens anidados (`{"tokens": {"access_token": "..."}}`). Si el
   frontend espera el formato plano, el login fallaría en la app móvil.
   → Los tests se corrigieron para reflejar el contrato real; **vale la
   pena confirmar con el código del frontend cuál de los dos formatos
   está consumiendo**, porque uno de los dos lados tiene un bug.

4. **Código muerto**: existe un archivo completo
   `app/api/v1/endpoints/google_auth.py` con una implementación de login
   con Google, pero su router nunca se registra en `app/api/v1/api.py`.
   El endpoint que realmente funciona es el que está duplicado dentro de
   `auth.py`. Se recomienda eliminar el archivo huérfano para evitar
   confusión futura.

5. **`/activities/stats` sin token devuelve 403, no 401.** Es el
   comportamiento estándar de `HTTPBearer` en FastAPI cuando no se envía
   ningún header `Authorization` (reserva 401 para tokens inválidos). No
   es necesariamente un bug, pero es una inconsistencia semántica que
   vale la pena documentar.

## 6. Cómo correr la suite

### Localmente
```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# Crear una base de datos vacía para pruebas y apuntar DATABASE_URL ahí
# (ver .env.example), luego:
pytest tests/ -v --cov=app --cov-report=term-missing
```

### En CI (automático)
Cada `push` o `pull request` dispara `.github/workflows/backend-ci.yml`,
que levanta un PostgreSQL 16 real, instala dependencias, corre toda la
suite con cobertura, y publica el reporte de cobertura y el resultado en
formato JUnit como artefactos descargables desde la pestaña *Actions* del
repositorio en GitHub.

## 7. Pendiente / siguientes pasos

- Sumar pruebas para el frontend (React Native + Jest) y su propio
  workflow de CI — repo `RunZaApp` aún por confirmar/subir.
- Resolver el punto 3 (formato de tokens) con el equipo de frontend.
- Decidir si se elimina `google_auth.py` (código muerto) o se documenta
  como deprecated.
- Si el tiempo lo permite: pruebas E2E (Detox o similar) para los flujos
  críticos de la app móvil.
