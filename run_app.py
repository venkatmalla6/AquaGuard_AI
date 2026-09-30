import os, sys, time, subprocess
from pathlib import Path
root = Path(__file__).parent.resolve()
frontend = root / 'frontend'
print('='*75 + '\n AQUAGUARD AI: REAL-TIME AQUATIC DROWNING DETECTION PLATFORM\n' + '='*75)
print(' Starting services...')
print('   * Backend  : http://localhost:8000')
print('   * API Docs : http://localhost:8000/docs')
print('   * Frontend : http://localhost:5173')
print('   * Login    : admin@aquaguard.ai / demo1234')
print('-'*75)
p_be = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.app.main:app', '--host', '0.0.0.0', '--port', '8000'], cwd=str(root))
time.sleep(2)
p_fe = subprocess.Popen(['npm.cmd' if os.name == 'nt' else 'npm', 'run', 'dev'], cwd=str(frontend))
try:
    while True:
        if p_be.poll() is not None or p_fe.poll() is not None:
            break
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    for p in [p_be, p_fe]:
        if p.poll() is None:
            p.terminate()
    print('Stopped AquaGuard AI services.')
