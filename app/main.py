"""
ComicCraft – AI Comic Story Creator Using Gemini Models
Main FastAPI Application Entrypoint
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Load environment configuration
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("comiccraft")

# Directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"

# Ensure runtime directories exist
PANELS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI application
app = FastAPI(
    title="ComicCraft – AI Comic Story Creator",
    description="Create stunning multi-panel comic stories with narration, dialogues, and comic illustrations using Google Gemini and Stable Diffusion.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static asset directory
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register routes
from app.routes import router as comic_router
app.include_router(comic_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "comiccraft", "version": "1.0.1"}


@app.on_event("startup")
async def startup_event():
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    hf_key = os.getenv("HF_API_KEY", "").strip()
    logger.info("==================================================")
    logger.info(" ComicCraft AI Comic Story Creator is starting up!")
    logger.info(f" Gemini AI Status: {'Configured' if gemini_key and gemini_key != 'your_gemini_api_key' else 'Development / Demo Mode'}")
    logger.info(f" Hugging Face Status: {'Configured' if hf_key and hf_key != 'your_huggingface_api_key' else 'Stylized Graphic Fallback'}")
    logger.info(" Open http://127.0.0.1:8000 in your browser")
    logger.info("==================================================")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
