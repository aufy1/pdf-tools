"""
pdf_cleaner.py

Odpowiedzialność:
1. Tworzenie tymczasowej kopii pliku PDF.
2. Usuwanie WSZYSTKIEGO, co jest warstwą tekstową.
3. Zachowanie obrazów (bitmap) i grafiki wektorowej (tabel, linii, tła) w stanie nienaruszonym.
"""

import fitz

def create_clean_layout_pdf(input_path: str, output_temp_path: str) -> None:
    """
    Otwiera PDF, usuwa z niego wszelki tekst (zostawiając grafikę) 
    i zapisuje jako plik tymczasowy gotowy do wstawienia tłumaczeń.
    """
    doc = fitz.open(input_path)

    for page in doc:
        text_blocks = page.get_text("blocks")
        
        for block in text_blocks:
            rect = fitz.Rect(block[:4])
            
            page.add_redact_annot(rect)

        page.apply_redactions(images=0, graphics=0, text=0)
        
        page.clean_contents()

    # Zapisz wyczyszczony plik
    doc.save(output_temp_path, garbage=4, deflate=True)
    doc.close()

if __name__ == "__main__":
    create_clean_layout_pdf("input.pdf", "clean_debug.pdf")
    print("Stworzono plik clean_debug.pdf bez tekstu (poprawiona wersja).")