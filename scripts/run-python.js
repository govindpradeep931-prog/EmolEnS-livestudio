const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

function findPython() {
    const repoRoot = path.join(__dirname, '..');
    const venvPython = path.join(repoRoot, 'backend', '.venv', 'Scripts', 'python.exe');
    if (fs.existsSync(venvPython)) return venvPython;

    if (process.env.PYTHON && fs.existsSync(process.env.PYTHON)) return process.env.PYTHON;

    if (process.platform === 'win32') {
        const localPrograms = path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python');
        if (fs.existsSync(localPrograms)) {
            const candidates = fs.readdirSync(localPrograms)
                .filter(name => /^Python\d+$/i.test(name))
                .sort((a, b) => {
                    const versionA = Number(a.replace(/\D/g, ''));
                    const versionB = Number(b.replace(/\D/g, ''));
                    const rank = version => (version <= 312 && version >= 310 ? 1000 + version : version);
                    return rank(versionB) - rank(versionA);
                })
                .map(name => path.join(localPrograms, name, 'python.exe'));
            const pythonExe = candidates.find(candidate => fs.existsSync(candidate));
            if (pythonExe) return pythonExe;
        }
    }

    return 'python';
}

const result = spawnSync(findPython(), process.argv.slice(2), {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
});

process.exit(result.status ?? 1);
