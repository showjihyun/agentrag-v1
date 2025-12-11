"""
Seed script for model pricing data.

Run this script to populate the model_pricings table with default pricing data.

Usage:
    python -m backend.scripts.seed_model_pricing
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
import logging
import uuid

from sqlalchemy import Column, String, Float, Boolean, DateTime, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment or config
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/agenticrag")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ModelPricing(Base):
    """Model pricing configuration - standalone definition for seeding."""
    __tablename__ = "model_pricings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    input_price_per_1k = Column(Float, nullable=False, default=0.0)
    output_price_per_1k = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Default model pricing data (per 1K tokens, USD)
DEFAULT_PRICING = [
    # OpenAI
    {"provider": "openai", "model": "gpt-4o", "input": 0.0025, "output": 0.01},
    {"provider": "openai", "model": "gpt-4o-mini", "input": 0.00015, "output": 0.0006},
    {"provider": "openai", "model": "gpt-4-turbo", "input": 0.01, "output": 0.03},
    {"provider": "openai", "model": "gpt-4", "input": 0.03, "output": 0.06},
    {"provider": "openai", "model": "gpt-3.5-turbo", "input": 0.0005, "output": 0.0015},
    {"provider": "openai", "model": "gpt-3.5-turbo-16k", "input": 0.003, "output": 0.004},
    
    # Anthropic
    {"provider": "anthropic", "model": "claude-3-5-sonnet", "input": 0.003, "output": 0.015},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "input": 0.003, "output": 0.015},
    {"provider": "anthropic", "model": "claude-3-opus", "input": 0.015, "output": 0.075},
    {"provider": "anthropic", "model": "claude-3-sonnet", "input": 0.003, "output": 0.015},
    {"provider": "anthropic", "model": "claude-3-haiku", "input": 0.00025, "output": 0.00125},
    
    # Google
    {"provider": "google", "model": "gemini-1.5-pro", "input": 0.00125, "output": 0.005},
    {"provider": "google", "model": "gemini-1.5-flash", "input": 0.000075, "output": 0.0003},
    {"provider": "google", "model": "gemini-1.0-pro", "input": 0.0005, "output": 0.0015},
    {"provider": "google", "model": "gemini-2.0-flash-exp", "input": 0.0001, "output": 0.0004},
    
    # Mistral
    {"provider": "mistral", "model": "mistral-large", "input": 0.002, "output": 0.006},
    {"provider": "mistral", "model": "mistral-medium", "input": 0.0027, "output": 0.0081},
    {"provider": "mistral", "model": "mistral-small", "input": 0.001, "output": 0.003},
    {"provider": "mistral", "model": "codestral", "input": 0.001, "output": 0.003},
    
    # Cohere
    {"provider": "cohere", "model": "command-r-plus", "input": 0.003, "output": 0.015},
    {"provider": "cohere", "model": "command-r", "input": 0.0005, "output": 0.0015},
    
    # Local (Ollama) - Free
    {"provider": "ollama", "model": "llama3.1", "input": 0, "output": 0},
    {"provider": "ollama", "model": "llama3.1:70b", "input": 0, "output": 0},
    {"provider": "ollama", "model": "llama3.1:8b", "input": 0, "output": 0},
    {"provider": "ollama", "model": "llama3", "input": 0, "output": 0},
    {"provider": "ollama", "model": "llama2", "input": 0, "output": 0},
    {"provider": "ollama", "model": "mistral", "input": 0, "output": 0},
    {"provider": "ollama", "model": "mixtral", "input": 0, "output": 0},
    {"provider": "ollama", "model": "codellama", "input": 0, "output": 0},
    {"provider": "ollama", "model": "phi3", "input": 0, "output": 0},
    {"provider": "ollama", "model": "gemma2", "input": 0, "output": 0},
    {"provider": "ollama", "model": "qwen2.5", "input": 0, "output": 0},
    {"provider": "ollama", "model": "deepseek-coder-v2", "input": 0, "output": 0},
    
    # Groq (fast inference)
    {"provider": "groq", "model": "llama-3.1-70b-versatile", "input": 0.00059, "output": 0.00079},
    {"provider": "groq", "model": "llama-3.1-8b-instant", "input": 0.00005, "output": 0.00008},
    {"provider": "groq", "model": "mixtral-8x7b-32768", "input": 0.00024, "output": 0.00024},
    
    # Together AI
    {"provider": "together", "model": "meta-llama/Llama-3.1-70B-Instruct-Turbo", "input": 0.00088, "output": 0.00088},
    {"provider": "together", "model": "meta-llama/Llama-3.1-8B-Instruct-Turbo", "input": 0.00018, "output": 0.00018},
]


def seed_model_pricing():
    """Seed the model_pricings table with default data."""
    db = SessionLocal()
    
    try:
        added = 0
        updated = 0
        
        for pricing_data in DEFAULT_PRICING:
            existing = db.query(ModelPricing).filter(
                ModelPricing.provider == pricing_data["provider"],
                ModelPricing.model == pricing_data["model"]
            ).first()
            
            if existing:
                # Update if prices changed
                if (existing.input_price_per_1k != pricing_data["input"] or 
                    existing.output_price_per_1k != pricing_data["output"]):
                    existing.input_price_per_1k = pricing_data["input"]
                    existing.output_price_per_1k = pricing_data["output"]
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                    logger.info(f"Updated pricing for {pricing_data['provider']}/{pricing_data['model']}")
            else:
                # Create new
                pricing = ModelPricing(
                    provider=pricing_data["provider"],
                    model=pricing_data["model"],
                    input_price_per_1k=pricing_data["input"],
                    output_price_per_1k=pricing_data["output"],
                    currency="USD",
                    is_active=True,
                )
                db.add(pricing)
                added += 1
                logger.info(f"Added pricing for {pricing_data['provider']}/{pricing_data['model']}")
        
        db.commit()
        logger.info(f"Seeding complete: {added} added, {updated} updated")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed model pricing: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_model_pricing()
