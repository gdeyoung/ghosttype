"""End-to-end test: does RepilotKey's SendInput actually reach pynput?

This is the load-bearing question for using the Copilot key as ghosttype's
push-to-toggle. Repilot claims the key via a Windows AppExtension and then
synthesizes a keystroke with SendInput. If that injection does not land in the
global input stream, ghosttype will never see it.

We do NOT need the Copilot key or package identity to test this: we run the
built handler exe directly and have it inject F13, while a pynput listener
watches for it. If the listener sees F13, the injection path is proven.

Requires a built Repilot checkout beside this repo (see REPILOT_REPO).

Config: %AppData%\\Repilot\\settings.json
  {"Action":{"Type":1,"Combo":{"Modifiers":0,"VirtualKey":124}}}   # 124 = VK_F13

Run:  venv/Scripts/python.exe ... (run from ghosttype venv)
"""
import ctypes
import json
import os
import subprocess
import sys
import time

from pynput import keyboard

# Resolve the Repilot checkout relative to this script's parent dir, so the test
# is not tied to one machine's home directory. Override with REPILOT_REPO.
DEFAULT_REPO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Repilot')
REPO = os.environ.get('REPILOT_REPO', DEFAULT_REPO)
EXE = os.path.join(
    REPO, 'RepilotKey', 'bin', 'x64', 'Release',
    'net10.0-windows10.0.22000.0', 'win-x64', 'publish', 'RepilotKey.exe')
SETTINGS_DIR = os.path.join(os.environ['APPDATA'], 'Repilot')
SETTINGS = os.path.join(SETTINGS_DIR, 'settings.json')

VK_F13 = 0x7C  # 124

failures = []

if not os.path.exists(EXE):
    print(f'FAIL: handler exe not found at {EXE}')
    sys.exit(1)
print(f'handler  = {EXE}  ({os.path.getsize(EXE):,} bytes)')

# Configure the handler to synthesize a bare F13.
os.makedirs(SETTINGS_DIR, exist_ok=True)
with open(SETTINGS, 'w', encoding='utf-8') as f:
    json.dump({'Action': {'Type': 1, 'Combo': {'Modifiers': 0, 'VirtualKey': VK_F13}}}, f)
print(f'wrote settings.json -> KeyCombo F13 (vk={VK_F13})')

# Clear the handler's auto-repeat debounce so our run isn't suppressed.
repeat = os.path.join(SETTINGS_DIR, 'repeat-state')
if os.path.exists(repeat):
    os.remove(repeat)

received = []


def on_press(key):
    name = getattr(key, 'name', None)
    vk = getattr(key, 'vk', None)
    received.append((name, vk))
    print(f'  pynput PRESS name={name!r} vk={vk!r}')


def on_release(key):
    print(f'  pynput RELEASE name={getattr(key, "name", None)!r}')


listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
time.sleep(0.6)

print('\nrunning RepilotKey.exe ...')
r = subprocess.run([EXE], capture_output=True, text=True, timeout=30)
print(f'  exit={r.returncode}')
if r.stdout.strip():
    print(f'  stdout: {r.stdout.strip()[:400]}')
if r.stderr.strip():
    print(f'  stderr: {r.stderr.strip()[:400]}')

time.sleep(1.2)
listener.stop()

log = os.path.join(SETTINGS_DIR, 'key-handler.log')
if os.path.exists(log):
    tail = open(log, encoding='utf-8', errors='replace').read().strip().splitlines()[-3:]
    print('\nhandler log:')
    for line in tail:
        print('  ', line)

f13_hits = [x for x in received if x[0] == 'f13' or x[1] == VK_F13]
print(f'\nevents received = {received}')
print(f'F13 hits        = {len(f13_hits)}')

if r.returncode != 0:
    failures.append(f'handler exited {r.returncode}')
if not received:
    failures.append('pynput received nothing — SendInput injection did not land')
if not f13_hits:
    failures.append('pynput did not see F13 — ghosttype could never bind it')

print('\n' + '=' * 60)
if failures:
    print('REPOL->PYNPUT TEST FAILED:')
    for f in failures:
        print('  -', f)
    sys.exit(1)
print('PASSED — Repilot\'s SendInput injection is visible to pynput.')
print('So a Copilot-key remap to F13 WOULD reach ghosttype.')