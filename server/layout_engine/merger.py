import re
from typing import List, Tuple, Optional
from .models import ProcessedBlock, BlockType
from .config import Config

def _strategy_0_guard(b1: ProcessedBlock, b2: ProcessedBlock) -> Optional[str]:
    if b1.is_hard_boundary or b2.is_hard_boundary: return "HARD_BOUNDARY"
    if abs(b1.bbox.x0 - b2.bbox.x0) > Config.X_THRESHOLD: return f"X_DIFF"
    if (b2.bbox.x0 - b1.bbox.x1) > Config.H_GAP_THRESHOLD: return "HORIZONTAL_GAP"
    h1, h2 = b1.bbox.height, b2.bbox.height
    if min(h1, h2) > 0 and (max(h1, h2) / min(h1, h2)) > 1.5: return "HEIGHT_RATIO"
    if b1.density < Config.DENSITY_THRESHOLD or b2.density < Config.DENSITY_THRESHOLD: return "LOW_DENSITY"
    if b1.char_width_avg > 0 and b2.char_width_avg > 0:
        if max(b1.char_width_avg, b2.char_width_avg) / min(b1.char_width_avg, b2.char_width_avg) > 1.2: return "CHAR_WIDTH"
    if len(b1.text.strip()) <= 3 or len(b2.text.strip()) <= 3: return "SHORT_TOKEN"
    if re.search(r'\d', b1.text) and re.search(r'\d', b2.text):
         if len(b1.text) < 10 or len(b2.text) < 10: return "NUMERIC_SEQ"
    if Config.LIST_PATTERN.match(b2.text.strip()): return "NEW_LIST"
    return None

def _strategy_2_linguistics(b1: ProcessedBlock, b2: ProcessedBlock) -> Tuple[bool, str]:
    t1, t2 = b1.text.strip(), b2.text.strip()
    if len(t1) <= 5 and len(t2) <= 5: return False, "BOTH_SHORT"
    if t1.isdigit() and t2.isdigit(): return False, "BOTH_NUM"
    if any(c in "|;:" for c in t1 + t2): return False, "TABULAR"
    if abs(b1.bbox.x0 - b2.bbox.x0) < 9.0:
        if t1.endswith(('.', '?', '!', ':')): return False, "SENT_END"
        if t2 and t2[0].islower(): return True, "LOWERCASE"
        if t1.endswith('-'): return True, "HYPHEN"
        if not t1.endswith('.'): return True, "IMPLICIT"
    return False, "FAIL"

def merge_blocks(blocks: List[ProcessedBlock]) -> List[ProcessedBlock]:
    sorted_blocks = sorted(blocks, key=lambda b: (int(b.bbox.x0 / 20), b.bbox.y0))
    merged: List[ProcessedBlock] = []
    
    while sorted_blocks:
        curr = sorted_blocks.pop(0)
        if curr.block_type in [BlockType.TABLE_CELL, BlockType.ISOLATED_SYMBOL, BlockType.NO_TRANSLATE]:
            merged.append(curr); continue
        
        merged_happened = True
        while merged_happened and sorted_blocks:
            merged_happened = False; best_idx = -1
            for i, cand in enumerate(sorted_blocks):
                if cand.block_type in [BlockType.TABLE_CELL, BlockType.ISOLATED_SYMBOL, BlockType.NO_TRANSLATE]: continue
                y_dist = cand.bbox.y0 - curr.bbox.y1
                if y_dist < -2.0: continue
                if y_dist > Config.Y_TOLERANCE:
                    if abs(cand.bbox.x0 - curr.bbox.x0) < 20: break 
                    continue
                
                if _strategy_0_guard(curr, cand): continue
                can_merge, _ = _strategy_2_linguistics(curr, cand)
                if can_merge: best_idx = i; break
            
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