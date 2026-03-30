from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Tech Quiz Application",
    description="FastAPI backend for AI-powered Tech Quiz. Provides endpoints for quiz delivery, attempt tracking, and AI feedback.",
    version="1.0.0"
)

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Tech Quiz API setup by Antigravity"}

from routes.api import router as api_router
app.include_router(api_router, prefix="/api", tags=["Quiz"])
