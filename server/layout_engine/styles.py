from typing import List, Dict, Any, Tuple
from .models import StyleInfo

def srgb_to_rgb(srgb_int: int) -> Tuple[float, float, float]:
    if not isinstance(srgb_int, int): return (0, 0, 0)
    r = ((srgb_int >> 16) & 255) / 255.0
    g = ((srgb_int >> 8) & 255) / 255.0
    b = (srgb_int & 255) / 255.0
    return (r, g, b)

def analyze_style(spans: List[Dict[str, Any]]) -> Tuple[StyleInfo, float]:
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
    
    return StyleInfo(font_key, ref_span["size"], srgb_to_rgb(ref_span["color"]), flags, 0), avg_w