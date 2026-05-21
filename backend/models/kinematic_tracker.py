import cv2
import numpy as np
import os
import time

FACE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
MODEL_FILENAME = "face_landmarker.task"


def _default_arousal():
    return {
        "arousal": 0.0,
        "velocity": 0.0,
        "acceleration": 0.0,
        "mesh_points": [],
    }


class KinematicTracker:
    def __init__(self, fps=30.0, velocity_threshold=0.05):
        self.face_landmarker = None
        self._frame_ts_ms = 0
        self.prev_landmarks = None
        self.prev_time = None
        self.prev_velocity = 0.0
        self.fps_target = fps
        self.velocity_threshold = velocity_threshold
        # Expressive landmarks (compatible with Face Mesh indices)
        self.key_indices = [13, 14, 78, 308, 33, 263, 65, 295, 52, 282]
        self._init_landmarker()

    def _model_path(self):
        return os.path.join(os.path.dirname(__file__), MODEL_FILENAME)

    def _ensure_model(self):
        path = self._model_path()
        # Valid bundle is ~3.6 MB; reject empty/partial downloads
        if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
            return path
        if os.path.exists(path):
            os.remove(path)
        print(f"Downloading Face Landmarker model to {path} ...")
        import urllib.request
        urllib.request.urlretrieve(FACE_LANDMARKER_URL, path)
        if os.path.getsize(path) < 1_000_000:
            raise RuntimeError("Face Landmarker model download failed or is incomplete.")
        print("Face Landmarker model ready.")
        return path

    def _init_landmarker(self):
        try:
            import mediapipe as mp
            from mediapipe.tasks import python as mp_tasks
            from mediapipe.tasks.python import vision
            from mediapipe.tasks.python.core import base_options as base_options_lib

            model_path = self._ensure_model()
            base_options = base_options_lib.BaseOptions(model_asset_path=model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
            self._mp_image_cls = mp.Image
            self._mp_image_format = mp.ImageFormat.SRGB
            print("KinematicTracker: MediaPipe FaceLandmarker loaded.")
        except Exception as e:
            print(f"KinematicTracker: MediaPipe init failed, using fallback: {e}")

    def process_frame(self, frame_bgr):
        if self.face_landmarker is None:
            return _default_arousal()

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = self._mp_image_cls(
            image_format=self._mp_image_format, data=np.ascontiguousarray(rgb)
        )
        self._frame_ts_ms += int(1000 / self.fps_target)
        results = self.face_landmarker.detect_for_video(mp_image, self._frame_ts_ms)
        current_time = time.time()

        arousal = 0.0
        velocity = 0.0
        acceleration = 0.0
        mesh_points = []

        if not results.face_landmarks:
            return _default_arousal()

        landmarks = results.face_landmarks[0]
        n_landmarks = len(landmarks)
        safe_indices = [i for i in self.key_indices if i < n_landmarks]
        if not safe_indices:
            return _default_arousal()

        current_points = np.array(
            [[landmarks[i].x, landmarks[i].y, landmarks[i].z] for i in safe_indices]
        )
        mesh_points = [[float(l.x), float(l.y)] for l in landmarks]

        if self.prev_landmarks is not None and self.prev_time is not None:
            dt = current_time - self.prev_time
            if dt > 0:
                displacement = np.linalg.norm(current_points - self.prev_landmarks, axis=1)
                avg_displacement = np.mean(displacement)
                velocity = avg_displacement / dt
                acceleration = (velocity - self.prev_velocity) / dt
                arousal = min(
                    1.0,
                    (velocity / self.velocity_threshold) * 0.5 + abs(acceleration) * 0.1,
                )

        self.prev_landmarks = current_points
        self.prev_velocity = velocity
        self.prev_time = current_time

        return {
            "arousal": arousal,
            "velocity": velocity,
            "acceleration": acceleration,
            "mesh_points": mesh_points,
        }
