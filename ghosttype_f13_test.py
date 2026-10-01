"""Prove ghosttype's KeyListener fires on an injected F13.

Previous test proved pynput SEES the F13. This proves ghosttype's KeyChord turns
that into on_activate/on_deactivate callbacks — the thing that starts and stops
recording. Real KeyListener + real KeyChord, no Qt.
"""
import sys
sys.path.insert(0, 'src')
from utils import ConfigManager
ConfigManager.initialize()
from key_listener import KeyListener, KeyCode, InputEvent

fired = []
kl = KeyListener()
kl.add_callback('on_activate', lambda: fired.append('activate'))
kl.add_callback('on_deactivate', lambda: fired.append('deactivate'))
kl.set_activation_keys(kl.parse_key_combination('f13'))

def press():
    kl.on_input_event((KeyCode.F13, InputEvent.KEY_PRESS))
def release():
    kl.on_input_event((KeyCode.F13, InputEvent.KEY_RELEASE))

print('recording_mode =', ConfigManager.get_config_value('recording_options','recording_mode'))
print('\n-- press 1 (start) --'); press();  print('   callbacks:', fired)
print('-- press 2 (stop)  --'); press(); release(); print('   callbacks:', fired)
print('-- press 3 (start) --'); press();  print('   callbacks:', fired)

fails = []
if fired[:2] != ['activate', 'deactivate']:
    fails.append(f'expected activate,deactivate got {fired[:2]}')
if len(fired) < 3 or fired[2] != 'activate':
    fails.append('third press did not re-activate — listener did not re-arm')
print('\n' + '=' * 50)
if fails:
    print('FAILED:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('PASSED — ghosttype fires activate/deactivate on F13, and re-arms.')
