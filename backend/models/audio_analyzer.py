import numpy as np
from transformers import pipeline
from transformers.utils import logging as transformers_logging

transformers_logging.set_verbosity_error()

class AudioAnalyzer:
    def __init__(self):
        # ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition is already in local HF cache
        try:
            self.audio_classifier = pipeline(
                "audio-classification",
                model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
            )
            # Label mapping for this model's output labels
            self.label_mapping = {
                "disgust": "Disgust",
                "fear": "Fear",
                "anger": "Angry",
                "neutral": "Neutral",
                "happiness": "Happy",
                "sadness": "Sad",
                "boredom": "Neutral",   # map boredom -> Neutral
            }
            print("Loaded SER Wav2Vec2 (ehcalabres) model.")
        except Exception as e:
            print(f"Failed to load speech transformer, using heuristic fallback: {e}")
            self.audio_classifier = None
            self.label_mapping = {}

    def estimate_speaking_rate(self, audio_np, sample_rate=16000):
        if len(audio_np) == 0:
            return 0.0
        # Window size for short-term energy (20ms window)
        win_size = int(0.02 * sample_rate)
        # Hop size for moving forward (10ms hop)
        hop_size = int(0.01 * sample_rate)
        
        # Calculate short-term energy (STE)
        ste = []
        for i in range(0, len(audio_np) - win_size, hop_size):
            window = audio_np[i : i + win_size]
            ste.append(np.sum(window**2))
        ste = np.array(ste)
        
        if len(ste) == 0 or np.max(ste) == 0:
            return 0.0
            
        # Smooth with moving average (5 frames = 50ms)
        smoothed = np.convolve(ste, np.ones(5)/5, mode='same')
        
        # Peak detection corresponding to syllable nuclei
        peaks = 0
        threshold = 0.15 * np.max(smoothed)
        min_dist_frames = 15 # 150ms minimum separation between syllables
        last_peak_frame = -min_dist_frames
        
        for i in range(1, len(smoothed) - 1):
            if smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1]:
                if smoothed[i] > threshold and (i - last_peak_frame) >= min_dist_frames:
                    peaks += 1
                    last_peak_frame = i
                    
        duration = len(audio_np) / sample_rate
        speaking_rate = peaks / duration if duration > 0 else 0.0
        return speaking_rate

    def analyze_audio(self, audio_data):
        if len(audio_data) == 0:
            return None
            
        # Convert bytes to numpy array (assuming 16-bit PCM for simplicity)
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        rms = np.sqrt(np.mean(audio_np**2))
        zcr = np.mean(np.abs(np.diff(np.sign(audio_np)))) / 2
        
        # Heuristic mapping for basic metrics
        emotions = {
            'Angry': min(1.0, rms * 5 + zcr * 2),
            'Happy': min(1.0, rms * 4 + zcr),
            'Sad': max(0.0, 1.0 - rms * 10),
            'Neutral': max(0.0, 0.5 - rms * 5),
            'Fear': min(1.0, zcr * 5),
            'Surprise': min(1.0, rms * 6),
            'Disgust': min(1.0, zcr * 3)
        }
        
        # Run Speech Transformer if available
        if self.audio_classifier:
            try:
                res = self.audio_classifier(audio_np)
                for item in res:
                    mapped_label = self.label_mapping.get(item['label'])
                    if mapped_label:
                        emotions[mapped_label] = float(item['score'])
            except Exception as e:
                print(f"Audio transformer inference error: {e}")
                
        # Estimate acoustic rate (speaking rate)
        speaking_rate = self.estimate_speaking_rate(audio_np)
        
        # Normalize
        total = sum(emotions.values()) + 1e-6
        normalized_emotions = {k: v/total for k, v in emotions.items()}
        
        return {
            "emotions": normalized_emotions,
            "speaking_rate": speaking_rate,
            "energy": float(rms)
        }
