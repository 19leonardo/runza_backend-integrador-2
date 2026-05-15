"""
Servicio de generación de rutinas con IA simbólica (sistema basado en reglas).
Implementa la 'IA simulada' descrita en el informe (sección 5.4.6).
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.user import User
from app.models.exercise import Exercise, Routine, RoutineExercise, ExerciseCompletion


class RoutineService:

    # Mapeo: objetivo del usuario → categorías de ejercicios prioritarias
    OBJETIVO_A_CATEGORIAS = {
        "resistencia": ["cardio", "agilidad"],
        "fuerza": ["fuerza", "tecnica"],
        "velocidad": ["agilidad", "cardio"],
        "prevencion_lesiones": ["fuerza"],  # filtraremos por objetivo="prevencion_lesiones"
        "forma": ["fuerza", "cardio", "tecnica"],
        "perder_peso": ["cardio", "agilidad"],
        "ganar_musculo": ["fuerza"],
    }

    # Mapeo: nivel_actividad del usuario → dificultades permitidas
    NIVEL_A_DIFICULTAD = {
        "sedentario": ["facil"],
        "ligero": ["facil", "medio"],
        "moderado": ["facil", "medio"],
        "activo": ["facil", "medio", "dificil"],
        "muy_activo": ["medio", "dificil"],
    }

    @staticmethod
    def _seleccionar_ejercicios(
        db: Session,
        categoria: str,
        deporte: str,
        objetivo: Optional[str],
        dificultades_permitidas: List[str],
        cantidad: int,
        tiene_lesiones: bool = False
    ) -> List[Exercise]:
        """Selecciona N ejercicios de una categoría aplicando filtros."""
        query = db.query(Exercise).filter(
            Exercise.is_active == True,
            Exercise.category == categoria,
            Exercise.nivel_dificultad.in_(dificultades_permitidas),
            or_(Exercise.deporte == deporte, Exercise.deporte.is_(None))
        )

        # Si tiene lesiones, evitar alto impacto (dificultad dificil)
        if tiene_lesiones:
            query = query.filter(Exercise.nivel_dificultad != "dificil")

        # Filtro por objetivo (si aplica)
        if objetivo and categoria == "fuerza" and objetivo == "prevencion_lesiones":
            query = query.filter(Exercise.objetivo == "prevencion_lesiones")

        ejercicios = query.all()

        # Si no hay suficientes, devolver todos los disponibles
        if len(ejercicios) <= cantidad:
            return ejercicios

        # Selección determinista (rotar por hash del día para que varíe)
        import random
        random.seed(date.today().toordinal())
        return random.sample(ejercicios, cantidad)

    @staticmethod
    def generar_rutina_diaria(db: Session, user: User) -> Routine:
        """
        Genera una rutina personalizada aplicando reglas IF-THEN.
        Es la 'IA simbólica' del informe (sección 5.4.5).
        """
        if not user.onboarding_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes completar el onboarding antes de generar rutinas"
            )

        # Si ya existe rutina para hoy, devolverla
        hoy = date.today()
        rutina_existente = db.query(Routine).filter(
            Routine.user_id == user.id,
            Routine.fecha == hoy
        ).first()
        if rutina_existente:
            return rutina_existente

        # Obtener categorías prioritarias según objetivo
        categorias_principales = RoutineService.OBJETIVO_A_CATEGORIAS.get(
            user.objetivo, ["fuerza", "cardio"]
        )

        # Obtener dificultades permitidas según nivel de actividad
        dificultades = RoutineService.NIVEL_A_DIFICULTAD.get(
            user.nivel_actividad, ["facil", "medio"]
        )

        # Detectar si tiene lesiones (texto no vacío y diferente a "ninguna")
        tiene_lesiones = bool(
            user.lesiones and 
            user.lesiones.strip().lower() not in ["", "ninguna", "no", "n/a"]
        )

        # === REGLA 1: Calcular cuántos ejercicios por bloque ===
        duracion = user.duracion_sesion or 60  # minutos
        if duracion <= 30:
            ejercicios_principales = 3
        elif duracion <= 60:
            ejercicios_principales = 5
        else:
            ejercicios_principales = 7

        # === REGLA 2: Toda rutina inicia con calentamiento ===
        bloque_calentamiento = RoutineService._seleccionar_ejercicios(
            db, "calentamiento", user.deporte, None, dificultades, 2, tiene_lesiones
        )

        # === REGLA 3: Bloque principal según objetivo ===
        bloque_principal = []
        ejercicios_por_categoria = max(1, ejercicios_principales // len(categorias_principales))
        for cat in categorias_principales:
            ejs = RoutineService._seleccionar_ejercicios(
                db, cat, user.deporte, user.objetivo, dificultades,
                ejercicios_por_categoria, tiene_lesiones
            )
            bloque_principal.extend(ejs)

        # === REGLA 4: Vuelta a la calma con estiramientos ===
        bloque_estiramiento = RoutineService._seleccionar_ejercicios(
            db, "estiramiento", user.deporte, None, dificultades, 2, tiene_lesiones
        )

        # Combinar bloques en orden
        ejercicios_finales = bloque_calentamiento + bloque_principal + bloque_estiramiento

        if not ejercicios_finales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron ejercicios disponibles para tu perfil"
            )

        # Calcular puntos totales y duración estimada
        total_puntos = sum(e.points_value for e in ejercicios_finales)
        duracion_estimada = sum(
            (e.duracion_segundos * e.sets) + (e.descanso_segundos * (e.sets - 1))
            for e in ejercicios_finales
        ) // 60  # convertir a minutos

        # Crear rutina
        nombre_rutina = f"Rutina del {hoy.strftime('%d/%m/%Y')} — {user.objetivo.capitalize()}"
        nueva_rutina = Routine(
            user_id=user.id,
            fecha=hoy,
            nombre=nombre_rutina,
            descripcion=f"Rutina personalizada para {user.deporte} con objetivo {user.objetivo}",
            duracion_estimada_minutos=duracion_estimada,
            total_puntos_disponibles=total_puntos,
        )
        db.add(nueva_rutina)
        db.flush()  # para obtener el ID antes de commit

        # Agregar ejercicios en orden
        for orden, ejercicio in enumerate(ejercicios_finales, start=1):
            routine_exercise = RoutineExercise(
                routine_id=nueva_rutina.id,
                exercise_id=ejercicio.id,
                orden=orden,
            )
            db.add(routine_exercise)

        db.commit()
        db.refresh(nueva_rutina)
        return nueva_rutina

    @staticmethod
    def obtener_rutina_hoy(db: Session, user: User) -> Routine:
        """Devuelve la rutina de hoy, generándola si no existe."""
        hoy = date.today()
        rutina = db.query(Routine).filter(
            Routine.user_id == user.id,
            Routine.fecha == hoy
        ).first()

        if not rutina:
            rutina = RoutineService.generar_rutina_diaria(db, user)

        return rutina

    @staticmethod
    def formatear_rutina(rutina: Routine) -> dict:
        """Convierte la rutina a dict para respuesta JSON."""
        ejercicios_data = []
        for re in sorted(rutina.exercises, key=lambda x: x.orden):
            ex = re.exercise
            ejercicios_data.append({
                "id": re.id,
                "exercise_id": ex.id,
                "orden": re.orden,
                "is_completed": re.is_completed,
                "nombre": ex.nombre,
                "descripcion": ex.descripcion,
                "category": ex.category,
                "nivel_dificultad": ex.nivel_dificultad,
                "duracion_segundos": ex.duracion_segundos,
                "sets": ex.sets,
                "repeticiones": ex.repeticiones,
                "descanso_segundos": ex.descanso_segundos,
                "points_value": ex.points_value,
            })

        return {
            "id": rutina.id,
            "user_id": rutina.user_id,
            "fecha": rutina.fecha,
            "nombre": rutina.nombre,
            "descripcion": rutina.descripcion,
            "duracion_estimada_minutos": rutina.duracion_estimada_minutos,
            "total_puntos_disponibles": rutina.total_puntos_disponibles,
            "is_completed": rutina.is_completed,
            "created_at": rutina.created_at,
            "exercises": ejercicios_data,
        }