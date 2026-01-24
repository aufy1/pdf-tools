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

# Próg łączenia w pikselach
MERGE_DISTANCE = 12.0 

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

def should_translate(text):
    text = text.strip()
    if len(text) < 2: return False
    if text.replace('.', '').replace(',', '').replace(' ', '').isdigit(): return False
    keywords = ["PIT", "CIT", "NIP", "PESEL", "REGON", "KRS", "IP", "PWA", "RUB", "TAB", "RYS"]
    if any(k in text.upper() for k in keywords) and len(text) < 15: return False
    if not re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', text): return False
    return True

def get_dominant_style(spans, registered_fonts):
    """
    Określa dominujący styl (czcionkę, rozmiar, kolor) dla grupy spanów.
    Bierzemy styl, który zajmuje najwięcej znaków w grupie.
    """
    if not spans: return None
    
    # Zliczamy wystąpienia stylów
    style_counts = {}
    
    for s in spans:
        txt_len = len(s["text"].strip())
        if txt_len == 0: continue
        
        # Klucz stylu: (flags, size, color)
        key = (s["flags"], s["size"], s["color"])
        style_counts[key] = style_counts.get(key, 0) + txt_len
        
    if not style_counts:
        # Fallback do pierwszego
        s = spans[0]
        best_key = (s["flags"], s["size"], s["color"])
    else:
        best_key = max(style_counts, key=style_counts.get)
        
    flags, size, color = best_key
    
    # Mapowanie flag na nazwę fontu
    is_bold = bool(flags & 2**4)
    is_italic = bool(flags & 2**1)
    
    style_name = "regular"
    if is_bold and is_italic: style_name = "bold_italic"
    elif is_bold: style_name = "bold"
    elif is_italic: style_name = "italic"
    
    font_ref = registered_fonts.get(style_name, registered_fonts.get("regular"))
    
    return {
        "font": font_ref,
        "size": size,
        "color": srgb_to_rgb(color),
        "flags": flags
    }

def merge_spans_by_distance(spans, threshold=12.0):
    """
    Kluczowa funkcja: łączy spany, jeśli są blisko siebie (<= threshold).
    Zwraca listę grup (klastrów).
    """
    if not spans: return []
    
    # Sortujemy spany od lewej do prawej, żeby logika dystansu działała poprawnie
    sorted_spans = sorted(spans, key=lambda s: s["bbox"][0])
    
    groups = []
    current_group = [sorted_spans[0]]
    
    for i in range(1, len(sorted_spans)):
        prev = current_group[-1]
        curr = sorted_spans[i]
        
        # Obliczamy dystans: X początku obecnego - X końca poprzedniego
        distance = curr["bbox"][0] - prev["bbox"][2]
        
        if distance <= threshold:
            # Są blisko - dodajemy do obecnej grupy
            current_group.append(curr)
        else:
            # Są daleko - zamykamy grupę i otwieramy nową
            groups.append(current_group)
            current_group = [curr]
            
    groups.append(current_group)
    return groups

def get_union_rect(group_spans):
    """Oblicza wspólny prostokąt (bbox) dla grupy spanów."""
    if not group_spans: return fitz.Rect(0,0,0,0)
    
    x0 = min(s["bbox"][0] for s in group_spans)
    y0 = min(s["bbox"][1] for s in group_spans)
    x1 = max(s["bbox"][2] for s in group_spans)
    y1 = max(s["bbox"][3] for s in group_spans)
    
    return fitz.Rect(x0, y0, x1, y1)

def process_pdf_translation(input_path: str, output_path: str):
    
    if "regular" not in GLOBAL_FONT_BUFFERS:
        print("CRITICAL: Brak fontów. Zwracam oryginał.")
        doc = fitz.open(input_path)
        doc.save(output_path)
        return

    doc = fitz.open(input_path)

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
                # 1. Grupujemy spany używając logiki 12 pikseli
                span_groups = merge_spans_by_distance(line["spans"], threshold=MERGE_DISTANCE)
                
                for group in span_groups:
                    # Łączymy tekst grupy
                    full_text = "".join([s["text"] for s in group])
                    
                    if not should_translate(full_text):
                        continue
                    
                    # 2. Obliczamy wspólny obszar (Union Rect)
                    union_rect = get_union_rect(group)
                    
                    # 3. Pobieramy styl (bierzemy dominujący w grupie)
                    style = get_dominant_style(group, registered_fonts)
                    
                    try:
                        translated_text = ai_translator.translate_text(full_text, target_lang='uk')
                    except: continue

                    if not translated_text or translated_text == full_text: continue

                    operations.append({
                        "rect": union_rect,      # Gdzie wstawić
                        "text": translated_text, # Co wstawić
                        "style": style,          # Jak wstawić
                        "orig_text": full_text
                    })

        # --- WYKONANIE ZMIAN NA STRONIE ---
        if not operations: continue
        
        # Krok 1: Ukrycie oryginału i wyczyszczenie tła
        for op in operations:
            # Dodajemy redakcję (biały prostokąt) dokładnie na union_rect
            page.add_redact_annot(op["rect"], fill=False) 
            
            # (Opcjonalnie) Wstawiamy mikrotekst dla zachowania "Searchable PDF"
            try:
                page.insert_text((op["rect"].x0, op["rect"].y1), " ", 
                                 fontname=op["style"]["font"], fontsize=5, render_mode=1)
            except: pass

        page.apply_redactions()

        # Krok 2: Wstawianie nowego tekstu z Word Wrap
        for op in operations:
            rect = op["rect"]
            
            # Lekka korekta wysokości (padding), żeby tekst nie dotykał linii tabeli
            # Rozszerzamy minimalnie w dół (np. 2px), bo ukraiński tekst bywa wyższy
            insert_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1 + 3)
            
            current_size = op["style"]["size"]
            min_size = 5.0
            step = 0.5
            
            # Pętla dopasowania rozmiaru czcionki
            while current_size >= min_size:
                try:
                    # insert_textbox zwraca ujemną wartość, jeśli tekst się nie zmieścił
                    res = page.insert_textbox(
                        insert_rect, 
                        op["text"], 
                        fontsize=current_size, 
                        fontname=op["style"]["font"], 
                        color=op["style"]["color"],
                        align=0, # 0 = Left (zazwyczaj najlepsze wewnątrz zwartej grupy), 1 = Center
                        expandtabs=0
                    )
                    
                    if res >= 0: # Udało się zmieścić
                        break
                except:
                    break
                
                current_size -= step
            
            # Jeśli pętla nie znalazła miejsca, wstawiamy na siłę małą czcionką
            if current_size < min_size:
                 try:
                    page.insert_textbox(
                        insert_rect, 
                        op["text"], 
                        fontsize=min_size, 
                        fontname=op["style"]["font"], 
                        color=op["style"]["color"],
                        align=0
                    )
                 except: pass

    doc.save(output_path)
    doc.close()
    print(f"Zapisano: {output_path}")