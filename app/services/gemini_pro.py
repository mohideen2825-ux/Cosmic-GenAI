"""
ComicCraft - Gemini Pro Story Generation Service
Expands the 5-panel comic outline into full comic narration, dialogue, and scene directions.
"""

import os
import json
import re
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("comiccraft.gemini_pro")


def _clean_json_text(raw_text: str) -> str:
    """Clean markdown code fences and extraneous text from JSON response."""
    text = raw_text.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
    return text


def _generate_dev_fallback_story(
    outline: List[Dict[str, Any]],
    character_name: str,
    setting: str,
    tone: str,
    story_prompt: str
) -> List[Dict[str, Any]]:
    """
    Intelligent development fallback story generator when Gemini Pro is unavailable.
    Provides engaging, context-aware comic narration and dialogue for each panel.
    """
    logger.info("Using development fallback for comic story expansion.")

    dev_narratives = [
        {
            "narration": f"Deep within the heart of {setting}, destiny began to stir. For {character_name}, the quiet world was about to change forever.",
            "dialogue": f'{character_name}: "Something feels different today... The air is charged with electric potential."'
        },
        {
            "narration": f"Without warning, an anomalous presence manifested. The very fabric of {setting} seemed to shimmer with ancient energy.",
            "dialogue": f'{character_name}: "By the stars! Is that what I think it is? There is no turning back now."'
        },
        {
            "narration": f"Danger struck with merciless speed. Every instinct {character_name} possessed was pushed to its absolute limit as the {tone.lower()} storm gathered.",
            "dialogue": f'{character_name}: "I have trained for this moment. I won\'t falter when it counts the most!"'
        },
        {
            "narration": f"With a surge of indomitable courage, the climactic strike was unleashed, echoing across {setting} with deafening brilliance.",
            "dialogue": f'{character_name}: "This ends now! Witness the power of a true hero!"'
        },
        {
            "narration": f"Silence returned to {setting}. The dust settled, revealing peace restored. A new chapter had only just begun.",
            "dialogue": f'{character_name}: "We made it through. Tomorrow brings a new adventure."'
        }
    ]

    expanded_panels = []
    for i, panel in enumerate(outline):
        dev_info = dev_narratives[min(i, len(dev_narratives) - 1)]
        expanded_panels.append({
            "panel": panel.get("panel", i + 1),
            "title": panel.get("title", f"Chapter {i + 1}"),
            "scene_description": panel.get("scene_description", f"{character_name} in {setting}"),
            "image_prompt": panel.get("image_prompt", f"{character_name} in {setting}"),
            "narration": dev_info["narration"],
            "dialogue": dev_info["dialogue"]
        })

    return expanded_panels


def generate_story(
    outline: List[Dict[str, Any]],
    character_name: str,
    setting: str,
    tone: str,
    story_prompt: str
) -> List[Dict[str, Any]]:
    """
    Receive the generated 5-panel outline and expand each panel into a complete
    comic-style story with narration, character dialogue, and enhanced scene descriptions.
    
    Returns a list of dictionaries, each containing:
    - 'panel': Panel number (1 to 5)
    - 'title': Panel title
    - 'scene_description': Detailed scene visual
    - 'image_prompt': Image prompt
    - 'narration': Comic box narration
    - 'dialogue': Spoken character line / speech bubble
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your_gemini_api_key":
        logger.warning("GEMINI_API_KEY not configured. Falling back to development story.")
        return _generate_dev_fallback_story(outline, character_name, setting, tone, story_prompt)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        outline_summary = json.dumps(outline, indent=2)

        prompt_system = f"""
You are a master comic book author for legendary graphic novels.
You have been given a 5-panel comic outline. Your job is to expand it into an immersive comic story.

Original Story Idea: "{story_prompt}"
Main Character: {character_name}
Setting: {setting}
Tone: {tone}

5-PANEL OUTLINE:
{outline_summary}

YOUR TASK:
For each of the 5 panels, craft:
1. "narration": A dramatic, cinematic comic narration caption (like the yellow boxes in comic books). 1-2 powerful sentences.
2. "dialogue": An authentic character dialogue speech line spoken by {character_name} (format: '{character_name}: "..."') or an interactive exchange.
3. Keep the "title", "scene_description", and "image_prompt" from the outline, enhancing them if necessary.
4. Ensure emotional continuity, pacing, and tone adherence throughout all 5 panels.

OUTPUT FORMAT:
Return ONLY a valid JSON list of 5 panel objects.
Example:
[
  {{
    "panel": 1,
    "title": "Panel Title",
    "scene_description": "...",
    "image_prompt": "...",
    "narration": "The neon city breathed with uneasy calm as dusk approached...",
    "dialogue": "{character_name}: \\"This is our only chance to make things right.\\""
  }}
]
"""

        model_names = [
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
            "gemini-2.5-flash",
            "gemini-pro-latest",
            "gemini-1.5-pro",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]
        response_text = None
        last_error = None

        for m_name in model_names:
            try:
                model = genai.GenerativeModel(m_name)
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
            raise RuntimeError(f"All Gemini Pro models failed: {last_error}")

        cleaned = _clean_json_text(response_text)
        data = json.loads(cleaned)

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Gemini Pro response is not a valid list.")

        expanded_panels = []
        for i, base_outline in enumerate(outline):
            item = data[i] if (i < len(data) and isinstance(data[i], dict)) else {}
            expanded_panels.append({
                "panel": int(item.get("panel", base_outline.get("panel", i + 1))),
                "title": str(item.get("title", base_outline.get("title", f"Panel {i + 1}"))),
                "scene_description": str(item.get("scene_description", base_outline.get("scene_description", ""))),
                "image_prompt": str(item.get("image_prompt", base_outline.get("image_prompt", ""))),
                "narration": str(item.get("narration", f"{character_name} moves through {setting}.")),
                "dialogue": str(item.get("dialogue", f'{character_name}: "Let\'s keep moving forward!"'))
            })

        return expanded_panels

    except Exception as exc:
        logger.error(f"Error in generate_story: {exc}. Utilizing robust fallback.", exc_info=True)
        return _generate_dev_fallback_story(outline, character_name, setting, tone, story_prompt)
