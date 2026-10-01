"""Generate the ghosttype tray/app icon as a multi-resolution .ico.

Replaces the upstream WhisperWriter bear mascot with a ghost that matches the
app name. Drawn with QPainter as vectors at every size Windows actually asks the
tray for (16, 24, 32, 48, 64, 128, 256), so it stays crisp instead of being one
bitmap upscaled.

Run:  venv/Scripts/python.exe make_icon.py
Out:  assets/ghosttype.ico  and  assets/ghosttype.png (256px preview)
"""
import os
import struct
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'src'))

from PyQt5.QtCore import Qt, QRectF, QPointF, QBuffer, QByteArray  # noqa: E402
from PyQt5.QtGui import (QImage, QPainter, QPainterPath, QColor, QPen,  # noqa: E402
                         QBrush, QLinearGradient)
from PyQt5.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv)

BODY_TOP = QColor('#8fbcd9')   # light slate-blue crown
BODY_BOT = QColor('#4a7fa5')   # deeper tail — matches theme ACCENT
OUTLINE = QColor('#2f5470')
EYE = QColor('#1b2733')
SIZES = [16, 24, 32, 48, 64, 128, 256]


def draw_ghost(px):
    """Render the ghost at px x px onto a transparent QImage."""
    img = QImage(px, px, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)

    s = px / 256.0  # design at 256, scale from there
    left, right = 46 * s, 210 * s
    top, bottom = 34 * s, 214 * s

    path = QPainterPath()
    path.moveTo(QPointF(left, bottom))
    path.lineTo(left, top + 92 * s)
    path.arcTo(QRectF(left, top, right - left, 190 * s), 180, -180)
    path.lineTo(right, bottom)

    # Scalloped hem: three arcs bulging downward gives the classic ghost skirt.
    seg = (right - left) / 3.0
    for i in range(3):
        path.arcTo(QRectF(left + i * seg, bottom - 52 * s, seg, 96 * s), 180, 180)
    path.closeSubpath()

    grad = QLinearGradient(left, top, left, bottom)
    grad.setColorAt(0.0, BODY_TOP)
    grad.setColorAt(1.0, BODY_BOT)
    p.setBrush(QBrush(grad))
    p.setPen(QPen(OUTLINE, max(1.0, 5 * s)))
    p.drawPath(path)

    # Two eyes. At 16px they must stay solid enough to read as a face.
    eye_w, eye_h = 34 * s, 46 * s
    for cx in (104 * s, 152 * s):
        p.setBrush(QBrush(EYE))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, 100 * s), eye_w / 2, eye_h / 2)

    p.end()
    return img


def png_bytes(img):
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QBuffer.WriteOnly)
    img.save(buf, 'PNG')
    buf.close()
    return bytes(ba)


def write_ico(images, path):
    """Write a classic multi-image .ico directory (PNG-compressed entries)."""
    entries, blobs, offset = [], [], 6 + 16 * len(images)
    for im in images:
        data = png_bytes(im)
        entries.append(struct.pack(
            '<BBBBHHII',
            im.width() % 256, im.height() % 256,   # 0 => 256
            0, 0,                                  # palette / reserved
            1, 32,                                 # colour planes, bpp
            len(data), offset))
        blobs.append(data)
        offset += len(data)
    with open(path, 'wb') as f:
        f.write(struct.pack('<HHH', 0, 1, len(images)))
        for e in entries:
            f.write(e)
        for b in blobs:
            f.write(b)


print('rendering ghost icon...')
images = [draw_ghost(n) for n in SIZES]

ico_path = os.path.join(BASE, 'assets', 'ghosttype.ico')
write_ico(images, ico_path)

png_path = os.path.join(BASE, 'assets', 'ghosttype.png')
images[-1].save(png_path, 'PNG')

print(f'wrote {ico_path}  ({os.path.getsize(ico_path):,} bytes)')
print(f'wrote {png_path}  ({os.path.getsize(png_path):,} bytes)')
print('sizes embedded:', SIZES)