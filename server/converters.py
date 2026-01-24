import os
import subprocess
from pdf2docx import Converter

def convert_pdf_to_word(input_path: str, output_path: str):
    cv = None
    try:
        print(f"SYSTEM: Rozpoczynam konwersję PDF->DOCX (HIGH GRAPHICS): {input_path}")
        
        cv = Converter(input_path)

        cv.convert(output_path, start=0, end=None, multi_processing=True, cpu_count=2)
        
        print(f"SYSTEM: Zapisano DOCX: {output_path}")

    except Exception as e:
        print(f"ERR: Błąd konwersji do Worda: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise e
    finally:
        if cv:
            cv.close()