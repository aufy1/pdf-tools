import fitz  # PyMuPDF
from translator import ai_translator
import os

# Map fonts
FONTS_MAP = {
    "regular":     "/app/fonts/Roboto_Condensed-Regular.ttf",
    "bold":        "/app/fonts/Roboto_Condensed-Bold.ttf",
    "italic":      "/app/fonts/Roboto_Condensed-Italic.ttf",
    "bold_italic": "/app/fonts/Roboto_Condensed-BoldItalic.ttf"
}

def srgb_to_rgb(srgb_int):
    """Convert int color to (r, g, b)"""
    if not isinstance(srgb_int, int): return (0, 0, 0)
    r = ((srgb_int >> 16) & 255) / 255.0
    g = ((srgb_int >> 8) & 255) / 255.0
    b = (srgb_int & 255) / 255.0
    return (r, g, b)

def get_line_style(spans):
    """Analyze line style"""
    if not spans:
        return 11, 0, 0
    
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

def process_pdf_translation(input_path: str, output_path: str):
    
    def load_font_to_page(page, font_key, internal_name):
        path = FONTS_MAP.get(font_key)
        if path and os.path.exists(path):
            try:
                page.insert_font(fontname=internal_name, fontfile=path)
                return True
            except:
                return False
        return False

    try:
        doc = fitz.open(input_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        raise e

    for page in doc:
        has_reg = load_font_to_page(page, "regular", "my_reg")
        has_bold = load_font_to_page(page, "bold", "my_bold")
        has_ital = load_font_to_page(page, "italic", "my_ital")

        try:
            blocks = page.get_text("dict")["blocks"]
        except:
            continue

        for block in blocks:
            if "lines" not in block: continue

            for line in block["lines"]:
                
                # 1. Compose text
                full_text = "".join([s["text"] for s in line["spans"]])
                
                if len(full_text.strip()) < 2 or full_text.replace('.','').replace(' ', '').isdigit():
                    continue

                # 2. Analyze style
                font_size, flags, color_int = get_line_style(line["spans"])
                text_color = srgb_to_rgb(color_int)
                
                is_bold = bool(flags & 2**4)
                is_italic = bool(flags & 2**1)

                font_ref = "helv"
                if is_bold and has_bold:
                    font_ref = "my_bold"
                elif is_italic and has_ital:
                    font_ref = "my_ital"
                elif has_reg:
                    font_ref = "my_reg"

                # 3. Translate
                try:
                    translated_text = ai_translator.translate_text(full_text, target_lang='uk')
                except:
                    continue

                if not translated_text or translated_text == full_text:
                    continue

                # 4. Geometry
                bbox = line["bbox"] # [x0, y0, x1, y1]

                # WHITEOUT RECT
                clean_rect = fitz.Rect(bbox[0]-2, bbox[1]-1, bbox[2]+2, bbox[3]+1)
                
                try:
                    page.draw_rect(clean_rect, color=(1, 1, 1), fill=(1, 1, 1))
                except:
                    pass

                # INSERT RECT (Initial)
                # Slightly wider to accommodate Ukrainian text
                insert_rect = fitz.Rect(bbox[0], bbox[1], bbox[2]+15, bbox[3]+3)

                # 5. Iterative Fitting (The "Squeeze" Logic)
                current_size = font_size
                
                # We limit the reduction to max 5pt less than original, or absolute min of 6pt
                min_allowed_size = max(6, font_size - 5) 
                
                step = 0.5 # Decrease step
                success = False

                while current_size >= min_allowed_size:
                    res = page.insert_textbox(
                        insert_rect, 
                        translated_text, 
                        fontsize=current_size, 
                        fontname=font_ref, 
                        color=text_color,
                        align=0 # Left align
                    )
                    
                    if res >= 0:
                        success = True
                        break # Fits!
                    
                    # Reduce size and try again
                    current_size -= step

                # FALLBACK: If it still doesn't fit even at min size
                if not success:
                    # We force insert it by increasing the vertical height of the box
                    # This might overlap slightly with the line below, but it's better than invisible text
                    expanded_rect = fitz.Rect(bbox[0], bbox[1], bbox[2]+20, bbox[3]+15)
                    page.insert_textbox(
                        expanded_rect, 
                        translated_text, 
                        fontsize=min_allowed_size, # Use the minimum readable size
                        fontname=font_ref, 
                        color=text_color,
                        align=0
                    )

    doc.save(output_path)
    doc.close()
    print(f"Saved to: {output_path}")