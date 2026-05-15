from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date

class IMCRequest(BaseModel):
    weight_kg: float
    height_cm: float

    @field_validator("weight_kg")
    @classmethod
    def weight_valid(cls, v):
        if v < 20 or v > 300:
            raise ValueError("Peso fuera de rango válido (20-300 kg)")
        return v

    @field_validator("height_cm")
    @classmethod
    def height_valid(cls, v):
        if v < 100 or v > 250:
            raise ValueError("Estatura fuera de rango válido (100-250 cm)")
        return v


class IMCResponse(BaseModel):
    imc: float
    categoria: str
    descripcion: str


# ---------- Onboarding completo (los 5 pasos juntos) ----------
class OnboardingRequest(BaseModel):
    # Paso 1: Datos personales
    genero: str  # "masculino", "femenino", "otro"
    birth_date: str  # formato "YYYY-MM-DD"
    weight_kg: float
    height_cm: float
    nivel_actividad: str  # "sedentario", "ligero", "moderado", "activo", "muy_activo"

    # Paso 2: Deporte
    deporte: str  # "futbol", "baloncesto", "running", "ciclismo", "tenis", "crossfit", "gimnasio"
    posicion: Optional[str] = None  # solo para fútbol/baloncesto

    # Paso 3: Objetivo
    objetivo: str  # "resistencia", "fuerza", "velocidad", "prevencion_lesiones", "forma", "perder_peso", "ganar_musculo"

    # Paso 4: Disponibilidad
    dias_semana: int  # 1-7
    duracion_sesion: int  # minutos: 15, 30, 45, 60, 90

    # Paso 5: Equipamiento y limitaciones
    equipamiento: Optional[str] = None  # texto libre o JSON serializado
    lesiones: Optional[str] = None

    @field_validator("genero")
    @classmethod
    def genero_valido(cls, v):
        valores = ["masculino", "femenino", "otro"]
        if v.lower() not in valores:
            raise ValueError(f"Género debe ser uno de: {valores}")
        return v.lower()

    @field_validator("nivel_actividad")
    @classmethod
    def nivel_valido(cls, v):
        valores = ["sedentario", "ligero", "moderado", "activo", "muy_activo"]
        if v.lower() not in valores:
            raise ValueError(f"Nivel de actividad debe ser uno de: {valores}")
        return v.lower()

    @field_validator("deporte")
    @classmethod
    def deporte_valido(cls, v):
        valores = ["futbol", "baloncesto", "running", "ciclismo", "tenis", "crossfit", "gimnasio"]
        if v.lower() not in valores:
            raise ValueError(f"Deporte debe ser uno de: {valores}")
        return v.lower()

    @field_validator("objetivo")
    @classmethod
    def objetivo_valido(cls, v):
        valores = [
            "resistencia", "fuerza", "velocidad", "prevencion_lesiones",
            "forma", "perder_peso", "ganar_musculo"
        ]
        if v.lower() not in valores:
            raise ValueError(f"Objetivo debe ser uno de: {valores}")
        return v.lower()

    @field_validator("dias_semana")
    @classmethod
    def dias_validos(cls, v):
        if v < 1 or v > 7:
            raise ValueError("Días por semana debe estar entre 1 y 7")
        return v

    @field_validator("duracion_sesion")
    @classmethod
    def duracion_valida(cls, v):
        if v not in [15, 30, 45, 60, 90, 120]:
            raise ValueError("Duración debe ser 15, 30, 45, 60, 90 o 120 minutos")
        return v

    @field_validator("birth_date")
    @classmethod
    def fecha_valida(cls, v):
        try:
            fecha = date.fromisoformat(v)
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 8 or edad > 100:
                raise ValueError("Edad debe estar entre 8 y 100 años")
            return v
        except ValueError as e:
            raise ValueError(f"Fecha inválida: {str(e)}")


class OnboardingResponse(BaseModel):
    message: str
    onboarding_completed: bool
    imc: float
    edad: int
    perfil: dict