# Fail-soft imports: server/tests should still run even without ML deps installed.
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except Exception as e:
    SentimentIntensityAnalyzer = None
    print(f"vaderSentiment not available: {e}")

try:
    from transformers import pipeline
except Exception as e:
    pipeline = None
    print(f"transformers not available: {e}")

# Multilingual translation support
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("deep-translator not installed. Text modality will be English-only.")

class TextAnalyzer:
    def __init__(self):
        self.lexicon_analyzer = None
        if SentimentIntensityAnalyzer is not None:
            try:
                self.lexicon_analyzer = SentimentIntensityAnalyzer()
            except Exception as e:
                print(f"Failed to init VADER: {e}")
                self.lexicon_analyzer = None

        self.transformer = None
        if pipeline is not None:
            try:
                self.transformer = pipeline(
                    "sentiment-analysis",
                    model="j-hartmann/emotion-english-distilroberta-base",
                )
            except Exception as e:
                print(f"Failed to load transformer, using mock: {e}")
                self.transformer = None

    def translate_to_english(self, text):
        """Auto-detect language and translate any text to English."""
        if not text or not TRANSLATOR_AVAILABLE:
            return text, "en"
        try:
            translator = GoogleTranslator(source='auto', target='en')
            translated = translator.translate(text)
            detected_lang = "auto"
            print(f"[Multilingual] Translated to English: '{translated}'")
            return translated, detected_lang
        except Exception as e:
            print(f"[Multilingual] Translation failed, using original text: {e}")
            return text, "en"

    def analyze_text(self, text):
        if not text:
            return None

        # === MULTILINGUAL: Translate to English first ===
        english_text, detected_lang = self.translate_to_english(text)

        # 1. Lexicon Dictionary Analysis (VADER) on English text
        if self.lexicon_analyzer:
            lexicon_scores = self.lexicon_analyzer.polarity_scores(english_text)
            compound = lexicon_scores['compound']
            lexicon_emotions = {
                'Happy':   max(0.0, compound),
                'Sad':     max(0.0, -compound),
                'Neutral': lexicon_scores['neu'],
                'Angry':   max(0.0, -compound) * 0.5,
                'Disgust': max(0.0, -compound) * 0.2,
                'Fear':    max(0.0, -compound) * 0.3,
                'Surprise': max(0.0, compound) * 0.3
            }
        else:
            # deterministic fallback so downstream fusion/tests don't crash
            lexicon_emotions = {
                'Happy': 0.0,
                'Sad': 0.0,
                'Neutral': 1.0,
                'Angry': 0.0,
                'Disgust': 0.0,
                'Fear': 0.0,
                'Surprise': 0.0,
            }

        # 2. Emotion Transformer Model on English text
        transformer_emotions = {}
        if self.transformer:
            try:
                res = self.transformer(english_text, top_k=None)[0]
                label_mapping = {
                    'anger':   'Angry',
                    'disgust': 'Disgust',
                    'fear':    'Fear',
                    'joy':     'Happy',
                    'sadness': 'Sad',
                    'surprise':'Surprise',
                    'neutral': 'Neutral'
                }
                for item in res:
                    mapped_label = label_mapping.get(item['label'])
                    if mapped_label:
                        transformer_emotions[mapped_label] = float(item['score'])
            except Exception as e:
                print(f"Transformer error: {e}")

        return {
            "lexicon": lexicon_emotions,
            "transformer": transformer_emotions,
            "detected_language": detected_lang,
            "translated_text": english_text if detected_lang != "en" else None
        }
