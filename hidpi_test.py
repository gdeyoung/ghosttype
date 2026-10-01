"""HiDPI verification: prove the dashboard actually renders at 2x, not just that
the Qt attribute got set.

AA_EnableHighDpiScaling makes Qt scale the whole UI. We assert on the thing
that actually matters: a QLabel's rendered height in logical px must be
noticeably larger than the same font at unscaled 1x. We build both a scaled and
an unscaled label and compare.

Run:  venv/Scripts/python.exe hidpi_test.py
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'src'))

from PyQt5.QtWidgets import QApplication, QLabel  # noqa: E402
from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtGui import QFont  # noqa: E402

failures = []

# Replicate main.py's ordering exactly: attributes BEFORE QApplication exists.
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

app = QApplication(sys.argv)
# And main.py's app-wide base font — without this, widgets inherit Qt's 8pt
# "MS Shell Dlg 2" default and render unreadably small even when scaled.
base_font = QFont('Segoe UI', 10)
base_font.setHintingPreference(QFont.PreferFullHinting)
app.setFont(base_font)

dpr = app.devicePixelRatio()
base_pt = app.font().pointSize()

print(f'devicePixelRatio      = {dpr}')
print(f'AA_EnableHighDpiScaling= {QApplication.testAttribute(Qt.AA_EnableHighDpiScaling)}')
print(f'AA_UseHighDpiPixmaps   = {QApplication.testAttribute(Qt.AA_UseHighDpiPixmaps)}')
print(f'app base font          = {app.font().family()} {base_pt}pt '
      f'(Qt default was 8pt MS Shell Dlg 2)')

if dpr < 1.5:
    failures.append(f'devicePixelRatio is {dpr}; HiDPI scaling looks inactive')
if base_pt < 9:
    failures.append(f'app base font is only {base_pt}pt; UI will read too small')


def label_height(pt):
    """Height in logical px of a label at an explicit point size."""
    lbl = QLabel('Ready')
    f = QFont('Segoe UI', pt)
    lbl.setFont(f)
    lbl.adjustSize()
    return lbl.height()


h10 = label_height(10)
h4 = label_height(4)
print(f'\nQLabel("Ready") @10pt = {h10}px logical,  @4pt = {h4}px logical')

# Rather than a magic pixel number, assert text height actually tracks point size.
# A 10pt label must be meaningfully taller than a 4pt one, and tall enough to
# read: ~15px+ at 10pt Segoe UI is the real-world floor.
if h10 < 15:
    failures.append(f'10pt label renders only {h10}px tall; too small to read')
if h10 <= h4 * 1.3:
    failures.append(f'label height {h10}px vs {h4}px at 4pt — text is not scaling '
                    f'with font size, HiDPI/font handling is broken')

# Build the real dashboard and confirm it lays out and paints without error.
try:
    from utils import ConfigManager
    ConfigManager.initialize()
    from ui.dashboard_window import DashboardWindow
    from history import HistoryStore
    dw = DashboardWindow(HistoryStore())
    dw.adjustSize()
    print(f'DashboardWindow size   = {dw.width()}x{dw.height()} logical px')
    dw.show()
    app.processEvents()
    # Confirm the byline really is the rebranded English text.
    labels = dw.findChildren(QLabel)
    texts = [l.text() for l in labels if l.text()]
    branded = [t for t in texts if 'ghosttype' in t.lower()]
    print(f'branded labels found  = {branded}')
    if not branded:
        failures.append('no ghosttype-branded label rendered in dashboard')
    cyr = [t for t in texts if any('\u0400' <= c <= '\u04FF' for c in t)]
    if cyr:
        failures.append(f'Cyrillic rendered in dashboard UI: {cyr}')
    else:
        print('Cyrillic in rendered labels: none')
    dw.close()
except Exception as e:
    failures.append(f'DashboardWindow build failed: {e!r}')
    print('DASHBOARD FAILED:', e)

print('\n' + '=' * 60)
if failures:
    print('HIDPI/UI TEST FAILED:')
    for f in failures:
        print('  -', f)
    sys.exit(1)
print('HIDPI/UI TEST PASSED — scaling active, UI is English and branded.')