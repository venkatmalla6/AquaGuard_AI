from pathlib import Path
import base64
import sys

def write_file(path, payload):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = base64.b64decode(payload)
    with open(p, 'wb') as f:
        f.write(data)
    print(f'Wrote {path} ({len(data)} bytes)')

if __name__ == '__main__':
    write_file(sys.argv[1], sys.argv[2])
