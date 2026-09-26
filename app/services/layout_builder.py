"""
ComicCraft - Comic Layout Builder Service
Combines generated story panels and illustrations into a unified comic layout structure.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger("comiccraft.layout_builder")


def build_comic_layout(
    story_panels: List[Dict[str, Any]],
    image_paths: List[str]
) -> List[Dict[str, Any]]:
    """
    Combine the generated story information with generated images.
    Matches every image with its corresponding panel in chronological order.
    
    Returns a structured layout list:
    [
        {
            "panel": 1,
            "title": "The Beginning",
            "image": "/static/panels/panel_1.png",
            "scene_description": "...",
            "narration": "...",
            "dialogue": "..."
        },
        ...
    ]
    """
    layout = []

    for idx, panel_data in enumerate(story_panels):
        # Match image by index, fallback if image list is shorter
        img_path = image_paths[idx] if idx < len(image_paths) else "/static/panels/default.png"

        panel_entry = {
            "panel": int(panel_data.get("panel", idx + 1)),
            "title": str(panel_data.get("title", f"Panel {idx + 1}")),
            "image": img_path,
            "scene_description": str(panel_data.get("scene_description", "")),
            "narration": str(panel_data.get("narration", "")),
            "dialogue": str(panel_data.get("dialogue", "")),
            "image_prompt": str(panel_data.get("image_prompt", ""))
        }
        layout.append(panel_entry)

    logger.info(f"Built comic layout with {len(layout)} structured panels.")
    return layout
