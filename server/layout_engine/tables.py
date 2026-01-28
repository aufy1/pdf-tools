import fitz
from typing import List, Dict, Any
from .models import ProcessedBlock, BlockType

# --- 1. LOGIKA OBLICZEŃ WYSOKOŚCI ---

def calculate_text_height(text: str, font: fitz.Font, fontsize: float, width: float) -> float:
    if width <= 0: return fontsize * 1.2
    lines = 0
    space_width = font.text_length(" ", fontsize)
    for p in text.split('\n'):
        if not p: lines += 1; continue
        current_w = 0.0
        lines += 1
        for word in p.split():
            w = font.text_length(word, fontsize)
            if w > width:
                if current_w > 0: lines += 1
                current_w = 0; continue
            if current_w + w <= width: current_w += w + space_width
            else: lines += 1; current_w = w + space_width
    return lines * (fontsize * 1.2)

def get_vertical_centering_offset(text: str, font: fitz.Font, fontsize: float, rect: fitz.Rect) -> float:
    if not text or rect.height <= 0: return 0.0
    try:
        text_h = calculate_text_height(text, font, fontsize, rect.width)
        if text_h < rect.height:
            return (rect.height - text_h) / 2
    except: pass
    return 0.0

# --- 2. DETEKCJA WYRÓWNANIA (ALGORITHM) ---

def detect_cell_alignment(cell_rect: fitz.Rect, text_original_rect: fitz.Rect) -> int:
    """
    Oblicza wyrównanie na podstawie odległości tekstu od fizycznych ramek komórki.
    Zwraca: 0 (Left), 1 (Center), 2 (Right)
    """
    border_left = cell_rect.x0
    border_right = cell_rect.x1
    
    text_left = text_original_rect.x0
    text_right = text_original_rect.x1
    
    dist_left = text_left - border_left
    dist_right = border_right - text_right
    
    cell_width = border_right - border_left
    text_width = text_right - text_left
    
    # Jeśli tekst zajmuje prawie całą komórkę (>85%), uznajemy za LEWO (bezpieczniej)
    if cell_width > 0 and (text_width / cell_width) > 0.85:
        if abs(dist_left - dist_right) < 2.0: return 1
        return 0

    tolerance = 9.0

    if abs(dist_left - dist_right) <= tolerance:
        return 1 # Center
    
    if dist_left < dist_right:
        return 0 # Left
        
    return 2 # Right

# --- 3. LOGIKA RYSOWANIA ---

def draw_table_cell(page: fitz.Page, block: ProcessedBlock, font_map: Dict[str, str], font_objs: Dict[str, fitz.Font]) -> None:
    clean_text = block.text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
    if not clean_text.strip(): return

    font_name = font_map.get(block.style.font_key, "helv")
    font_obj = font_objs.get(block.style.font_key, font_objs.get("regular"))
    start_fs = block.style.size - 1.0
    if start_fs < 5.0: start_fs = 5.0
    curr_fs = start_fs
    base_rect = fitz.Rect(block.bbox)
    inserted = False
    
    detected_align = getattr(block.style, 'align', 0)

    while curr_fs >= 4.0:
        insert_rect = fitz.Rect(base_rect)
        try:
            y_off = get_vertical_centering_offset(clean_text, font_obj, curr_fs, insert_rect)
            insert_rect.y0 += y_off
        except: pass

        try:
            res = page.insert_textbox(
                insert_rect, clean_text, fontsize=curr_fs, fontname=font_name, 
                color=block.style.color, align=detected_align 
            )
            if res >= 0: inserted = True; break
        except: pass
        curr_fs -= 0.5
    
    if not inserted:
        try: page.insert_text((base_rect.x0, base_rect.y1), clean_text, fontsize=start_fs, fontname=font_name, color=block.style.color)
        except: pass

# --- 4. DETEKCJA TABEL (POPRAWIONA) ---

def detect_physical_tables(page: fitz.Page, blocks: List[ProcessedBlock]) -> List[ProcessedBlock]:
    """
    Wykrywa tabele, scala bloki wewnątrz komórek i ustawia ich bbox na pełny rozmiar komórki.
    """
    
    blocks_to_remove = set()
    new_cell_blocks = []

    try:
        tables = page.find_tables(
            horizontal_strategy="lines",
            vertical_strategy="lines",
            snap_tolerance=4,
            join_tolerance=4,
            intersection_tolerance=4,
            edge_min_length=3,
        )

        for tab in tables:
            if len(tab.cells) <= 1: continue

            for cell in tab.header.cells + tab.cells:
                cell_rect = fitz.Rect(cell)
                if cell_rect.width > page.rect.width * 0.95: continue

                # 1. ZNAJDŹ WSZYSTKIE BLOKI W TEJ KOMÓRCE
                blocks_inside = []
                for i, b in enumerate(blocks):
                    if i in blocks_to_remove: continue
                    
                    center_x = (b.bbox.x0 + b.bbox.x1) / 2
                    center_y = (b.bbox.y0 + b.bbox.y1) / 2
                    
                    if (cell_rect.x0 <= center_x <= cell_rect.x1) and \
                       (cell_rect.y0 <= center_y <= cell_rect.y1):
                        blocks_inside.append((i, b))

                if not blocks_inside: continue

                # 2. SCALANIE ZAWARTOŚCI
                blocks_inside.sort(key=lambda x: (x[1].bbox.y0, x[1].bbox.x0))
                merged_text = " ".join([b.text for _, b in blocks_inside])
                
                # Tworzymy "Super-Blok"
                primary_block_index, primary_block = blocks_inside[0]
                
                # WAŻNE: Kopiujemy właściwości, ale BBOX to teraz CAŁA KOMÓRKA
                cell_block = primary_block 
                cell_block.bbox = fitz.Rect(cell_rect) 
                cell_block.text = merged_text
                cell_block.block_type = BlockType.TABLE_CELL
                cell_block.is_hard_boundary = True

                # 3. DETEKCJA WYRÓWNANIA
                all_spans_bbox_x0 = []
                all_spans_bbox_x1 = []
                
                for _, b in blocks_inside:
                    if b.original_spans:
                        all_spans_bbox_x0.extend(s['bbox'][0] for s in b.original_spans)
                        all_spans_bbox_x1.extend(s['bbox'][2] for s in b.original_spans)
                
                align_val = 0 
                if all_spans_bbox_x0 and all_spans_bbox_x1:
                    raw_x0 = min(all_spans_bbox_x0)
                    raw_x1 = max(all_spans_bbox_x1)
                    text_geom = fitz.Rect(raw_x0, cell_rect.y0, raw_x1, cell_rect.y1)
                    align_val = detect_cell_alignment(cell_rect, text_geom)
                
                cell_block.style.align = align_val
                new_cell_blocks.append(cell_block)
                
                for idx, _ in blocks_inside:
                    blocks_to_remove.add(idx)

    except Exception as e:
        print(f"Table detection warning: {e}")
        return blocks # W razie błędu zwracamy oryginał

    # 4. KONSTRUKCJA WYNIKOWEJ LISTY
    final_blocks = []
    for i, b in enumerate(blocks):
        if i not in blocks_to_remove:
            final_blocks.append(b)
            
    final_blocks.extend(new_cell_blocks)
    final_blocks.sort(key=lambda b: (b.bbox.y0, b.bbox.x0))
    
    return final_blocks