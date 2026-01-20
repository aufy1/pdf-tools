import fitz  # PyMuPDF
from translator import ai_translator
import os
import re

# --- KONFIGURACJA ---
FONT_PATHS = {
    "regular":     "/app/fonts/Roboto_Condensed-Regular.ttf",
    "bold":        "/app/fonts/Roboto_Condensed-Bold.ttf",
    "italic":      "/app/fonts/Roboto_Condensed-Italic.ttf",
    "bold_italic": "/app/fonts/Roboto_Condensed-BoldItalic.ttf"
}

# Ładowanie globalne
GLOBAL_FONT_BUFFERS = {}
print("SYSTEM: Ładowanie czcionek...")
for key, path in FONT_PATHS.items():
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                GLOBAL_FONT_BUFFERS[key] = f.read()
        except Exception as e:
            print(f"  ERR: {path}: {e}")

def srgb_to_rgb(srgb_int):
    if not isinstance(srgb_int, int): return (0, 0, 0)
    r = ((srgb_int >> 16) & 255) / 255.0
    g = ((srgb_int >> 8) & 255) / 255.0
    b = (srgb_int & 255) / 255.0
    return (r, g, b)

def get_line_style(spans):
    if not spans: return 11, 0, 0
    style_counts = {}
    for s in spans:
        txt = s["text"].strip()
        if not txt: continue
        key = (s["size"], s["flags"], s["color"])
        style_counts[key] = style_counts.get(key, 0) + len(txt)
    if not style_counts:
        return spans[0]["size"], spans[0]["flags"], spans[0]["color"]
    best_style = max(style_counts, key=style_counts.get)
    return best_style[0], best_style[1], best_style[2]

def should_translate(text):
    text = text.strip()
    if len(text) < 2: return False
    if text.replace('.', '').replace(',', '').replace(' ', '').isdigit(): return False
    
    # Rozszerzona lista słów kluczowych, których nie ruszamy
    keywords = ["PIT", "CIT", "NIP", "PESEL", "REGON", "KRS", "IP", "PWA", "RUB"]
    if any(k in text for k in keywords) and len(text) < 15: return False
    
    if not re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', text): return False
    return True

def process_pdf_translation(input_path: str, output_path: str):
    
    if "regular" not in GLOBAL_FONT_BUFFERS:
        print("CRITICAL: Brak fontów. Zwracam oryginał.")
        doc = fitz.open(input_path)
        doc.save(output_path)
        return

    try:
        doc_src = fitz.open(input_path)
        pdf_bytes = doc_src.tobytes(garbage=4, deflate=True)
        doc_src.close()
        doc = fitz.open("pdf", pdf_bytes)
    except Exception as e:
        print(f"Błąd PDF: {e}")
        raise e

    for page_num, page in enumerate(doc):
        prefix = f"p{page_num}"
        registered_fonts = {} 
        for style_key, buffer in GLOBAL_FONT_BUFFERS.items():
            font_name = f"{prefix}_{style_key}"
            try:
                page.insert_font(fontname=font_name, fontbuffer=buffer)
                registered_fonts[style_key] = font_name
            except: pass

        try:
            blocks = page.get_text("dict")["blocks"]
        except:
            continue

        operations = [] 

        for block in blocks:
            if "lines" not in block: continue

            for line in block["lines"]:
                full_text = "".join([s["text"] for s in line["spans"]])
                
                if not should_translate(full_text):
                    continue

                font_size, flags, color_int = get_line_style(line["spans"])
                text_color = srgb_to_rgb(color_int)
                
                is_bold = bool(flags & 2**4)
                is_italic = bool(flags & 2**1)
                
                style_key = "regular"
                if is_bold and is_italic: style_key = "bold_italic"
                elif is_bold: style_key = "bold"
                elif is_italic: style_key = "italic"
                
                if style_key not in registered_fonts:
                    if is_bold and "bold" in registered_fonts: style_key = "bold"
                    else: style_key = "regular"
                
                font_ref = registered_fonts.get(style_key, registered_fonts.get("regular"))

                try:
                    translated_text = ai_translator.translate_text(full_text, target_lang='uk')
                except: continue

                if not translated_text or translated_text == full_text: continue

                bbox = line["bbox"]
                clean_rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])

                operations.append({
                    "clean_rect": clean_rect,
                    "bbox": bbox,
                    "text": translated_text,
                    "orig_size": font_size,
                    "font_ref": font_ref,
                    "color": text_color
                })

        if not operations: continue

        # --- WYKONANIE ---
        
        final_ops = []
        for op in operations:
            try:
                page.insert_text(op["bbox"][:2], "t", fontname=op["font_ref"], fontsize=5, render_mode=1)
                final_ops.append(op)
            except: continue

        if final_ops:
            for op in final_ops:
                page.add_redact_annot(op["clean_rect"], fill=False)
            page.apply_redactions()

            for op in final_ops:
                bbox = op["bbox"]
                
                # --- KLUCZOWA KOREKTA POZYCJONOWANIA ---
                
                # Dynamiczny offset w dół.
                # Bierzemy 25% wielkości czcionki (np. dla 10pt -> 2.5pt w dół)
                # Ale nie mniej niż 2.0pt. To odsunie tekst od górnej krawędzi (sufitu).
                y_correction = max(2.0, op["orig_size"] * 0.25)
                
                insert_rect = fitz.Rect(
                    bbox[0], 
                    bbox[1] + y_correction,     # Przesunięcie w dół (padding top)
                    bbox[2] + 50,               
                    # Ważne: Dolną krawędź też przesuwamy o tyle samo + mały margines (1.5),
                    # żeby zachować wysokość oryginału i zmusić pętlę do zmniejszenia czcionki, 
                    # jeśli tekst jest za duży.
                    bbox[3] + y_correction + 1.5  
                )
                
                current_size = op["orig_size"]
                min_allowed_size = max(6, current_size * 0.6)
                step = 0.5
                success = False
                
                while current_size >= min_allowed_size:
                    try:
                        res = page.insert_textbox(
                            insert_rect, 
                            op["text"], 
                            fontsize=current_size, 
                            fontname=op["font_ref"], 
                            color=op["color"],
                            align=0
                        )
                        if res >= 0:
                            success = True
                            break 
                    except:
                        break
                    
                    current_size -= step

                if not success:
                    try:
                        # Fallback z lekkim rozszerzeniem w dół
                        expanded_rect = fitz.Rect(
                            bbox[0], 
                            bbox[1] + y_correction, 
                            bbox[2] + 60, 
                            bbox[3] + 15 
                        )
                        page.insert_textbox(
                            expanded_rect, 
                            op["text"], 
                            fontsize=min_allowed_size,
                            fontname=op["font_ref"], 
                            color=op["color"],
                            align=0
                        )
                    except:
                        pass

    doc.save(output_path)
    doc.close()
    print(f"Zapisano: {output_path}")