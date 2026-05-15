"""
Script para sembrar el catálogo inicial de ejercicios de RunZa.
Ejecutar: python seed_exercises.py
Basado en literatura científica del informe (Bompa, Bangsbo, Hewett, Myer, Behm).
"""
from app.core.database import SessionLocal, engine
from app.models.exercise import Exercise


EJERCICIOS_BASE = [
    # ========== CALENTAMIENTO (4 ejercicios) ==========
    {
        "nombre": "Trote suave",
        "descripcion": "Trote ligero para activación cardiovascular inicial.",
        "category": "calentamiento",
        "deporte": "futbol",
        "objetivo": None,
        "nivel_dificultad": "facil",
        "duracion_segundos": 300,
        "sets": 1,
        "repeticiones": 1,
        "descanso_segundos": 0,
        "points_value": 5,
    },
    {
        "nombre": "Movilidad de cadera",
        "descripcion": "Círculos de cadera y aperturas para preparar las articulaciones.",
        "category": "calentamiento",
        "deporte": "futbol",
        "objetivo": None,
        "nivel_dificultad": "facil",
        "duracion_segundos": 60,
        "sets": 2,
        "repeticiones": 10,
        "descanso_segundos": 15,
        "points_value": 5,
    },
    {
        "nombre": "Skipping bajo",
        "descripcion": "Elevación de rodillas a baja altura para activación neuromuscular.",
        "category": "calentamiento",
        "deporte": "futbol",
        "objetivo": None,
        "nivel_dificultad": "facil",
        "duracion_segundos": 30,
        "sets": 3,
        "repeticiones": 1,
        "descanso_segundos": 30,
        "points_value": 5,
    },
    {
        "nombre": "Estiramientos dinámicos",
        "descripcion": "Estiramientos activos de isquiotibiales, cuádriceps y aductores.",
        "category": "calentamiento",
        "deporte": "futbol",
        "objetivo": None,
        "nivel_dificultad": "facil",
        "duracion_segundos": 240,
        "sets": 1,
        "repeticiones": 1,
        "descanso_segundos": 0,
        "points_value": 5,
    },

    # ========== FUERZA (6 ejercicios) ==========
    {
        "nombre": "Sentadilla con peso corporal",
        "descripcion": "Fortalece cuádriceps, glúteos y core. Mantén la curvatura lumbar.",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "fuerza",
        "nivel_dificultad": "facil",
        "duracion_segundos": 60,
        "sets": 3,
        "repeticiones": 15,
        "descanso_segundos": 45,
        "points_value": 15,
    },
    {
        "nombre": "Zancadas alternadas",
        "descripcion": "Trabaja cada pierna individualmente. La rodilla no debe sobrepasar la punta del pie.",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "fuerza",
        "nivel_dificultad": "medio",
        "duracion_segundos": 60,
        "sets": 3,
        "repeticiones": 12,
        "descanso_segundos": 45,
        "points_value": 15,
    },
    {
        "nombre": "Plancha frontal",
        "descripcion": "Estabilidad del core. Mantén línea recta desde hombros hasta tobillos.",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "fuerza",
        "nivel_dificultad": "medio",
        "duracion_segundos": 45,
        "sets": 3,
        "repeticiones": 1,
        "descanso_segundos": 30,
        "points_value": 15,
    },
    {
        "nombre": "Sentadilla búlgara",
        "descripcion": "Pie trasero elevado. Excelente para fuerza unilateral y equilibrio.",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "fuerza",
        "nivel_dificultad": "dificil",
        "duracion_segundos": 60,
        "sets": 3,
        "repeticiones": 10,
        "descanso_segundos": 60,
        "points_value": 20,
    },
    {
        "nombre": "Puente de glúteos",
        "descripcion": "Activación de cadena posterior. Aprieta los glúteos en la parte alta.",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "fuerza",
        "nivel_dificultad": "facil",
        "duracion_segundos": 45,
        "sets": 3,
        "repeticiones": 15,
        "descanso_segundos": 30,
        "points_value": 10,
    },
    {
        "nombre": "Curl nórdico",
        "descripcion": "Excéntrico de isquiotibiales. Prevención de lesiones musculares (Myer et al., 2020).",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "prevencion_lesiones",
        "nivel_dificultad": "dificil",
        "duracion_segundos": 60,
        "sets": 3,
        "repeticiones": 6,
        "descanso_segundos": 90,
        "points_value": 25,
    },

    # ========== CARDIO / RESISTENCIA (4 ejercicios) ==========
    {
        "nombre": "Carrera continua moderada",
        "descripcion": "Trote a ritmo constante para resistencia aeróbica (RPE 5-6).",
        "category": "cardio",
        "deporte": "futbol",
        "objetivo": "resistencia",
        "nivel_dificultad": "medio",
        "duracion_segundos": 1200,
        "sets": 1,
        "repeticiones": 1,
        "descanso_segundos": 0,
        "points_value": 25,
    },
    {
        "nombre": "Intervalos HIIT",
        "descripcion": "30s sprint + 30s descanso. Mejora capacidad anaeróbica (Bangsbo, 2018).",
        "category": "cardio",
        "deporte": "futbol",
        "objetivo": "resistencia",
        "nivel_dificultad": "dificil",
        "duracion_segundos": 30,
        "sets": 8,
        "repeticiones": 1,
        "descanso_segundos": 30,
        "points_value": 30,
    },
    {
        "nombre": "Test Cooper modificado",
        "descripcion": "Carrera continua de 12 minutos para medir VO2máx estimado.",
        "category": "cardio",
        "deporte": "futbol",
        "objetivo": "resistencia",
        "nivel_dificultad": "dificil",
        "duracion_segundos": 720,
        "sets": 1,
        "repeticiones": 1,
        "descanso_segundos": 0,
        "points_value": 30,
    },
    {
        "nombre": "Saltos a la cuerda",
        "descripcion": "Coordinación, agilidad y resistencia. Aterrizaje suave con rodillas flexionadas.",
        "category": "cardio",
        "deporte": "futbol",
        "objetivo": "resistencia",
        "nivel_dificultad": "facil",
        "duracion_segundos": 60,
        "sets": 4,
        "repeticiones": 1,
        "descanso_segundos": 45,
        "points_value": 15,
    },

    # ========== AGILIDAD Y VELOCIDAD (4 ejercicios) ==========
    {
        "nombre": "Carrera en zigzag",
        "descripcion": "Slalom con conos. Trabaja cambios de dirección y agilidad.",
        "category": "agilidad",
        "deporte": "futbol",
        "objetivo": "velocidad",
        "nivel_dificultad": "medio",
        "duracion_segundos": 30,
        "sets": 6,
        "repeticiones": 1,
        "descanso_segundos": 45,
        "points_value": 20,
    },
    {
        "nombre": "Escalera de agilidad",
        "descripcion": "Pasos rápidos en escalera marcada en el piso. Mejora frecuencia de pisada.",
        "category": "agilidad",
        "deporte": "futbol",
        "objetivo": "velocidad",
        "nivel_dificultad": "medio",
        "duracion_segundos": 45,
        "sets": 4,
        "repeticiones": 1,
        "descanso_segundos": 30,
        "points_value": 20,
    },
    {
        "nombre": "Sprint 20 metros",
        "descripcion": "Aceleración máxima en distancia corta. Recuperación completa entre series.",
        "category": "agilidad",
        "deporte": "futbol",
        "objetivo": "velocidad",
        "nivel_dificultad": "medio",
        "duracion_segundos": 10,
        "sets": 6,
        "repeticiones": 1,
        "descanso_segundos": 60,
        "points_value": 20,
    },
    {
        "nombre": "Salto al cajón",
        "descripcion": "Pliometría explosiva. CRÍTICO: aterrizar con rodillas flexionadas (Hewett, 2017).",
        "category": "agilidad",
        "deporte": "futbol",
        "objetivo": "velocidad",
        "nivel_dificultad": "dificil",
        "duracion_segundos": 30,
        "sets": 4,
        "repeticiones": 8,
        "descanso_segundos": 60,
        "points_value": 25,
    },

    # ========== TÉCNICA DE FÚTBOL (4 ejercicios) ==========
    {
        "nombre": "Pases cortos contra pared",
        "descripcion": "Precisión y control de pelota. Usa ambos pies.",
        "category": "tecnica",
        "deporte": "futbol",
        "objetivo": "forma",
        "nivel_dificultad": "facil",
        "duracion_segundos": 300,
        "sets": 1,
        "repeticiones": 1,
        "descanso_segundos": 0,
        "points_value": 15,
    },
    {
        "nombre": "Conducción con cambios de dirección",
        "descripcion": "Control de balón en movimiento. Mantén balón cerca del pie.",
        "category": "tecnica",
        "deporte": "futbol",
        "objetivo": "forma",
        "nivel_dificultad": "medio",
        "duracion_segundos": 60,
        "sets": 4,
        "repeticiones": 1,
        "descanso_segundos": 45,
        "points_value": 20,
    },
    {
        "nombre": "Toques de cabeza",
        "descripcion": "Domina el juego aéreo. Golpea con la frente, no con la coronilla.",
        "category": "tecnica",
        "deporte": "futbol",
        "objetivo": "forma",
        "nivel_dificultad": "medio",
        "duracion_segundos": 60,
        "sets": 3,
        "repeticiones": 15,
        "descanso_segundos": 30,
        "points_value": 15,
    },
    {
        "nombre": "Tiro a portería",
        "descripcion": "Practica diferentes tipos de remate. Apoya bien el pie de apoyo.",
        "category": "tecnica",
        "deporte": "futbol",
        "objetivo": "forma",
        "nivel_dificultad": "medio",
        "duracion_segundos": 60,
        "sets": 4,
        "repeticiones": 10,
        "descanso_segundos": 45,
        "points_value": 20,
    },

    # ========== ESTIRAMIENTO / VUELTA A LA CALMA (3 ejercicios) ==========
    {
        "nombre": "Estiramiento de isquiotibiales",
        "descripcion": "Sentado, alcanza puntas de los pies. Mantén 30 segundos sin rebotar.",
        "category": "estiramiento",
        "deporte": "futbol",
        "objetivo": None,
        "nivel_dificultad": "facil",
        "duracion_segundos": 60,
        "sets": 2,
        "repeticiones": 1,
        "descanso_segundos": 0,
        "points_value": 5,
    },
    {
        "nombre": "Estiramiento de cuádriceps",
        "descripcion": "De pie, lleva el talón hacia el glúteo. Mantén 30 segundos cada pierna.",
        "category": "estiramiento",
        "deporte": "futbol",
        "objetivo": None,
        "nivel_dificultad": "facil",
        "duracion_segundos": 60,
        "sets": 2,
        "repeticiones": 1,
        "descanso_segundos": 0,
        "points_value": 5,
    },
    {
        "nombre": "Estiramiento de aductores",
        "descripcion": "Sentado con plantas de pies juntas. Empuja rodillas suavemente al piso.",
        "category": "estiramiento",
        "deporte": "futbol",
        "objetivo": None,
        "nivel_dificultad": "facil",
        "duracion_segundos": 45,
        "sets": 2,
        "repeticiones": 1,
        "descanso_segundos": 0,
        "points_value": 5,
    },

    # ========== PREVENCIÓN DE LESIONES (3 ejercicios neuromusculares) ==========
    {
        "nombre": "Equilibrio en una pierna",
        "descripcion": "Propiocepción. Ojos cerrados aumenta dificultad. Programa PEN (Myer, 2020).",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "prevencion_lesiones",
        "nivel_dificultad": "facil",
        "duracion_segundos": 30,
        "sets": 3,
        "repeticiones": 1,
        "descanso_segundos": 15,
        "points_value": 10,
    },
    {
        "nombre": "Aterrizaje técnico desde altura",
        "descripcion": "Salta desde un cajón bajo y aterriza con rodillas flexionadas. Previene ruptura LCA.",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "prevencion_lesiones",
        "nivel_dificultad": "medio",
        "duracion_segundos": 30,
        "sets": 3,
        "repeticiones": 8,
        "descanso_segundos": 45,
        "points_value": 20,
    },
    {
        "nombre": "Plancha lateral",
        "descripcion": "Estabilidad lateral del core. Trabaja oblicuos y cuadrado lumbar.",
        "category": "fuerza",
        "deporte": "futbol",
        "objetivo": "prevencion_lesiones",
        "nivel_dificultad": "medio",
        "duracion_segundos": 30,
        "sets": 3,
        "repeticiones": 1,
        "descanso_segundos": 30,
        "points_value": 15,
    },
]


def seed():
    db = SessionLocal()
    try:
        # Verificar si ya hay ejercicios
        existing = db.query(Exercise).count()
        if existing > 0:
            print(f"⚠️  La base de datos ya tiene {existing} ejercicios. ¿Borrar y recrear? (s/n): ", end="")
            respuesta = input().strip().lower()
            if respuesta == "s":
                db.query(Exercise).delete()
                db.commit()
                print("🗑️  Ejercicios anteriores eliminados.")
            else:
                print("❌ Operación cancelada.")
                return

        for data in EJERCICIOS_BASE:
            ejercicio = Exercise(**data)
            db.add(ejercicio)

        db.commit()
        total = db.query(Exercise).count()
        print(f"✅ Sembrados {total} ejercicios correctamente en la base de datos.")
        print("\nResumen por categoría:")
        from sqlalchemy import func
        resumen = db.query(Exercise.category, func.count(Exercise.id)).group_by(Exercise.category).all()
        for categoria, count in resumen:
            print(f"  • {categoria}: {count} ejercicios")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()