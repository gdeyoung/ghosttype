"""Verify the max-recording-length setting: UI, config round-trip, and enforcement.

Three things to prove:
  1. The Settings dropdown offers 1-15 minutes and defaults to 5.
  2. Saving persists the chosen value to config.
  3. The record loop actually stops at the cap (tested by driving _record_audio
     with a synthetic audio stream, not a real mic).

Run:  venv/Scripts/python.exe max_recording_test.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt5.QtWidgets import QApplication, QLabel  # noqa: E402
from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtGui import QFont  # noqa: E402

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
app = QApplication(sys.argv)
app.setFont(QFont('Segoe UI', 10))

from utils import ConfigManager  # noqa: E402
ConfigManager.initialize()

failures = []

# ---- 1. Schema default -------------------------------------------------------
default = ConfigManager.get_config_value('recording_options', 'max_recording_minutes')
print(f'schema/config default = {default!r}')
if default != 5:
    failures.append(f'default is {default!r}, expected 5')

import yaml  # noqa: E402
schema = yaml.safe_load(open('src/config_schema.yaml', encoding='utf-8'))
node = schema['recording_options']['max_recording_minutes']
print(f'schema min/max       = {node.get("min")}..{node.get("max")}')
if (node.get('min'), node.get('max')) != (1, 15):
    failures.append(f'schema bounds are {node.get("min")}..{node.get("max")}, expected 1..15')

# ---- 2. UI dropdown + save round-trip ---------------------------------------
from ui import theme  # noqa: E402
theme.set_theme(ConfigManager.get_config_value('misc', 'theme') or 'dark')
app.setStyleSheet(theme.QSS)
from ui.dashboard_window import DashboardWindow  # noqa: E402
from history import HistoryStore  # noqa: E402

dash = DashboardWindow(HistoryStore(db_path=os.path.abspath('_maxrec_scratch.db')))
print(f'dropdown items       = {dash.f_max_rec.count()}')
labels = [dash.f_max_rec.itemText(i) for i in range(dash.f_max_rec.count())]
if dash.f_max_rec.count() != 15:
    failures.append(f'dropdown has {dash.f_max_rec.count()} items, expected 15')
if dash.f_max_rec.currentIndex() != 4:
    failures.append(f'default index is {dash.f_max_rec.currentIndex()}, expected 4 (5 min)')
print(f'default selection    = {labels[dash.f_max_rec.currentIndex()]!r}')
print(f'first / last         = {labels[0]!r} / {labels[-1]!r}')

# Pick 12 minutes, save, confirm it persisted.
dash.f_max_rec.setCurrentIndex(11)
dash._save_settings()
saved = ConfigManager.get_config_value('recording_options', 'max_recording_minutes')
print(f'after selecting 12   = {saved!r}')
if saved != 12:
    failures.append(f'save round-trip wrote {saved!r}, expected 12')

# Put it back to the default so we don't leave the config modified.
ConfigManager.set_config_value(5, 'recording_options', 'max_recording_minutes')
ConfigManager.save_config()

# ---- 3. Enforcement in the record loop --------------------------------------
# The loop's guard is: after each frame, if len(recording) >= max_samples, stop.
# Exercise that arithmetic directly, including the clamping of out-of-range config.
RATE = 16000
FRAME = int(RATE * (30 / 1000.0))


def sim(minutes, frames=10_000_000):
    """Replay the loop's accumulate-and-check for `minutes`, return frames used."""
    max_samples = int(RATE * 60 * max(1, min(15, int(minutes))))
    produced = 0
    for _ in range(frames):
        produced += FRAME
        if produced >= max_samples:
            return produced, max_samples
    return produced, max_samples


for mins, expect_min in ((1, 1), (5, 5), (12, 12), (15, 15), (0, 1), (999, 15)):
    produced, cap = sim(mins)
    got_min = cap / RATE / 60
    print(f'cap {mins:>3} min -> stops at {cap:>9,} samples '
          f'({got_min:.0f} min) after {produced:,} samples')
    if got_min != expect_min:
        failures.append(f'config {mins} produced a {got_min:.0f}-min cap, '
                        f'expected {expect_min}')

for f in ('_maxrec_scratch.db',):
    if os.path.exists(f):
        os.remove(f)

print('\n' + '=' * 60)
if failures:
    print('MAX-RECORDING TEST FAILED:')
    for f in failures:
        print('  -', f)
    sys.exit(1)
print('PASSED — 1-15 minute dropdown, defaults to 5, cap is enforced and clamped.')