import fitz
from typing import List
from .models import ProcessedBlock
from .extractor import extract_blocks_from_page
from .tables import detect_physical_tables
from .classifier import classify_block_types
from .merger import merge_blocks

class LayoutEngine:
    def __init__(self, page: fitz.Page):
        self.page = page

    def run(self) -> List[ProcessedBlock]:
        # 1. Ekstrakcja surowych bloków
        blocks = extract_blocks_from_page(self.page)
        
        # 2. Wykrywanie tabel fizycznych (modyfikuje bloki i ustawia TABLE_CELL)
        blocks = detect_physical_tables(self.page, blocks)
        
        # 3. Klasyfikacja reszty (listy, paragrafy)
        blocks = classify_block_types(blocks)
        
        # 4. Łączenie paragrafów
        blocks = merge_blocks(blocks)
        
        return blocks