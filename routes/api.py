"""Main API router that combines all route modules"""
from fastapi import APIRouter
from .quizzes import router as quizzes_router
from .attempts import router as attempts_router

router = APIRouter()

# Include all route modules
router.include_router(quizzes_router)
router.include_router(attempts_router)
