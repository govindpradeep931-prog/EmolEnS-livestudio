# Demo Manual

Use this manual to demonstrate the project from a clean startup to a complete live session.

## 1. Start The Project

From the repo root:

```powershell
npm start
```

Open:

```text
http://localhost:8000
```

Confirm health:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/health
```

Expected:

```json
{"status":"ok","frontend":true,"backend":{"status":"ok","models_ready":true}}
```

## 2. Live Emotion Demo

1. Open the `Live Studio` tab.
2. Click `Visual`.
3. Allow camera permission.
4. Click `Audio`.
5. Allow microphone permission.
6. Click `Text`.
7. Type a sentence such as:

```text
I am excited and happy about this project.
```

8. Click `Start Session`.
9. Watch these areas update:

| Area | What To Show |
| --- | --- |
| Live Feed | Face bounding box and mesh overlay. |
| Emotion Fusion Radar | Current fused emotion distribution. |
| Dominant/Confidence/Reload Rate | Real-time top emotion and update rate. |
| Acoustic Detector | Audio waveform and speech emotion output. |
| Kinematic Arousal Tracker | Movement-based arousal score. |
| Running Timeline | Emotion trend over time. |

10. Change facial expression, tone, and text to show multimodal updates.
11. Click `End Session`.
12. Review the session summary modal.

## 3. Telugu And Tamil Text Demo

Open `Live Studio`, activate `Text`, and enter Telugu:

```text
నేను ఈరోజు చాలా సంతోషంగా ఉన్నాను
```

Or Tamil:

```text
நான் இன்று மிகவும் மகிழ்ச்சியாக இருக்கிறேன்
```

Start the session. The backend detects the script, translates to English when the translator is available, and uses the translated text for emotion analysis.

## 4. Converter Demo

1. Open the `Converter` tab.
2. Enter text in `Text to translate`.
3. Pick a target language such as `Telugu`, `Tamil`, `Hindi`, `French`, or `Japanese`.
4. Click `Translate`.
5. The browser calls Node `/translate`, which proxies to the Python backend.

## 5. Speech-To-Text Demo

1. Open the `Converter` tab.
2. Click `Start Listening`.
3. Speak into the microphone.
4. Click `Stop & Process`.
5. The app sends audio to `/transcribe`.
6. The Whisper worker returns text and places it into the transcript area.

## 6. Media Upload Demo

1. Open the `Media Upload` tab.
2. Select a video, audio, or text file.
3. Click `Analyze File`.
4. The current implementation simulates file analysis and then generates a Seaborn report from session emotion data.

## 7. Seaborn Report Demo

After ending a live session:

1. In the session summary modal, click `Generate Seaborn Report`.
2. The Node server runs `backend/seaborn_worker.py`.
3. The generated image is served from `/reports`.

## 8. Talking Points

- The app runs as one browser-facing service on port `8000`.
- Python ML runs behind Node on port `8001`.
- The browser never talks directly to the backend port.
- WebSocket streaming keeps live analysis responsive.
- The fusion engine combines modalities using weights and smoothing.
- The system is fail-soft: missing heavyweight models do not crash the entire app when fallbacks are available.

## 9. Stop The Project

Find running processes:

```powershell
Get-Process node,python -ErrorAction SilentlyContinue
```

Stop them:

```powershell
Get-Process node,python -ErrorAction SilentlyContinue | Stop-Process
```

