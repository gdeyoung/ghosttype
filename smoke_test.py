"""Smoke test: verify ghosttype's critical imports work after install.

Run from ~/work/ghosttype-src with the venv activated:
    venv\Scripts\python.exe smoke_test.py
"""
import sys

failures = []
checks = [
    ("faster_whisper", "Speech-to-text engine"),
    ("PyQt5", "GUI dashboard"),
    ("PyQt5.QtWidgets", "Qt widgets"),
    ("pynput", "Global hotkey listener"),
    ("sounddevice", "Microphone input"),
    ("soundfile", "Audio file I/O"),
    ("webrtcvad", "Voice activity detection"),
    ("onnxruntime", "ONNX inference runtime"),
    ("huggingface_hub", "Model downloads"),
    ("requests", "HTTP client"),
    ("yaml", "YAML config"),
]

for mod, purpose in checks:
    try:
        __import__(mod)
        print(f"  OK  {mod:30s} ({purpose})")
    except Exception as e:
        print(f"  FAIL {mod:30s} ({purpose}): {type(e).__name__}: {e}")
        failures.append((mod, e))

print()
if failures:
    print(f"{len(failures)} import(s) failed. Install incomplete.")
    sys.exit(1)
else:
    print(f"All {len(checks)} imports OK. Install complete.")
    print("\nNext steps:")
    print("  1. python download_model.py             # 142 MB base.en")
    print("  2. python run.py                        # launch the GUI")
    print("  3. In Settings: set hotkey to F9, recording_mode to hold_to_record")
    print("  4. Hold F9 in any text box, speak, release")
