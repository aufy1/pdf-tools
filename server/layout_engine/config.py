import re

class Config:
    X_THRESHOLD = 5.0
    H_GAP_THRESHOLD = 15.0
    Y_TOLERANCE = 6.0
    SPACES_THRESHOLD = 20.0
    COLUMN_GAP_THRESHOLD = 20.0
    DENSITY_THRESHOLD = 0.05

    NO_TRANSLATE_PATTERNS = [
        r'\b\d{1,4}\.[A-Z]\b',
        r'\b[A-Z]+\d*\b',
        r'\b[A-Z]{2,}\b',
        r'^\d+$',
        r'^\W+$'
    ]
    
    LIST_PATTERN = re.compile(r'^(\d{1,3}[.)]|\-|\+|•|o)\s')