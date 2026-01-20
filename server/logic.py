# /server/logic.py
import fitz  # PyMuPDF
from translator import ai_translator
import os

FONT_PATH = "fonts/Roboto-Regular.ttf"

def process_pdf_translation(input_path: str, output_path: str):
    """
    Główna logika: Otwiera PDF, iteruje po blokach tekstu,
    tłumaczy, czyści tło i nadrukowuje nowy tekst.
    """
    doc = fitz.open(input_path)
    
    # Rejestracja czcionki z obsługą cyrylicy
    font_name = "roboto"
    if os.path.exists(FONT_PATH):
        fitz.Font(fontname=font_name, fontfile=FONT_PATH, script="cyrl")
    else:
        print("UWAGA: Brak pliku czcionki! Cyrylica może nie działać.")
        font_name = "helv" # Fallback (nie obsługuje UA dobrze)

    for page_num, page in enumerate(doc):
        # 1. Pobieramy strukturę tekstu (JSON dict)
        # flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    original_text = span["text"]
                    bbox = span["bbox"] # [x0, y0, x1, y1]
                    
                    # Filtrowanie: Ignoruj liczby i bardzo krótkie teksty
                    if len(original_text.strip()) < 2 or original_text.replace('.','').isdigit():
                        continue

                    # 2. Tłumaczenie
                    translated_text = ai_translator.translate_text(original_text, target_lang='uk')

                    if translated_text == original_text:
                        continue

                    # 3. KROK CLEANING (Biały Korektor)
                    # Rysujemy prostokąt w kolorze tła (zakładamy biały)
                    # Padding -0.5, żeby nie zamazać linii tabeli obok
                    clean_rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
                    page.draw_rect(clean_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

                    # 4. KROK OVERLAY (Wstawianie tekstu)
                    # Obliczamy rozmiar, żeby zmieścić się w pudełku
                    insert_rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
                    
                    # Logika Auto-Fit (Prosta)
                    fontsize = span["size"]
                    
                    # Wstawiamy Textbox
                    # align=0 (left), 1 (center) - bierzemy z oryginału jeśli możliwe, tu default left
                    res = page.insert_textbox(
                        insert_rect, 
                        translated_text, 
                        fontsize=fontsize, 
                        fontname=font_name,
                        color=(0, 0, 0), # Czarny
                        align=0 
                    )

                    # Jeśli res < 0, to tekst się nie zmieścił.
                    # W wersji PRO tutaj byłaby pętla zmniejszająca fontsize
                    if res < 0:
                        # Próba ratunkowa: mniejszy font
                        page.insert_textbox(
                            insert_rect, 
                            translated_text, 
                            fontsize=fontsize * 0.8, 
                            fontname=font_name,
                            color=(0, 0, 0)
                        )

    doc.save(output_path)
    doc.close()