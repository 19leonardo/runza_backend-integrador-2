from fastapi import APIRouter
from app.api.v1.endpoints import auth, onboarding, routines, pose, loads

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(routines.router, prefix="/routines", tags=["Rutinas"])
api_router.include_router(pose.router, prefix="/pose", tags=["Análisis de Pose"])
api_router.include_router(loads.router, prefix="/loads", tags=["Carga de Entrenamiento "])