import fitz
from typing import List
from .models import ProcessedBlock, BlockType

def detect_physical_tables(page: fitz.Page, blocks: List[ProcessedBlock]) -> None:
    """
    Wykrywa tabele i ustawia flagę centrowania (align=1) oraz BlockType.TABLE_CELL.
    Modyfikuje listę blocks in-place.
    """
    try:
        tables = page.find_tables(horizontal_strategy="lines", vertical_strategy="lines")
        for tab in tables:
            for cell in tab.header.cells + tab.cells:
                cell_rect = fitz.Rect(cell)
                for b in blocks:
                    center_x = (b.bbox.x0 + b.bbox.x1) / 2
                    center_y = (b.bbox.y0 + b.bbox.y1) / 2
                    center_pt = fitz.Point(center_x, center_y)
                    
                    if center_pt in cell_rect:
                        b.block_type = BlockType.TABLE_CELL
                        b.bbox = cell_rect + (-2, -2, 2, 2)
                        b.is_hard_boundary = True
                        b.style.align = 1  # 1 = CENTER
    except Exception as e:
        print(f"Table detection warning: {e}")