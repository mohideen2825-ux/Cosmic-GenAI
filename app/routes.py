"""
ComicCraft - FastAPI Routes
Handles HTML page rendering, form processing, JSON API endpoints, and image testing.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Request, Form, HTTPException, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout
from app.services.exporters import save_pdf

logger = logging.getLogger("comiccraft.routes")

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class PromptRequest(BaseModel):
    """Pydantic model for JSON-based comic generation requests."""
    story_prompt: str = Field(..., min_length=3, max_length=1500, description="The core plot or premise of the comic")
    character_name: str = Field(..., min_length=1, max_length=100, description="Name of the protagonist")
    setting: str = Field(..., min_length=2, max_length=150, description="Environment or backdrop of the comic")
    tone: str = Field(..., min_length=2, max_length=50, description="Emotional or narrative tone")
    art_style: str = Field(..., min_length=2, max_length=50, description="Visual illustration style")
    panel_count: int = Field(5, ge=1, le=10, description="Number of panels to generate (default 5)")
    custom_panel_notes: Optional[str] = Field(None, description="Optional custom scene beats or notes per panel")


def _is_api_key_configured() -> bool:
    """Check if a real Gemini API key is configured in the environment."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(key and key != "your_gemini_api_key")


@router.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def index_page(request: Request):
    """
    Renders the ComicCraft homepage with the creation form and inspiration ideas.
    """
    has_gemini = _is_api_key_configured()
    hf_configured = bool(os.getenv("HF_API_KEY", "").strip() and os.getenv("HF_API_KEY") != "your_huggingface_api_key")

    inspiration_prompts = [
        {
            "prompt": "An ordinary teenager finds a glowing ancient compass in their attic that points toward hidden secrets in the old clock tower.",
            "character": "Leo Vance",
            "setting": "City",
            "tone": "Mystery",
            "art_style": "Comic Book"
        },
        {
            "prompt": "A courageous robotic botanist ventures across uncharted alien terrain to safeguard the galaxy's last bioluminescent seedling.",
            "character": "Unit 7-B",
            "setting": "Space",
            "tone": "Adventure",
            "art_style": "Sci-Fi / Anime"
        },
        {
            "prompt": "A playful apprentice alchemist accidentally turns the royal banquet dishes into mischievous, talking woodland creatures.",
            "character": "Pip Sparkler",
            "setting": "Fantasy World",
            "tone": "Funny",
            "art_style": "Cartoon"
        }
    ]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "has_gemini": has_gemini,
            "hf_configured": hf_configured,
            "inspiration_prompts": inspiration_prompts
        }
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic_form(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    custom_setting: Optional[str] = Form(None),
    tone: str = Form("Adventure"),
    art_style: str = Form("Comic Book"),
    panel_count: int = Form(5),
    custom_panel_notes: Optional[str] = Form(None)
):
    """
    Primary comic generation form endpoint.
    Executes the complete generation workflow:
    Input Validation -> generate_outline() -> generate_story() -> generate_image() -> build_comic_layout() -> save_pdf() -> Render Preview.
    """
    # 1. Validation & Input Sanitization
    story_prompt = story_prompt.strip()
    character_name = character_name.strip()
    
    if not story_prompt or len(story_prompt) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story prompt must be at least 3 characters long."
        )
    if not character_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character name cannot be blank."
        )

    # Resolve setting (if custom selected)
    final_setting = custom_setting.strip() if (setting.lower() == "custom" and custom_setting and custom_setting.strip()) else setting.strip()
    if not final_setting:
        final_setting = "Mysterious Realm"

    try:
        logger.info(f"Initiating comic generation: character='{character_name}', setting='{final_setting}', tone='{tone}', style='{art_style}', panels={panel_count}")

        # 2. Gemini Flash - Outline Generation
        outline = generate_outline(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=final_setting,
            tone=tone,
            art_style=art_style,
            panel_count=panel_count,
            custom_panel_notes=custom_panel_notes
        )

        # 3. Gemini Pro - Story & Dialogue Expansion
        story_panels = generate_story(
            outline=outline,
            character_name=character_name,
            setting=final_setting,
            tone=tone,
            story_prompt=story_prompt
        )

        # 4. Stable Diffusion / Art Generator for every panel
        image_paths = []
        for p in story_panels:
            p_num = p.get("panel", len(image_paths) + 1)
            img_prompt = p.get("image_prompt", f"{character_name} in {final_setting}")
            img_url = generate_image(
                prompt=img_prompt,
                panel_num=p_num,
                art_style=art_style,
                character_name=character_name,
                setting=final_setting
            )
            image_paths.append(img_url)

        # 5. Build Comic Layout
        layout = build_comic_layout(story_panels, image_paths)

        # 6. Save PDF
        comic_title = f"{character_name}'s {tone} in {final_setting}"
        if outline and len(outline) > 0 and outline[0].get("title"):
            comic_title = f"{character_name}: {outline[0]['title']}"

        pdf_url = save_pdf(
            layout=layout,
            comic_title=comic_title,
            character_name=character_name,
            setting=final_setting,
            tone=tone,
            art_style=art_style
        )

        is_dev_mode = not _is_api_key_configured()

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "request": request,
                "layout": layout,
                "comic_title": comic_title,
                "story_prompt": story_prompt,
                "character_name": character_name,
                "setting": final_setting,
                "tone": tone,
                "art_style": art_style,
                "pdf_url": pdf_url,
                "is_dev_mode": is_dev_mode
            }
        )

    except Exception as exc:
        logger.error(f"Error generating comic: {exc}", exc_info=True)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "error_message": f"Something went wrong while generating your comic: {str(exc)}. Please try again.",
                "has_gemini": _is_api_key_configured(),
                "hf_configured": bool(os.getenv("HF_API_KEY", "").strip())
            },
            status_code=500
        )


@router.post("/generate-comic/json")
async def generate_comic_json(req: PromptRequest):
    """
    JSON API endpoint for programmatic comic creation.
    Returns structured panels, metadata, and generated PDF URL.
    """
    try:
        outline = generate_outline(
            story_prompt=req.story_prompt,
            character_name=req.character_name,
            setting=req.setting,
            tone=req.tone,
            art_style=req.art_style,
            panel_count=req.panel_count,
            custom_panel_notes=req.custom_panel_notes
        )

        story_panels = generate_story(
            outline=outline,
            character_name=req.character_name,
            setting=req.setting,
            tone=req.tone,
            story_prompt=req.story_prompt
        )

        image_paths = []
        for p in story_panels:
            p_num = p.get("panel", len(image_paths) + 1)
            img_prompt = p.get("image_prompt", f"{req.character_name} in {req.setting}")
            img_url = generate_image(
                prompt=img_prompt,
                panel_num=p_num,
                art_style=req.art_style,
                character_name=req.character_name,
                setting=req.setting
            )
            image_paths.append(img_url)

        layout = build_comic_layout(story_panels, image_paths)

        comic_title = f"{req.character_name}'s {req.tone} Tale"
        pdf_url = save_pdf(
            layout=layout,
            comic_title=comic_title,
            character_name=req.character_name,
            setting=req.setting,
            tone=req.tone,
            art_style=req.art_style
        )

        return JSONResponse(
            content={
                "success": True,
                "comic_title": comic_title,
                "panels": layout,
                "pdf": pdf_url,
                "is_dev_mode": not _is_api_key_configured()
            }
        )

    except Exception as exc:
        logger.error(f"JSON generation failed: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Unable to generate comic: {str(exc)}"
            }
        )


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(
    request: Request,
    pdf: Optional[str] = Query(None),
    title: Optional[str] = Query("ComicCraft Adventure"),
    character: Optional[str] = Query("Hero")
):
    """
    Dedicated success page after comic PDF export.
    Displays confirmation, download link, and 'Create Another Comic' button.
    """
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "request": request,
            "pdf_url": pdf,
            "comic_title": title,
            "character_name": character
        }
    )


@router.get("/test-image")
async def test_image_route(
    request: Request,
    prompt: str = Query("A courageous hero standing on a rooftop overlooking a neon city", description="Image prompt"),
    art_style: str = Query("Comic Book", description="Art style: Anime, Comic Book, Cartoon, Realistic, Fantasy, Manga")
):
    """
    Developer utility endpoint for independently testing image generation.
    """
    try:
        img_url = generate_image(
            prompt=prompt,
            panel_num=1,
            art_style=art_style,
            character_name="Test Hero",
            setting="Cyberpunk Metropolis"
        )

        # Check if browser requested HTML or API requested JSON
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>ComicCraft - Image Test</title>
                <link rel="stylesheet" href="/static/css/style.css">
                <style>
                    body {{ display: flex; flex-direction: column; align-items: center; padding: 2rem; background: #0f111a; color: #fff; font-family: sans-serif; }}
                    .card {{ background: #1a1e2e; padding: 1.5rem; border-radius: 12px; border: 2px solid #ffbe0b; max-width: 800px; text-align: center; }}
                    img {{ max-width: 100%; border-radius: 8px; border: 3px solid #000; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
                    .btn {{ margin-top: 1rem; display: inline-block; padding: 10px 20px; background: #ffbe0b; color: #000; font-weight: bold; text-decoration: none; border-radius: 6px; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>ComicCraft Image Test Utility</h1>
                    <p><strong>Prompt:</strong> {prompt}</p>
                    <p><strong>Art Style:</strong> {art_style}</p>
                    <div style="margin: 1.5rem 0;">
                        <img src="{img_url}" alt="Generated Image Test">
                    </div>
                    <p>File URL: <code>{img_url}</code></p>
                    <a href="/" class="btn">Return to ComicCraft</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        return JSONResponse({
            "success": True,
            "prompt": prompt,
            "art_style": art_style,
            "image_url": img_url
        })
    except Exception as exc:
        logger.error(f"Image test route error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(exc)}
        )
