from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

app = FastAPI(
    title="AI Tech Quiz Application",
    description="FastAPI backend for AI-powered Tech Quiz. Provides endpoints for quiz delivery, attempt tracking, and AI feedback.",
    version="1.0.0"
)

# Allow local frontend development servers.
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"], # More permissive for testing
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("--- Environment Variable Check ---")
    print(f"SUPABASE_URL: {'Set' if settings.SUPABASE_URL else 'NOT SET'}")
    print(f"SUPABASE_KEY: {'Set' if settings.SUPABASE_KEY else 'NOT SET'}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {'Set' if settings.SUPABASE_SERVICE_ROLE_KEY else 'NOT SET'}")
    print(f"GEMINI_API_KEY: {'Set' if settings.GEMINI_API_KEY else 'NOT SET'}")
    print("----------------------------------")

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Tech Quiz API setup by Antigravity"}

from routes.api import router as api_router
app.include_router(api_router, prefix="/api", tags=["Quiz"])
