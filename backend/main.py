import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
import logging
import warnings
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*unauthenticated requests to the HF Hub.*")
# Set these to "1" ONLY if you have already downloaded the HuggingFace models locally:
# os.environ["TRANSFORMERS_OFFLINE"] = "1"
# os.environ["HF_HUB_OFFLINE"] = "1"

import asyncio
import base64
import json
import threading
import cv2
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect
import uvicorn

# Ensure imports work when running from repo root or from this folder
import sys as _sys
from pathlib import Path as _Path
_THIS_DIR = _Path(__file__).resolve().parent
if str(_THIS_DIR) not in _sys.path:
    _sys.path.insert(0, str(_THIS_DIR))

from languages import SUPPORTED_LANGUAGES, SUPPORTED_LANGUAGE_CODES


class TranslationRequest(BaseModel):
    text: str
    target_language: str = "en"
    source_language: str = "auto"

# Model handles (loaded in background so the server binds quickly)
visual_fer = None
text_analyzer = None
audio_analyzer = None
kinematic_tracker = None
FusionEngine = None
_models_ready = threading.Event()


def _load_models():
    global visual_fer, text_analyzer, audio_analyzer, kinematic_tracker, FusionEngine
    print("[Emotion Recognition] Loading ML models (this may take a minute on first run)...")

    try:
        from models.fer_model import VisualFER
        from models.text_analyzer import TextAnalyzer
        from models.audio_analyzer import AudioAnalyzer
        from models.fusion_engine import FusionEngine as LoadedFusionEngine
        from models.kinematic_tracker import KinematicTracker
        FusionEngine = LoadedFusionEngine
    except Exception as e:
        print(f"Failed to import ML modules: {e}")
        _models_ready.set()
        return

    try:
        visual_fer = VisualFER()
    except Exception as e:
        print(f"Failed to init VisualFER: {e}")
        visual_fer = None

    try:
        text_analyzer = TextAnalyzer()
    except Exception as e:
        print(f"Failed to init TextAnalyzer: {e}")
        text_analyzer = None

    try:
        audio_analyzer = AudioAnalyzer()
    except Exception as e:
        print(f"Failed to init AudioAnalyzer: {e}")
        audio_analyzer = None

    try:
        kinematic_tracker = KinematicTracker()
    except Exception as e:
        print(f"Failed to init KinematicTracker: {e}")
        kinematic_tracker = None

    _models_ready.set()
    print("[Emotion Recognition] ML models ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    loader = threading.Thread(target=_load_models, daemon=True, name="emotion-recognition-model-loader")
    loader.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {
            "status": "Optimizing Multimodal Emotion Recognition backend is running",
        "models_ready": _models_ready.is_set(),
        "message": "Use /docs for API documentation and /ws for WebSocket connections."
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "models_ready": _models_ready.is_set()}


@app.get("/languages")
def languages():
    return {"languages": SUPPORTED_LANGUAGES}


@app.post("/translate")
def translate(request: TranslationRequest):
    target = request.target_language
    if target not in SUPPORTED_LANGUAGE_CODES:
        return {
            "success": False,
            "error": f"Unsupported target language: {target}",
            "languages": SUPPORTED_LANGUAGES,
        }

    try:
        from models.text_analyzer import translate_with_service
        return translate_with_service(
            request.text,
            target=target,
            source=request.source_language or "auto",
        )
    except Exception as e:
        return {
            "success": False,
            "text": request.text,
            "translated_text": request.text,
            "source_language": request.source_language or "auto",
            "target_language": target,
            "error": f"Translation service unavailable: {e}",
        }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected")
    session_data = {"timeline": []}
    if FusionEngine is None:
        from models.fusion_engine import FusionEngine as LocalFusionEngine
        fusion_engine = LocalFusionEngine()
    else:
        fusion_engine = FusionEngine()

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            active_modalities = payload.get("active_modalities", [])
            response_payload = {}

            visual_res = None
            text_res = None
            audio_res = None

            # Process Visual
            if "visual" in active_modalities and "image" in payload:
                if not visual_fer:
                    visual_res = None
                else:
                    img_str = payload["image"]
                    if "," in img_str:
                        img_str = img_str.split(",")[1]
                    img_data = base64.b64decode(img_str)
                    np_arr = np.frombuffer(img_data, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                    if frame is not None:
                        visual_res = visual_fer.analyze_frame(frame)
                        response_payload["visual_emotions"] = visual_res

                        # Run kinematic tracking for arousal & face mesh
                        if kinematic_tracker:
                            try:
                                arousal_data = kinematic_tracker.process_frame(frame)
                                response_payload["arousal"] = arousal_data
                            except Exception as ke:
                                print(f"Kinematic tracking error: {ke}")

            # Process Text
            if "text" in active_modalities and "text" in payload:
                if text_analyzer:
                    text_res = text_analyzer.analyze_text(payload["text"])
                else:
                    text_res = None
                response_payload["text_emotions"] = text_res

            # Process Audio
            if "audio" in active_modalities and "audio" in payload:
                if not audio_analyzer:
                    audio_res = None
                else:
                    # Decode base64 audio safely
                    audio_str = payload["audio"]
                    if "," in audio_str:
                        audio_str = audio_str.split(",")[1]
                    audio_bytes = base64.b64decode(audio_str)
                    audio_res = audio_analyzer.analyze_audio(audio_bytes)
                response_payload["audio_emotions"] = audio_res

            # Fusion
            fused_emotions = fusion_engine.fuse(visual_res, text_res, audio_res, active_modalities)
            response_payload["fused_emotions"] = fused_emotions

            session_data["timeline"].append(fused_emotions)

            await websocket.send_json(response_payload)

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8001"))
    print("=" * 50)
    print("  Optimizing Multimodal Emotion Recognition ML Backend")
    print(f"  http://localhost:{port}")
    print(f"  API docs: http://localhost:{port}/docs")
    print("=" * 50)
    print("Start the UI in another terminal:")
    print('  cd optimizing-multimodal-emotion-recognition && node server.js')
    print("  (or run .\\start.ps1 to launch both)")
    print("=" * 50)
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
    except OSError as e:
        if getattr(e, "winerror", None) == 10048 or "address already in use" in str(e).lower():
            print(f"\nERROR: Port {port} is already in use.")
            print("Stop the other emotion recognition backend process, then try again.")
        raise
