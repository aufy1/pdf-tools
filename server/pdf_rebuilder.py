"""
pdf_rebuilder.py

Strategia "Smart Separation" z DEBUGOWANIEM:
1. TABELE: Używa draw_table_cell z tables.py.
2. TEKST: Używa draw_line_segments (start od lewej).
3. DEBUG: Rysuje ramki (Czerwona=Tabela, Zielona=Tekst).
"""

import fitz
import os
import sys
from typing import List, Dict, Tuple

# Importy z pakietu
from layout_engine import LayoutEngine, BlockType
from layout_engine.tables import draw_table_cell 
from layout_engine.tagger import StyleTagger, RichSegment 

from translator import ai_translator
from pdf_cleaner import create_clean_layout_pdf
from layout_engine.config import DEBUG_MODE

# --- HELPERY DLA TEKSTU ---

def get_fitz_font_object(flags: int, font_objects: Dict[str, fitz.Font]) -> fitz.Font:
    is_bold = (flags & 2**4); is_italic = (flags & 2**1)
    if is_bold and is_italic: return font_objects.get("bold_italic", font_objects.get("regular"))
    if is_bold: return font_objects.get("bold", font_objects.get("regular"))
    if is_italic: return font_objects.get("italic", font_objects.get("regular"))
    return font_objects.get("regular")

def get_fontname_for_flags(flags: int, font_map: Dict[str, str]) -> str:
    is_bold = (flags & 2**4); is_italic = (flags & 2**1)
    if is_bold and is_italic: return font_map.get("bold_italic", "helv")
    if is_bold: return font_map.get("bold", "helv")
    if is_italic: return font_map.get("italic", "helv")
    return font_map.get("regular", "helv")

def draw_line_segments(page: fitz.Page, rect: fitz.Rect, segments: List[RichSegment], font_objects: Dict[str, fitz.Font], font_map_names: Dict[str, str], dry_run: bool = False) -> Tuple[bool, float]:
    """
    Rysuje tekst w JEDNEJ linii (bez word-wrapu), zaczynając sztywno od LEWEJ (rect.x0).
    """
    if not segments: return True, 0.0
    
    cursor_x = rect.x0
    baseline_y = rect.y1 - 2.0 
    total_width = 0.0
    
    # 1. Obliczanie szerokości
    for seg in segments:
        font_obj = get_fitz_font_object(seg.font_flags, font_objects)
        total_width += font_obj.text_length(seg.text, fontsize=seg.size)
    
    if total_width > (rect.width * 1.05): return False, total_width

    # 2. Rysowanie
    if not dry_run:
        for seg in segments:
            font_name = get_fontname_for_flags(seg.font_flags, font_map_names)
            font_obj = get_fitz_font_object(seg.font_flags, font_objects)
            try:
                page.insert_text(
                    (cursor_x, baseline_y), 
                    seg.text, 
                    fontname=font_name, 
                    fontsize=seg.size, 
                    color=seg.color
                )
            except: pass
            
            cursor_x += font_obj.text_length(seg.text, fontsize=seg.size)
            
    return True, total_width

# --- GŁÓWNY PROCES ---

def process_pdf_rebuild(input_path: str, output_path: str, source_lang: str, target_lang: str) -> None:
    temp_clean_path = "temp_clean_layout.pdf"
    print(f"1. Tworzenie czystego layoutu...")
    try: create_clean_layout_pdf(input_path, temp_clean_path)
    except Exception as e: print(f"Błąd cleanera: {e}"); return

    src_doc = fitz.open(input_path)
    tgt_doc = fitz.open(temp_clean_path)

    # --- FONT SETUP ---
    font_paths = {
        "regular": "/app/fonts/Roboto_Condensed-Regular.ttf",
        "bold": "/app/fonts/Roboto_Condensed-Bold.ttf",
        "italic": "/app/fonts/Roboto_Condensed-Italic.ttf",
        "bold_italic": "/app/fonts/Roboto_Condensed-BoldItalic.ttf"
    }
    font_binaries = {}
    fallback_path = "arial.ttf"
    for style, path in font_paths.items():
        if os.path.exists(path):
            with open(path, "rb") as f: font_binaries[style] = f.read()
    if not font_binaries and os.path.exists(fallback_path):
        with open(fallback_path, "rb") as f:
            blob = f.read()
            font_binaries = {k: blob for k in font_paths.keys()}

    fitz_font_objects = {}
    default_calc_font = fitz.Font("helv")
    for style, blob in font_binaries.items():
        try: fitz_font_objects[style] = fitz.Font(fontbuffer=blob)
        except: pass
    fitz_font_objects.setdefault("regular", default_calc_font)

    tagger = StyleTagger()

    print(f"2. Przetwarzanie (DEBUG MODE = {DEBUG_MODE})...")

    for page_num, src_page in enumerate(src_doc):
        tgt_page = tgt_doc[page_num]
        print(f"   -> Strona {page_num + 1}/{len(src_doc)}")

        font_map_names = {}
        for style, buffer in font_binaries.items():
            fname = f"F{page_num}_{style}"
            try:
                tgt_page.insert_font(fontname=fname, fontbuffer=buffer)
                font_map_names[style] = fname
            except: pass

        engine = LayoutEngine(src_page)
        blocks = engine.run() 
        
        for b in blocks:
            # Pomiń puste, ale rysuj ramki debugowe nawet dla pustych/nietłumaczonych
            # żeby widzieć co algorytm wykrył
            
            is_table_cell = (b.block_type == BlockType.TABLE_CELL)

            # =========================================================
            #               RYSOWANIE RAMEK DEBUGOWYCH
            # =========================================================
            if DEBUG_MODE:
                if is_table_cell:
                    # CZERWONA ramka dla TABEL
                    try: tgt_page.draw_rect(b.bbox, color=(1, 0, 0), width=0.8)
                    except: pass
                else:
                    # ZIELONA ramka dla TEKSTU
                    try: tgt_page.draw_rect(b.bbox, color=(0, 1, 0), width=0.5)
                    except: pass
            # =========================================================

            if b.block_type in [BlockType.NO_TRANSLATE, BlockType.ISOLATED_SYMBOL] or not b.text.strip():
                continue

            # =========================
            # ŚCIEŻKA A: TABELA
            # =========================
            if is_table_cell:
                try:
                    trans = ai_translator.translate_text(b.text, source_lang.lower(), target_lang.lower())
                    final_text = trans if trans else b.text
                except: final_text = b.text
                
                b.text = final_text
                draw_table_cell(tgt_page, b, font_map_names, fitz_font_objects)

            # =========================
            # ŚCIEŻKA B: ZWYKŁY TEKST
            # =========================
            else:
                tagged_text = tagger.spans_to_tagged_text(b.original_spans)
                try:
                    trans = ai_translator.translate_text(tagged_text, source_lang.lower(), target_lang.lower())
                    final_text = trans if trans else tagged_text
                except: final_text = tagged_text

                rich_segments = tagger.parse_tagged_response(final_text, b.style)
                
                start_fs = b.style.size
                curr_scale = 1.0 
                base_rect = fitz.Rect(b.bbox)
                best_segments = None
                
                while curr_scale > 0.4:
                    test_segments = []
                    for s in rich_segments:
                        test_segments.append(RichSegment(
                            text=s.text, font_flags=s.font_flags, color=s.color, size=max(4.0, s.size * curr_scale)
                        ))
                    fits, _ = draw_line_segments(tgt_page, base_rect, test_segments, fitz_font_objects, font_map_names, dry_run=True)
                    if fits: best_segments = test_segments; break
                    curr_scale -= 0.1
                
                if best_segments:
                    draw_line_segments(tgt_page, base_rect, best_segments, fitz_font_objects, font_map_names, dry_run=False)
                elif rich_segments:
                    draw_line_segments(tgt_page, base_rect, rich_segments, fitz_font_objects, font_map_names, dry_run=False)

    src_doc.close()
    tgt_doc.save(output_path, garbage=4, deflate=True)
    tgt_doc.close()
    if os.path.exists(temp_clean_path): os.remove(temp_clean_path)

if __name__ == "__main__":
    process_pdf_rebuild("input.pdf", "output.pdf", "PL", "UK")