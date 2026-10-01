"""Capture real screenshots of the ghosttype UI for the README.

Renders the actual widgets (not a mock-up) and crops tightly to the content:

  assets/screenshot-settings.png  — the Settings page
  assets/screenshot-indicator.png — the recording pill, isolated

The settings shot uses the live config, so it shows the real current values
(hotkey f13, press_to_toggle, autostart on, tone off) rather than placeholders.

The indicator is captured per state so the README can show what it looks like
while recording.

Run:  venv/Scripts/python.exe make_screenshots.py
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'src'))

from PyQt5.QtCore import Qt, QTimer  # noqa: E402
from PyQt5.QtGui import QFont  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

# Same startup order as main.py: HiDPI attributes BEFORE the app exists.
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

app = QApplication(sys.argv)
app.setFont(QFont('Segoe UI', 10))

from utils import ConfigManager  # noqa: E402
ConfigManager.initialize()

from ui import theme  # noqa: E402
theme.set_theme(ConfigManager.get_config_value('misc', 'theme') or 'dark')
app.setStyleSheet(theme.QSS)

from ui.dashboard_window import DashboardWindow  # noqa: E402
from history import HistoryStore  # noqa: E402
from ui.status_window import StatusWindow  # noqa: E402


def settle(ms=350):
    """Let Qt lay out, apply the stylesheet, and paint."""
    end = [False]
    QTimer.singleShot(ms, lambda: end.__setitem__(0, True))
    while not end[0]:
        app.processEvents()


def save(widget, name):
    path = os.path.join(BASE, 'assets', name)
    pm = widget.grab()
    pm.save(path, 'PNG')
    print(f'  wrote assets/{name}  ({pm.width()}x{pm.height()})')
    return path


print('capturing Settings page...')
# NOTE: build against a throwaway history DB, never the user's real one. A
# screenshot of the History page populated from live transcriptions would publish
# whatever the user happened to dictate. These captures ship in a public README.
# HistoryStore opens the DB in its constructor, so the path must be passed in.
_scratch_db = os.path.join(BASE, '_screenshot_history_scratch.db')
_hist = HistoryStore(db_path=_scratch_db)

dash = DashboardWindow(_hist)
dash.show()
settle()
dash._switch_page(1)          # index 1 = Settings
settle(500)
save(dash, 'screenshot-settings.png')

# The settings page scrolls; the toggles (autostart, tone, post-processing)
# sit below the fold. Scroll the inner area so the README can show those too.
for area in dash.findChildren(type(dash).__mro__[0]):
    pass
scroller = None
from PyQt5.QtWidgets import QScrollArea
for sa in dash.findChildren(QScrollArea):
    if sa.isVisible():
        scroller = sa
        break
if scroller is not None:
    bar = scroller.verticalScrollBar()
    bar.setValue(bar.maximum())
    settle(400)
    save(dash, 'screenshot-settings-scrolled.png')
    bar.setValue(0)
    settle(200)

# Also grab the History page — it shows the transcriptions from testing.
dash._switch_page(0)
settle(400)
# Seed the throwaway DB with obviously-generic entries so the History shot shows
# the feature without publishing anything real.
for _txt in (
    'Meeting notes: reviewed the quarterly numbers and the roadmap draft.',
    'Reminder: the build finishes in about four minutes.',
    'Shopping list is in the shared document.',
):
    _hist.add(_txt, 4.2, 'base')
dash.refresh_history()
settle(400)
save(dash, 'screenshot-history.png')
for _f in (_scratch_db,):
    if os.path.exists(_f):
        os.remove(_f)

print('capturing recording indicator...')
ind = StatusWindow()
ind.show()
ind.updateStatus('recording')
for lvl in (0.9, 0.45, 0.75, 0.3, 0.6):
    ind.updateAudioLevel(lvl)
settle(300)
save(ind, 'screenshot-indicator.png')

print('done.')
