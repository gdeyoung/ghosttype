"""Interactive hotkey tester — press a key, see whether ghosttype can bind it.

The F-row on a Dell XPS 16 is dual-purpose: the top row is the media row by
default, so "F9" is really Fn+F9 and the F-keys need the Fn key held. That makes
them a bad push-to-talk. This tool prints, live, exactly what ghosttype's
key_listener would bind for whatever you press — including keys the Fn row
cannot reach cleanly.

It does NOT need the app running and it never records audio.

Usage:
    venv/Scripts/python.exe hotkey_test.py          # 60s capture
    venv/Scripts/python.exe hotkey_test.py 120      # longer
"""
import sys
import time

sys.path.insert(0, 'src')

from utils import ConfigManager  # noqa: E402
from key_listener import KeyListener, KeyCode  # noqa: E402
from pynput import keyboard  # noqa: E402

ConfigManager.initialize()
listener = KeyListener()

# Reverse map so we can name what ghosttype would bind.
# Enum members must be iterated (KeyCode.__members__) — vars(KeyCode) yields the
# auto() sentinel, not the members, so a vars()-based map silently comes out empty.
NAME_BY_CODE = {m.name: m for m in KeyCode}
# pynput special keys that ghosttype's own enum may cover under another name.
PYNPUT_ALIAS = {
    'caps_lock': 'CAPS_LOCK', 'scroll_lock': 'SCROLL_LOCK', 'num_lock': 'NUM_LOCK',
    'insert': 'INSERT', 'menu': 'MENU', 'pause': 'PAUSE',
}

DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0

print(f'Listening {DURATION:.0f}s. Press candidate keys one at a time.\n')
print('Try: Caps Lock, Scroll Lock, F9, F10, F11, F12, Insert, Pause,')
print('     the Copilot key, and the media/volume row.\n')

seen = []


def describe(key):
    """Map a pynput key to the ghosttype KeyCode name, if bindable."""
    name = getattr(key, 'name', None)
    if name is None:
        return None, 'character key (not bindable alone)'
    # e.g. 'caps_lock' -> CAPS_LOCK
    ghost = PYNPUT_ALIAS.get(name) or name.upper()
    if ghost in NAME_BY_CODE:
        return ghost, 'BINDABLE'
    return None, f'no ghosttype KeyCode named {ghost!r}'


def on_press(key):
    name = getattr(key, 'name', None)
    vk = getattr(key, 'vk', None)
    ch = getattr(key, 'char', None)
    ghost, verdict = describe(key)
    line = (f'PRESS {("name=" + repr(name)) if name else (f"vk={vk} char={ch!r}")}'
            f'  -> {ghost or "-"}  [{verdict}]')
    print(line)
    if name:
        seen.append(name)


def on_release(key):
    name = getattr(key, 'name', None)
    if name:
        print(f'RELEASE {name}')


l = keyboard.Listener(on_press=on_press, on_release=on_release)
l.start()
time.sleep(DURATION)
l.stop()

print(f'\n--- keys that ghosttype could bind ---')
bindable = sorted({n for n in seen if PYNPUT_ALIAS.get(n) or n.upper() in NAME_BY_CODE})
print(', '.join(bindable) if bindable else '(none captured)')
notbindable = sorted({n for n in seen if n not in bindable})
if notbindable:
    print(f'\nnot bindable: {", ".join(notbindable)}')

if 'caps_lock' in seen:
    print('\nRecommendation: caps_lock — single key, on the home row, never needs Fn.')