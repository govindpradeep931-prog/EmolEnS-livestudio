# Optimizing Multimodal Emotion Recognition: Evaluating the Impact of Speech, Text and Visual Modalities

Optimizing Multimodal Emotion Recognition is a real-time multimodal emotion analysis application for evaluating the impact of speech, text, and visual modalities. It combines face video, microphone audio, and typed or transcribed text into one live emotion dashboard with radar charts, timeline graphs, arousal tracking, language conversion, and session reports.

## What It Does

- Detects face emotion from webcam frames.
- Tracks face landmarks and kinematic arousal from facial movement.
- Analyzes speech/audio emotion and speaking rate.
- Analyzes text emotion with multilingual translation support.
- Supports Telugu, Tamil, other Indian languages, and international languages.
- Fuses visual, audio, and text signals into one live emotion score.
- Updates live dashboard graphs at a faster 10 Hz stream interval.
- Generates Seaborn report images from session emotion data.

## Project Structure

| Path | Purpose |
| --- | --- |
| `index.js` | Root entry point. Starts the Node server. |
| `server.js` | Express server, static frontend host, backend launcher, WebSocket proxy, API proxy. |
| `frontend/index.html` | Main browser UI. |
| `frontend/js/app.js` | Live capture, WebSocket streaming, charts, translation UI, demo workflows. |
| `frontend/css/style.css` | Dashboard styling. |
| `backend/main.py` | FastAPI ML backend and WebSocket processor. |
| `backend/models/` | Visual, audio, text, fusion, and kinematic analysis modules. |
| `backend/languages.py` | Supported language list and script detection helpers. |
| `scripts/run-python.js` | Finds installed Python and runs Python commands for tests. |
| `docs/ARCHITECTURE.md` | Architecture notes and flowcharts. |
| `docs/DEMO_MANUAL.md` | Step-by-step demo manual. |
| `docs/APPENDIX.md` | Appendices: APIs, languages, troubleshooting, model notes. |

## Requirements

- Node.js 20 or newer.
- Python 3.10 or newer. Python 3.12 is verified on this machine.
- Webcam and microphone permissions for full live analysis.
- Internet access for first-time model/package downloads and translation service calls.

## Setup

Install Node dependencies:

```powershell
npm install
```

Install Python backend dependencies:

```powershell
& "C:\Users\govin\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r backend\requirements.txt
```

If Python is already on PATH, this also works:

```powershell
python -m pip install -r backend\requirements.txt
```

## Run

```powershell
npm start
```

Open:

```text
http://localhost:8000
```

The Node server starts the Python backend automatically. By default:

- Frontend/Node: `http://localhost:8000`
- Backend/FastAPI: `http://localhost:8001`
- Browser WebSocket endpoint: `/ws`

If a port is busy, the server selects a nearby free port and prints it.

## Verify

Run tests:

```powershell
npm test
```

Check health:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/health
```

Expected healthy response:

```json
{"status":"ok","frontend":true,"backend":{"status":"ok","models_ready":true}}
```

## How It Works

1. The browser captures video frames, audio chunks, and text input.
2. The browser sends payloads to Node over `/ws`.
3. Node proxies WebSocket messages to the FastAPI backend.
4. Backend modules analyze each active modality.
5. `FusionEngine` performs weighted late fusion and short-term smoothing.
6. The backend returns fused emotion scores, face overlays, arousal, and standalone modality results.
7. The browser updates radar charts, timeline graphs, panels, and session summaries.

## Documentation

- [Architecture and Flowcharts](docs/ARCHITECTURE.md)
- [Demo Manual](docs/DEMO_MANUAL.md)
- [Appendix](docs/APPENDIX.md)

## Deployment

The repo includes:

- `Dockerfile`
- `Procfile`
- `render.yaml`

Docker is recommended because the app needs both Node.js and Python ML packages.

```bash
docker build -t optimizing-multimodal-emotion-recognition .
docker run --rm -p 8000:8000 optimizing-multimodal-emotion-recognition
```

## Notes

- Heavy ML models can take time to load on first startup.
- If a model cannot load, the backend uses fail-soft fallback behavior where possible.
- Browser camera and microphone permissions are required for visual/audio modes.
