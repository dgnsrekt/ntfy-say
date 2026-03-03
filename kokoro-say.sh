#!/bin/bash
# Send text to remote Kokoro TTS server; play audio locally via paplay.
# Falls back to piper if the remote server is unreachable.

KOKORO_HOST="dev4-whitebox.lan"
KOKORO_PORT=7777

if [ -z "$1" ]; then
    echo "Usage: kokoro-say.sh \"text to speak\""
    exit 1
fi

python3 - "$1" <<'PYEOF'
import socket, subprocess, sys

HOST = "dev4-whitebox.lan"
PORT = 7777
text = sys.argv[1]

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((HOST, PORT))
    s.sendall(text.encode("utf-8"))
    s.shutdown(socket.SHUT_WR)  # signal end of text

    proc = subprocess.Popen(
        ["paplay", "--raw", "--format=s16le", "--rate=24000", "--channels=1"],
        stdin=subprocess.PIPE,
    )
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        proc.stdin.write(chunk)
    proc.stdin.close()
    proc.wait()
    s.close()
except Exception as e:
    print(f"Remote kokoro error: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo "Falling back to piper" >&2
    echo "$1" | piper -m /models/en_US-amy-medium.onnx \
        -c /models/en_US-amy-medium.onnx.json --output-raw \
        | paplay --raw --rate=22050 --channels=1 --format=s16le
fi
