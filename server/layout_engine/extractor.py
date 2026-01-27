import fitz
import re
from typing import List, Dict, Optional, Any
from .models import ProcessedBlock, BlockType
from .styles import analyze_style
from .config import Config

def _create_block(spans: List[Dict[str, Any]]) -> Optional[ProcessedBlock]:
    full_text = "".join(s["text"] for s in spans).strip()
    if not full_text: return None

    x0 = min(s["bbox"][0] for s in spans)
    y0 = min(s["bbox"][1] for s in spans)
    x1 = max(s["bbox"][2] for s in spans)
    y1 = max(s["bbox"][3] for s in spans)
    bbox = fitz.Rect(x0, y0, x1, y1)

    style, avg_w = analyze_style(spans)
    density = len(full_text) / bbox.width if bbox.width > 0 else 0

    return ProcessedBlock(
        text=full_text,
        bbox=bbox,
        style=style,
        block_type=BlockType.UNKNOWN,
        char_width_avg=avg_w,
        density=density,
        original_spans=spans
    )

def extract_blocks_from_page(page: fitz.Page) -> List[ProcessedBlock]:
    raw_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
    blocks: List[ProcessedBlock] = []
    
    for b in raw_dict.get("blocks", []):
        if b.get("type") != 0: continue
        for line in b.get("lines", []):
            sorted_spans = sorted(line["spans"], key=lambda s: s["bbox"][0])
            current_group: List[Dict[str, Any]] = []
            last_x1 = -999.0
            
            for span in sorted_spans:
                text = span["text"]
                x0 = span["bbox"][0]
                is_gap_large = (last_x1 != -999.0 and (x0 - last_x1) > Config.SPACES_THRESHOLD)
                has_double_space = "  " in text
                
                if is_gap_large and current_group:
                    nb = _create_block(current_group)
                    if nb: blocks.append(nb)
                    current_group = []
                
                if has_double_space and not is_gap_large:
                    # Logika podziału spanu z podwójną spacją
                    sub_parts = re.split(r'(\s{2,})', text)
                    cursor_x = x0
                    char_w = (span["bbox"][2] - x0) / len(text) if len(text) > 0 else 0
                    for part in sub_parts:
                        if not part.strip():
                            cursor_x += len(part) * char_w
                            continue
                        part_width = len(part) * char_w
                        sub_span = span.copy()
                        sub_span["text"] = part
                        sub_span["bbox"] = (cursor_x, span["bbox"][1], cursor_x + part_width, span["bbox"][3])
                        
                        if current_group:
                            nb = _create_block(current_group)
                            if nb: blocks.append(nb)
                            current_group = []
                        current_group.append(sub_span)
                        nb = _create_block(current_group)
                        if nb: blocks.append(nb)
                        current_group = []
                        cursor_x += part_width
                else:
                    current_group.append(span)
                    last_x1 = span["bbox"][2]
            
            if current_group:
                nb = _create_block(current_group)
                if nb: blocks.append(nb)
    
    return blocks