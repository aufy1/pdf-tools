import fitz  # PyMuPDF
from translator import ai_translator
import os

# Ścieżka do pliku, który wgrasz ręcznie
# Pamiętaj: wgraj "Roboto_Condensed-Regular.ttf" i zmień mu nazwę na "Roboto-Regular.ttf"
FONT_PATH = "/app/fonts/Roboto-Regular.ttf"

def process_pdf_translation(input_path: str, output_path: str):
    # 1. Sprawdzenie czy plik fizycznie istnieje (diagnostyka)
    has_font = os.path.exists(FONT_PATH)
    
    if not has_font:
        print(f"BŁĄD: Nie widzę pliku {FONT_PATH}!")
        print("Upewnij się, że plik jest w folderze server/fonts na Twoim komputerze.")
        # Nie przerywamy, zadziała na domyślnej (bez polskich znaków), żebyś widział, że system żyje
    else:
        print(f"SUKCES: Znaleziono czcionkę: {FONT_PATH}")

    try:
        doc = fitz.open(input_path)
        
        for page_num, page in enumerate(doc):
            # 2. Rejestracja czcionki na KAŻDEJ stronie
            # To jest kluczowe dla poprawnego wyświetlania cyrylicy
            font_ref = "helv" # Domyślna (bezpiecznik)
            
            if has_font:
                try:
                    # Rejestrujemy czcionkę pod wewnętrzną nazwą "myroboto"
                    page.insert_font(fontname="myroboto", fontfile=FONT_PATH)
                    font_ref = "myroboto"
                except Exception as e:
                    print(f"Ostrzeżenie (strona {page_num}): Nie udało się zarejestrować czcionki: {e}")

            # 3. Pobieranie bloków tekstu
            try:
                blocks = page.get_text("dict")["blocks"]
            except Exception:
                continue

            for block in blocks:
                if "lines" not in block: continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        original_text = span["text"]
                        bbox = span["bbox"] # [x0, y0, x1, y1]
                        font_size = span["size"]
                        
                        # Filtrowanie śmieci (pojedyncze litery, same cyfry)
                        if len(original_text.strip()) < 2 or original_text.replace('.','').isdigit():
                            continue

                        # 4. Tłumaczenie
                        try:
                            translated_text = ai_translator.translate_text(original_text, target_lang='uk')
                        except Exception as e:
                            print(f"Błąd tłumaczenia fragmentu: {e}")
                            continue

                        # Jeśli tłumaczenie puste lub identyczne -> pomiń
                        if not translated_text or translated_text == original_text:
                            continue

                        # 5. WHITEOUT (Zamazanie starego tekstu)
                        # Rysujemy biały prostokąt z lekkim marginesem (-1 / +2 px)
                        try:
                            rect = fitz.Rect(bbox[0]-1, bbox[1], bbox[2]+2, bbox[3])
                            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                        except:
                            pass

                        # 6. INSERT (Wstawienie nowego tekstu)
                        try:
                            # Próba wstawienia tekstu
                            res = page.insert_textbox(
                                rect, 
                                translated_text, 
                                fontsize=font_size, 
                                fontname=font_ref, # Używamy "myroboto" lub "helv"
                                color=(0, 0, 0),   # Czarny tekst
                                align=0            # Wyrównanie do lewej
                            )
                            
                            # Logika "Auto-Shrink": Jeśli tekst się nie mieści (res < 0),
                            # próbujemy go wstawić ponownie, ale z mniejszą czcionką (70%)
                            if res < 0:
                                page.insert_textbox(
                                    rect, 
                                    translated_text, 
                                    fontsize=font_size * 0.7, 
                                    fontname=font_ref,
                                    color=(0, 0, 0),
                                    align=0
                                )
                        except Exception as e:
                            # Ignorujemy błąd pojedynczego boksu, żeby reszta strony się zrobiła
                            print(f"Błąd wstawiania tekstu w boksie: {e}")

        # Zapisz wynik
        doc.save(output_path)
        doc.close()
        print(f"Zakończono przetwarzanie: {output_path}")
        return True

    except Exception as e:
        print(f"CRITICAL ERROR (cały dokument): {e}")
        # Tu rzucamy błąd wyżej, żeby API wiedziało, że coś poszło bardzo nie tak
        raise e