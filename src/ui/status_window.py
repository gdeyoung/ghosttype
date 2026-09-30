"""Unobtrusive recording indicator — a slim pill, not a panel.

Design constraints that drove this rewrite:

1. MUST NOT STEAL FOCUS. The whole point is to dictate into whatever app has
   focus. A window that takes focus would send the transcribed text to itself.
   Hence Qt.WindowDoesNotAcceptFocus + WA_ShowWithoutActivating + NoFocus policy,
   and we never call activateWindow()/raise_() in a way that grants focus.

2. MUST BE SMALL. The old 84x84 circle was fine, but the *dashboard* was the
   real screen hog — it auto-showed at launch and covered ~32% of a 1600x1000
   display. This file is only the transient indicator; the dashboard is now
   tray-only (see main.py).

3. MUST SAY SOMETHING. A dot alone doesn't tell you whether it heard you. So:
   state word + elapsed timer + live mic level.
"""

import math
import os
from collections import deque

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRectF, QTimer, QPoint
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen, QPainterPath
from PyQt5.QtWidgets import QApplication, QLabel, QHBoxLayout, QWidget, QMainWindow

from brand import (
    INDICATOR_LISTENING, INDICATOR_TRANSCRIBING, INDICATOR_TYPED,
    INDICATOR_READY,
)

# Pill geometry, in logical px. Deliberately small: ~340x48 is a sliver.
PILL_W, PILL_H = 340, 48
PILL_RADIUS = 10
MARGIN_BOTTOM = 96   # clear of the Windows taskbar
TYPED_FLASH_MS = 1100  # how long "Typed" acknowledgement stays up


def _tint(pixmap, color):
    """Return a copy of pixmap recolored to the given QColor (keeps alpha)."""
    if pixmap.isNull():
        return pixmap
    tinted = QPixmap(pixmap.size())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), color)
    painter.end()
    return tinted


class LevelMeter(QWidget):
    """Compact 5-bar mic meter. Colour follows state so it doubles as a status cue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = 5
        self.levels = deque([0.0] * self.bars, maxlen=self.bars)
        self.color = QColor('#ff5c72')
        self.setFixedSize(30, 18)
        self.setFocusPolicy(Qt.NoFocus)
        self._phase = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(90)
        self._anim_timer.timeout.connect(self._advance)
        self._animating = False

    def _advance(self):
        self._phase = (self._phase + 0.22) % 1.0
        self.levels.append(0.18 + 0.42 * (0.5 + 0.5 * math.sin(self._phase * 6.28318)))
        self.update()

    def set_color(self, qcolor):
        self.color = qcolor
        self.update()

    def update_level(self, level):
        self.levels.append(max(0.05, level))
        self.update()

    def reset(self):
        self.stop_idle_animation()
        self.levels = deque([0.0] * self.bars, maxlen=self.bars)
        self.update()

    def start_idle_animation(self):
        """Slow travelling wave — reads as 'working' without a spinner."""
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def stop_idle_animation(self):
        self._anim_timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        step = w / self.bars
        bar_w = max(2, int(step * 0.5))
        for i, lvl in enumerate(self.levels):
            bar_h = max(2, lvl * h * 0.9)
            x = int(i * step + (step - bar_w) / 2)
            y = int((h - bar_h) / 2)
            c = QColor(self.color)
            c.setAlpha(140 + int(115 * min(1.0, lvl)))
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bar_w, int(bar_h), 2, 2)


class StatusWindow(QMainWindow):
    """Slim always-on-top pill that never takes focus."""

    statusSignal = pyqtSignal(str)
    closeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # WindowDoesNotAcceptFocus is the load-bearing flag: without it this
        # window can become foreground and swallow the text we are dictating.
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(PILL_W, PILL_H)
        self.setWindowTitle('ghosttype')

        central = QWidget(self)
        central.setStyleSheet('background: transparent;')
        central.setFocusPolicy(Qt.NoFocus)
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setFocusPolicy(Qt.NoFocus)
        mic = os.path.join('assets', 'microphone.png')
        pencil = os.path.join('assets', 'pencil.png')
        self.microphone_pixmap = _tint(
            QPixmap(mic).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation),
            QColor('#ff5c72'))
        self.pencil_pixmap = _tint(
            QPixmap(pencil).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation),
            QColor('#ffb454'))
        self.check_pixmap = _tint(
            QPixmap(pencil).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation),
            QColor('#46d18b'))
        self.icon_label.setPixmap(self.microphone_pixmap)

        self.state_label = QLabel(INDICATOR_READY)
        self.state_label.setFocusPolicy(Qt.NoFocus)
        f = QFont('Segoe UI', 10)
        f.setWeight(QFont.DemiBold)
        self.state_label.setFont(f)
        self.state_label.setStyleSheet('color: #e7e9f0; background: transparent;')

        self.timer_label = QLabel('')
        self.timer_label.setFocusPolicy(Qt.NoFocus)
        tf = QFont('Consolas', 9)
        self.timer_label.setFont(tf)
        self.timer_label.setStyleSheet('color: #9aa0b4; background: transparent;')

        self.meter = LevelMeter()

        layout.addWidget(self.icon_label)
        layout.addWidget(self.state_label)
        layout.addStretch(1)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.meter)

        # Elapsed-time ticker, only ticking while recording.
        self._elapsed = 0.0
        self._ticker = QTimer(self)
        self._ticker.setInterval(100)
        self._ticker.timeout.connect(self._tick)

        # Hides the "Typed" acknowledgement on its own.
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._on_flash_done)

        self._visible_state = None
        self.statusSignal.connect(self.updateStatus)

    # -- positioning -------------------------------------------------------

    def _reposition(self):
        """Bottom-centre of the screen the cursor is on, clear of the taskbar."""
        screen = QApplication.screenAt(QPoint(0, 0)) or QApplication.primaryScreen()
        if screen is None:
            screen = QApplication.primaryScreen()
        geom = screen.availableGeometry() if screen else None
        if geom is None:
            return
        x = geom.x() + (geom.width() - self.width()) // 2
        y = geom.y() + geom.height() - self.height() - MARGIN_BOTTOM
        self.move(x, y)

    def show(self):
        self._reposition()
        # show() not showActive() — never request focus.
        super().show()
        self._reposition()

    # -- painting ----------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0.75, 0.75, PILL_W - 1.5, PILL_H - 1.5)

        path = QPainterPath()
        path.addRoundedRect(rect, PILL_RADIUS, PILL_RADIUS)

        # Dark translucent body.
        body = QColor(18, 19, 24, 238)
        painter.fillPath(path, QBrush(body))

        # Accent edge keyed to state.
        edge = QColor(self._edge_color())
        edge.setAlpha(210)
        painter.setPen(QPen(edge, 1.5))
        painter.drawPath(path)

    def _edge_color(self):
        return {
            'recording': '#ff5c72',
            'transcribing': '#ffb454',
            'typed': '#46d18b',
        }.get(self._visible_state, '#46d18b')

    # -- state -------------------------------------------------------------

    @pyqtSlot(str)
    def updateStatus(self, status):
        if status == 'recording':
            self._flash_timer.stop()
            self._visible_state = 'recording'
            self.icon_label.setPixmap(self.microphone_pixmap)
            self.state_label.setText(INDICATOR_LISTENING)
            self.meter.set_color(QColor('#ff5c72'))
            self.meter.reset()
            self.meter.stop_idle_animation()
            self._elapsed = 0.0
            self.timer_label.setText('0.0s')
            self._ticker.start()
            self.show()
            self.update()

        elif status == 'transcribing':
            self._ticker.stop()
            self._visible_state = 'transcribing'
            self.icon_label.setPixmap(self.pencil_pixmap)
            self.state_label.setText(INDICATOR_TRANSCRIBING)
            self.meter.set_color(QColor('#ffb454'))
            self.timer_label.setText('')
            self.meter.reset()
            self.meter.start_idle_animation()
            self.show()
            self.update()

        elif status == 'idle':
            self._ticker.stop()
            self.timer_label.setText('')
            # Stay up only if we're mid-flash; otherwise get out of the way.
            if not self._flash_timer.isActive():
                self.close()

    def show_typed(self, text):
        """Brief acknowledgement that the text actually landed."""
        self._ticker.stop()
        self._visible_state = 'typed'
        self.icon_label.setPixmap(self.check_pixmap)
        self.state_label.setText(INDICATOR_TYPED)
        self.timer_label.setText('')
        self.meter.set_color(QColor('#46d18b'))
        self.meter.reset()
        self.meter.start_idle_animation()
        self.show()
        self.update()
        self._flash_timer.start(TYPED_FLASH_MS)

    def _on_flash_done(self):
        self.close()

    def _tick(self):
        self._elapsed += 0.1
        self.timer_label.setText(f'{self._elapsed:.1f}s')

    @pyqtSlot(float)
    def updateAudioLevel(self, level):
        if self._visible_state == 'recording':
            self.meter.update_level(level)

    def closeEvent(self, event):
        self._ticker.stop()
        self._flash_timer.stop()
        self.meter.stop_idle_animation()
        self._visible_state = None
        self.closeSignal.emit()
        super().closeEvent(event)