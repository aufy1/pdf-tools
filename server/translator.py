from deep_translator import GoogleTranslator
import re
from typing import List, Tuple

class TranslatorEngine:
    def __init__(self):
        self.no_translate_patterns = [
            r'\b\d{1,4}\.[A-Z]\b',
            r'\b[A-Z]+\d*\b',
            r'\b[A-Z]{2,}\b',
            r'\d{2,}-\d{2,}',
            r'\b(?:P\.|ul\.|al\.)'
        ]

    def _mask_text(self, text: str) -> Tuple[str, List[str]]:
        placeholders: List[str] = []
        masked_text = text

        def replacer(match):
            val = match.group(0)
            placeholders.append(val)
            return f"__PH{len(placeholders)-1}__"

        for pattern in self.no_translate_patterns:
            masked_text = re.sub(pattern, replacer, masked_text)
            
        return masked_text, placeholders

    def _unmask_text(self, text: str, placeholders: List[str]) -> str:
        for i, ph in enumerate(placeholders):
            text = text.replace(f"__PH{i}__", ph)
        return text

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text or not text.strip():
            return ""
        
        masked, placeholders = self._mask_text(text)
        
        if not masked.strip() or masked == text:
            try:
                if masked == text and not any(p in text for p in placeholders):
                     return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
                else:
                     return text
            except Exception:
                return text

        try:
            translated = GoogleTranslator(source=source_lang, target=target_lang).translate(masked)
            return self._unmask_text(translated, placeholders)
        except Exception:
            return text

ai_translator = TranslatorEngine()