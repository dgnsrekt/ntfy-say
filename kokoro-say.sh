#!/bin/bash
# Send text to the Kokoro TTS server for instant speech.
# Falls back to piper if the server isn't running.

SOCKET="/tmp/kokoro-say.sock"

if [ -z "$1" ]; then
    echo "Usage: kokoro-say.sh \"text to speak\""
    exit 1
fi

if [ -S "$SOCKET" ]; then
    python3 -c "
import socket, sys
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('$SOCKET')
s.sendall(sys.argv[1].encode())
s.close()
" "$1"
else
    echo "Kokoro server not running, falling back to piper" >&2
    echo "$1" | piper -m /models/en_US-amy-medium.onnx -c /models/en_US-amy-medium.onnx.json --output-raw \
        | paplay --raw --rate=22050 --channels=1 --format=s16le
fi
