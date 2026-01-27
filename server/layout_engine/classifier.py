import re
from typing import List, Dict
from .models import ProcessedBlock, BlockType
from .config import Config

def classify_block_types(blocks: List[ProcessedBlock]) -> List[ProcessedBlock]:
    # 1. Heurystyka wierszy (wykrywanie tabeli po układzie kolumnowym)
    y_groups: Dict[int, List[ProcessedBlock]] = {}
    for b in blocks:
        if b.block_type == BlockType.TABLE_CELL: continue
        y_k = int(b.bbox.y0 / 5)
        if y_k not in y_groups: y_groups[y_k] = []
        y_groups[y_k].append(b)
    
    for _, group in y_groups.items():
        if len(group) >= 2:
            x_positions = sorted([b.bbox.x0 for b in group])
            is_row = False
            for i in range(len(x_positions) - 1):
                if (x_positions[i+1] - x_positions[i]) > Config.COLUMN_GAP_THRESHOLD:
                    is_row = True; break
            
            has_numbers = any(re.search(r'\d', b.text) for b in group)
            has_short = any(len(b.text.strip()) <= 3 for b in group)
            
            if is_row or has_numbers or has_short:
                for b in group: b.block_type = BlockType.TABLE_CELL

    # 2. Reszta typów (No Translate, Listy, Paragrafy)
    for b in blocks:
        if b.block_type == BlockType.TABLE_CELL: continue
        
        # Sprawdzenie No Translate
        matched_no_translate = False
        for pattern in Config.NO_TRANSLATE_PATTERNS:
            if re.fullmatch(pattern, b.text.strip()): 
                b.block_type = BlockType.NO_TRANSLATE
                matched_no_translate = True
                break
        if matched_no_translate: continue
        
        if len(b.text.strip()) == 1 and not b.text.isalnum(): 
            b.block_type = BlockType.ISOLATED_SYMBOL
            continue
            
        if Config.LIST_PATTERN.match(b.text.strip()): 
            b.block_type = BlockType.LIST_ITEM
            continue
            
        b.block_type = BlockType.PARAGRAPH
        
    return blocks