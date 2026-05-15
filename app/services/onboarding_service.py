from sqlalchemy.orm import Session
from datetime import date
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.onboarding import OnboardingRequest


class OnboardingService:

    @staticmethod
    def calcular_imc(weight_kg: float, height_cm: float) -> dict:
        """Calcula el IMC y devuelve categoría."""
        height_m = height_cm / 100
        imc = round(weight_kg / (height_m ** 2), 2)

        if imc < 18.5:
            categoria = "bajo_peso"
            descripcion = "Bajo peso. Considera ganar masa muscular."
        elif imc < 25:
            categoria = "normal"
            descripcion = "Peso saludable. Sigue así."
        elif imc < 30:
            categoria = "sobrepeso"
            descripcion = "Sobrepeso. RunZa te ayuda a alcanzar tu meta."
        else:
            categoria = "obesidad"
            descripcion = "Obesidad. Empezaremos con rutinas de bajo impacto."

        return {"imc": imc, "categoria": categoria, "descripcion": descripcion}

    @staticmethod
    def calcular_edad(birth_date_str: str) -> int:
        fecha = date.fromisoformat(birth_date_str)
        hoy = date.today()
        return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))

    @staticmethod
    def completar_onboarding(db: Session, user: User, data: OnboardingRequest) -> dict:
        # Validación de posición según deporte
        if data.deporte == "futbol":
            posiciones_validas = ["arquero", "defensa", "mediocampista", "delantero"]
            if data.posicion and data.posicion.lower() not in posiciones_validas:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Posición de fútbol inválida. Opciones: {posiciones_validas}"
                )
        elif data.deporte == "baloncesto":
            posiciones_validas = ["base", "escolta", "alero", "ala_pivot", "pivot"]
            if data.posicion and data.posicion.lower() not in posiciones_validas:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Posición de baloncesto inválida. Opciones: {posiciones_validas}"
                )
        else:
            # Para otros deportes la posición no aplica
            data.posicion = None

        # Actualizar usuario con los datos del onboarding
        user.genero = data.genero
        user.birth_date = data.birth_date
        user.weight_kg = data.weight_kg
        user.height_cm = data.height_cm
        user.nivel_actividad = data.nivel_actividad
        user.deporte = data.deporte
        user.posicion = data.posicion.lower() if data.posicion else None
        user.objetivo = data.objetivo
        user.dias_semana = data.dias_semana
        user.duracion_sesion = data.duracion_sesion
        user.equipamiento = data.equipamiento
        user.lesiones = data.lesiones
        user.onboarding_completed = True

        db.commit()
        db.refresh(user)

        imc_data = OnboardingService.calcular_imc(data.weight_kg, data.height_cm)
        edad = OnboardingService.calcular_edad(data.birth_date)

        return {
            "message": "Onboarding completado correctamente. ¡Bienvenido a RunZa!",
            "onboarding_completed": True,
            "imc": imc_data["imc"],
            "edad": edad,
            "perfil": {
                "genero": user.genero,
                "edad": edad,
                "peso": user.weight_kg,
                "estatura": user.height_cm,
                "imc": imc_data["imc"],
                "categoria_imc": imc_data["categoria"],
                "deporte": user.deporte,
                "posicion": user.posicion,
                "objetivo": user.objetivo,
                "nivel_actividad": user.nivel_actividad,
                "dias_semana": user.dias_semana,
                "duracion_sesion": user.duracion_sesion,
            }
        }