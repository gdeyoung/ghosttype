"""Verify the recording indicator is unobtrusive AND does not steal focus.

The focus part is the load-bearing test. ghosttype dictates into whatever app has
focus; if the indicator window can become foreground, the transcribed text gets
typed into the indicator instead of the user's editor.

We check the three things that actually cause focus theft on Windows:
  1. Qt.WindowDoesNotAcceptFocus is set in the window flags
  2. WA_ShowWithoutActivating is set
  3. The focus policy is NoFocus, not Qt.StrongFocus

Plus size/unobtrusiveness: the pill must stay under ~2% of the screen.

Run:  venv/Scripts/python.exe indicator_test.py
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'src'))

from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtWidgets import QApplication, QLabel  # noqa: E402
from PyQt5.QtGui import QFont  # noqa: E402

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

app = QApplication(sys.argv)
f = QFont('Segoe UI', 10)
app.setFont(f)

failures = []

from ui.status_window import StatusWindow, PILL_W, PILL_H  # noqa: E402

sw = StatusWindow()
flags = sw.windowFlags()

print('=== FOCUS SAFETY (the important part) ===')
has_no_accept = bool(flags & Qt.WindowDoesNotAcceptFocus)
has_no_activate = sw.testAttribute(Qt.WA_ShowWithoutActivating)
no_focus_policy = sw.focusPolicy() == Qt.NoFocus
is_tool = bool(flags & Qt.Tool)
on_top = bool(flags & Qt.WindowStaysOnTopHint)
frameless = bool(flags & Qt.FramelessWindowHint)

print(f'WindowDoesNotAcceptFocus = {has_no_accept}')
print(f'WA_ShowWithoutActivating = {has_no_activate}')
print(f'focusPolicy == NoFocus   = {no_focus_policy}  ({sw.focusPolicy()})')
print(f'Qt.Tool                  = {is_tool}')
print(f'WindowStaysOnTopHint     = {on_top}')
print(f'FramelessWindowHint      = {frameless}')

# Without WindowDoesNotAcceptFocus the pill can become the foreground window.
if not has_no_accept:
    failures.append('WindowDoesNotAcceptFocus NOT set — indicator can steal focus '
                    'and swallow dictated text')
if not has_no_activate:
    failures.append('WA_ShowWithoutActivating NOT set — show() may activate the window')
if not no_focus_policy:
    failures.append(f'focusPolicy is {sw.focusPolicy()}, expected NoFocus')
if not is_tool:
    failures.append('window is not Qt.Tool; it will appear in the taskbar/alt-tab')
if not frameless:
    failures.append('window is not frameless; it will draw a title bar')
if not on_top:
    failures.append('window is not always-on-top; it would be hidden behind the app')

print('\n=== SIZE / UNOBTRUSIVENESS ===')
geom = app.primaryScreen().availableGeometry()
area = geom.width() * geom.height()
pct = (PILL_W * PILL_H) / area * 100
print(f'pill        = {PILL_W}x{PILL_H} px')
print(f'screen      = {geom.width()}x{geom.height()}')
print(f'pill covers = {pct:.2f}% of screen')
if pct > 2.0:
    failures.append(f'pill covers {pct:.2f}% of screen; want < 2%')
# The old dashboard was ~32%; assert the pill is dramatically smaller.
if pct > 5:
    failures.append('pill is not meaningfully smaller than the old dashboard')

print('\n=== STATE MACHINE ===')
try:
    sw.updateStatus('recording')
    app.processEvents()
    vis_rec = sw.isVisible()
    print(f'recording    -> visible={vis_rec} label={sw.state_label.text()!r} '
          f'timer={sw.timer_label.text()!r}')
    if sw.state_label.text() != 'Listening':
        failures.append(f'recording label is {sw.state_label.text()!r}, want "Listening"')
    if not sw.timer_label.text():
        failures.append('elapsed timer not showing during recording')

    sw.updateStatus('transcribing')
    app.processEvents()
    print(f'transcribing -> visible={sw.isVisible()} label={sw.state_label.text()!r}')
    if sw.state_label.text() != 'Transcribing…':
        failures.append(f'transcribing label is {sw.state_label.text()!r}')

    sw.show_typed('hello world')
    app.processEvents()
    print(f'typed        -> visible={sw.isVisible()} label={sw.state_label.text()!r}')
    if sw.state_label.text() != 'Typed':
        failures.append(f'typed label is {sw.state_label.text()!r}, want "Typed"')

    sw.updateStatus('idle')
    app.processEvents()
    print(f'idle         -> visible={sw.isVisible()} (should stay up for the flash)')
except Exception as e:
    failures.append(f'state machine raised: {e!r}')
    print('STATE MACHINE FAILED:', e)

# Confirm focus did not land on the indicator after all that show() churn.
print(f'\nfocus still on indicator? {app.focusWidget() is not None and app.focusWidget() is sw}')

print('\n' + '=' * 60)
if failures:
    print('INDICATOR TEST FAILED:')
    for x in failures:
        print('  -', x)
    sys.exit(1)
print('INDICATOR TEST PASSED — slim, unobtrusive, and focus-safe.')