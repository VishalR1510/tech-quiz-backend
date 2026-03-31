from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

app = FastAPI(
    title="AI Tech Quiz Application",
    description="FastAPI backend for AI-powered Tech Quiz. Provides endpoints for quiz delivery, attempt tracking, and AI feedback.",
    version="1.0.0"
)

# CORS configuration - restrict to specific origins
allowed_origins = [
    "https://tech-quiz-frontend-iota.vercel.app"
    "http://localhost:5173",      # Vite dev server
    "http://localhost:3000",      # Alternative dev port
    "http://127.0.0.1:5173",      # Localhost alternative
    "http://127.0.0.1:3000",      # Localhost alternative
    # Add your production frontend URL here
    # "https://yourdomain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Tech Quiz API setup by Antigravity"}

from routes.api import router as api_router
app.include_router(api_router, prefix="/api", tags=["Quiz"])
