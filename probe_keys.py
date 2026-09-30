"""Live key probe: print exactly what the OS delivers for a given key press.

Run this, then press the key you want to test. It reports the pynput key name,
vk, char, and the raw Win32 scan code / virtual key, which is the only reliable
way to find out what a non-standard key (Copilot, F-lock, media keys) emits.

Usage:  venv/Scripts/python.exe probe_keys.py            # 20s capture
        venv/Scripts/python.exe probe_keys.py 60         # 60s capture
"""
import ctypes, sys, time
from pynput import keyboard

DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
u32 = ctypes.windll.user32

print(f'Listening for {DURATION:.0f}s — press the key you want to inspect.\n')
seen = []

def on_press(k):
    name = getattr(k, 'name', None)
    vk = getattr(k, 'vk', None)
    ch = getattr(k, 'char', None)
    scan = u32.MapVirtualKeyW(vk, 0) if vk else None
    line = f'name={name!r:24s} vk={vk!r:8s} char={ch!r:8s} scancode={scan}'
    print('PRESS  ' + line)
    seen.append(line)

def on_release(k):
    name = getattr(k, 'name', None)
    vk = getattr(k, 'vk', None)
    print(f'RELEASE name={name!r} vk={vk!r}')

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
time.sleep(DURATION)
listener.stop()

print(f'\n--- {len(seen)} press events ---')
if not seen:
    print('NOTHING captured. If the key needs Fn, hold Fn while pressing it.')
