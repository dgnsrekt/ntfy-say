#!/usr/bin/env python3
"""Remote Kokoro TTS server. Listens on TCP, streams raw PCM audio back to client.

Usage:
    ./kokoro-server-tcp.py                  # Start with default voice
    ./kokoro-server-tcp.py af_sarah         # Start with specific voice
"""
import json
import signal
import socket
import sys

import numpy as np
from kokoro import KPipeline

HOST = "0.0.0.0"
PORT = 7777
SAMPLE_RATE = 24000
DEFAULT_VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_sarah"


def handle_client(conn, pipeline):
    data = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk

    raw = data.decode("utf-8").strip()
    if not raw:
        return

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

    if not text:
        return

    print(f"Speaking: {text[:80]}{'...' if len(text) > 80 else ''}", flush=True)
    voice = voice or DEFAULT_VOICE

    for result in pipeline(text, voice=voice):
        if result.output is not None and result.output.audio is not None:
            audio_np = result.output.audio.cpu().numpy()
            audio_int16 = (audio_np * 32767).astype(np.int16)
            conn.sendall(audio_int16.tobytes())


def main():
    print(f"Loading Kokoro pipeline (device=cuda, voice={DEFAULT_VOICE})...", flush=True)
    pipeline = KPipeline(lang_code="a", device="cuda")

    for result in pipeline("warmup", voice=DEFAULT_VOICE):
        pass
    print("Pipeline ready.", flush=True)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Listening on {HOST}:{PORT}", flush=True)

    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    while True:
        conn, addr = server.accept()
        try:
            handle_client(conn, pipeline)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr, flush=True)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
