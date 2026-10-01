"""Verify the completion tone is off by default and stays toggleable.

Stubs play_completion_sound so nothing actually makes noise, then drives
on_transcription_complete and counts how many times the sound would have fired.
"""
import sys, types
sys.path.insert(0, 'src')
from utils import ConfigManager
ConfigManager.initialize()

fired = []
# Patch the symbol main.py imported, so we can count calls.
import main as m
m.play_completion_sound = lambda: fired.append(1)

cfg = ConfigManager.get_config_value('misc', 'noise_on_completion')
print('noise_on_completion =', cfg)

class FakeWindow:
    def show_typed(self, r): pass
class FakeDash:
    isVisible = lambda self: False
    def refresh_history(self): pass
    def set_status(self, s): pass
class Harness(m.WhisperWriterApp):
    def __init__(self):
        self.result_thread = None
        self.target_window = None
        self.status_window = None
        self.dashboard = FakeDash()
        self.history = types.SimpleNamespace(add=lambda *a, **k: None)
        self.input_simulator = types.SimpleNamespace(typewrite=lambda t, w=None: None)
        self.key_listener = types.SimpleNamespace(start=lambda: None)
        self._rec_duration = 0.0

h = Harness()
h.on_transcription_complete('hello world')
print('sound fired        =', len(fired))

fails = []
if cfg is not False:
    fails.append(f'config is {cfg!r}, expected False (off by default)')
if fired:
    fails.append(f'sound played {len(fired)} time(s) despite being off')
if not h.status_window and False:
    pass

# Now prove it is still TOGGLEABLE, not deleted.
ConfigManager.set_config_value(True, 'misc', 'noise_on_completion')
fired.clear()
h.on_transcription_complete('again')
print('\nafter enabling     =', len(fired), 'sound(s)')
if len(fired) != 1:
    fails.append('sound did not play when explicitly enabled — feature broken/removed')
ConfigManager.set_config_value(False, 'misc', 'noise_on_completion')

print('\n' + '=' * 50)
if fails:
    print('FAILED:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('PASSED — silent by default, still works when turned on.')
