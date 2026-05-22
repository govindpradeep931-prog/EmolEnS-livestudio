let activeModalities = [];
let isLive = false;
let stream = null;
let captureInterval = null;
let socket = null;
const LIVE_UPDATE_MS = 100;
const MAX_TIMELINE_POINTS = 60;
let lastUpdateAt = performance.now();
let updatesPerSecond = 0;

const fallbackLanguages = [
    { code: 'en', name: 'English', group: 'International' },
    { code: 'hi', name: 'Hindi', group: 'Indian' },
    { code: 'te', name: 'Telugu', group: 'Indian' },
    { code: 'ta', name: 'Tamil', group: 'Indian' },
    { code: 'ml', name: 'Malayalam', group: 'Indian' },
    { code: 'kn', name: 'Kannada', group: 'Indian' },
    { code: 'bn', name: 'Bengali', group: 'Indian' },
    { code: 'mr', name: 'Marathi', group: 'Indian' },
    { code: 'gu', name: 'Gujarati', group: 'Indian' },
    { code: 'pa', name: 'Punjabi', group: 'Indian' },
    { code: 'ur', name: 'Urdu', group: 'Indian' },
    { code: 'or', name: 'Odia', group: 'Indian' },
    { code: 'as', name: 'Assamese', group: 'Indian' },
    { code: 'sa', name: 'Sanskrit', group: 'Indian' },
    { code: 'es', name: 'Spanish', group: 'International' },
    { code: 'fr', name: 'French', group: 'International' },
    { code: 'de', name: 'German', group: 'International' },
    { code: 'it', name: 'Italian', group: 'International' },
    { code: 'pt', name: 'Portuguese', group: 'International' },
    { code: 'ru', name: 'Russian', group: 'International' },
    { code: 'ar', name: 'Arabic', group: 'International' },
    { code: 'zh-CN', name: 'Chinese', group: 'International' },
    { code: 'ja', name: 'Japanese', group: 'International' },
    { code: 'ko', name: 'Korean', group: 'International' },
    { code: 'id', name: 'Indonesian', group: 'International' },
    { code: 'tr', name: 'Turkish', group: 'International' }
];

// Audio State
let audioContext = null;
let analyser = null;
let dataArray = null;
let animationId = null;
let accumulatedAudio = [];
let audioProcessor = null;

// DOM Elements
const videoFeed = document.getElementById('video-feed');
const textInput = document.getElementById('text-input');
const liveDot = document.getElementById('live-dot');
const startBtn = document.getElementById('btn-start');
const stopBtn = document.getElementById('btn-stop');
const arousalFill = document.getElementById('arousal-fill');
const arousalVal = document.getElementById('arousal-val');
const velVal = document.getElementById('vel-val');
const accVal = document.getElementById('acc-val');
const acousticCanvas = document.getElementById('acoustic-waveform');
const acousticCtx = acousticCanvas.getContext('2d');
const visualStatus = document.getElementById('status-visual');
const audioStatus = document.getElementById('status-audio');
const textStatus = document.getElementById('status-text');
const dominantEmotionEl = document.getElementById('dominant-emotion');
const confidenceEl = document.getElementById('confidence-val');
const updateRateEl = document.getElementById('update-rate');

// Session Data
let sessionEmotions = { 'Angry': 0, 'Disgust': 0, 'Fear': 0, 'Happy': 0, 'Sad': 0, 'Surprise': 0, 'Neutral': 0 };
let frameCount = 0;

const emotionColors = {
    'Angry': '#ef4444', 'Disgust': '#10b981', 'Fear': '#8b5cf6', 'Happy': '#f59e0b', 'Sad': '#3b82f6', 'Surprise': '#f472b6', 'Neutral': '#64748b'
};

// Initialize Charts
const radarCtx = document.getElementById('radarChart').getContext('2d');
const radarChart = new Chart(radarCtx, {
    type: 'radar',
    data: {
        labels: Object.keys(emotionColors),
        datasets: [{
            data: [0, 0, 0, 0, 0, 0, 0],
            backgroundColor: 'rgba(99, 102, 241, 0.4)',
            borderColor: '#6366f1',
            pointBackgroundColor: '#ec4899',
        }]
    },
    options: {
        responsive: true, maintainAspectRatio: false,
        scales: { r: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { display: false }, min: 0, max: 1 } },
        plugins: { legend: { display: false } }
    }
});

const timelineCtx = document.getElementById('timelineChart').getContext('2d');
const timelineChart = new Chart(timelineCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: Object.keys(emotionColors).map(e => ({
            label: e, data: [], borderColor: emotionColors[e], borderWidth: 2, tension: 0.4, pointRadius: 0
        }))
    },
    options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { max: 1, min: 0 }, x: { ticks: { maxTicksLimit: 10 } } },
        plugins: { legend: { position: 'right' } },
        animation: false
    }
});

// Capture a video frame and convert to base64 JPEG
function captureVideoFrame() {
    const hiddenCanvas = document.getElementById('canvas-hidden');
    const ctx = hiddenCanvas.getContext('2d');
    
    // Match resolution
    hiddenCanvas.width = videoFeed.videoWidth || 640;
    hiddenCanvas.height = videoFeed.videoHeight || 480;
    
    ctx.drawImage(videoFeed, 0, 0, hiddenCanvas.width, hiddenCanvas.height);
    return hiddenCanvas.toDataURL('image/jpeg', 0.5);
}

// Convert a flat array of Int16 values to base64 string
function int16ToBase64(int16Array) {
    const buffer = new Int16Array(int16Array).buffer;
    const bytes = new Uint8Array(buffer);
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

async function initVisual() {
    try {
        const vStream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoFeed.srcObject = vStream;
        videoFeed.onloadedmetadata = () => {
            videoFeed.play();
        };
        return true;
    } catch (e) {
        console.warn("Visual init failed:", e);
        return false;
    }
}

async function initAudio() {
    try {
        const aStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(aStream);
        
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        
        dataArray = new Uint8Array(analyser.frequencyBinCount);
        drawAcoustic();
        
        // Setup separate audio streaming processor
        audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        source.connect(audioProcessor);
        audioProcessor.connect(audioContext.destination);
        
        audioProcessor.onaudioprocess = (e) => {
            if (!isLive) return;
            const inputData = e.inputBuffer.getChannelData(0);
            const pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcm16[i] = Math.min(1, Math.max(-1, inputData[i])) * 0x7FFF;
            }
            accumulatedAudio.push(...pcm16);
        };
        
        return true;
    } catch (e) {
        console.warn("Audio init failed:", e);
        return false;
    }
}

function drawAcoustic() {
    if (!analyser) return;
    animationId = requestAnimationFrame(drawAcoustic);
    analyser.getByteTimeDomainData(dataArray);
    
    acousticCtx.fillStyle = 'rgba(0, 0, 0, 0.2)';
    acousticCtx.fillRect(0, 0, acousticCanvas.width, acousticCanvas.height);
    acousticCtx.lineWidth = 2;
    acousticCtx.strokeStyle = '#6366f1';
    acousticCtx.beginPath();
    
    const sliceWidth = acousticCanvas.width / dataArray.length;
    let x = 0;
    for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * acousticCanvas.height / 2;
        if (i === 0) acousticCtx.moveTo(x, y);
        else acousticCtx.lineTo(x, y);
        x += sliceWidth;
    }
    acousticCtx.lineTo(acousticCanvas.width, acousticCanvas.height / 2);
    acousticCtx.stroke();
}

async function loadLanguages() {
    let languages = fallbackLanguages;
    try {
        const response = await fetch('/languages');
        const data = await response.json();
        if (Array.isArray(data.languages) && data.languages.length) {
            languages = data.languages;
        }
    } catch (e) {
        console.warn('Using fallback language list:', e);
    }

    const select = document.getElementById('target-lang');
    if (!select) return;

    const grouped = languages.reduce((acc, language) => {
        const group = language.group || 'International';
        if (!acc[group]) acc[group] = [];
        acc[group].push(language);
        return acc;
    }, {});

    select.innerHTML = Object.entries(grouped).map(([group, items]) => {
        const options = items
            .map(language => `<option value="${language.code}">${language.name}</option>`)
            .join('');
        return `<optgroup label="${group} Languages">${options}</optgroup>`;
    }).join('');
}

// Render dynamic face bounding boxes and MediaPipe mesh points
function drawFaceOverlay(faceRect, meshPoints) {
    const overlay = document.getElementById('canvas-overlay');
    if (!overlay) return;
    const ctx = overlay.getContext('2d');
    
    // Clear previous drawing
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    
    // Adjust resolution dynamically to match client size
    overlay.width = videoFeed.clientWidth || 640;
    overlay.height = videoFeed.clientHeight || 480;
    
    // 1. Draw CNN Face Bounding Box
    if (faceRect && faceRect.length === 4) {
        const videoW = videoFeed.videoWidth || 640;
        const videoH = videoFeed.videoHeight || 480;
        
        const boxX = (faceRect[0] / videoW) * overlay.width;
        const boxY = (faceRect[1] / videoH) * overlay.height;
        const boxW = (faceRect[2] / videoW) * overlay.width;
        const boxH = (faceRect[3] / videoH) * overlay.height;
        
        ctx.strokeStyle = '#10b981'; // Emerald Green
        ctx.lineWidth = 3;
        ctx.strokeRect(boxX, boxY, boxW, boxH);
        
        ctx.fillStyle = '#10b981';
        ctx.font = 'bold 12px Outfit';
        ctx.fillText('FACE DETECTED (CNN)', boxX, boxY > 15 ? boxY - 5 : 15);
        
        document.getElementById('standalone-vis-box').innerText = `[x:${faceRect[0]}, y:${faceRect[1]}, w:${faceRect[2]}, h:${faceRect[3]}]`;
    } else {
        document.getElementById('standalone-vis-box').innerText = "Searching face...";
    }
    
    // 2. Draw 468 MediaPipe FaceMesh landmarks
    if (meshPoints && meshPoints.length > 0) {
        ctx.fillStyle = 'rgba(99, 102, 241, 0.8)'; // Indigo dots
        meshPoints.forEach(pt => {
            const px = pt[0] * overlay.width;
            const py = pt[1] * overlay.height;
            ctx.beginPath();
            ctx.arc(px, py, 1.2, 0, 2 * Math.PI);
            ctx.fill();
        });
        
        // Highlight lips
        const lipIndices = [13, 14, 78, 308];
        ctx.strokeStyle = 'rgba(236, 72, 153, 0.6)'; // Glowing Pink
        ctx.lineWidth = 1;
        ctx.beginPath();
        lipIndices.forEach((idx, i) => {
            if (meshPoints[idx]) {
                const lx = meshPoints[idx][0] * overlay.width;
                const ly = meshPoints[idx][1] * overlay.height;
                if (i === 0) ctx.moveTo(lx, ly);
                else ctx.lineTo(lx, ly);
            }
        });
        ctx.closePath();
        ctx.stroke();
    }
}

function updateModalityUI(modality, enabled) {
    const btn = document.getElementById(`btn-${modality}`);
    if (enabled) {
        if (!activeModalities.includes(modality)) activeModalities.push(modality);
        btn.classList.add('active');
    } else {
        activeModalities = activeModalities.filter(x => x !== modality);
        btn.classList.remove('active');
    }
    const label = modality === 'visual' ? 'Visual' : modality === 'audio' ? 'Audio' : 'Text';
    const statusEl = modality === 'visual' ? visualStatus : modality === 'audio' ? audioStatus : textStatus;
    if (statusEl) {
        statusEl.textContent = enabled ? `${label} active` : `${label} inactive`;
        statusEl.classList.toggle('inactive', !enabled);
        statusEl.classList.toggle('active-badge', enabled);
    }
}

async function toggleModality(m) {
    if (activeModalities.includes(m)) {
        updateModalityUI(m, false);
        if (m === 'visual' && videoFeed.srcObject) {
            videoFeed.srcObject.getTracks().forEach(t => t.stop());
            videoFeed.srcObject = null;
            const overlay = document.getElementById('canvas-overlay');
            if (overlay) overlay.getContext('2d').clearRect(0, 0, overlay.width, overlay.height);
        }
        if (m === 'audio' && audioContext) {
            cancelAnimationFrame(animationId);
            if (audioProcessor) {
                audioProcessor.disconnect();
                audioProcessor = null;
            }
            audioContext.close();
            audioContext = null;
            analyser = null;
        }
        return;
    }

    let success = true;
    if (m === 'visual') success = await initVisual();
    if (m === 'audio') success = await initAudio();
    if (m === 'text') {
        success = true;
        textInput.disabled = false;
    }

    if (success) {
        updateModalityUI(m, true);
    } else {
        alert(`Could not activate ${m} modality. Please check permissions.`);
    }
}

// Collapsible Separate Panels
function toggleStandalonePanel(m) {
    const el = document.getElementById(`standalone-${m}-panel`);
    if (el) {
        el.style.display = el.style.display === 'none' ? 'block' : 'none';
    }
}

function triggerStandaloneAnalysis(m) {
    toggleStandalonePanel(m);
    if (m === 'text' && isLive && socket && socket.readyState === WebSocket.OPEN) {
        // Immediately query the server for text transformer emotions separately
        socket.send(JSON.stringify({
            active_modalities: ['text'],
            text: textInput.value
        }));
    }
}

async function startSession() {
    if (isLive) return;
    if (activeModalities.length === 0) {
        alert("Please activate at least one modality (Visual, Audio, or Text) first.");
        return;
    }
    
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
    
    socket.onopen = () => {
        console.log("WebSocket connected to Optimizing Multimodal Emotion Recognition ML Backend");
        isLive = true;
        liveDot.classList.add('active');
        startBtn.disabled = true;
        stopBtn.disabled = false;
        
        // Streaming Event Loop (10 Hz = every 100ms)
        captureInterval = setInterval(() => {
            if (!isLive || socket.readyState !== WebSocket.OPEN) return;
            
            const payload = {
                active_modalities: activeModalities,
                image: activeModalities.includes('visual') ? captureVideoFrame() : null,
                text: activeModalities.includes('text') ? textInput.value : null,
                audio: activeModalities.includes('audio') && accumulatedAudio.length > 0 ? int16ToBase64(accumulatedAudio) : null
            };
            
            socket.send(JSON.stringify(payload));
            accumulatedAudio = []; // Reset audio buffer
        }, LIVE_UPDATE_MS);
    };
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // 1. Process Fused Emotions
        if (data.fused_emotions) {
            updateDashboard(data.fused_emotions);
        }
        
        // 2. Process Arousal & Face Mesh Overlay
        if (data.arousal) {
            const a = data.arousal.arousal || 0.0;
            const v = data.arousal.velocity || 0.0;
            const acc = data.arousal.acceleration || 0.0;
            
            arousalFill.style.width = `${a * 100}%`;
            arousalVal.innerText = a.toFixed(2);
            velVal.innerText = v.toFixed(3);
            accVal.innerText = acc.toFixed(3);
            
            // Draw overlays (Bounding Box + Landmark Mesh)
            const faceRect = data.visual_emotions ? data.visual_emotions.face_rect : null;
            drawFaceOverlay(faceRect, data.arousal.mesh_points);
        }
        
        // 3. Update Separate Visual Panel
        if (data.visual_emotions) {
            const emotions = data.visual_emotions.emotions || data.visual_emotions;
            let emoStr = Object.entries(emotions).map(([k, v]) => `${k}: ${(v * 100).toFixed(1)}%`).join(' | ');
            document.getElementById('standalone-vis-emotions').innerText = emoStr;
        }
        
        // 4. Update Separate Text Panel
        if (data.text_emotions) {
            const lex = data.text_emotions.lexicon || {};
            const trans = data.text_emotions.transformer || {};
            
            document.getElementById('standalone-text-lexicon').innerText = lex.Happy ? `Compound Sentiment: ${(lex.Happy - lex.Sad).toFixed(2)}` : "N/A";
            
            let transStr = Object.entries(trans).length > 0
                ? Object.entries(trans).map(([k, v]) => `${k}: ${(v * 100).toFixed(1)}%`).join(' | ')
                : "Waiting for text input...";
            document.getElementById('standalone-text-transformer').innerText = transStr;
        }
        
        // 5. Update Separate Audio Panel
        if (data.audio_emotions) {
            const rate = data.audio_emotions.speaking_rate || 0.0;
            document.getElementById('standalone-audio-rate').innerText = `${rate.toFixed(1)} syllables/sec`;
            
            const emotions = data.audio_emotions.emotions || data.audio_emotions;
            let emoStr = Object.entries(emotions).map(([k, v]) => `${k}: ${(v * 100).toFixed(1)}%`).join(' | ');
            document.getElementById('standalone-audio-transformer').innerText = emoStr;
        }
    };
    
    socket.onerror = (err) => {
        console.error("WebSocket connection failure:", err);
    };
    
    socket.onclose = () => {
        console.log("WebSocket connection closed.");
        stopSession();
    };
}

function updateDashboard(fused) {
    const emotions = Object.keys(emotionColors);
    const vals = emotions.map(e => fused[e] || 0.0);
    radarChart.data.datasets[0].data = vals;
    radarChart.update('none');

    const ranked = emotions
        .map((emotion, index) => ({ emotion, score: vals[index] }))
        .sort((a, b) => b.score - a.score);
    const top = ranked[0] || { emotion: 'Neutral', score: 0 };
    const nowPerf = performance.now();
    updatesPerSecond = 1000 / Math.max(1, nowPerf - lastUpdateAt);
    lastUpdateAt = nowPerf;

    if (dominantEmotionEl) dominantEmotionEl.innerText = top.emotion;
    if (confidenceEl) confidenceEl.innerText = `${(top.score * 100).toFixed(1)}%`;
    if (updateRateEl) updateRateEl.innerText = `${updatesPerSecond.toFixed(1)} Hz`;
    
    const now = new Date().toLocaleTimeString();
    timelineChart.data.labels.push(now);
    emotions.forEach((e, i) => {
        timelineChart.data.datasets[i].data.push(vals[i]);
        sessionEmotions[e] += vals[i];
    });
    
    if (timelineChart.data.labels.length > MAX_TIMELINE_POINTS) {
        timelineChart.data.labels.shift();
        timelineChart.data.datasets.forEach(d => d.data.shift());
    }
    timelineChart.update('none');
    frameCount++;
}

function stopSession() {
    isLive = false;
    clearInterval(captureInterval);
    liveDot.classList.remove('active');
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    if (socket) {
        if (socket.readyState === WebSocket.OPEN) socket.close();
        socket = null;
    }
    
    const overlay = document.getElementById('canvas-overlay');
    if (overlay) overlay.getContext('2d').clearRect(0, 0, overlay.width, overlay.height);
    
    showSummary();
}

function showSummary() {
    const modal = document.getElementById('summary-modal');
    const stats = document.getElementById('summary-stats');
    stats.innerHTML = '';
    Object.keys(sessionEmotions).forEach(e => {
        const avg = ((sessionEmotions[e] / (frameCount || 1)) * 100).toFixed(1);
        stats.innerHTML += `<div class="stat-box" style="border-bottom: 3px solid ${emotionColors[e]}"><div class="label">${e}</div><div class="val">${avg}%</div></div>`;
    });
    modal.classList.add('show');
}

function closeModal() {
    document.getElementById('summary-modal').classList.remove('show');
    sessionEmotions = { 'Angry': 0, 'Disgust': 0, 'Fear': 0, 'Happy': 0, 'Sad': 0, 'Surprise': 0, 'Neutral': 0 };
    frameCount = 0;
}

// === TAB NAVIGATION ===
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    document.getElementById(`tab-${tabId}`).style.display = 'block';
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.background = 'transparent';
    });
    const activeBtn = document.querySelector(`.tab-btn[onclick="switchTab('${tabId}')"]`);
    if(activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.background = 'var(--primary)';
    }
    
    const controls = document.getElementById('live-controls');
    controls.style.display = (tabId === 'live') ? 'flex' : 'none';
}

// === MULTI-MODAL SERVICES ===

// Whisper Integration
let sttMediaRecorder = null;
let sttAudioChunks = [];
let isListening = false;

async function toggleSpeechToText() {
    const btn = document.getElementById('btn-stt');
    const output = document.getElementById('stt-output');
    
    if (isListening && sttMediaRecorder) {
        sttMediaRecorder.stop();
        isListening = false;
        btn.innerText = 'Start Listening';
        btn.classList.remove('active');
        output.innerText = "Processing with Whisper...";
        return;
    }
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        sttMediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        sttAudioChunks = [];
        
        sttMediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) sttAudioChunks.push(e.data);
        };
        
        sttMediaRecorder.onstop = async () => {
            const audioBlob = new Blob(sttAudioChunks, { type: 'audio/webm' });
            
            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'audio/webm' },
                    body: audioBlob
                });
                
                const data = await response.json();
                if (data.success) {
                    output.innerText = data.text;
                    if (document.getElementById('text-input')) {
                        document.getElementById('text-input').value = data.text;
                    }
                } else {
                    output.innerText = "Error: " + data.error;
                }
            } catch (err) {
                output.innerText = "Failed to connect to Whisper backend.";
            }
            
            stream.getTracks().forEach(t => t.stop());
        };
        
        sttMediaRecorder.start();
        isListening = true;
        btn.innerText = 'Stop & Process';
        btn.classList.add('active');
        output.innerText = "Listening... (Speak now)";
        
    } catch (e) {
        alert("Microphone access denied.");
    }
}

// Text Translation Integration
async function translateText() {
    const text = document.getElementById('translate-input').value;
    const targetLang = document.getElementById('target-lang').value;
    const output = document.getElementById('translate-output');
    
    if (!text) return;
    
    output.innerText = "Translating...";
    try {
        const response = await fetch('/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                source_language: 'auto',
                target_language: targetLang
            })
        });
        const data = await response.json();
        if (data.success) {
            output.innerText = data.translated_text;
        } else {
            output.innerText = data.error || 'Translation failed.';
        }
    } catch (e) {
        output.innerText = "Error translating text. Check backend connection.";
        console.error(e);
    }
}

document.addEventListener('DOMContentLoaded', loadLanguages);

// Simulated Media File Analyzer
async function analyzeUploadedFile() {
    const fileInput = document.getElementById('media-upload');
    if (!fileInput.files.length) {
        alert("Please select a file first.");
        return;
    }
    
    const file = fileInput.files[0];
    alert(`Analyzing ${file.name}... (Simulating deep analysis)`);
    
    setTimeout(() => {
        alert("Analysis Complete! Generating Seaborn Report...");
        generateSeabornReport();
    }, 2000);
}

// Seaborn Analysis Plots
async function generateSeabornReport() {
    const container = document.getElementById('seaborn-results');
    const imagesContainer = document.getElementById('seaborn-images');
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
    }
    
    try {
        const response = await fetch('/generate-seaborn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emotions: sessionEmotions })
        });
        
        const data = await response.json();
        if (data.success && data.imageUrl) {
            imagesContainer.innerHTML = `<img src="${data.imageUrl}" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">`;
        } else {
            imagesContainer.innerHTML = `<p style="color: #ef4444;">Error: ${data.error || 'Could not generate plot.'}</p>`;
        }
    } catch (e) {
        console.error(e);
        imagesContainer.innerHTML = `<p style="color: #ef4444;">Server error. Ensure backend is running.</p>`;
    }
}
