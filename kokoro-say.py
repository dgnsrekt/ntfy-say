#!/home/dgnsrekt/Services/ntfy-say/kokoro-env/bin/python
"""Reads text from arg or stdin, outputs raw s16le PCM at 24kHz mono to stdout."""
import sys
import numpy as np
from kokoro import KPipeline

VOICE = "af_sarah"
if len(sys.argv) > 1 and sys.argv[1].startswith("-v"):
    VOICE = sys.argv[2] if len(sys.argv) > 2 else VOICE
    text_args = sys.argv[3:]
else:
    text_args = sys.argv[1:]

if text_args:
    text = " ".join(text_args)
else:
    text = sys.stdin.read()

text = text.strip()
if not text:
    sys.exit(0)

pipeline = KPipeline(lang_code="a", device="cuda")

for result in pipeline(text, voice=VOICE):
    if result.output is not None and result.output.audio is not None:
        audio_np = result.output.audio.cpu().numpy()
        audio_int16 = (audio_np * 32767).astype(np.int16)
        sys.stdout.buffer.write(audio_int16.tobytes())
