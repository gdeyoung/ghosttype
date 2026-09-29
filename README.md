# ghosttype

Hold-to-talk voice typing for Windows. Press a hotkey, speak, release — your words appear in whatever app has focus. Fully offline. Local Whisper.

This is Greg DeYoung's fork of [CatBoneheaD/Whisper-Writer](https://github.com/CatBoneheaD/Whisper-Writer), maintained for personal use across the Greg DeYoung fleet.

## What it does

Hold a hotkey, speak, release. Your voice is transcribed locally by faster-whisper and typed into the focused window — same workflow as BoxType/Voxtype on Omarchy Linux. Recording modes include `hold_to_record` (BoxType-style push-to-talk), `press_to_toggle`, `continuous`, and `voice_activity_detection`.

## Features

- **Modern dashboard** (Voice Ink-style) with dark & light themes — sidebar with History / Settings, live status indicator.
- **Transcription history** stored locally in SQLite — search, one-click copy, re-insert into the active window, delete.
- **In-app model switcher** — full multilingual set (tiny…large-v3); not-installed models download on selection.
- **Language picker & translation** — choose spoken language or translate to English.
- **Text post-processing** — spoken-command replacements, auto-capitalization, trailing space.
- **Settings UI** — hotkey with press-to-capture, recording mode, language, device, theme, autostart — no YAML required.
- **Start with Windows** (optional) and **silent launch** via `launch.vbs` — lives in the system tray.
- **Single-instance guard** — no more doubled text from a second launch.
- **Hold-to-record** — BoxType-equivalent push-to-talk mode.

Transcription runs **locally** by default (faster-whisper), or through the **OpenAI API** if you enable it in Settings.

## Pedigree

ghosttype is built on the work of three upstream projects. All credit goes to the original authors.

```
ghosttype (this fork)
    │
    └── CatBoneheaD/Whisper-Writer  (active 2026, Windows-first fork)
            https://github.com/CatBoneheaD/Whisper-Writer
            Added: modern dashboard, hold_to_record mode, in-app model
            switcher, transcription history, system tray, single-instance
            guard, Windows install fixes (av==11.0.0 workarounds),
            press-to-capture hotkey, light theme, post-processing.

            └── savbell/whisper-writer  (original project, 1.1k★, MIT)
                    https://github.com/savbell/whisper-writer
                    The original WhisperWriter — PyQt dashboard,
                    faster-whisper integration, push-to-talk, evdev
                    input layer, recording mode framework.

                    └── openai/whisper  (the model, not a code fork)
                            https://github.com/openai/whisper
                            The underlying speech recognition model.
                            ghosttype uses the faster-whisper inference
                            runtime against OpenAI's Whisper weights.
                            No code is derived from OpenAI's repository;
                            we depend on the trained model artifacts only.
```

The license chain breaks at CatBoneheaD's relicense in their 2026 rewrite (MIT → GPLv3), because the Qt dashboard work they added is GPL-compatible.

## Getting started

### Prerequisites

- [Git](https://git-scm.com/downloads)
- [Python 3.11](https://www.python.org/downloads/)
- *(Optional, for GPU)* an NVIDIA GPU. The required `nvidia-cublas-cu12` and `nvidia-cudnn-cu12` libraries install automatically via `requirements.txt`, and the app adds them to `PATH` at startup — no manual CUDA setup needed.

### Installation

```bash
# 1. Clone
git clone https://github.com/gdeyoung/ghosttype.git
cd ghosttype

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Verify install before downloading the model
venv\Scripts\python.exe smoke_test.py

# 5. Pre-download a local model (defaults to base.en, ~142 MB)
python download_model.py             # base.en — fastest, English-optimized
# or:
python download_model.py small.en    # 466 MB — better accuracy
python download_model.py large-v3    # 3.1 GB — best, but slow on CPU

# 6. Run
python run.py
```

### Launch without a console (recommended)

Double-click **`launch.vbs`** — it starts the app silently with `pythonw.exe` (no console window). Create a desktop shortcut to `launch.vbs` and set its icon to `assets/ww-logo.ico`.

Default hotkey is `Ctrl+Shift+Space`. Change it in Settings — the **press-to-capture** button makes it easy to set F9 to match your Omarchy BoxType workflow.

## Recording modes

- `continuous` *(default)*: stops after a pause, transcribes, then keeps listening. Press the hotkey again to stop.
- `voice_activity_detection`: stops after a pause; won't restart until you press the hotkey.
- `press_to_toggle`: starts on hotkey, stops on the next hotkey press.
- `hold_to_record`: records while the hotkey is held down. **Set this to match BoxType.**

## Configuration

Everything can be set in the in-app **Settings** page. Settings save to `config.yaml` (git-ignored, your personal config stays local). Missing values fall back to defaults in `src/config_schema.yaml`.

## License

GPLv3 — see `LICENSE`. Inherited from CatBoneheaD's fork. Any derivative work must also be GPLv3.
