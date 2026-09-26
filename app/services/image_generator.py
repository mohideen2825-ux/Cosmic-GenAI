"""
ComicCraft - Stable Diffusion & Comic Image Generator Service
Generates comic-style panel illustrations using Hugging Face Diffusers,
Hugging Face Inference API, or high-fidelity fallback rendering.
"""

import os
import uuid
import math
import random
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

load_dotenv()

logger = logging.getLogger("comiccraft.image_generator")

# Directory setup
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PANELS_DIR = BASE_DIR / "static" / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)


def _render_stylized_comic_art(
    prompt: str,
    output_path: Path,
    panel_num: int = 1,
    art_style: str = "Comic Book",
    character_name: str = "Hero",
    setting: str = "World"
) -> str:
    """
    Renders a high-resolution, stylized comic illustration using Pillow.
    Features:
    - Themed color gradients based on art style and setting
    - Halftone comic dot textures and speed lines
    - Graphic comic silhouettes, explosive geometric frames, and badges
    - Crisp comic panel border and caption typography
    """
    width, height = 768, 512
    img = Image.new("RGBA", (width, height), (20, 20, 30, 255))
    draw = ImageDraw.Draw(img)

    # Color palettes tailored by art style and mood
    style_palettes = {
        "Anime": [(25, 20, 60), (90, 45, 130), (255, 110, 160), (255, 220, 180)],
        "Comic Book": [(20, 25, 45), (180, 30, 30), (255, 190, 0), (255, 245, 210)],
        "Cartoon": [(30, 60, 120), (45, 170, 230), (255, 220, 40), (255, 255, 255)],
        "Realistic": [(15, 20, 28), (40, 55, 75), (130, 110, 95), (200, 190, 180)],
        "Fantasy": [(20, 15, 45), (80, 30, 110), (30, 170, 160), (230, 220, 150)],
        "Manga": [(20, 20, 20), (60, 60, 60), (160, 160, 160), (245, 245, 245)],
    }
    palette = style_palettes.get(art_style, style_palettes["Comic Book"])
    c_bg_dark, c_mid, c_accent, c_light = palette

    # 1. Background gradient
    for y in range(height):
        factor = y / height
        r = int(c_bg_dark[0] * (1 - factor) + c_mid[0] * factor)
        g = int(c_bg_dark[1] * (1 - factor) + c_mid[1] * factor)
        b = int(c_bg_dark[2] * (1 - factor) + c_mid[2] * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # 2. Comic burst / Radial rays from center
    center_x = width // 2 + (panel_num - 3) * 40
    center_y = int(height * 0.45)
    num_rays = 28
    for i in range(num_rays):
        if i % 2 == 0:
            angle1 = (2 * math.pi / num_rays) * i
            angle2 = (2 * math.pi / num_rays) * (i + 0.7)
            r_outer = max(width, height) * 1.2
            x1 = center_x + r_outer * math.cos(angle1)
            y1 = center_y + r_outer * math.sin(angle1)
            x2 = center_x + r_outer * math.cos(angle2)
            y2 = center_y + r_outer * math.sin(angle2)
            ray_color = (c_accent[0], c_accent[1], c_accent[2], 35)
            draw.polygon([(center_x, center_y), (x1, y1), (x2, y2)], fill=ray_color)

    # 3. Comic halftone dots effect overlay in upper corners
    for dx in range(20, width - 20, 24):
        for dy in range(20, height - 20, 24):
            dist = math.hypot(dx - center_x, dy - center_y)
            if dist > 220:
                dot_size = min(6, int((dist - 200) / 45))
                if dot_size > 0:
                    draw.ellipse(
                        [dx - dot_size, dy - dot_size, dx + dot_size, dy + dot_size],
                        fill=(c_light[0], c_light[1], c_light[2], 40)
                    )

    # 4. Stylized glowing energy orb / celestial body / anomaly
    orb_radius = 85
    for r_i in range(orb_radius, 0, -6):
        alpha = int(255 * (1 - r_i / orb_radius) * 0.6)
        draw.ellipse(
            [center_x - r_i, center_y - r_i, center_x + r_i, center_y + r_i],
            fill=(c_accent[0], c_accent[1], c_accent[2], alpha)
        )

    # 5. Stylized silhouette of character in action pose
    # Ground terrain / cliff silhouette
    ground_y = int(height * 0.78)
    terrain_pts = [
        (0, height),
        (0, ground_y + 15),
        (int(width * 0.25), ground_y),
        (int(width * 0.5), ground_y - 20),
        (int(width * 0.75), ground_y + 10),
        (width, ground_y - 5),
        (width, height)
    ]
    draw.polygon(terrain_pts, fill=(12, 12, 18, 255))

    # Hero silhouette
    char_base_x = center_x
    char_base_y = ground_y - 20

    # Silhouette body parts
    # Cape / Aura
    draw.polygon([
        (char_base_x - 10, char_base_y - 70),
        (char_base_x - 55, char_base_y - 15),
        (char_base_x - 35, char_base_y + 10),
        (char_base_x - 5, char_base_y - 40)
    ], fill=(c_accent[0], c_accent[1], c_accent[2], 180))

    # Torso & Legs
    draw.polygon([
        (char_base_x - 14, char_base_y - 70),
        (char_base_x + 14, char_base_y - 70),
        (char_base_x + 22, char_base_y - 10),
        (char_base_x + 25, char_base_y + 18),
        (char_base_x + 8, char_base_y + 18),
        (char_base_x, char_base_y - 25),
        (char_base_x - 12, char_base_y + 18),
        (char_base_x - 26, char_base_y + 18),
        (char_base_x - 14, char_base_y - 30)
    ], fill=(15, 15, 22, 255))

    # Head
    draw.ellipse(
        [char_base_x - 13, char_base_y - 102, char_base_x + 13, char_base_y - 74],
        fill=(15, 15, 22, 255)
    )

    # Heroic weapon / focal energy burst
    draw.line(
        [(char_base_x + 15, char_base_y - 65), (char_base_x + 75, char_base_y - 125)],
        fill=(c_light[0], c_light[1], c_light[2], 240),
        width=5
    )
    draw.ellipse(
        [char_base_x + 65, char_base_y - 135, char_base_x + 85, char_base_y - 115],
        fill=(c_light[0], c_light[1], c_light[2], 255)
    )

    # 6. Comic Heavy Ink Border
    border_thick = 8
    draw.rectangle([border_thick // 2, border_thick // 2, width - border_thick // 2, height - border_thick // 2], outline=(15, 15, 20, 255), width=border_thick)

    # 7. Comic Tag Badges
    # Top-Left Panel Badge
    badge_w, badge_h = 130, 36
    draw.rectangle([14, 14, 14 + badge_w, 14 + badge_h], fill=(255, 220, 0, 255), outline=(15, 15, 20, 255), width=3)
    
    # Bottom-Right Style Badge
    style_w, style_h = 170, 30
    draw.rectangle([width - 14 - style_w, height - 14 - style_h, width - 14, height - 14], fill=(15, 15, 20, 230), outline=(255, 220, 0, 255), width=2)

    # Try default fonts or system font
    try:
        font_large = ImageFont.truetype("arialbd.ttf", 18)
        font_small = ImageFont.truetype("arialbd.ttf", 13)
        font_prompt = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large
        font_prompt = font_large

    draw.text((24, 21), f"PANEL #{panel_num}", fill=(10, 10, 15, 255), font=font_large)
    draw.text((width - 14 - style_w + 12, height - 14 - style_h + 7), f"{art_style.upper()} STYLE", fill=(255, 220, 0, 255), font=font_small)

    # Bottom Prompt Preview Bar
    prompt_snippet = prompt.replace("\n", " ").strip()
    if len(prompt_snippet) > 85:
        prompt_snippet = prompt_snippet[:82] + "..."
    draw.rectangle([14, height - 42, width - 14 - style_w - 10, height - 14], fill=(10, 10, 18, 210), outline=(50, 50, 70, 255), width=1)
    draw.text((22, height - 35), prompt_snippet, fill=(210, 210, 225, 255), font=font_prompt)

    # Convert to RGB and save
    final_img = img.convert("RGB")
    final_img.save(str(output_path), format="PNG", quality=95)
    logger.info(f"Generated stylized comic art panel: {output_path.name}")
    return f"/static/panels/{output_path.name}"


def _generate_via_hf_api(prompt: str, output_path: Path, hf_token: str) -> bool:
    """Attempt image generation using Hugging Face Inference API."""
    import requests

    headers = {"Authorization": f"Bearer {hf_token}"}
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

    try:
        logger.info("Calling Hugging Face Inference API for image generation...")
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": "blurry, deformed, bad anatomy, duplicate, low quality, watermark, signature, extra limbs",
                "num_inference_steps": 25
            }
        }
        response = requests.post(api_url, headers=headers, json=payload, timeout=45)

        if response.status_code == 200 and "image" in response.headers.get("content-type", ""):
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Successfully generated image via HF API: {output_path.name}")
            return True
        else:
            logger.warning(f"HF API returned status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as exc:
        logger.warning(f"Hugging Face API call failed: {exc}")
        return False


def _generate_via_diffusers_local(prompt: str, output_path: Path) -> bool:
    """Attempt local generation with diffusers if configured in environment."""
    if os.getenv("USE_LOCAL_DIFFUSERS", "false").lower() not in ("true", "1", "yes"):
        return False

    try:
        import torch
        from diffusers import AutoPipelineForText2Image

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model_id = os.getenv("SD_MODEL_ID", "stabilityai/sd-turbo")
        logger.info(f"Loading local diffusers pipeline ({model_id}) on {device}...")

        pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=dtype,
            variant="fp16" if torch.cuda.is_available() else None
        )
        pipe.to(device)

        image = pipe(
            prompt=prompt,
            num_inference_steps=20 if device == "cuda" else 5,
            guidance_scale=7.5
        ).images[0]

        image.save(str(output_path))
        logger.info(f"Successfully generated image via local diffusers: {output_path.name}")
        return True
    except Exception as exc:
        logger.warning(f"Local diffusers generation failed: {exc}")
        return False


def generate_image(
    prompt: str,
    panel_num: int = 1,
    art_style: str = "Comic Book",
    character_name: str = "Hero",
    setting: str = "World"
) -> str:
    """
    Accept an image generation prompt and generate a comic-style illustration.
    Saves image in static/panels/ with a unique, safe filename.
    Returns the web URL path (e.g. /static/panels/panel_abc123_1.png).
    
    Tries in sequence:
    1. Hugging Face Inference API (if HF_API_KEY is present)
    2. Local Diffusers Pipeline (if USE_LOCAL_DIFFUSERS is enabled)
    3. Stylized Graphic Comic Illustrator Fallback (Pillow)
    """
    safe_uid = uuid.uuid4().hex[:8]
    filename = f"panel_{safe_uid}_{panel_num}.png"
    output_path = PANELS_DIR / filename

    # 1. Hugging Face API check
    hf_token = os.getenv("HF_API_KEY", "").strip()
    if hf_token and hf_token != "your_huggingface_api_key":
        if _generate_via_hf_api(prompt, output_path, hf_token):
            return f"/static/panels/{filename}"

    # 2. Local Diffusers check
    if _generate_via_diffusers_local(prompt, output_path):
        return f"/static/panels/{filename}"

    # 3. High quality stylized comic illustration fallback
    return _render_stylized_comic_art(
        prompt=prompt,
        output_path=output_path,
        panel_num=panel_num,
        art_style=art_style,
        character_name=character_name,
        setting=setting
    )
