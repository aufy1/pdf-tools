from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
from enum import Enum, auto
import fitz

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
    is_hard_boundary: bool = False