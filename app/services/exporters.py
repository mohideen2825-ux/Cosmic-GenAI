"""
ComicCraft - PDF Exporter Service
Compiles the comic panels, illustrations, dialogue, and narration into a
multi-page PDF using FPDF.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fpdf import FPDF

logger = logging.getLogger("comiccraft.exporters")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
EXPORTS_DIR = BASE_DIR / "static" / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_pdf_text(text: str) -> str:
    """
    Sanitize text to be safely compatible with standard FPDF fonts (latin-1/ascii).
    Replaces smart quotes, dashes, ellipsis, and unprintable characters.
    """
    if not text:
        return ""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2014": " - ",
        "\u2013": " - ",
        "\u2026": "...",
        "\u00a0": " ",
        "\u2022": "*",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    
    # Strip any characters that can't be encoded in latin-1
    return text.encode("latin-1", errors="replace").decode("latin-1")


class ComicPDF(FPDF):
    """Custom FPDF class styled for comic books."""

    def __init__(self, comic_title: str = "ComicCraft Comic", character_name: str = "Hero", tone: str = "Adventure"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.comic_title = _sanitize_pdf_text(comic_title)
        self.character_name = _sanitize_pdf_text(character_name)
        self.tone = _sanitize_pdf_text(tone)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Running top bar on all pages except cover
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(120, 120, 140)
            self.cell(0, 8, f"ComicCraft AI  |  {self.comic_title}  |  Hero: {self.character_name}", border=0, align="L")
            self.ln(9)
            self.set_draw_color(220, 220, 230)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 160)
        footer_text = f"Page {self.page_no()}  *  Generated with ComicCraft AI Story Creator"
        self.cell(0, 8, footer_text, align="C")


def save_pdf(
    layout: List[Dict[str, Any]],
    comic_title: str = "ComicCraft Adventure",
    character_name: str = "Hero",
    setting: str = "The World",
    tone: str = "Action",
    art_style: str = "Comic Book"
) -> str:
    """
    Generate and save a multi-page PDF document containing all comic panels.
    Each panel features:
    - Panel Header & Title
    - High-resolution Illustration
    - Caption Narration Box
    - Character Dialogue Box
    - Scene Description
    
    Saves inside static/exports/ and returns the web URL path.
    """
    filename = f"comic_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = EXPORTS_DIR / filename

    pdf = ComicPDF(comic_title=comic_title, character_name=character_name, tone=tone)

    # PAGE 1: COVER PAGE
    pdf.add_page()

    # Cover decorative border
    pdf.set_draw_color(25, 25, 35)
    pdf.set_line_width(1.5)
    pdf.rect(10, 10, pdf.w - 20, pdf.h - 20)
    pdf.set_line_width(0.5)
    pdf.rect(12, 12, pdf.w - 24, pdf.h - 24)

    pdf.ln(25)

    # Brand badge
    pdf.set_fill_color(255, 215, 0)
    pdf.set_text_color(15, 15, 20)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "COMICCRAFT STUDIOS PRESENTS", border=1, align="C", fill=True)
    pdf.ln(16)

    # Comic Title
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(30, 30, 45)
    clean_title = _sanitize_pdf_text(comic_title)
    pdf.multi_cell(0, 12, clean_title.upper(), align="C")
    pdf.ln(8)

    # Subtitle / Metadata Table
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(80, 80, 100)
    pdf.cell(0, 7, f"STARRING: {_sanitize_pdf_text(character_name).upper()}", align="C")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Setting: {_sanitize_pdf_text(setting)}   |   Tone: {_sanitize_pdf_text(tone)}   |   Style: {_sanitize_pdf_text(art_style)}", align="C")
    pdf.ln(14)

    # Cover Featured Illustration (Panel 1 or First Panel Image)
    if layout and len(layout) > 0:
        first_img_rel = layout[0].get("image", "").lstrip("/")
        first_img_path = BASE_DIR / first_img_rel
        if first_img_path.exists():
            img_w = 150
            img_x = (pdf.w - img_w) / 2
            pdf.image(str(first_img_path), x=img_x, y=pdf.get_y(), w=img_w)
            pdf.ln(105)

    # Cover quote
    if layout and len(layout) > 0:
        first_quote = layout[0].get("dialogue", "")
        if first_quote:
            pdf.set_fill_color(245, 245, 250)
            pdf.set_font("Helvetica", "I", 11)
            pdf.set_text_color(60, 60, 80)
            pdf.multi_cell(0, 8, f'"{_sanitize_pdf_text(first_quote)}"', align="C", fill=True)

    # INDIVIDUAL PANEL PAGES (1 or 2 panels per page for spacious comic aesthetic)
    for p in layout:
        pdf.add_page()

        panel_num = p.get("panel", 1)
        p_title = _sanitize_pdf_text(p.get("title", f"Panel {panel_num}"))
        p_narration = _sanitize_pdf_text(p.get("narration", ""))
        p_dialogue = _sanitize_pdf_text(p.get("dialogue", ""))
        p_scene = _sanitize_pdf_text(p.get("scene_description", ""))

        # 1. Panel Header Banner
        pdf.set_fill_color(25, 25, 35)
        pdf.set_text_color(255, 220, 0)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(35, 10, f" PANEL {panel_num} ", border=1, align="C", fill=True)
        pdf.set_fill_color(240, 240, 245)
        pdf.set_text_color(20, 20, 30)
        pdf.cell(0, 10, f"  {p_title}", border=1, align="L", fill=True)
        pdf.ln(13)

        # 2. Narration Box (Top classic comic yellow caption)
        if p_narration:
            pdf.set_fill_color(255, 250, 205) # Ivory/Light goldenrod
            pdf.set_draw_color(180, 160, 50)
            pdf.set_text_color(40, 35, 10)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, f"NARRATION: {p_narration}", border=1, fill=True)
            pdf.ln(5)

        # 3. Illustration
        img_rel = p.get("image", "").lstrip("/")
        full_img_path = BASE_DIR / img_rel
        if full_img_path.exists():
            img_w = 160
            img_x = (pdf.w - img_w) / 2
            cur_y = pdf.get_y()
            pdf.set_draw_color(20, 20, 30)
            pdf.set_line_width(0.8)
            pdf.image(str(full_img_path), x=img_x, y=cur_y, w=img_w)
            pdf.rect(img_x, cur_y, img_w, (img_w * 512 / 768))
            pdf.set_line_width(0.2)
            pdf.ln((img_w * 512 / 768) + 6)

        # 4. Dialogue Box (Speech Balloon styling)
        if p_dialogue:
            pdf.set_fill_color(240, 248, 255) # Light Alice Blue
            pdf.set_draw_color(60, 100, 180)
            pdf.set_text_color(15, 30, 60)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 7, f"DIALOGUE: {p_dialogue}", border=1, fill=True)
            pdf.ln(4)

        # 5. Scene Direction Note
        if p_scene:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 120)
            pdf.multi_cell(0, 5, f"Scene Direction: {p_scene}")

    # Output PDF file
    pdf.output(str(pdf_path))
    logger.info(f"Successfully generated PDF: {pdf_path.name}")
    return f"/static/exports/{filename}"
