from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import interactions
from app.seed_data import seed_if_empty

Base.metadata.create_all(bind=engine)
seed_if_empty()

app = FastAPI(
    title="AI-First CRM — HCP Module API",
    description="Log Interaction Screen backend: structured-form + LangGraph conversational agent (Groq gemma2-9b-it).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router, prefix="/api", tags=["interactions"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "hcp-crm-backend"}
