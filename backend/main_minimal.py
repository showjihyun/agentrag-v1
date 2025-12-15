# Minimal FastAPI application for testing dashboard functionality

import warnings
import os
import sys

# Configure warnings
def configure_warnings():
    warnings.filterwarnings("ignore", message=".*Pydantic.*deprecated.*", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=".*model_fields.*", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=".*StreamingChoices.*", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*Message.*serialized value.*", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*SQLAlchemy.*deprecated.*", category=DeprecationWarning)

configure_warnings()

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal lifespan context manager."""
    logger.info("Starting minimal backend server...")
    yield
    logger.info("Shutting down minimal backend server...")

app = FastAPI(
    title="Agentic RAG System (Minimal)",
    version="1.0.0",
    description="Minimal version for testing",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# Include only dashboard router
from backend.api.agent_builder import dashboard as agent_builder_dashboard
app.include_router(agent_builder_dashboard.router)

@app.get("/")
async def root():
    return {"message": "Minimal Agentic RAG Backend", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)