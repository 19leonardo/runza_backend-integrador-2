"""
Script para simular 28 días de entrenamiento de Jay.
Útil para probar el ACWR con datos realistas.
Simula un futbolista amateur con 4 sesiones por semana.
"""
import random
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.models.user import User
from app.models.exercise import Routine, Exercise, RoutineExercise, ExerciseCompletion
from app.models.training_load import SessionLoad

def seed_loads():
    db = SessionLocal()
    try:
        # Obtener al usuario Jay
        user = db.query(User).filter(User.email == "jay@runza.com").first()
        if not user:
            print("❌ No se encontró el usuario jay@runza.com")
            return

        # Borrar cargas existentes para empezar limpio
        existing = db.query(SessionLoad).filter(SessionLoad.user_id == user.id).count()
        if existing > 0:
            print(f"⚠️  Ya hay {existing} cargas registradas. ¿Borrar y recrear? (s/n): ", end="")
            if input().strip().lower() != "s":
                print("❌ Cancelado.")
                return
            db.query(SessionLoad).filter(SessionLoad.user_id == user.id).delete()
            db.commit()
            print("🗑️  Cargas anteriores eliminadas.")

        random.seed(42)  # Reproducible
        hoy = date.today()
        total_creadas = 0

        # Simular últimos 28 días
        # Patrón realista: futbolista amateur entrena 4 días/semana
        # Días de entrenamiento: Lunes, Martes, Jueves, Sábado
        dias_entrenamiento = [0, 1, 3, 5]  # lunes=0

        for dias_atras in range(28, 0, -1):
            fecha = hoy - timedelta(days=dias_atras)
            if fecha.weekday() not in dias_entrenamiento:
                continue

            # Variación realista en RPE y duración
            # RPE entre 5 y 8 (entrenamiento normal de futbolista)
            rpe = round(random.uniform(5.5, 8.0), 1)
            duracion = random.choice([45, 60, 75, 90])
            carga = rpe * duracion

            sesion = SessionLoad(
                user_id=user.id,
                fecha=fecha,
                rpe=rpe,
                duracion_minutos=duracion,
                carga_interna=carga,
                notas=f"Sesión simulada {fecha.strftime('%d/%m')}",
            )
            db.add(sesion)
            total_creadas += 1

        db.commit()
        print(f"\n✅ Simuladas {total_creadas} sesiones de entrenamiento.")
        print("   Ahora prueba GET /api/v1/loads/acwr para ver el ACWR realista.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_loads()