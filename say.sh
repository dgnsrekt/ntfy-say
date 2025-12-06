#!/bin/bash
# Container TTS script using piper with PulseAudio output

if [ -z "$1" ]; then
    echo "Usage: say.sh \"text to speak\""
    exit 1
fi

echo "$1" | piper -m /models/en_US-amy-medium.onnx -c /models/en_US-amy-medium.onnx.json --output-raw \
    | paplay --raw --rate=22050 --channels=1 --format=s16le
