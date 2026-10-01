"""Deep smoke test: prove run.py's preload order yields a USABLE model.

smoke_test.py only checks that imports succeed. It cannot catch the two failure
modes that actually bite on Windows:
  1. ctranslate2/PyQt5 DLL conflict -> segfault when the model loads after Qt
  2. an inherited PYTHONPATH pointing at another env's site-packages

So this test replays run.py's real startup order (scrub -> CUDA PATH -> load model
BEFORE PyQt5) and then pushes a synthetic WAV through model.transcribe().

Run:  venv/Scripts/python.exe smoke_test_model.py
"""
import os
import sys
import wave
import struct
import math

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'src'))

import run  # noqa: E402  (helpers are defined at module level, safe to import)

failures = []


def step(n, msg):
    print(f'\n=== {n}. {msg} ===', flush=True)


step(1, 'scrub inherited PYTHONPATH (must happen before any package import)')
before = os.environ.get('PYTHONPATH', '(unset)')
run._scrub_inherited_pythonpath()
print(f'PYTHONPATH: {before}  ->  {os.environ.get("PYTHONPATH", "(unset)")}')

step(2, 'prepend bundled CUDA DLL dirs to PATH')
run._setup_cuda_path(BASE)

step(3, 'import faster_whisper (the DLL canary)')
try:
    import faster_whisper
    print('OK from', faster_whisper.__file__)
except Exception as e:
    print('FAILED:', e)
    sys.exit(f'faster_whisper import failed: {e!r}')

step(4, 'load WhisperModel BEFORE PyQt5 (run.py startup order)')
try:
    from utils import ConfigManager
    ConfigManager.initialize()
    from transcription import create_local_model
    model = create_local_model()
    print('loaded:', type(model).__name__ if model else None)
except Exception as e:
    print('FAILED:', e)
    sys.exit(f'create_local_model failed: {e!r}')

if model is None:
    print('FAILED: create_local_model returned None')
    sys.exit('model is None — check config.yaml model_path')

step(5, 'import PyQt5 AFTER the model (this order must not segfault)')
try:
    import PyQt5.QtWidgets  # noqa: F401
    print('OK — no segfault')
except Exception as e:
    failures.append(f'PyQt5 import after model failed: {e!r}')
    print('FAILED:', e)

step(6, 'transcribe a synthetic 16 kHz mono WAV (full compute path)')
wav_path = os.path.join(BASE, 'smoke_test_input.wav')
rate, secs = 16000, 1.0
frames = bytearray()
for i in range(int(rate * secs)):
    # 180 Hz tone with a wobble: not speech, but it exercises the whole
    # decode -> features -> ctranslate2 kernel path end to end.
    v = int(12000 * math.sin(2 * math.pi * 180 * i / rate))
    frames += struct.pack('<h', v)
with wave.open(wav_path, 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(bytes(frames))

try:
    segments, info = model.transcribe(wav_path, beam_size=1)
    text = ''.join(s.text for s in segments)
    print(f'OK — language={info.language} text={text!r}')
    if not isinstance(text, str):
        failures.append('transcribe did not return str')
except Exception as e:
    failures.append(f'transcribe failed: {e!r}')
    print('FAILED:', e)
finally:
    if os.path.exists(wav_path):
        os.remove(wav_path)

print('\n' + '=' * 60)
if failures:
    print('DEEP SMOKE TEST FAILED:')
    for f in failures:
        print('  -', f)
    sys.exit(1)
print('DEEP SMOKE TEST PASSED — all 6 steps green.')
