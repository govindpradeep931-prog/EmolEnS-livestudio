# mer6

Project workspace containing **EmoLens Live Studio** and related assets.

## EmoLens (main app)

Multimodal emotion fusion — visual, audio, and text streams combined in real time.

**Documentation:** [emolens/README.md](emolens/README.md)

**Quick start:**
```powershell
cd emolens
.\start.ps1
```
Then open http://localhost:8000

If port `8000` is already busy, the launcher prints the alternate localhost URL it selected.

If Node.js is installed on PATH, you can also run:
```powershell
npm start
```

The Node server starts the Python ML backend automatically and proxies browser WebSocket traffic through `/ws`, so the app can run on one public web port when deployed.

**Deployment:**

The repo includes `Dockerfile`, `Procfile`, and `render.yaml`. The Docker path is recommended because the app needs both Node.js and Python ML packages.

On Render, create a new Blueprint from this repository or use the included `render.yaml`. For a generic Docker host:
```bash
docker build -t emolens-live-studio .
docker run --rm -p 8000:8000 emolens-live-studio
```

## Other folders

| Folder | Description |
|--------|-------------|
| `emolens/` | EmoLens application (Python backend + Node frontend) |
| `node-v24.15.0-win-x64/` | Portable Node.js runtime (used if system Node is missing) |
| `whisper-main/` | Local Whisper source (optional STT) |
| `Emotion-Detection-FER2013-master/` | Reference FER2013 emotion detection project |
