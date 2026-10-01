"""One-shot setup for the public ghosttype repo: description, topics, homepage.

Kept as a script so the settings are reproducible and reviewable rather than
typed into a web form once and forgotten.

Run:  venv/Scripts/python.py setup_repo_meta.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

REPO = 'gdeyoung/ghosttype'
API = f'https://api.github.com/repos/{REPO}'

# Lead with the outcome and the differentiator, not the fork. The old text
# described a hold-to-talk workflow and opened with "Fork of ...".
DESCRIPTION = (
    'Offline voice typing for Windows. Press a hotkey, speak, and the words '
    'land in whatever app has focus. Local Whisper \u2014 no API key, no account. '
    'Tray-only, ~1% of screen, never steals focus. Works on laptops with media '
    'function rows and a Copilot key.'
)

TOPICS = [
    'voice-typing', 'dictation', 'whisper', 'speech-to-text', 'windows',
    'windows-11', 'productivity', 'offline-first', 'pynput', 'pyqt5',
    'accessibility', 'dictation-windows',
]

token = os.environ.get('GITHUB_TOKEN')
if not token:
    sys.exit('GITHUB_TOKEN not set — `set -a; source ~/AppData/Local/hermes/.env; set +a` first')


def call(method, url, payload=None):
    req = urllib.request.Request(url, data=payload, method=method)
    req.add_header('Authorization', 'Bearer ' + token)
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=45)
        return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]


# GitHub's topics endpoint is PUT /repos/{owner}/{repo}/topics with a bare list.
status, body = call('PUT', API + '/topics',
                    json.dumps({'names': TOPICS}).encode())
print(f'topics    -> HTTP {status}', TOPICS if status == 200 else body)

status, body = call('PATCH', API,
                    json.dumps({'description': DESCRIPTION}).encode())
print(f'description-> HTTP {status}')
if status == 200:
    print('   ', body.get('description'))
else:
    print('   ', body)

# Verify
status, body = call('GET', API)
print('\nverify:')
print('  description:', body.get('description'))
print('  topics     :', body.get('topics'))
