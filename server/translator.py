# /server/translator.py
from deep_translator import GoogleTranslator

# Singleton, żeby nie ładować modelu za każdym razem (ważne przy NLLB)
class TranslatorEngine:
    def __init__(self):
        # Tutaj w przyszłości załadujesz model NLLB / CTranslate2
        # self.model = ctranslate2.Translator("models/nllb-200-distilled-600M")
        # self.tokenizer = ...
        pass

    def translate_text(self, text: str, source_lang='pl', target_lang='uk') -> str:
        """
        Tłumaczy tekst zachowując (w miarę możliwości) formatowanie.
        """
        if not text or text.strip() == "":
            return ""
        
        try:
            # WERSJA MVP (Google Translate Free API)
            # Uwaga: Limit 5000 znaków na request, w produkcji użyj lokalnego modelu!
            translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
            return translated
        except Exception as e:
            print(f"Błąd tłumaczenia: {e}")
            return text # Zwróć oryginał w razie błędu

# Globalna instancja
ai_translator = TranslatorEngine()