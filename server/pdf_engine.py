import fitz
import re
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from translator import ai_translator

class BlockType(Enum):
    PARAGRAPH = auto()
    TABLE_CELL = auto()
    LIST_ITEM = auto()
    HEADER = auto()
    FOOTER = auto()
    ISOLATED_SYMBOL = auto()
    NO_TRANSLATE = auto()
    UNKNOWN = auto()

@dataclass
class StyleInfo:
    font_key: str
    size: float
    color: Tuple[float, float, float]
    flags: int
    align: int

@dataclass
class ProcessedBlock:
    text: str
    bbox: fitz.Rect
    style: StyleInfo
    block_type: BlockType = BlockType.UNKNOWN
    char_width_avg: float = 0.0
    density: float = 0.0
    original_spans: List[Dict[str, Any]] = field(default_factory=list)

class LayoutEngine:
    def __init__(self, page: fitz.Page):
        self.page = page
        self.X_THRESHOLD = 5.0
        self.H_GAP_THRESHOLD = 15.0
        self.Y_TOLERANCE = 6.0
        self.SPACES_THRESHOLD = 20.0
        self.COLUMN_GAP_THRESHOLD = 20.0
        self.DENSITY_THRESHOLD = 0.05
        
        self.NO_TRANSLATE_PATTERNS: List[str] = [
            r'\b\d{1,4}\.[A-Z]\b',
            r'\b[A-Z]+\d*\b',
            r'\b[A-Z]{2,}\b',
            r'^\d+$',
            r'^\W+$'
        ]
        self.LIST_PATTERN = re.compile(r'^(\d{1,3}[.)]|\-|\+|•|o)\s')
        self.fonts_map: Dict[str, str] = {}

    def srgb_to_rgb(self, srgb_int: int) -> Tuple[float, float, float]:
        if not isinstance(srgb_int, int): return (0, 0, 0)
        r = ((srgb_int >> 16) & 255) / 255.0
        g = ((srgb_int >> 8) & 255) / 255.0
        b = (srgb_int & 255) / 255.0
        return (r, g, b)

    def analyze_style(self, spans: List[Dict[str, Any]]) -> Tuple[StyleInfo, float]:
        if not spans:
            return StyleInfo("regular", 9.0, (0, 0, 0), 0, 0), 0.0
        
        ref_span = next((s for s in spans if s["text"].strip()), spans[0])
        total_chars = 0
        total_width = 0.0
        
        for s in spans:
            txt_len = len(s["text"])
            if txt_len > 0:
                total_chars += txt_len
                total_width += (s["bbox"][2] - s["bbox"][0])
        
        avg_w = total_width / total_chars if total_chars > 0 else 0.0
        flags = ref_span["flags"]
        font_key = "regular"
        if flags & 2**4 and flags & 2**1: font_key = "bold_italic"
        elif flags & 2**4: font_key = "bold"
        elif flags & 2**1: font_key = "italic"
        
        return StyleInfo(font_key, ref_span["size"], self.srgb_to_rgb(ref_span["color"]), flags, 0), avg_w

    def _create_block(self, spans: List[Dict[str, Any]]) -> Optional[ProcessedBlock]:
        full_text = "".join(s["text"] for s in spans).strip()
        if not full_text: 
            return None

        x0 = min(s["bbox"][0] for s in spans)
        y0 = min(s["bbox"][1] for s in spans)
        x1 = max(s["bbox"][2] for s in spans)
        y1 = max(s["bbox"][3] for s in spans)
        bbox = fitz.Rect(x0, y0, x1, y1)

        style, avg_w = self.analyze_style(spans)
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

    def extract_blocks(self) -> List[ProcessedBlock]:
        raw_dict = self.page.get_text("dict", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
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
                    
                    is_gap_large = (last_x1 != -999.0 and (x0 - last_x1) > self.SPACES_THRESHOLD)
                    has_double_space = "  " in text
                    
                    if is_gap_large:
                        if current_group:
                            nb = self._create_block(current_group)
                            if nb: blocks.append(nb)
                            current_group = []
                    
                    if has_double_space and not is_gap_large:
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
                                nb = self._create_block(current_group)
                                if nb: blocks.append(nb)
                                current_group = []
                            
                            current_group.append(sub_span)
                            nb = self._create_block(current_group)
                            if nb: blocks.append(nb)
                            current_group = []
                            cursor_x += part_width
                    else:
                        current_group.append(span)
                        last_x1 = span["bbox"][2]

                if current_group:
                    nb = self._create_block(current_group)
                    if nb: blocks.append(nb)

        return blocks

    def classify_blocks(self, blocks: List[ProcessedBlock]) -> List[ProcessedBlock]:
        y_groups: Dict[int, List[ProcessedBlock]] = {}
        for b in blocks:
            y_k = int(b.bbox.y0 / 5)
            if y_k not in y_groups: y_groups[y_k] = []
            y_groups[y_k].append(b)
        
        table_cell_ids: Set[int] = set()
        
        for _, group in y_groups.items():
            if len(group) >= 2:
                x_positions = sorted([b.bbox.x0 for b in group])
                is_row = False
                for i in range(len(x_positions) - 1):
                    if (x_positions[i+1] - x_positions[i]) > self.COLUMN_GAP_THRESHOLD:
                        is_row = True
                        break
                
                has_numbers = any(re.search(r'\d', b.text) for b in group)
                has_short = any(len(b.text.strip()) <= 3 for b in group)

                if is_row or has_numbers or has_short:
                    for b in group:
                        b.block_type = BlockType.TABLE_CELL
                        table_cell_ids.add(id(b))

        for b in blocks:
            if id(b) in table_cell_ids:
                continue

            for pattern in self.NO_TRANSLATE_PATTERNS:
                if re.fullmatch(pattern, b.text.strip()):
                    b.block_type = BlockType.NO_TRANSLATE
                    break
            
            if b.block_type == BlockType.NO_TRANSLATE:
                continue

            if len(b.text.strip()) == 1 and not b.text.isalnum():
                b.block_type = BlockType.ISOLATED_SYMBOL
                continue

            if self.LIST_PATTERN.match(b.text.strip()):
                b.block_type = BlockType.LIST_ITEM
                continue

            b.block_type = BlockType.PARAGRAPH
            
        return blocks

    def strategy_0_guard(self, b1: ProcessedBlock, b2: ProcessedBlock) -> Optional[str]:
        if abs(b1.bbox.x0 - b2.bbox.x0) > self.X_THRESHOLD:
            return f"X_DIFF_TOO_LARGE ({abs(b1.bbox.x0 - b2.bbox.x0):.1f} > {self.X_THRESHOLD})"
        
        if (b2.bbox.x0 - b1.bbox.x1) > self.H_GAP_THRESHOLD:
            return "HORIZONTAL_GAP_TOO_LARGE"

        h1, h2 = b1.bbox.height, b2.bbox.height
        if min(h1, h2) > 0 and (max(h1, h2) / min(h1, h2)) > 1.5:
            return "HEIGHT_RATIO_MISMATCH"

        if b1.density < self.DENSITY_THRESHOLD or b2.density < self.DENSITY_THRESHOLD:
            return "LOW_TEXT_DENSITY"

        if b1.char_width_avg > 0 and b2.char_width_avg > 0:
            ratio = max(b1.char_width_avg, b2.char_width_avg) / min(b1.char_width_avg, b2.char_width_avg)
            if ratio > 1.2:
                return "CHAR_WIDTH_MISMATCH"

        if len(b1.text.strip()) <= 3 or len(b2.text.strip()) <= 3:
            return "SHORT_TOKEN_DETECTED"

        if re.search(r'\d', b1.text) and re.search(r'\d', b2.text):
             if len(b1.text) < 10 or len(b2.text) < 10:
                 return "NUMERIC_DATA_SEQUENCE"

        if self.LIST_PATTERN.match(b2.text.strip()):
            return "NEW_LIST_ITEM_DETECTED"
            
        return None

    def strategy_2_linguistics(self, b1: ProcessedBlock, b2: ProcessedBlock) -> Tuple[bool, str]:
        t1 = b1.text.strip()
        t2 = b2.text.strip()
        
        if len(t1) <= 5 and len(t2) <= 5: 
            return False, "BOTH_TOO_SHORT"
        
        if t1.isdigit() and t2.isdigit(): 
            return False, "BOTH_NUMERIC"
        
        if any(c in "|;:" for c in t1 + t2): 
            return False, "TABULAR_CHARS_DETECTED"
        
        if abs(b1.bbox.x0 - b2.bbox.x0) < 9.0:
            if t1.endswith(('.', '?', '!', ':')): 
                return False, "SENTENCE_END_DETECTED"
            if t2 and t2[0].islower(): 
                return True, "CONTINUATION_LOWERCASE"
            if t1.endswith('-'): 
                return True, "HYPHENATION"
            if not t1.endswith('.'):
                return True, "IMPLICIT_CONTINUATION"

        return False, "LINGUISTIC_HEURISTIC_FAIL"

    def merge_blocks(self, blocks: List[ProcessedBlock]) -> List[ProcessedBlock]:
        sorted_blocks = sorted(blocks, key=lambda b: (int(b.bbox.x0 / 20), b.bbox.y0))
        merged: List[ProcessedBlock] = []
        
        while sorted_blocks:
            curr = sorted_blocks.pop(0)
            
            if curr.block_type != BlockType.PARAGRAPH:
                merged.append(curr)
                continue
            
            merged_happened = True
            while merged_happened and sorted_blocks:
                merged_happened = False
                best_idx = -1
                
                for i, cand in enumerate(sorted_blocks):
                    if cand.block_type != BlockType.PARAGRAPH:
                        continue
                        
                    y_dist = cand.bbox.y0 - curr.bbox.y1
                    
                    if y_dist < -2.0: 
                        continue

                    if y_dist > self.Y_TOLERANCE:
                        if abs(cand.bbox.x0 - curr.bbox.x0) < 20:
                            print(f"[LOG] Vertical Break: '{curr.text[:15]}...' vs '{cand.text[:15]}...' Dist: {y_dist:.1f}")
                            break 
                        continue

                    guard_reject = self.strategy_0_guard(curr, cand)
                    if guard_reject:
                        print(f"[LOG] Guard REJECT: '{curr.text[:15]}...' + '{cand.text[:15]}...' -> {guard_reject}")
                        continue

                    can_merge_ling, ling_reason = self.strategy_2_linguistics(curr, cand)
                    if can_merge_ling:
                        print(f"[LOG] MERGE ACCEPT: '{curr.text[:15]}...' + '{cand.text[:15]}...' -> {ling_reason}")
                        best_idx = i
                        break
                    else:
                        print(f"[LOG] Linguistic REJECT: '{curr.text[:15]}...' + '{cand.text[:15]}...' -> {ling_reason}")
                
                if best_idx != -1:
                    nxt = sorted_blocks.pop(best_idx)
                    sep = "" if curr.text.endswith("-") else " "
                    txt = curr.text[:-1] if curr.text.endswith("-") else curr.text
                    
                    curr.text = txt + sep + nxt.text
                    curr.bbox.include_rect(nxt.bbox)
                    curr.original_spans.extend(nxt.original_spans)
                    merged_happened = True
            
            merged.append(curr)
            
        return merged

    def run(self) -> List[ProcessedBlock]:
        blocks = self.extract_blocks()
        blocks = self.classify_blocks(blocks)
        final_blocks = self.merge_blocks(blocks)
        return final_blocks

def process_pdf(input_path: str, output_path: str, source_lang: str, target_lang: str) -> None:
    doc = fitz.open(input_path)
    font_paths = {
        "regular": "/app/fonts/Roboto_Condensed-Regular.ttf",
        "bold": "/app/fonts/Roboto_Condensed-Bold.ttf",
        "italic": "/app/fonts/Roboto_Condensed-Italic.ttf",
        "bold_italic": "/app/fonts/Roboto_Condensed-BoldItalic.ttf"
    }
    
    font_buffers = {}
    for key, path in font_paths.items():
        try:
            with open(path, "rb") as f:
                font_buffers[key] = f.read()
        except Exception: pass

    for page_num, page in enumerate(doc):
        font_map = {}
        for k, v in font_buffers.items():
            fname = f"F{page_num}_{k}"
            try:
                page.insert_font(fontname=fname, fontbuffer=v)
                font_map[k] = fname
            except Exception: pass
            
        engine = LayoutEngine(page)
        blocks = engine.run()
        
        for b in blocks:
            page.draw_rect(b.bbox, color=None, fill=(1, 1, 1), overlay=True)

        for b in blocks:
            text_to_insert = b.text
            if b.block_type not in [BlockType.NO_TRANSLATE, BlockType.ISOLATED_SYMBOL] and b.text.strip():
                try:
                    text_to_insert = ai_translator.translate_text(
                        b.text, source_lang.lower(), target_lang.lower()
                    )
                except Exception:
                    text_to_insert = b.text

            if not text_to_insert or not text_to_insert.strip():
                continue

            fitz_font = font_map.get(b.style.font_key, "helv")
            insert_rect = fitz.Rect(b.bbox.x0, b.bbox.y0, b.bbox.x1, b.bbox.y1 + 2)
            
            fontsize = b.style.size
            min_fs = 5.0
            inserted = False
            
            curr_fs = fontsize
            while curr_fs >= min_fs:
                try:
                    res = page.insert_textbox(
                        insert_rect, 
                        text_to_insert, 
                        fontsize=curr_fs, 
                        fontname=fitz_font, 
                        color=b.style.color,
                        align=b.style.align
                    )
                    if res >= 0: 
                        inserted = True
                        break
                except Exception:
                    pass
                curr_fs -= 0.5
            
            if not inserted:
                try:
                    page.insert_textbox(
                        insert_rect, 
                        text_to_insert, 
                        fontsize=min_fs, 
                        fontname=fitz_font, 
                        color=b.style.color,
                        align=b.style.align
                    )
                except Exception: pass

    doc.save(output_path)
    doc.close()

if __name__ == "__main__":
    import sys
    print("PDF Engine Standalone Test (Layout Guard Strict)")
    i = "input.pdf"
    o = "output.pdf"
    if len(sys.argv) > 2:
        i, o = sys.argv[1], sys.argv[2]
    
    print(f"Processing: {i} -> {o}")
    try:
        process_pdf(i, o, "PL", "UK")
        print("Success.")
    except Exception as e:
        print(f"Error: {e}")