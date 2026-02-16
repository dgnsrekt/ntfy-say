#!/home/dgnsrekt/Services/ntfy-say/kokoro-env/bin/python
"""Persistent Kokoro TTS server. Stays warm in memory for instant inference.

Listens on a Unix socket for text, speaks it via paplay.

Usage:
    ./kokoro-server.py                  # Start with default voice
    ./kokoro-server.py af_sarah         # Start with specific voice
"""
import json
import os
import signal
import socket
import subprocess
import sys

import numpy as np
from kokoro import KPipeline

SOCKET_PATH = "/tmp/kokoro-say.sock"
SAMPLE_RATE = 24000
DEFAULT_VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_sarah"


def cleanup(signum=None, frame=None):
    try:
        os.unlink(SOCKET_PATH)
    except FileNotFoundError:
        pass
    sys.exit(0)


def speak(pipeline, text, voice=None):
    voice = voice or DEFAULT_VOICE
    proc = subprocess.Popen(
        ["paplay", "--raw", "--format=s16le", f"--rate={SAMPLE_RATE}", "--channels=1"],
        stdin=subprocess.PIPE,
    )
    for result in pipeline(text, voice=voice):
        if result.output is not None and result.output.audio is not None:
            audio_np = result.output.audio.cpu().numpy()
            audio_int16 = (audio_np * 32767).astype(np.int16)
            proc.stdin.write(audio_int16.tobytes())
    proc.stdin.close()
    proc.wait()


def main():
    print(f"Loading Kokoro pipeline (device=cuda, voice={DEFAULT_VOICE})...")
    pipeline = KPipeline(lang_code="a", device="cuda")

    # Warm up CUDA with a silent inference
    for result in pipeline("warmup", voice=DEFAULT_VOICE):
        pass
    print("Pipeline ready.")

    # Clean up any stale socket
    try:
        os.unlink(SOCKET_PATH)
    except FileNotFoundError:
        pass

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)
    server.listen(1)
    print(f"Listening on {SOCKET_PATH}")

    while True:
        conn, _ = server.accept()
        try:
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk

            raw = data.decode("utf-8").strip()
            if not raw:
                continue

            # Support JSON {"text": "...", "voice": "..."} or plain text
            voice = None
            if raw.startswith("{"):
                try:
                    msg = json.loads(raw)
                    text = msg.get("text", "")
                    voice = msg.get("voice")
                except json.JSONDecodeError:
                    text = raw
            else:
                text = raw

            if text:
                print(f"Speaking: {text[:80]}{'...' if len(text) > 80 else ''}")
                speak(pipeline, text, voice)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
