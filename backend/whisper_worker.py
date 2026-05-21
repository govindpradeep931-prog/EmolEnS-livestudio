import sys
import json
import warnings
import os

# Suppress warnings for clean JSON output
warnings.filterwarnings("ignore")

# === Use local whisper-main repository ===
WHISPER_MAIN_PATH = os.path.join(os.path.dirname(__file__), '..', 'whisper-main')
WHISPER_MAIN_PATH = os.path.abspath(WHISPER_MAIN_PATH)
if os.path.exists(WHISPER_MAIN_PATH):
    sys.path.insert(0, WHISPER_MAIN_PATH)
    print(f"[Whisper] Using local whisper-main from: {WHISPER_MAIN_PATH}", file=sys.stderr)
else:
    print(f"[Whisper] whisper-main not found at {WHISPER_MAIN_PATH}, falling back to pip whisper.", file=sys.stderr)

def transcribe(audio_path):
    try:
        import whisper

        # Use 'base' model — supports 99 languages automatically
        model = whisper.load_model("base")

        # task="translate" → transcribes ANY language and outputs English text
        # task="transcribe" → outputs text in the original language
        result = model.transcribe(audio_path, task="translate")

        detected_lang = result.get("language", "unknown")
        text = result.get("text", "").strip()

        print(json.dumps({
            "success": True,
            "text": text,
            "detected_language": detected_lang
        }))

    except ImportError:
        print(json.dumps({
            "success": False,
            "error": "Whisper library missing. Ensure whisper-main is present or run 'pip install openai-whisper'."
        }))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        transcribe(sys.argv[1])
    else:
        print(json.dumps({"success": False, "error": "No audio file provided"}))
