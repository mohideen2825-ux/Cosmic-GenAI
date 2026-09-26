"""
ComicCraft - Gemini Flash Comic Outline Service
Generates a structured 5-panel comic outline using Google Gemini Flash model.
"""

import os
import json
import re
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("comiccraft.gemini_flash")


def _clean_json_text(raw_text: str) -> str:
    """Clean markdown code fences and extraneous text from JSON response."""
    text = raw_text.strip()
    # Strip markdown code blocks like ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
    return text


def _generate_dev_fallback_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str
) -> List[Dict[str, Any]]:
    """
    Intelligent development fallback generator when Gemini API key is not configured.
    Provides a dynamic, coherent 5-panel story structure tailored to user inputs.
    """
    logger.info("Using development fallback for 5-panel comic outline.")

    # Character appearance signature for consistency across panels
    char_desc = f"{character_name}, expressive face, distinct signature outfit suitable for {setting}"

    return [
        {
            "panel": 1,
            "title": f"Arrival in {setting}",
            "scene_description": f"Establishing shot of {setting}. {character_name} stands at the threshold, taking in the breathtaking surroundings. The mood is distinctly {tone.lower()}.",
            "image_prompt": f"A vibrant wide shot of {setting}, {char_desc}, looking out with determination, {art_style} art style, dramatic lighting, rich textures, comic book illustration, dynamic perspective, sharp details, masterwork."
        },
        {
            "panel": 2,
            "title": "The Inciting Spark",
            "scene_description": f"{character_name} discovers an unusual anomaly or challenge in {setting}. A mysterious glow or strange event related to '{story_prompt[:60]}...' triggers urgent action.",
            "image_prompt": f"Medium shot, {char_desc} discovering a mysterious glowing artifact in {setting}, surprise and curiosity on their face, {art_style} comic illustration, vibrant colors, expressive shading, cinematic atmosphere."
        },
        {
            "panel": 3,
            "title": "The Rising Conflict",
            "scene_description": f"The situation intensifies. {character_name} faces an unexpected obstacle or confrontation in {setting}, testing their resolve under {tone.lower()} tension.",
            "image_prompt": f"Action dynamic angle, {char_desc} in the midst of a tense challenge in {setting}, sparks and energy swirling, {art_style} graphic novel style, high contrast, dramatic shadows, intense energy."
        },
        {
            "panel": 4,
            "title": "The Climax: Turning the Tide",
            "scene_description": f"{character_name} gathers courage and executes a clever or heroic maneuver, turning the situation around with bold determination.",
            "image_prompt": f"Low angle heroic pose of {char_desc} unleashing an extraordinary move in {setting}, radiant aura, {art_style} comic panel artwork, dynamic speed lines, bold linework, spectacular visual effects."
        },
        {
            "panel": 5,
            "title": "A New Dawn",
            "scene_description": f"The aftermath in {setting}. {character_name} stands victorious and at peace, gazing toward new horizons with a satisfied smile. Tone: {tone}.",
            "image_prompt": f"Golden hour warm lighting, wide scenic view of {setting}, {char_desc} smiling with a peaceful, confident posture, {art_style} comic style, gorgeous colorful background, tranquil celebratory atmosphere."
        }
    ]


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str
) -> List[Dict[str, Any]]:
    """
    Accept user's story prompt and character information, and generate
    a structured 5-panel comic outline.
    
    Every panel dictionary contains:
    - 'panel': Panel number (1 to 5)
    - 'title': Panel title
    - 'scene_description': Description of the scene
    - 'image_prompt': Detailed visual prompt for image generation
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your_gemini_api_key":
        logger.warning("GEMINI_API_KEY not configured. Falling back to development outline.")
        return _generate_dev_fallback_outline(story_prompt, character_name, setting, tone, art_style)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        prompt_system = f"""
You are an expert comic book scriptwriter and visual director.
Your task is to create a structured 5-panel comic book outline based on the user's concept.

Story Concept: "{story_prompt}"
Main Character: {character_name}
Setting: {setting}
Story Tone: {tone}
Art Style: {art_style}

CRITICAL RULES:
1. Generate EXACTLY 5 chronological panels (Panel 1 to Panel 5).
2. Maintain strong narrative continuity:
   - Panel 1: The Hook & Introduction in {setting}
   - Panel 2: The Inciting Incident / Discovery
   - Panel 3: Rising Tension / The Challenge
   - Panel 4: The Climax / Critical Action
   - Panel 5: Resolution / Satisfying Ending
3. Character Visual Consistency:
   - Establish consistent visual details for {character_name} (hair color, clothing, distinct traits) and repeat them across all image prompts.
4. Each panel MUST contain:
   - panel: integer (1 to 5)
   - title: short punchy comic title (e.g. "The Whispering Shadows")
   - scene_description: 2-3 sentences describing the narrative action and emotional mood
   - image_prompt: a rich, self-contained visual illustration prompt designed for Stable Diffusion image generator. Include character appearance, pose, camera angle, setting details, lighting, mood, and art style '{art_style}'. Avoid text/speech inside the image prompt.

OUTPUT FORMAT:
Return ONLY a valid JSON list of 5 panel objects. Do not include extra conversational text.
Example:
[
  {{
    "panel": 1,
    "title": "The Beginning",
    "scene_description": "...",
    "image_prompt": "..."
  }}
]
"""

        # Try flash models first, fallback to standard
        model_names = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-pro"]
        response_text = None
        last_error = None

        for m_name in model_names:
            try:
                model = genai.GenerativeModel(m_name)
                # Some versions support response_mime_type
                try:
                    res = model.generate_content(
                        prompt_system,
                        generation_config={"response_mime_type": "application/json"}
                    )
                except Exception:
                    res = model.generate_content(prompt_system)
                
                if res and res.text:
                    response_text = res.text
                    break
            except Exception as e:
                last_error = e
                continue

        if not response_text:
            raise RuntimeError(f"All Gemini models failed: {last_error}")

        cleaned = _clean_json_text(response_text)
        data = json.loads(cleaned)

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Gemini response is not a valid list of panels.")

        # Ensure all panels have required keys
        formatted_panels = []
        for i, item in enumerate(data[:5], start=1):
            formatted_panels.append({
                "panel": int(item.get("panel", i)),
                "title": str(item.get("title", f"Panel {i}")),
                "scene_description": str(item.get("scene_description", "")),
                "image_prompt": str(item.get("image_prompt", f"{character_name} in {setting}, {art_style} style"))
            })

        # If less than 5 panels returned, pad up to 5
        while len(formatted_panels) < 5:
            p_num = len(formatted_panels) + 1
            formatted_panels.append({
                "panel": p_num,
                "title": f"Panel {p_num}",
                "scene_description": f"The story continues with {character_name} in {setting}.",
                "image_prompt": f"{character_name} in {setting}, {art_style} comic style"
            })

        return formatted_panels

    except Exception as exc:
        logger.error(f"Error in generate_outline: {exc}. Utilizing robust fallback.", exc_info=True)
        return _generate_dev_fallback_outline(story_prompt, character_name, setting, tone, art_style)
