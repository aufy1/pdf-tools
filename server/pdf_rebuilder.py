"""
pdf_rebuilder.py

Zmiany:
- Logika startowa czcionki: 
  * Tabela: start = oryginał - 1pt.
  * Reszta: start = oryginał.
- Zachowano algorytm stopniowego zmniejszania (shrink-to-fit) w pętli.
- Zachowano centrowanie pionowe dla tabel.
"""

import fitz
import os
import sys
import math
from layout_engine import LayoutEngine, BlockType
from translator import ai_translator
from pdf_cleaner import create_clean_layout_pdf

def calculate_text_height(text: str, font: fitz.Font, fontsize: float, width: float) -> float:
    """
    Symuluje wysokość tekstu w pikselach (z uwzględnieniem zawijania wierszy).
    """
    if width <= 0: return fontsize * 1.2
    
    # Usuwamy nadmiarowe białe znaki, które mogą sztucznie zawyżać wysokość
    paragraphs = text.split('\n')
    lines = 0
    
    # Pobieramy szerokość spacji raz
    space_width = font.text_length(" ", fontsize)
    # Standardowa interlinia ~1.2
    line_height = fontsize * 1.2

    for p in paragraphs:
        if not p:
            lines += 1
            continue
            
        words = p.split()
        current_line_width = 0.0
        lines += 1 # Pierwsza linia akapitu
        
        for word in words:
            word_width = font.text_length(word, fontsize)
            
            # Słowo szersze niż kolumna -> i tak zajmie linię
            if word_width > width:
                if current_line_width > 0:
                    lines += 1
                current_line_width = 0 # Reset po wymuszonym łamaniu
                continue

            if current_line_width + word_width <= width:
                current_line_width += word_width + space_width
            else:
                lines += 1
                current_line_width = word_width + space_width
                
    return lines * line_height

def process_pdf_rebuild(input_path: str, output_path: str, source_lang: str, target_lang: str) -> None:
    temp_clean_path = "temp_clean_layout.pdf"
    
    print(f"1. Tworzenie czystego layoutu (klonowanie grafiki)...")
    try:
        create_clean_layout_pdf(input_path, temp_clean_path)
    except Exception as e:
        print(f"Błąd podczas czyszczenia PDF: {e}")
        return

    src_doc = fitz.open(input_path)
    tgt_doc = fitz.open(temp_clean_path)

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

    # Cache obiektów czcionek do obliczeń
    fitz_font_objects = {}
    for style, blob in font_binaries.items():
        try:
            fitz_font_objects[style] = fitz.Font(fontbuffer=blob)
        except Exception: pass
    
    default_calc_font = fitz.Font("helv")

    print(f"2. Przetwarzanie stron i tłumaczenie...")

    for page_num, src_page in enumerate(src_doc):
        tgt_page = tgt_doc[page_num]
        print(f"   -> Strona {page_num + 1}/{len(src_doc)}")

        font_map_names = {}
        primary_font_name = "helv"
        
        for style, buffer in font_binaries.items():
            fname = f"F{page_num}_{style}"
            try:
                tgt_page.insert_font(fontname=fname, fontbuffer=buffer)
                font_map_names[style] = fname
                primary_font_name = fname
            except Exception: pass

        engine = LayoutEngine(src_page)
        blocks = engine.run() 
        
        for b in blocks:
            text_to_insert = b.text
            
            # Tłumaczenie
            if b.block_type not in [BlockType.NO_TRANSLATE, BlockType.ISOLATED_SYMBOL] and b.text.strip():
                try:
                    translated = ai_translator.translate_text(
                        b.text, source_lang.lower(), target_lang.lower()
                    )
                    text_to_insert = translated if translated else b.text
                except Exception:
                    text_to_insert = b.text
            
            if not text_to_insert.strip(): continue

            font_insert_name = font_map_names.get(b.style.font_key, primary_font_name)
            calc_font_obj = fitz_font_objects.get(b.style.font_key, default_calc_font)

            # --- KONFIGURACJA STARTOWA ---
            # LayoutEngine ustawia align=1 dla komórek tabeli
            is_table_cell = (b.style.align == 1)
            original_fontsize = b.style.size

            if is_table_cell:
                # Tabela: Startujemy od (Oryginał - 1.0)
                start_fs = original_fontsize - 1.0
            else:
                # Zwykły tekst: Startujemy od (Oryginał)
                start_fs = original_fontsize

            # Zabezpieczenie przed zbyt małą czcionką na starcie
            if start_fs < 5.0: start_fs = 5.0

            # Bazowy prostokąt
            base_rect = fitz.Rect(b.bbox.x0, b.bbox.y0, b.bbox.x1, b.bbox.y1)
            
            # Jeśli to NIE jest tabela, dodajemy minimalny margines błędu do ramki, 
            # żeby tekst nie był ucinany przez drobne różnice w renderowaniu fontów
            if not is_table_cell:
                base_rect.x1 += 2
                base_rect.y1 += 2

            curr_fs = start_fs
            inserted = False
            
            # Pętla SHRINK-TO-FIT (zmniejszamy aż wejdzie)
            while curr_fs >= 4.0:
                insert_rect = fitz.Rect(base_rect)
                
                # --- LOGIKA CENTROWANIA PIONOWEGO (TYLKO TABELE) ---
                if is_table_cell:
                    try:
                        text_pixel_height = calculate_text_height(
                            text_to_insert, 
                            calc_font_obj, 
                            curr_fs, 
                            insert_rect.width
                        )
                        available_height = insert_rect.height
                        
                        if text_pixel_height < available_height:
                            padding_top = (available_height - text_pixel_height) / 2
                            # Przesuwamy w dół, ale zostawiamy margines błędu (np. 1px),
                            # żeby insert_textbox nie uznał, że tekst wystaje dołem.
                            insert_rect.y0 += max(0, padding_top - 1)
                    except Exception:
                        pass
                # ---------------------------------------------------

                try:
                    res = tgt_page.insert_textbox(
                        insert_rect, 
                        text_to_insert, 
                        fontsize=curr_fs, 
                        fontname=font_insert_name, 
                        color=b.style.color,
                        align=b.style.align # 1=Center dla tabel
                    )
                    
                    if res >= 0: 
                        inserted = True
                        break # Sukces, tekst wszedł
                except Exception: pass
                
                # Jeśli nie wszedł, zmniejszamy czcionkę i próbujemy znowu
                curr_fs -= 0.5
            
            # Fallback (insert_text) - jeśli mimo zmniejszania do 4pt się nie udało
            if not inserted:
                try:
                    # W fallbacku używamy oryginalnego start_fs, żeby było czytelnie
                    tgt_page.insert_text(
                        (base_rect.x0, base_rect.y1), 
                        text_to_insert,
                        fontsize=start_fs, 
                        fontname=font_insert_name,
                        color=b.style.color
                    )
                except Exception as e:
                    print(f"Failed to insert text block: {e}")

    src_doc.close()
    tgt_doc.save(output_path, garbage=4, deflate=True)
    tgt_doc.close()
    
    if os.path.exists(temp_clean_path):
        os.remove(temp_clean_path)

if __name__ == "__main__":
    i = "input.pdf"
    o = "output.pdf"
    if len(sys.argv) > 2:
        i, o = sys.argv[1], sys.argv[2]
    
    print(f"Rebuilding PDF (Final Logic): {i} -> {o}")
    try:
        process_pdf_rebuild(i, o, "PL", "UK")
        print("Success!")
    except Exception as e:
        print(f"Fatal Error: {e}")