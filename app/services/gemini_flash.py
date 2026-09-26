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
    art_style: str,
    panel_count: int = 5,
    custom_panel_notes: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Intelligent development fallback generator when Gemini API key is not configured.
    Provides a dynamic, coherent comic structure tailored to user inputs and panel count.
    """
    logger.info(f"Using development fallback for {panel_count}-panel comic outline.")

    # Character appearance signature for consistency across panels
    char_desc = f"{character_name}, expressive face, distinct signature outfit suitable for {setting}"

    story_templates = [
        ("The Beginning", f"Establishing shot of {setting}. {character_name} stands at the threshold, taking in the surroundings under {tone.lower()} skies."),
        ("The Discovery", f"{character_name} uncovers an intriguing artifact or anomaly related to '{story_prompt[:50]}...' in {setting}."),
        ("Rising Tension", f"A sudden complication emerges in {setting}, testing {character_name}'s quick reflexes and courage."),
        ("The Confrontation", f"The conflict peaks as {character_name} directly faces the central dilemma under intense pressure."),
        ("Turning the Tide", f"{character_name} executes a bold maneuver, unleashing clever tactics to gain the upper hand."),
        ("The Climax", f"A decisive explosion of action and power sweeps across {setting}."),
        ("Resolution", f"The dust clears over {setting}. {character_name} surveys the restored balance with quiet triumph."),
        ("A New Horizon", f"{character_name} prepares for whatever legendary challenge awaits next beyond {setting}.")
    ]

    panels = []
    for i in range(1, panel_count + 1):
        idx = min(i - 1, len(story_templates) - 1)
        # If last panel, use final resolution template
        if i == panel_count and panel_count > 1:
            idx = min(6, len(story_templates) - 1)
        t_title, t_desc = story_templates[idx]

        # Use custom notes if user provided them
        if custom_panel_notes and f"panel {i}" in custom_panel_notes.lower():
            t_desc = f"Custom Scene: {custom_panel_notes}"

        panels.append({
            "panel": i,
            "title": f"{t_title}",
            "scene_description": f"{character_name} in {setting}. {t_desc}",
            "image_prompt": f"A dynamic {art_style} comic illustration of {char_desc} in {setting}, {t_title.lower()} scene, highly detailed, dramatic lighting, masterpiece."
        })

    return panels


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
    panel_count: int = 5,
    custom_panel_notes: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Accept user's story prompt and character information, and generate
    a structured comic outline with custom panel count and optional panel beats.
    
    Every panel dictionary contains:
    - 'panel': Panel number (1 to panel_count)
    - 'title': Panel title
    - 'scene_description': Description of the scene
    - 'image_prompt': Detailed visual prompt for image generation
    """
    panel_count = max(1, min(10, int(panel_count)))
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your_gemini_api_key":
        logger.warning("GEMINI_API_KEY not configured. Falling back to development outline.")
        return _generate_dev_fallback_outline(story_prompt, character_name, setting, tone, art_style, panel_count, custom_panel_notes)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        custom_instructions = ""
        if custom_panel_notes and custom_panel_notes.strip():
            custom_instructions = f"\nCUSTOM PANEL SETUP / SCENE BEATS REQUESTED BY USER:\n{custom_panel_notes.strip()}\nFollow these user beats closely for the corresponding panels."

        prompt_system = f"""
You are an expert comic book scriptwriter and visual director.
Your task is to create a structured {panel_count}-panel comic book outline based on the user's concept.

Story Concept: "{story_prompt}"
Main Character: {character_name}
Setting: {setting}
Story Tone: {tone}
Art Style: {art_style}
Total Panels: {panel_count}
{custom_instructions}

CRITICAL RULES:
1. Generate EXACTLY {panel_count} chronological panels (Panel 1 to Panel {panel_count}).
2. Maintain strong narrative continuity:
   - Panel 1: The Hook / Establishing Scene
   - Middle Panels: Pacing, Discovery, Challenge, and Climax
   - Final Panel {panel_count}: Resolution / Punchline / Satisfying Ending
3. Character Visual Consistency:
   - Establish consistent visual details for {character_name} (hair, clothing, distinct traits) and repeat them across all image prompts.
4. Each panel MUST contain:
   - panel: integer (1 to {panel_count})
   - title: short punchy comic title
   - scene_description: 2-3 sentences describing the narrative action and emotional mood
   - image_prompt: a rich, self-contained visual illustration prompt designed for image generation. Include character appearance, pose, camera angle, setting details, lighting, mood, and art style '{art_style}'. Avoid text/speech inside the image prompt.

OUTPUT FORMAT:
Return ONLY a valid JSON list of {panel_count} panel objects. Do not include extra markdown outside of JSON.
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
        model_names = [
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-pro-latest",
            "gemini-pro"
        ]
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
        for i, item in enumerate(data[:panel_count], start=1):
            formatted_panels.append({
                "panel": int(item.get("panel", i)),
                "title": str(item.get("title", f"Panel {i}")),
                "scene_description": str(item.get("scene_description", "")),
                "image_prompt": str(item.get("image_prompt", f"{character_name} in {setting}, {art_style} style"))
            })

        # If less than requested panels returned, pad up to panel_count
        while len(formatted_panels) < panel_count:
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
        return _generate_dev_fallback_outline(story_prompt, character_name, setting, tone, art_style, panel_count, custom_panel_notes)
