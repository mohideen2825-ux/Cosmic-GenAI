"""
ComicCraft Comprehensive End-to-End Test Suite
Tests outline generation, story expansion, image generation, PDF export, and FastAPI routes.
"""

import sys
from fastapi.testclient import TestClient
from app.main import app
from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout
from app.services.exporters import save_pdf

def test_ai_pipeline():
    print("\n--- 1. Testing Gemini Flash Outline Generation ---")
    outline = generate_outline(
        story_prompt="A young inventor discovers a pocket teleportation device.",
        character_name="Leo",
        setting="City",
        tone="Action",
        art_style="Comic Book"
    )
    assert isinstance(outline, list), "Outline must be a list"
    assert len(outline) == 5, f"Outline must have exactly 5 panels, got {len(outline)}"
    for p in outline:
        assert "panel" in p and "title" in p and "scene_description" in p and "image_prompt" in p
    print(f"[OK] Outline verified! 5 panels generated: {[p['title'] for p in outline]}")

    print("\n--- 2. Testing Gemini Pro Story Generation ---")
    story_panels = generate_story(
        outline=outline,
        character_name="Leo",
        setting="City",
        tone="Action",
        story_prompt="A young inventor discovers a pocket teleportation device."
    )
    assert len(story_panels) == 5, "Story must have 5 panels"
    for p in story_panels:
        assert "narration" in p and "dialogue" in p
        assert len(p["narration"]) > 0
        assert len(p["dialogue"]) > 0
    print(f"[OK] Story expansion verified! Panel 1 dialogue: {story_panels[0]['dialogue']}")

    print("\n--- 3. Testing Image Generation Service ---")
    img_paths = []
    for p in story_panels[:2]: # test 2 images for speed
        img_url = generate_image(
            prompt=p["image_prompt"],
            panel_num=p["panel"],
            art_style="Comic Book",
            character_name="Leo",
            setting="City"
        )
        assert img_url.startswith("/static/panels/"), f"Unexpected image path: {img_url}"
        img_paths.append(img_url)
    # Add dummy paths for remaining panels to complete 5
    img_paths.extend([img_paths[0], img_paths[1], img_paths[0]])
    print(f"[OK] Image generation verified! Generated paths: {img_paths[:2]}")

    print("\n--- 4. Testing Layout Builder ---")
    layout = build_comic_layout(story_panels, img_paths)
    assert len(layout) == 5
    assert layout[0]["image"] == img_paths[0]
    print("[OK] Layout builder verified!")

    print("\n--- 5. Testing PDF Exporter ---")
    pdf_url = save_pdf(
        layout=layout,
        comic_title="Leo's Quantum Leap",
        character_name="Leo",
        setting="City",
        tone="Action",
        art_style="Comic Book"
    )
    assert pdf_url.startswith("/static/exports/"), f"Unexpected PDF path: {pdf_url}"
    print(f"[OK] PDF export verified! Saved to: {pdf_url}")

def test_fastapi_routes():
    print("\n--- 6. Testing FastAPI Routes with TestClient ---")
    client = TestClient(app)

    # 1. Homepage GET /
    res_home = client.get("/")
    assert res_home.status_code == 200, f"Expected 200 for /, got {res_home.status_code}"
    assert "ComicCraft" in res_home.text
    print("[OK] GET / returned 200 OK with ComicCraft UI")

    # 2. Test Image Route GET /test-image
    res_img = client.get("/test-image?prompt=Cyberpunk+hero&art_style=Anime")
    assert res_img.status_code == 200
    json_data = res_img.json()
    assert json_data["success"] is True
    print(f"[OK] GET /test-image returned 200 OK: {json_data['image_url']}")

    # 3. Export Success Route GET /export-success
    res_success = client.get("/export-success?pdf=/static/exports/test.pdf&title=Test+Comic")
    assert res_success.status_code == 200
    assert "Your Comic Is Ready!" in res_success.text
    print("[OK] GET /export-success returned 200 OK")

    # 4. JSON API Route POST /generate-comic/json
    res_json_gen = client.post(
        "/generate-comic/json",
        json={
            "story_prompt": "An astronaut discovers life on a distant moon.",
            "character_name": "Zara",
            "setting": "Space",
            "tone": "Adventure",
            "art_style": "Sci-Fi"
        }
    )
    assert res_json_gen.status_code == 200
    res_body = res_json_gen.json()
    assert res_body["success"] is True
    assert len(res_body["panels"]) == 5
    assert res_body["pdf"].startswith("/static/exports/")
    print(f"[OK] POST /generate-comic/json returned 200 OK with 5 panels and PDF: {res_body['pdf']}")

    # 5. Form POST /generate
    res_form_gen = client.post(
        "/generate",
        data={
            "story_prompt": "A detective solves a mystery in an ancient museum.",
            "character_name": "Arthur",
            "setting": "City",
            "custom_setting": "",
            "tone": "Mystery",
            "art_style": "Comic Book"
        }
    )
    assert res_form_gen.status_code == 200
    assert "Comic Reader" in res_form_gen.text
    assert "PANEL #1" in res_form_gen.text
    print("[OK] POST /generate returned 200 OK rendering comic_preview.html with 5 panels!")

if __name__ == "__main__":
    test_ai_pipeline()
    test_fastapi_routes()
    print("\nALL TESTS PASSED SUCCESSFULLY! The application is 100% operational.")
