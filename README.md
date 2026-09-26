# ComicCraft – AI Comic Story Creator Using Gemini Models

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%20Flash%20%26%20Pro-orange.svg?logo=google&logoColor=white)](https://aistudio.google.com/)
[![Stable Diffusion](https://img.shields.io/badge/Diffusers-Stable%20Diffusion-yellow.svg)](https://huggingface.co/)

**ComicCraft** is an AI-powered web application that turns creative story prompts into complete, beautifully illustrated 5-panel comic books. Users provide a story idea, character name, setting, tone, and art style. The application uses **Google Gemini Flash** to architect a cohesive 5-panel narrative arc, **Google Gemini Pro** to expand each panel with rich narration and dialogue, **Stable Diffusion** to generate illustrations, and **FPDF** to compile the finished comic into a downloadable PDF book.

---

## Architecture Flow

```text
               User Prompt & Character Details
                             │
                             ▼
                     FastAPI Backend
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   Gemini Flash Model                Gemini Pro Model
  (5-Panel Comic Arc)            (Narration & Dialogue)
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
              Stable Diffusion / HF Diffusers
             (Comic Illustration Generation)
                             │
                             ▼
                    Comic Layout Builder
                (Matching Story + Artwork)
                             │
                             ▼
                     Comic Web Preview
                             │
                             ▼
                     FPDF Book Engine
                             │
                             ▼
                 Multi-Page Comic Book PDF
```

---

## Key Features

- **Gemini Flash 5-Panel Outline**: Generates a 5-panel narrative with dramatic pacing (Introduction, Inciting Incident, Rising Conflict, Climax, and Resolution).
- **Gemini Pro Story & Dialogue Engine**: Expands each panel with comic captions (yellow narration boxes) and authentic character dialogue (speech bubbles).
- **Stable Diffusion Visual Generation**: Creates comic illustrations with character consistency across panels, with support for Hugging Face Inference API, local Diffusers, and stylized graphic fallback rendering.
- **Dynamic Comic Reader Interface**: Responsive comic book layout with halftone effects, speech balloons, narrator boxes, and action badges.
- **Automated PDF Export**: Compiles cover art, titles, illustrations, narration, dialogue, and scene directions into a multi-page PDF comic.
- **Dual Creation Modes**: Form-based interactive web UI and programmatic JSON API endpoint (`POST /generate-comic/json`).
- **Interactive Developer Tools**: Dedicated route (`GET /test-image`) to test image generation prompts independently.
- **Graceful Development / Demo Mode**: Runs cleanly even when API keys are not yet configured, allowing full UI and workflow testing without crashing.

---

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic, python-multipart, python-dotenv
- **AI Models**: Google Gemini 1.5 Flash / 2.0 Flash (`google-generativeai`), Gemini 1.5 Pro, Stable Diffusion (`diffusers`, `transformers`, `torch`, Hugging Face Inference API)
- **Document & Image Processing**: FPDF2, Pillow (PIL)
- **Frontend**: HTML5, CSS3 (Comic Modernism Design System), JavaScript, Jinja2 Templates

---

## Project Structure

```text
ComicCraft/
│
├── app/
│   ├── __init__.py               # App package initialization
│   ├── main.py                   # FastAPI initialization & static mounting
│   ├── routes.py                 # Web routes (/, /generate, /generate-comic/json, /test-image)
│   │
│   └── services/
│       ├── __init__.py           # Services package initialization
│       ├── gemini_flash.py       # 5-panel comic outline generator
│       ├── gemini_pro.py         # Narration & dialogue expansion service
│       ├── image_generator.py    # Stable Diffusion / illustration generator
│       ├── layout_builder.py     # Combines story data and illustrations
│       └── exporters.py          # FPDF multi-page comic book generator
│
├── templates/
│   ├── index.html                # Homepage with studio creation form & loading modal
│   ├── comic_preview.html        # Interactive sequential comic reader
│   └── export_success.html       # PDF export confirmation & download center
│
├── static/
│   ├── css/
│   │   └── style.css             # Comic design system (dark mode, speech bubbles, cards)
│   ├── js/
│   │   └── script.js             # Form validation & multi-phase loading sequence
│   ├── panels/                   # Directory for generated panel images
│   └── exports/                  # Directory for generated comic PDFs
│
├── .env                          # Local environment variables (API keys)
├── .env.example                  # Template for environment variables
├── .gitignore                    # Git ignore file
├── requirements.txt              # Project dependencies
└── README.md                     # Documentation
```

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone <repository_url>
cd ComicCraft
```

### 2. Create a virtual environment
**Windows (PowerShell/CMD):**
```bash
python -m venv comiccraft-env
comiccraft-env\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv comiccraft-env
source comiccraft-env/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and fill in your API credentials:
```env
# Google Gemini API Key (Get from: https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Hugging Face Token (Get from: https://huggingface.co/settings/tokens)
HF_API_KEY=your_huggingface_api_key_here

# Optional: Set to 'true' if running local diffusers on CUDA GPU
USE_LOCAL_DIFFUSERS=false
SD_MODEL_ID=stabilityai/sd-turbo
```

*(Note: If you run ComicCraft without keys, it automatically runs in Development/Demo Mode with stylized graphic rendering, so you can test the entire workflow immediately.)*

---

## Running the Application

Start the local server with Uvicorn:
```bash
uvicorn app.main:app --reload
```

Once started:
- **ComicCraft Web Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Routes & API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Renders the ComicCraft homepage creation form with inspiration chips |
| `POST` | `/generate` | Primary web form submission endpoint that executes the full pipeline |
| `POST` | `/generate-comic/json` | JSON REST API endpoint for programmatic comic creation |
| `GET` | `/export-success` | Dedicated success screen displaying PDF download actions |
| `GET` | `/test-image` | Developer utility to test image generation (`?prompt=...&art_style=...`) |

### Example JSON API Request
```bash
curl -X POST "http://127.0.0.1:8000/generate-comic/json" \
  -H "Content-Type: application/json" \
  -d '{
    "story_prompt": "A time traveler finds a mysterious pocket watch in an ancient clock tower.",
    "character_name": "Arjun",
    "setting": "City",
    "tone": "Mystery",
    "art_style": "Comic Book"
  }'
```

### Example JSON API Response
```json
{
  "success": true,
  "comic_title": "Arjun: The Whispering Clock",
  "panels": [
    {
      "panel": 1,
      "title": "The Whispering Shadows",
      "scene_description": "Arjun enters the old clock tower as gears grind above...",
      "narration": "In the silent heart of the old city, time had ceased to follow ordinary rules.",
      "dialogue": "Arjun: \"The ticking... it's coming from behind the wall!\"",
      "image": "/static/panels/panel_a1b2c3d4_1.png"
    }
  ],
  "pdf": "/static/exports/comic_e5f6g7h8.pdf",
  "is_dev_mode": false
}
```

---

## How Comic Generation Works

1. **Input Validation**: The backend checks for story prompt completeness and character specifications.
2. **Gemini Flash – Outline Generation (`generate_outline`)**:
   - Instructs Gemini Flash with a prompt demanding a 5-panel structure.
   - Enforces visual consistency rules for the protagonist across all panels.
3. **Gemini Pro – Story & Dialogue Expansion (`generate_story`)**:
   - Receives the outline and writes comic-style narration (captions) and character speech lines.
4. **Stable Diffusion – Image Generation (`generate_image`)**:
   - Renders each panel prompt.
   - Supports Hugging Face Inference API, local PyTorch Diffusers pipeline, and an artistic graphic rendering fallback.
5. **Layout Builder (`build_comic_layout`)**:
   - Matches panels and generated illustrations chronologically.
6. **PDF Compiler (`save_pdf`)**:
   - Uses FPDF to construct a comic book containing a cover page, titles, illustrations, narration boxes, and speech dialogue bubbles.

---

## Testing & Quality Assurance

Run the test suite or verify each component individually:

### 1. Test image generation independently
Open in browser:
```text
http://127.0.0.1:8000/test-image?prompt=A+cyberpunk+detective+in+rainy+streets&art_style=Comic+Book
```

### 2. Test JSON API via Swagger UI
Navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) and test `POST /generate-comic/json`.

### 3. Verify Local Services with Python
```bash
python -c "from app.services.image_generator import generate_image; print(generate_image('Hero flying', 1, 'Anime'))"
python -c "from app.services.gemini_flash import generate_outline; print(len(generate_outline('Hero saves day', 'Arjun', 'City', 'Action', 'Comic Book')))"
```

---

## Troubleshooting

- **Gemini API Key Issues**: Ensure `GEMINI_API_KEY` is pasted into `.env` without quotes. If the key is not provided, the application runs in development fallback mode.
- **Port Conflict**: If port 8000 is occupied, run on another port:
  ```bash
  uvicorn app.main:app --port 8080 --reload
  ```
- **Hugging Face Rate Limits**: If using `HF_API_KEY` and the model is cold or rate-limited, ComicCraft gracefully falls back to the high-resolution comic generator so the generation never breaks.

---

## License

MIT License. Built for educational and creative purposes.
