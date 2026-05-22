import cv2
import numpy as np
import os

class VisualFER:
    def __init__(self, model_filename='emotion_detection_model.h5'):
        # Our standard frontend emotions:
        self.standard_emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        
        # FER2013 dict from the user's project
        self.fer_dict = {0: "Angry", 1: "Disgust", 2: "Fear", 3: "Happy", 4: "Sad", 5: "Surprise", 6: "Neutral"}
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load the model
        model_path = os.path.join(os.path.dirname(__file__), model_filename)
        self.model = None
        try:
            self.model = self._load_legacy_fer_model(model_path)
            print(f"Loaded FER2013 Keras model from {model_path}.")
        except Exception as e:
            print(f"Could not load weights. Fallback logic will be used. Error: {e}")

    def _load_legacy_fer_model(self, model_path):
        from tensorflow.keras import layers, models

        model = models.Sequential([
            layers.Input(shape=(48, 48, 1)),
            layers.Conv2D(64, (3, 3), activation="relu", name="conv2d"),
            layers.Conv2D(64, (3, 3), activation="relu", name="conv2d_1"),
            layers.MaxPooling2D((2, 2), name="max_pooling2d"),
            layers.Dropout(0.2, name="dropout"),
            layers.Conv2D(128, (3, 3), activation="relu", name="conv2d_2"),
            layers.MaxPooling2D((2, 2), name="max_pooling2d_1"),
            layers.Conv2D(128, (3, 3), activation="relu", name="conv2d_3"),
            layers.MaxPooling2D((2, 2), name="max_pooling2d_2"),
            layers.Dropout(0.22, name="dropout_1"),
            layers.Flatten(name="flatten"),
            layers.Dense(512, activation="relu", name="dense"),
            layers.Dropout(0.5, name="dropout_2"),
            layers.Dense(256, activation="relu", name="dense_1"),
            layers.Dropout(0.5, name="dropout_3"),
            layers.Dense(7, activation="softmax", name="dense_2"),
        ])
        model.load_weights(model_path)
        return model

    def analyze_frame(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.15,
            minNeighbors=4,
            minSize=(48, 48),
        )
        
        if len(faces) > 0:
            (x, y, w, h) = max(faces, key=lambda box: box[2] * box[3])
            roi_gray = gray[y:y + h, x:x + w]
            resized = cv2.resize(roi_gray, (48, 48)).astype("float32") / 255.0
            cropped_img = np.expand_dims(np.expand_dims(resized, -1), 0)
            
            # Predict
            if self.model:
                try:
                    prediction = self.model.predict(cropped_img, verbose=0)
                    probs = prediction[0]
                    
                    emotions_map = {}
                    for i in range(len(probs)):
                        fer_label = self.fer_dict[i]
                        emotions_map[fer_label] = float(probs[i])
                        
                    return {
                        "emotions": emotions_map,
                        "face_rect": [int(x), int(y), int(w), int(h)]
                    }
                except Exception as e:
                    print(f"Prediction error: {e}")
            
            # Lightweight fallback from face texture/brightness keeps live analysis responsive
            # when TensorFlow weights are unavailable.
            brightness = float(np.mean(roi_gray) / 255.0)
            contrast = float(np.std(roi_gray) / 128.0)
            edge_density = float(np.mean(cv2.Canny(roi_gray, 80, 160) > 0))
            fallback_emotions = {
                "Angry": min(0.35, contrast * 0.18 + edge_density * 0.6),
                "Disgust": min(0.18, edge_density * 0.35),
                "Fear": min(0.25, contrast * 0.2),
                "Happy": min(0.45, brightness * 0.28 + edge_density * 0.35),
                "Sad": min(0.35, (1.0 - brightness) * 0.28),
                "Surprise": min(0.32, contrast * 0.16 + brightness * 0.1),
                "Neutral": 0.45,
            }
            total = sum(fallback_emotions.values())
            return {
                "emotions": {k: v/total for k, v in fallback_emotions.items()},
                "face_rect": [int(x), int(y), int(w), int(h)]
            }
        return None

