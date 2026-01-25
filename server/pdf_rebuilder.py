"""
pdf_rebuilder.py

Odpowiedzialność:
1. Rekonstrukcja dokumentu PDF (tworzenie nowych stron).
2. Przenoszenie obrazów i grafiki wektorowej (zachowanie layoutu).
3. Zarządzanie czcionkami (wsparcie dla Cyrylicy).
4. Integracja z tłumaczem AI.
5. Fizyczne wstawianie przetłumaczonego tekstu w odpowiednie miejsca.
"""

import fitz
import os
import sys
# Importujemy moduł silnika (zakładając, że plik nazywa się layout_engine.py)
from layout_engine import LayoutEngine, BlockType
# Import tłumacza (zgodnie z Twoim istniejącym kodem)
from translator import ai_translator

# ==================================================================================
# SILNIK REKONSTRUKCJI (RECONSTRUCTION ENGINE)
# ==================================================================================

def transfer_images(source_page: fitz.Page, target_page: fitz.Page):
    """Przenosi obrazy (bitmapy) z jednej strony na drugą."""
    image_list = source_page.get_images(full=True)
    for img in image_list:
        try:
            xref = img[0]
            bbox = source_page.get_image_bbox(img)
            # Pobieramy dane obrazu
            image_bytes = source_page.parent.extract_image(xref)["image"]
            target_page.insert_image(bbox, stream=image_bytes)
        except Exception as e:
            print(f"Warning transferring image: {e}")

def transfer_drawings(source_page: fitz.Page, target_page: fitz.Page):
    """
    Kopiuje grafikę wektorową (tabele, linie). 
    Zawiera zabezpieczenia przed błędami typów (None/Float).
    """
    drawings = source_page.get_drawings()
    shape = target_page.new_shape()
    
    for d in drawings:
        try:
            # Rysowanie kształtów
            for item in d["items"]:
                cmd = item[0]
                if cmd == "l":
                    shape.draw_line(item[1], item[2])
                elif cmd == "re":
                    shape.draw_rect(item[1])
                elif cmd == "c":
                    shape.draw_bezier(item[1], item[2], item[3], item[4])

            # Bezpieczne pobieranie właściwości (fix na fz_format_double)
            raw_width = d.get("width")
            # Jeśli width jest None, ustaw domyślne 1.0, jeśli jest liczbą, upewnij się że to float
            width = float(raw_width) if (raw_width is not None) else 1.0

            stroke = d.get("color") # Może być None
            fill = d.get("fill")    # Może być None
            
            if stroke is not None:
                shape.finish(color=stroke, fill=fill, width=width)
            else:
                shape.finish(fill=fill, width=width)
                
        except Exception as e:
            # Ignorujemy drobne błędy rysowania, żeby nie przerywać procesu
            continue
            
    shape.commit()

def process_pdf_rebuild(input_path: str, output_path: str, source_lang: str, target_lang: str) -> None:
    src_doc = fitz.open(input_path)
    tgt_doc = fitz.open()

    # Konfiguracja czcionek - ścieżki (dostosuj do środowiska Docker/Local)
    font_paths = {
        "regular": "/app/fonts/Roboto_Condensed-Regular.ttf",
        "bold": "/app/fonts/Roboto_Condensed-Bold.ttf",
        "italic": "/app/fonts/Roboto_Condensed-Italic.ttf",
        "bold_italic": "/app/fonts/Roboto_Condensed-BoldItalic.ttf"
    }
    
    available_fonts = {}
    fallback_path = "arial.ttf" # Fallback lokalny
    
    # Ładowanie dostępnych czcionek do pamięci
    for style, path in font_paths.items():
        if os.path.exists(path):
            with open(path, "rb") as f: available_fonts[style] = f.read()
            
    if not available_fonts:
        if os.path.exists(fallback_path):
            with open(fallback_path, "rb") as f:
                blob = f.read()
                available_fonts = {k: blob for k in font_paths.keys()}
        else:
            print("WARNING: No custom fonts found. Cyrillic support might fail.")

    # Główna pętla po stronach
    for page_num, src_page in enumerate(src_doc):
        # 1. Tworzenie nowej, pustej strony o tych samych wymiarach
        tgt_page = tgt_doc.new_page(width=src_page.rect.width, height=src_page.rect.height)
        
        # 2. Rejestracja czcionek na nowej stronie
        font_map = {}
        primary_font = "helv"
        
        for style, buffer in available_fonts.items():
            fname = f"F{page_num}_{style}"
            try:
                tgt_page.insert_font(fontname=fname, fontbuffer=buffer)
                font_map[style] = fname
                primary_font = fname
            except Exception: pass

        # 3. Kopiowanie warstwy wizualnej (bez tekstu)
        transfer_drawings(src_page, tgt_page)
        transfer_images(src_page, tgt_page)

        # 4. Przetwarzanie tekstu (Extract -> Translate -> Insert)
        # Używamy LayoutEngine z zaimportowanego pliku
        engine = LayoutEngine(src_page)
        blocks = engine.run() 
        
        for b in blocks:
            # Pomijamy nietłumaczalne bloki
            text_to_insert = b.text
            if b.block_type not in [BlockType.NO_TRANSLATE, BlockType.ISOLATED_SYMBOL] and b.text.strip():
                try:
                    # Wywołanie zewnętrznego tłumacza
                    translated = ai_translator.translate_text(
                        b.text, source_lang.lower(), target_lang.lower()
                    )
                    text_to_insert = translated if translated else b.text
                except Exception:
                    text_to_insert = b.text
            
            if not text_to_insert.strip(): continue

            # Wybór czcionki
            fitz_font = font_map.get(b.style.font_key, primary_font)
            
            # Lekkie poszerzenie ramki (padding), bo tekst tłumaczony może być dłuższy
            insert_rect = fitz.Rect(b.bbox.x0, b.bbox.y0, b.bbox.x1 + 10, b.bbox.y1 + 5)
            
            fontsize = b.style.size
            if fontsize < 5: fontsize = 5
            
            inserted = False
            curr_fs = fontsize
            
            # Algorytm dopasowania tekstu: zmniejszamy czcionkę, jeśli się nie mieści
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
            
            # Fallback: jeśli insert_textbox zawiódł, wstawiamy tekst "na sztywno" w punkcie
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
    tgt_doc.save(output_path)
    tgt_doc.close()

if __name__ == "__main__":
    i = "input.pdf"
    o = "output.pdf"
    if len(sys.argv) > 2:
        i, o = sys.argv[1], sys.argv[2]
    
    print(f"Rebuilding PDF (Split Files): {i} -> {o}")
    try:
        process_pdf_rebuild(i, o, "PL", "UK")
        print("Success!")
    except Exception as e:
        print(f"Fatal Error: {e}")