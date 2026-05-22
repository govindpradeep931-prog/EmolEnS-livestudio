# Appendix

## Appendix A: Supported Languages

Indian languages:

| Code | Language |
| --- | --- |
| `hi` | Hindi |
| `te` | Telugu |
| `ta` | Tamil |
| `ml` | Malayalam |
| `kn` | Kannada |
| `bn` | Bengali |
| `mr` | Marathi |
| `gu` | Gujarati |
| `pa` | Punjabi |
| `ur` | Urdu |
| `or` | Odia |
| `as` | Assamese |
| `sa` | Sanskrit |

International languages:

| Code | Language |
| --- | --- |
| `en` | English |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `pt` | Portuguese |
| `ru` | Russian |
| `ar` | Arabic |
| `zh-CN` | Chinese |
| `ja` | Japanese |
| `ko` | Korean |
| `id` | Indonesian |
| `tr` | Turkish |

## Appendix B: Model Notes

### Visual Emotion

File: `backend/models/fer_model.py`

- Uses OpenCV Haar cascade for face detection.
- Uses TensorFlow Keras `.h5` emotion model when available.
- Uses corrected FER2013 label order:

```text
0 Angry
1 Disgust
2 Fear
3 Happy
4 Sad
5 Surprise
6 Neutral
```

- Uses histogram equalization and largest-face selection.
- Uses a lightweight fallback if model loading fails.

### Text Emotion

File: `backend/models/text_analyzer.py`

- Detects script for Indian language hints.
- Translates text to English when `deep-translator` is available.
- Uses VADER lexicon sentiment.
- Uses transformer emotion pipeline when available.

### Audio Emotion

File: `backend/models/audio_analyzer.py`

- Converts PCM audio to normalized NumPy data.
- Estimates speaking rate from short-term energy peaks.
- Uses transformer audio classification when available.
- Uses RMS/ZCR heuristic fallback.

### Kinematic Arousal

File: `backend/models/kinematic_tracker.py`

- Uses MediaPipe FaceLandmarker.
- Tracks selected facial landmarks.
- Computes velocity and acceleration.
- Converts movement intensity into arousal score.

### Fusion

File: `backend/models/fusion_engine.py`

- Uses weighted late fusion.
- Normalizes scores.
- Smooths against previous frame scores within the current WebSocket session.

## Appendix C: Important Commands

Start:

```powershell
npm start
```

Test:

```powershell
npm test
```

Install backend dependencies:

```powershell
& "C:\Users\govin\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r backend\requirements.txt
```

Compile-check backend files:

```powershell
& "C:\Users\govin\AppData\Local\Programs\Python\Python312\python.exe" -m py_compile backend\main.py backend\models\text_analyzer.py backend\models\fer_model.py backend\models\fusion_engine.py backend\languages.py
```

Check server:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/health
```

## Appendix D: Troubleshooting

### Python is installed but app says backend unavailable

Python may not be on PATH. The Node server searches:

1. `backend\.venv\Scripts\python.exe`
2. `PYTHON` environment variable
3. Windows installs under `%LOCALAPPDATA%\Programs\Python`
4. `python`

If needed, set:

```powershell
$env:PYTHON="C:\Users\govin\AppData\Local\Programs\Python\Python312\python.exe"
npm start
```

### Camera or microphone does not work

- Use `http://localhost:8000`.
- Allow camera and microphone permissions in the browser.
- Close other apps using the camera.
- Refresh and activate the modality again.

### Backend dependencies missing

Run:

```powershell
& "C:\Users\govin\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r backend\requirements.txt
```

### Port already in use

The server tries nearby free ports. To inspect ports:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 8000,8001 -ErrorAction SilentlyContinue
```

### Stop all local app processes

```powershell
Get-Process node,python -ErrorAction SilentlyContinue | Stop-Process
```

## Appendix E: Demo Checklist

| Step | Expected Result |
| --- | --- |
| `npm start` | Node starts and launches Python backend. |
| Open `/health` | Backend reports `models_ready: true`. |
| Activate Visual | Webcam feed appears. |
| Activate Audio | Waveform appears. |
| Activate Text | Text input affects emotion results. |
| Start Session | Radar and timeline update live. |
| Change expression | Face overlay and fused emotion change. |
| Speak | Audio panel and speaking rate update. |
| Translate Telugu/Tamil | Converter returns translated output. |
| End Session | Summary modal appears. |

