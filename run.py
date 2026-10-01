import os
import sys
import multiprocessing


def _setup_cuda_path(base):
    """Prepend bundled CUDA DLL directories to PATH so ctranslate2/faster-whisper
    can find cublas64_12.dll and cudnn64_9.dll at import time.

    MUST run BEFORE ``import faster_whisper`` — ctranslate2 loads its CUDA
    dependencies once at module import. If PyQt5 imports first, its bundled
    MSVC runtime DLLs take over PATH and ctranslate2 can't find its cublas."""
    nvidia = os.path.join(base, 'venv', 'Lib', 'site-packages', 'nvidia')
    paths = []
    for sub in (os.path.join(nvidia, 'cublas', 'bin'),
                os.path.join(nvidia, 'cudnn', 'bin')):
        if os.path.isdir(sub):
            paths.append(sub)
    if paths:
        os.environ['PATH'] = os.pathsep.join(paths) + os.pathsep + os.environ.get('PATH', '')


def _scrub_inherited_pythonpath():
    """Strip inherited PYTHONPATH entries that point at OTHER Python environments
    (e.g. Hermes-managed installs). When PYTHONPATH includes a path that has its
    own site-packages, Python prepends it before our venv's site-packages, and we
    end up importing the wrong numpy/faster-whisper — manifests as
    `numpy._core._multiarray_umath` ImportError because the foreign numpy was built
    for a different Python version.

    Two things must be cleaned up:
    1. ``os.environ['PYTHONPATH']`` — affects subprocesses spawned later.
    2. ``sys.path`` — already populated at Python startup from PYTHONPATH.
       Bad paths may have already been imported by the time this runs, but removing
       them now prevents the FIRST import of any package from going wrong (and lets
       later imports like `import faster_whisper` find the right one).

    Critical: we only remove from sys.path the entries that came FROM PYTHONPATH.
    Python's runtime prepends PYTHONPATH entries at positions 1..N at startup,
    but stdlib paths (python311.zip, Lib, DLLs) and our own venv paths come from
    Python's own startup logic and must NOT be removed — otherwise ``import typing``
    fails with ``No module named 'typing'`` (stdlib gone).

    We keep entries that point at the ghosttype venv or the project root, and drop
    the rest. Safe no-op when launched from a clean shell (PYTHONPATH usually unset)."""
    base = os.path.dirname(os.path.abspath(__file__))
    keep_paths = (os.path.join(base, 'venv', 'Lib', 'site-packages'),
                  os.path.join(base, 'src'),
                  base)

    def _should_keep(p):
        return any(p == k or p.startswith(k + os.sep) for k in keep_paths)

    # 1. Env var (for future subprocesses).
    raw = os.environ.get('PYTHONPATH', '')
    incoming_paths = raw.split(os.pathsep) if raw else []
    if incoming_paths:
        kept_env = [p for p in incoming_paths if p and _should_keep(p)]
        if kept_env:
            os.environ['PYTHONPATH'] = os.pathsep.join(kept_env)
        else:
            os.environ.pop('PYTHONPATH', None)

    # 2. sys.path: remove ONLY the entries that came from PYTHONPATH (not stdlib,
    #    not our venv — those are added by Python itself). Incoming paths are
    #    prepended at startup, so they live at sys.path[1:1+len(incoming_paths)].
    if incoming_paths:
        sys.path[1:1 + len(incoming_paths)] = [
            p for p in incoming_paths if _should_keep(p)
        ]


def _preload_whisper_model():
    """Load faster-whisper + WhisperModel BEFORE any PyQt5 import.

    This is a Windows-specific workaround for a ctranslate2/PyQt5 DLL conflict:
    once PyQt5 is imported, its bundled MSVC runtime DLLs shadow the ones
    ctranslate2 needs, and ``WhisperModel(...)`` segfaults inside the C++
    compute kernel init. Loading faster_whisper first captures the correct
    runtime DLLs.

    Side benefit: by the time the GUI appears, the model is already in RAM,
    so the first transcription isn't delayed by a 2-second model load.

    Returns the loaded WhisperModel (or None if API mode / load failed)."""
    print('[ghosttype] Loading Whisper model before Qt init...', flush=True)

    # Initialize config + load model — no PyQt5 in this import chain.
    from utils import ConfigManager
    ConfigManager.initialize()
    from transcription import create_local_model

    if ConfigManager.get_config_value('model_options', 'use_api'):
        print('[ghosttype] use_api=true, skipping local model preload.', flush=True)
        return None

    try:
        model = create_local_model()
        print('[ghosttype] Whisper model loaded.', flush=True)
        return model
    except Exception as e:
        # Don't crash the whole app if preload fails — the ModelLoadThread
        # inside WhisperWriterApp will retry when the user clicks Record.
        print(f'[ghosttype] WARNING: preload failed: {e}', flush=True)
        print('[ghosttype] The app will retry loading on first use.', flush=True)
        return None


if __name__ == '__main__':
    # On Windows, multiprocessing uses 'spawn', which re-executes this file in
    # child processes. The __main__ guard + freeze_support() ensure those children
    # do NOT start a second copy of the app (which caused duplicated typing).
    multiprocessing.freeze_support()

    # Scrub BEFORE any package imports — sys.path may already be polluted by an
    # inherited PYTHONPATH that points at a different Python env's site-packages.
    _scrub_inherited_pythonpath()

    from dotenv import load_dotenv

    _base = os.path.dirname(os.path.abspath(__file__))
    # CUDA DLLs must be on PATH before faster_whisper imports ctranslate2.
    _setup_cuda_path(_base)
    os.chdir(_base)
    sys.path.insert(0, os.path.join(_base, 'src'))
    load_dotenv()

    # Preload the Whisper model BEFORE PyQt5 imports (DLL conflict avoidance).
    _preloaded_model = _preload_whisper_model()

    # NOW it's safe to import PyQt5 (via main.py and its UI submodules).
    from main import WhisperWriterApp

    app = WhisperWriterApp(preloaded_model=_preloaded_model)
    app.run()
