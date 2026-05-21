const express = require('express');
const http = require('http');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const WebSocket = require('ws');

const app = express();
const server = http.createServer(app);

const BACKEND_HOST = process.env.BACKEND_HOST || '127.0.0.1';
let BACKEND_PORT = Number(process.env.BACKEND_PORT || 8001);
let BACKEND_URL = '';
let BACKEND_WS_URL = '';
const START_BACKEND = process.env.START_BACKEND !== '0';

function getPythonExe() {
    const windowsVenv = path.join(__dirname, 'backend', '.venv', 'Scripts', 'python.exe');
    if (fs.existsSync(windowsVenv)) return windowsVenv;

    const unixVenv = path.join(__dirname, 'backend', '.venv', 'bin', 'python');
    if (fs.existsSync(unixVenv)) return unixVenv;

    return process.env.PYTHON || 'python';
}

const PYTHON_EXE = getPythonExe();
let backendProcess = null;

function startBackend() {
    if (!START_BACKEND) {
        console.log('Python backend auto-start disabled with START_BACKEND=0.');
        return;
    }

    backendProcess = spawn(PYTHON_EXE, ['main.py'], {
        cwd: path.join(__dirname, 'backend'),
        env: { ...process.env, PORT: String(BACKEND_PORT) },
        stdio: ['ignore', 'pipe', 'pipe']
    });

    backendProcess.stdout.on('data', data => process.stdout.write(`[backend] ${data}`));
    backendProcess.stderr.on('data', data => process.stderr.write(`[backend] ${data}`));
    backendProcess.on('exit', (code, signal) => {
        if (signal) {
            console.log(`[backend] stopped by ${signal}`);
            return;
        }
        console.log(`[backend] exited with code ${code}`);
    });
}

function stopBackend() {
    if (backendProcess && !backendProcess.killed) {
        backendProcess.kill();
    }
}

process.on('SIGINT', () => {
    stopBackend();
    process.exit(0);
});
process.on('SIGTERM', () => {
    stopBackend();
    process.exit(0);
});
process.on('exit', stopBackend);

app.use(express.json());
app.use('/static', express.static(path.join(__dirname, 'frontend')));
app.use('/reports', express.static(path.join(__dirname, 'frontend', 'reports')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend', 'index.html'));
});

app.get('/health', async (req, res) => {
    try {
        const response = await fetch(`${BACKEND_URL}/health`);
        const body = await response.json();
        res.json({ status: 'ok', frontend: true, backend: body });
    } catch (error) {
        res.status(503).json({ status: 'error', frontend: true, backend: 'unavailable' });
    }
});

app.post('/generate-seaborn', (req, res) => {
    const emotions = req.body.emotions || {};
    const pythonProcess = spawn(PYTHON_EXE, [path.join(__dirname, 'backend', 'seaborn_worker.py')]);
    let resultData = '';

    pythonProcess.stdout.on('data', data => {
        resultData += data.toString();
    });

    pythonProcess.stderr.on('data', data => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on('close', () => {
        try {
            const result = JSON.parse(resultData);
            if (result.success) {
                res.json({ success: true, imageUrl: `/reports/${result.filename}` });
            } else {
                res.json({ success: false, error: result.error });
            }
        } catch (error) {
            res.json({ success: false, error: 'Failed to parse Python output. Python may not be installed correctly.' });
        }
    });

    pythonProcess.stdin.write(JSON.stringify(emotions));
    pythonProcess.stdin.end();
});

app.post('/transcribe', express.raw({ type: 'audio/webm', limit: '50mb' }), (req, res) => {
    const tempFilePath = path.join(__dirname, 'backend', `temp_audio_${Date.now()}.webm`);
    fs.writeFileSync(tempFilePath, req.body);

    const pythonProcess = spawn(PYTHON_EXE, [path.join(__dirname, 'backend', 'whisper_worker.py'), tempFilePath]);
    let resultData = '';

    pythonProcess.stdout.on('data', data => {
        resultData += data.toString();
    });

    pythonProcess.stderr.on('data', data => {
        console.error(`Whisper Error: ${data}`);
    });

    pythonProcess.on('close', () => {
        if (fs.existsSync(tempFilePath)) {
            fs.unlinkSync(tempFilePath);
        }

        try {
            const result = JSON.parse(resultData);
            if (result.success) {
                res.json({ success: true, text: result.text });
            } else {
                res.json({ success: false, error: result.error });
            }
        } catch (error) {
            res.json({ success: false, error: 'Whisper processing failed. Please ensure openai-whisper is installed.' });
        }
    });
});

const wsServer = new WebSocket.Server({ noServer: true });

server.on('upgrade', (request, socket, head) => {
    if (request.url !== '/ws') {
        socket.destroy();
        return;
    }

    wsServer.handleUpgrade(request, socket, head, clientSocket => {
        const backendSocket = new WebSocket(BACKEND_WS_URL);
        const pendingMessages = [];

        backendSocket.on('open', () => {
            while (pendingMessages.length > 0) {
                const pending = pendingMessages.shift();
                backendSocket.send(pending.message, { binary: pending.isBinary });
            }

            backendSocket.on('message', (message, isBinary) => {
                if (clientSocket.readyState === WebSocket.OPEN) {
                    clientSocket.send(message, { binary: isBinary });
                }
            });
        });

        clientSocket.on('message', (message, isBinary) => {
            if (backendSocket.readyState === WebSocket.OPEN) {
                backendSocket.send(message, { binary: isBinary });
            } else {
                pendingMessages.push({ message, isBinary });
            }
        });

        const closeBoth = () => {
            if (clientSocket.readyState === WebSocket.OPEN) clientSocket.close();
            if (backendSocket.readyState === WebSocket.OPEN) backendSocket.close();
        };

        backendSocket.on('error', error => {
            console.error(`Backend WebSocket error: ${error.message}`);
            closeBoth();
        });
        clientSocket.on('error', closeBoth);
        backendSocket.on('close', closeBoth);
        clientSocket.on('close', closeBoth);
    });
});

function isPortFree(port) {
    return new Promise(resolve => {
        const probe = http.createServer();
        probe.once('error', () => resolve(false));
        probe.once('listening', () => {
            probe.close(() => resolve(true));
        });
        probe.listen(port, '0.0.0.0');
    });
}

async function findFreePort(preferredPort, reservedPorts = new Set()) {
    if (!reservedPorts.has(preferredPort) && await isPortFree(preferredPort)) return preferredPort;

    for (let port = preferredPort + 1; port < preferredPort + 100; port++) {
        if (!reservedPorts.has(port) && await isPortFree(port)) return port;
    }

    throw new Error(`No free port found near ${preferredPort}`);
}

async function startServer() {
    const requestedPort = Number(process.env.PORT || 8000);
    const reservedBackendPort = Number(process.env.BACKEND_PORT || 8001);
    const port = process.env.PORT ? requestedPort : await findFreePort(requestedPort, new Set([reservedBackendPort]));
    BACKEND_PORT = process.env.BACKEND_PORT ? BACKEND_PORT : await findFreePort(BACKEND_PORT, new Set([port]));
    BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;
    BACKEND_WS_URL = `ws://${BACKEND_HOST}:${BACKEND_PORT}/ws`;

    startBackend();
    server.listen(port, () => {
        console.log(`Node.js EmoLens Server running on http://localhost:${port}`);
        if (!process.env.PORT && port !== requestedPort) {
            console.log(`Port ${requestedPort} was busy, using ${port} instead.`);
        }
        if (!process.env.BACKEND_PORT && BACKEND_PORT !== 8001) {
            console.log(`Backend port 8001 was busy, using ${BACKEND_PORT} instead.`);
        }
        console.log(`Python executable: ${PYTHON_EXE}`);
        console.log(`Backend target: ${BACKEND_URL}`);
        console.log('Browser WebSocket endpoint: /ws');
    });
}

startServer().catch(error => {
    console.error(`Failed to start EmoLens: ${error.message}`);
    stopBackend();
    process.exit(1);
});
