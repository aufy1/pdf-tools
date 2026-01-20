from deep_translator import GoogleTranslator

class TranslatorEngine:
    def __init__(self):
        pass

    def translate_text(self, text: str, source_lang='pl', target_lang='uk') -> str:
        if not text or not text.strip():
            return ""
        try:
            # deep-translator jest świetny do prototypowania
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        except Exception as e:
            print(f"Translation Error: {e}")
            return text

ai_translator = TranslatorEngine()