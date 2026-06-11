"""
Servicio de nutrición.
Cálculo calórico con fórmula Mifflin-St Jeor (1990).
"""
import os
import base64
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.nutrition import MealLog, WaterLog
from app.services.food_validator import validar_foto_comida


# Carpeta donde se guardan las fotos de comida
UPLOAD_DIR = "uploads/meals"
os.makedirs(UPLOAD_DIR, exist_ok=True)

PUNTOS_POR_COMIDA = 5
PUNTOS_POR_COMIDA_VALIDADA = 10
PUNTOS_POR_AGUA = 3


class NutritionService:

    @staticmethod
    def _calcular_edad(birth_date_str: str) -> int:
        if not birth_date_str:
            return 25  # default si no hay fecha
        try:
            fecha = date.fromisoformat(birth_date_str)
            hoy = date.today()
            return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        except Exception:
            return 25

    @staticmethod
    def calcular_necesidades(user: User) -> dict:
        """Calcula TMB y GET con fórmula Mifflin-St Jeor (1990)."""
        peso = user.weight_kg or 70
        altura = user.height_cm or 170
        edad = NutritionService._calcular_edad(user.birth_date)
        genero = (user.genero or "masculino").lower()

        # Fórmula Mifflin-St Jeor
        if genero == "femenino":
            tmb = (10 * peso) + (6.25 * altura) - (5 * edad) - 161
        else:
            tmb = (10 * peso) + (6.25 * altura) - (5 * edad) + 5

        # Factor de actividad
        factores = {
            "sedentario": 1.2,
            "ligero": 1.375,
            "moderado": 1.55,
            "activo": 1.725,
            "muy_activo": 1.9,
        }
        factor = factores.get(user.nivel_actividad, 1.55)
        get = tmb * factor

        # Ajuste según objetivo
        objetivo = user.objetivo or "forma"
        if objetivo == "perder_peso":
            objetivo_calorico = get - 500
            explicacion = "Déficit de 500 kcal para pérdida de peso saludable (~0.5 kg/semana)"
        elif objetivo == "ganar_musculo":
            objetivo_calorico = get + 300
            explicacion = "Superávit de 300 kcal para ganancia muscular controlada"
        else:
            objetivo_calorico = get
            explicacion = "Calorías de mantenimiento según tu gasto energético"

        # Agua recomendada (35 ml por kg de peso, en vasos de 250ml)
        agua_ml = peso * 35
        agua_vasos = round(agua_ml / 250)

        return {
            "tmb": round(tmb, 2),
            "get": round(get, 2),
            "objetivo_calorico": round(objetivo_calorico, 2),
            "objetivo_usuario": objetivo,
            "explicacion": explicacion,
            "formula": "Mifflin-St Jeor (1990) — validada científicamente",
            "agua_recomendada_vasos": agua_vasos,
        }

    @staticmethod
    def registrar_comida(db: Session, user: User, data) -> dict:
        from app.schemas.nutrition import TIPOS_COMIDA
        if data.tipo_comida.lower() not in TIPOS_COMIDA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de comida debe ser uno de: {TIPOS_COMIDA}"
            )

        hoy = date.today()
        foto_path = None
        validado = False
        metodo = "ninguno"
        detalle = "Sin foto adjunta"
        puntos = PUNTOS_POR_COMIDA

        # Si hay foto, validarla
        if data.foto_base64:
            try:
                b64 = data.foto_base64
                if "," in b64:
                    b64 = b64.split(",")[1]
                img_bytes = base64.b64decode(b64)

                resultado = validar_foto_comida(img_bytes)
                validado = resultado.es_valido
                metodo = resultado.metodo
                detalle = resultado.detalle

                # Guardar foto como evidencia
                filename = f"meal_{user.id}_{hoy.isoformat()}_{func.now()}.jpg"
                filename = f"meal_{user.id}_{int(date.today().toordinal())}_{db.query(MealLog).count()}.jpg"
                foto_path = os.path.join(UPLOAD_DIR, filename)
                with open(foto_path, "wb") as f:
                    f.write(img_bytes)

                if validado:
                    puntos = PUNTOS_POR_COMIDA_VALIDADA
            except Exception as e:
                detalle = f"Error procesando foto: {str(e)}"
                validado = False

        comida = MealLog(
            user_id=user.id,
            fecha=hoy,
            tipo_comida=data.tipo_comida.lower(),
            descripcion=data.descripcion,
            calorias_estimadas=data.calorias_estimadas,
            foto_path=foto_path,
            validado=validado,
            metodo_validacion=metodo,
            detalle_validacion=detalle,
            puntos_otorgados=puntos,
        )
        db.add(comida)

        # Sumar puntos al usuario
        user.total_points = (user.total_points or 0) + puntos

        db.commit()
        db.refresh(comida)

        if validado:
            mensaje_val = f"Foto validada ✓ Ganaste {puntos} puntos."
        elif data.foto_base64:
            mensaje_val = f"Comida registrada. La foto no pasó validación pero igual ganaste {puntos} puntos."
        else:
            mensaje_val = f"Comida registrada. Ganaste {puntos} puntos. (Sube foto para ganar más)"

        return {
            "meal": {
                "id": comida.id,
                "fecha": comida.fecha,
                "tipo_comida": comida.tipo_comida,
                "descripcion": comida.descripcion,
                "calorias_estimadas": comida.calorias_estimadas,
                "validado": comida.validado,
                "metodo_validacion": comida.metodo_validacion,
                "detalle_validacion": comida.detalle_validacion,
                "puntos_otorgados": comida.puntos_otorgados,
                "tiene_foto": comida.foto_path is not None,
                "created_at": comida.created_at,
            },
            "puntos_ganados": puntos,
            "total_points": user.total_points,
            "mensaje_validacion": mensaje_val,
        }

    @staticmethod
    def comidas_de_hoy(db: Session, user: User) -> list:
        comidas = db.query(MealLog).filter(
            MealLog.user_id == user.id,
            MealLog.fecha == date.today(),
        ).order_by(MealLog.created_at.asc()).all()

        return [{
            "id": c.id,
            "fecha": c.fecha,
            "tipo_comida": c.tipo_comida,
            "descripcion": c.descripcion,
            "calorias_estimadas": c.calorias_estimadas,
            "validado": c.validado,
            "metodo_validacion": c.metodo_validacion,
            "detalle_validacion": c.detalle_validacion,
            "puntos_otorgados": c.puntos_otorgados,
            "tiene_foto": c.foto_path is not None,
            "created_at": c.created_at,
        } for c in comidas]

    @staticmethod
    def borrar_comida(db: Session, user: User, meal_id: int) -> dict:
        comida = db.query(MealLog).filter(
            MealLog.id == meal_id,
            MealLog.user_id == user.id,
        ).first()
        if not comida:
            raise HTTPException(status_code=404, detail="Comida no encontrada")

        # Restar los puntos otorgados
        user.total_points = max(0, (user.total_points or 0) - comida.puntos_otorgados)
        db.delete(comida)
        db.commit()
        return {"message": "Comida eliminada y puntos ajustados"}

    @staticmethod
    def registrar_agua(db: Session, user: User, vasos: int) -> dict:
        hoy = date.today()
        registro = db.query(WaterLog).filter(
            WaterLog.user_id == user.id,
            WaterLog.fecha == hoy,
        ).first()

        if registro:
            registro.vasos += vasos
        else:
            registro = WaterLog(user_id=user.id, fecha=hoy, vasos=vasos)
            db.add(registro)

        puntos = PUNTOS_POR_AGUA
        registro.puntos_otorgados = (registro.puntos_otorgados or 0) + puntos
        user.total_points = (user.total_points or 0) + puntos
        db.commit()
        db.refresh(registro)

        return {
            "message": f"Registraste {vasos} vaso(s). Total hoy: {registro.vasos}. +{puntos} puntos"
        }

    @staticmethod
    def resumen_dia(db: Session, user: User) -> dict:
        hoy = date.today()
        necesidades = NutritionService.calcular_necesidades(user)
        objetivo_cal = necesidades["objetivo_calorico"]

        comidas = db.query(MealLog).filter(
            MealLog.user_id == user.id,
            MealLog.fecha == hoy,
        ).all()

        calorias_consumidas = sum(c.calorias_estimadas or 0 for c in comidas)
        restantes = objetivo_cal - calorias_consumidas
        porcentaje = round((calorias_consumidas / objetivo_cal) * 100, 1) if objetivo_cal > 0 else 0

        agua = db.query(WaterLog).filter(
            WaterLog.user_id == user.id,
            WaterLog.fecha == hoy,
        ).first()
        vasos = agua.vasos if agua else 0
        agua_objetivo = necesidades["agua_recomendada_vasos"]

        if porcentaje < 50:
            mensaje = "Vas bajo en calorías hoy. No te saltes comidas."
        elif porcentaje <= 110:
            mensaje = "¡Buen balance calórico hoy! Sigue así."
        else:
            mensaje = "Te pasaste del objetivo calórico. Mañana ajusta las porciones."

        return {
            "fecha": hoy,
            "objetivo_calorico": objetivo_cal,
            "calorias_consumidas": calorias_consumidas,
            "calorias_restantes": round(restantes, 2),
            "porcentaje_cumplido": porcentaje,
            "comidas_registradas": len(comidas),
            "vasos_agua": vasos,
            "agua_objetivo": agua_objetivo,
            "agua_cumplida": vasos >= agua_objetivo,
            "mensaje": mensaje,
        }