"""
pdf_rebuilder.py

Odpowiedzialność:
1. Orkiestracja procesu tłumaczenia.
2. Wykorzystanie pdf_cleaner do przygotowania tła.
3. Analiza układu z oryginału (LayoutEngine).
4. Wstawianie przetłumaczonego tekstu na czyste tło.
"""

import fitz
import os
import sys
from layout_engine import LayoutEngine, BlockType
from translator import ai_translator
from pdf_cleaner import create_clean_layout_pdf

def process_pdf_rebuild(input_path: str, output_path: str, source_lang: str, target_lang: str) -> None:
    temp_clean_path = "temp_clean_layout.pdf"
    
    print(f"1. Tworzenie czystego layoutu (klonowanie grafiki)...")
    try:
        # Krok 1: Stwórz kopię PDF pozbawioną tekstu, ale z zachowaną grafiką
        create_clean_layout_pdf(input_path, temp_clean_path)
    except Exception as e:
        print(f"Błąd podczas czyszczenia PDF: {e}")
        return

    # Otwieramy oryginał (do czytania tekstu) i czystego klona (do pisania)
    src_doc = fitz.open(input_path)
    tgt_doc = fitz.open(temp_clean_path)

    # Konfiguracja czcionek - (Tutaj bez zmian, ładujemy je raz)
    font_paths = {
        "regular": "/app/fonts/Roboto_Condensed-Regular.ttf",
        "bold": "/app/fonts/Roboto_Condensed-Bold.ttf",
        "italic": "/app/fonts/Roboto_Condensed-Italic.ttf",
        "bold_italic": "/app/fonts/Roboto_Condensed-BoldItalic.ttf"
    }
    
    available_fonts = {}
    fallback_path = "arial.ttf"
    
    for style, path in font_paths.items():
        if os.path.exists(path):
            with open(path, "rb") as f: available_fonts[style] = f.read()
            
    if not available_fonts:
        if os.path.exists(fallback_path):
            with open(fallback_path, "rb") as f:
                blob = f.read()
                available_fonts = {k: blob for k in font_paths.keys()}

    print(f"2. Przetwarzanie stron i tłumaczenie...")

    for page_num, src_page in enumerate(src_doc):
        tgt_page = tgt_doc[page_num]
        
        print(f"   -> Strona {page_num + 1}/{len(src_doc)}")

        font_map = {}
        primary_font = "helv"
        
        for style, buffer in available_fonts.items():
            fname = f"F{page_num}_{style}"
            try:
                tgt_page.insert_font(fontname=fname, fontbuffer=buffer)
                font_map[style] = fname
                primary_font = fname
            except Exception: pass

        engine = LayoutEngine(src_page)
        blocks = engine.run() 
        
        for b in blocks:
            text_to_insert = b.text
            if b.block_type not in [BlockType.NO_TRANSLATE, BlockType.ISOLATED_SYMBOL] and b.text.strip():
                try:
                    translated = ai_translator.translate_text(
                        b.text, source_lang.lower(), target_lang.lower()
                    )
                    text_to_insert = translated if translated else b.text
                except Exception:
                    text_to_insert = b.text
            
            if not text_to_insert.strip(): continue

            fitz_font = font_map.get(b.style.font_key, primary_font)
            
            insert_rect = fitz.Rect(b.bbox.x0, b.bbox.y0, b.bbox.x1 + 10, b.bbox.y1 + 5)
            
            fontsize = b.style.size
            if fontsize < 5: fontsize = 5
            
            curr_fs = fontsize
            inserted = False
            
            while curr_fs >= 5.0:
                try:
                    res = tgt_page.insert_textbox(
                        insert_rect, 
                        text_to_insert, 
                        fontsize=curr_fs, 
                        fontname=fitz_font, 
                        color=b.style.color,
                        align=b.style.align
                    )
                    if res >= 0: 
                        inserted = True
                        break
                except Exception: pass
                curr_fs -= 0.5
            
            # Fallback (insert_text)
            if not inserted:
                try:
                    tgt_page.insert_text(
                        (b.bbox.x0, b.bbox.y1), 
                        text_to_insert,
                        fontsize=fontsize,
                        fontname=fitz_font,
                        color=b.style.color
                    )
                except Exception as e:
                    print(f"Failed to insert text block: {e}")

    src_doc.close()
    
    # Zapisz wynikowy plik
    tgt_doc.save(output_path, garbage=4, deflate=True)
    tgt_doc.close()
    
    # Sprzątanie pliku tymczasowego
    if os.path.exists(temp_clean_path):
        os.remove(temp_clean_path)

if __name__ == "__main__":
    i = "input.pdf"
    o = "output.pdf"
    if len(sys.argv) > 2:
        i, o = sys.argv[1], sys.argv[2]
    
    print(f"Rebuilding PDF (Clone Method): {i} -> {o}")
    try:
        process_pdf_rebuild(i, o, "PL", "UK")
        print("Success!")
    except Exception as e:
        print(f"Fatal Error: {e}")