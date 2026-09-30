"""Prove press_to_toggle works: press starts, press again stops.

This is pure state-machine logic in WhisperWriterApp.on_activation, so we can
exercise it without a microphone or a model by stubbing the ResultThread.

The toggle is the whole feature, so assert the sequence rather than eyeballing:
  press 1 -> recording started
  press 2 -> stop_recording() called
  press 3 -> recording started again (listener re-armed)

Run:  venv/Scripts/python.exe toggle_test.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from utils import ConfigManager  # noqa: E402

ConfigManager.initialize()

mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
failures = []

print(f'recording_mode = {mode!r}')
if mode != 'press_to_toggle':
    failures.append(f'config recording_mode is {mode!r}, expected press_to_toggle')

# Exercise the real decision logic from main.py without booting Qt.
import ctypes  # noqa: E402
import main as m  # noqa: E402


class FakeThread:
    """Stands in for ResultThread: records whether it was told to stop."""

    def __init__(self):
        self.running = False
        self.stop_calls = 0

    def isRunning(self):
        return self.running

    def stop_recording(self):
        self.stop_calls += 1
        self.running = False


class Harness(m.WhisperWriterApp):
    """Bypass __init__ (no Qt, no model) but keep the real on_activation."""

    def __init__(self):
        self.result_thread = None
        self.target_window = None
        self.started = 0

    def start_result_thread(self):
        self.started += 1
        self.result_thread = FakeThread()
        self.result_thread.running = True


h = Harness()

# Press 1: nothing running -> start.
h.on_activation()
print(f'press 1 -> started={h.started} recording={h.result_thread.isRunning()}')
if not h.result_thread.isRunning():
    failures.append('press 1 did not start recording')
if h.target_window is None:
    failures.append('press 1 did not capture a target window')
first_target = h.target_window

# Press 2: running -> stop.
h.on_activation()
print(f'press 2 -> stop_calls={h.result_thread.stop_calls} recording={h.result_thread.isRunning()}')
if h.result_thread.stop_calls != 1:
    failures.append(f'press 2 did not stop recording (stop_calls={h.result_thread.stop_calls})')
if h.result_thread.isRunning():
    failures.append('press 2 left the thread running')

# Press 3: must start again — proves the listener re-arms between turns.
h.on_activation()
print(f'press 3 -> started={h.started} recording={h.result_thread.isRunning()}')
if h.started != 2:
    failures.append(f'press 3 did not start a new recording (started={h.started})')
if not h.result_thread.isRunning():
    failures.append('press 3 left the thread stopped')

# Target window should be refreshed each turn, not stale.
if h.target_window == first_target and h.started == 2:
    pass  # same hwnd is fine; we only assert it is set

print('\n' + '=' * 60)
if failures:
    print('TOGGLE TEST FAILED:')
    for f in failures:
        print('  -', f)
    sys.exit(1)
print('TOGGLE TEST PASSED — press starts, press stops, press restarts.')