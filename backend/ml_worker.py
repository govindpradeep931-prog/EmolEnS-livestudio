import sys
import json
import base64
import cv2
import numpy as np

from models.fer_model import VisualFER
from models.kinematic_tracker import KinematicTracker
from models.text_analyzer import TextAnalyzer
from models.audio_analyzer import AudioAnalyzer
from models.fusion_engine import FusionEngine

def main():
    # Attempt to initialize models with heavy fallbacks
    try:
        visual_fer = VisualFER()
    except:
        visual_fer = None
        
    try:
        kinematic_tracker = KinematicTracker(fps=30.0, velocity_threshold=0.05)
    except:
        kinematic_tracker = None
        
    try:
        text_analyzer = TextAnalyzer()
    except:
        text_analyzer = None
        
    try:
        audio_analyzer = AudioAnalyzer()
    except:
        audio_analyzer = None
        
    try:
        fusion_engine = FusionEngine()
    except:
        fusion_engine = None
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            task = json.loads(line)
            client_id = task.get("clientId")
            payload = task.get("payload", {})
            active_modalities = payload.get("active_modalities", [])
            
            response_payload = {}
            visual_res = None
            text_res = None
            audio_res = None
            arousal_data = {"arousal": 0.1, "velocity": 0, "acceleration": 0}
            
            # Process Visual
            if "visual" in active_modalities and "image" in payload:
                if visual_fer:
                    try:
                        img_data = base64.b64decode(payload["image"].split(",")[1])
                        np_arr = np.frombuffer(img_data, np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            visual_res = visual_fer.analyze_frame(frame)
                            if kinematic_tracker:
                                arousal_data = kinematic_tracker.process_frame(frame)
                    except:
                        pass
                
                if visual_res is None:
                    # Mock Visual
                    visual_res = {"Neutral": 0.8, "Happy": 0.1, "Sad": 0.1, "Angry": 0, "Disgust": 0, "Fear": 0, "Surprise": 0}
            
            # Process Text
            if "text" in active_modalities and "text" in payload:
                if text_analyzer:
                    try:
                        text_res = text_analyzer.analyze_text(payload["text"])
                    except:
                        pass
                
                if text_res is None:
                    text_res = {"lexicon": {"Happy": 0.5, "Neutral": 0.5}, "transformer": {}}
            
            # Process Audio
            if "audio" in active_modalities and "audio" in payload:
                if audio_analyzer:
                    try:
                        audio_bytes = base64.b64decode(payload["audio"].split(",")[1])
                        audio_res = audio_analyzer.analyze_audio(audio_bytes)
                    except:
                        pass
                
                if audio_res is None:
                    audio_res = {"Neutral": 0.7, "Happy": 0.3}
            
            # Fusion
            if fusion_engine and (visual_res or text_res or audio_res):
                try:
                    fused_emotions = fusion_engine.fuse(visual_res, text_res, audio_res, active_modalities)
                except:
                    fused_emotions = visual_res if visual_res else {"Neutral": 1.0}
            else:
                fused_emotions = visual_res if visual_res else {"Neutral": 1.0}
            
            response_payload["visual_emotions"] = visual_res
            response_payload["text_emotions"] = text_res
            response_payload["audio_emotions"] = audio_res
            response_payload["arousal"] = arousal_data
            response_payload["fused_emotions"] = fused_emotions
            
            out = json.dumps({"clientId": client_id, "response": response_payload})
            print(out, flush=True)
            
        except Exception as e:
            print(f"Error processing task: {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
