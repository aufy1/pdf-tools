import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from .models import StyleInfo

@dataclass
class RichSegment:
    text: str
    font_flags: int  # z PyMuPDF (bold/italic)
    color: Tuple[float, float, float]
    size: float

class StyleTagger:
    """
    Zamienia surowe spany na tekst z tagami HTML (dla AI)
    i parsuje odpowiedź z powrotem na segmenty do rysowania.
    """
    
    def spans_to_tagged_text(self, spans: List[Dict[str, Any]]) -> str:
        if not spans: return ""
        
        # Pobieramy styl bazowy (najczęstszy w bloku)
        if not spans: return ""
        base_span = max(spans, key=lambda s: len(s["text"]))
        base_flags = base_span["flags"]
        base_color = base_span["color"] # int sRGB
        
        output = []
        
        for s in spans:
            text = s["text"]
            flags = s["flags"]
            color = s["color"]
            
            # Wykrywamy zmiany względem "poprzedniego" lub "bazowego"
            # Uproszczenie: używamy tagów XML, np. <b>, <i>, <span color="...">
            
            is_bold = (flags & 2**4)
            is_italic = (flags & 2**1)
            
            styles = []
            if is_bold: styles.append("<b>")
            if is_italic: styles.append("<i>")
            # Kolor dodajemy tylko jeśli różni się od bazowego
            if color != base_color:
                hex_col = f"#{color:06x}"
                styles.append(f'<span color="{hex_col}">')
                
            prefix = "".join(styles)
            
            # Zamykamy w odwrotnej kolejności
            closing = []
            if color != base_color: closing.append("</span>")
            if is_italic: closing.append("</i>")
            if is_bold: closing.append("</b>")
            suffix = "".join(closing)
            
            # Escapowanie znaków specjalnych HTML w tekście
            safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            output.append(f"{prefix}{safe_text}{suffix}")
            
        return "".join(output)

    def parse_tagged_response(self, text: str, base_style: StyleInfo) -> List[RichSegment]:
        """
        Parsuje przetłumaczony tekst (np. "To jest <b>ważne</b>") na listę segmentów.
        """
        segments = []
        
        # Regex do wyłapania tagów
        tokens = re.split(r'(</?b>|</?i>|<span[^>]*>|</span>)', text)
        
        current_flags = base_style.flags
        # Resetujemy flagi bold/italic z bazowego stylu, będziemy je nakładać z tagów
        current_flags &= ~(2**4 | 2**1) 
        
        current_color = base_style.color # krotka (r,g,b)
        current_size = base_style.size
        
        # Stos kolorów
        color_stack = [current_color]
        
        for token in tokens:
            if not token: continue
            
            if token == "<b>":
                current_flags |= 2**4 
            elif token == "</b>":
                current_flags &= ~2**4 
            elif token == "<i>":
                current_flags |= 2**1 
            elif token == "</i>":
                current_flags &= ~2**1 
            elif token.startswith("<span color="):
                match = re.search(r'color=["\']#?([0-9a-fA-F]{6})["\']', token)
                if match:
                    hex_str = match.group(1)
                    r = int(hex_str[0:2], 16) / 255.0
                    g = int(hex_str[2:4], 16) / 255.0
                    b = int(hex_str[4:6], 16) / 255.0
                    current_color = (r, g, b)
                    color_stack.append(current_color)
            elif token == "</span>":
                if len(color_stack) > 1: color_stack.pop()
                current_color = color_stack[-1]
            else:
                # To jest czysty tekst - odwracamy escape
                clean_text = token.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
                if clean_text:
                    segments.append(RichSegment(
                        text=clean_text,
                        font_flags=current_flags,
                        color=current_color,
                        size=current_size
                    ))
                
        return segments