# -*- coding: utf-8 -*-
"""탭 2: 보드 · 소자 구조 (재설계).
- 좌→우 신호/전력 흐름 블록도. 화살표는 블록 '가장자리'에서 출발해 빈 공간으로
  직각 경로(꺾인 선)로 라우팅하고, 블록 위에 그려 항상 보이게 한다.
- 라벨은 흰 배경 알약으로 그려 어디서든 읽힌다.
- 실제 보드 사진은 크게 + 클릭하면 전체화면.
"""
import math
import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QTextBrowser,
                             QLabel, QDialog, QScrollArea)
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont, QPolygonF,
                         QPixmap, QFontMetrics)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QSize

from . import style as S
from .board_data import COMPONENTS, LINKS

MEDIA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "학습자료", "media")

LINK_STYLE = {           # kind -> (color, width, dashed)
    "power": (S.RED, 4, False),
    "ctrl":  (S.STEEL, 2, False),
    "sense": (S.GREEN, 2, True),
    "comm":  ("#c0763a", 2, True),
}


# ───────────────────────── 블록도 캔버스 ─────────────────────────
class BoardCanvas(QWidget):
    selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(620, 520)
        self.sel = "mcu"
        self._rects = {}

    def _px(self, x, y):
        m = 16
        W, H = self.width(), self.height()
        return QPointF(m + x / 100 * (W - 2 * m), m + y / 100 * (H - 2 * m))

    def _rect_px(self, rect):
        x, y, w, h = rect
        p0 = self._px(x, y); p1 = self._px(x + w, y + h)
        return QRectF(p0, p1)

    def mousePressEvent(self, ev):
        for key, r in self._rects.items():
            if r.contains(ev.position()):
                self.sel = key
                self.selected.emit(key)
                self.update()
                return

    # --- 화살촉 ---
    def _arrow_head(self, qp, tip, a, color):
        h = 11
        poly = QPolygonF([
            QPointF(tip.x(), tip.y()),
            QPointF(tip.x() - h * math.cos(a - 0.45), tip.y() - h * math.sin(a - 0.45)),
            QPointF(tip.x() - h * math.cos(a + 0.45), tip.y() - h * math.sin(a + 0.45)),
        ])
        qp.setBrush(QBrush(color)); qp.setPen(Qt.PenStyle.NoPen)
        qp.drawPolygon(poly)

    def _draw_link(self, qp, link):
        color = QColor(LINK_STYLE[link["kind"]][0])
        width = LINK_STYLE[link["kind"]][1]
        dashed = LINK_STYLE[link["kind"]][2]
        pts = [self._px(*p) for p in link["pts"]]
        pen = QPen(color, width, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        if dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        qp.setPen(pen)
        for i in range(len(pts) - 1):
            qp.drawLine(pts[i], pts[i + 1])
        # 끝 화살촉
        a_end = math.atan2(pts[-1].y() - pts[-2].y(), pts[-1].x() - pts[-2].x())
        self._arrow_head(qp, pts[-1], a_end, color)
        if link.get("bidir"):
            a_st = math.atan2(pts[0].y() - pts[1].y(), pts[0].x() - pts[1].x())
            self._arrow_head(qp, pts[0], a_st, color)
        # 라벨 (흰 배경 알약)
        if link.get("label") and link.get("lpos"):
            self._draw_label(qp, link["lpos"], link["label"], color)

    def _draw_label(self, qp, lpos, text, color):
        c = self._px(*lpos)
        qp.setFont(QFont(S.FONT_UI, 8, QFont.Weight.Bold))
        fm = QFontMetrics(qp.font())
        tw = fm.horizontalAdvance(text); th = fm.height()
        pad = 4
        box = QRectF(c.x() - tw / 2 - pad, c.y() - th / 2 - 1,
                     tw + 2 * pad, th + 2)
        qp.setBrush(QBrush(QColor("white")))
        qp.setPen(QPen(QColor(color), 1))
        qp.drawRoundedRect(box, 7, 7)
        qp.setPen(QPen(QColor(color)))
        qp.drawText(box, Qt.AlignmentFlag.AlignCenter, text)

    def paintEvent(self, _):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        qp.fillRect(self.rect(), QColor(S.BG))
        self._rects = {k: self._rect_px(c["rect"]) for k, c in COMPONENTS.items()}

        # 1) 블록 먼저
        for key, c in COMPONENTS.items():
            r = self._rects[key]
            sel = (key == self.sel)
            qp.setBrush(QBrush(QColor(c["color"])))
            qp.setPen(QPen(QColor(S.AMBER if sel else "#ffffff"), 3 if sel else 1))
            qp.drawRoundedRect(r, 7, 7)
            qp.setPen(QPen(QColor("white")))
            qp.setFont(QFont(S.FONT_UI, 9, QFont.Weight.Bold))
            qp.drawText(r.adjusted(4, 4, -4, -4),
                        Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                        c["title"])
        # 2) 화살표는 블록 '위'에 그려 항상 보이게 (빈 공간 라우팅이라 본문 안 가림)
        for link in LINKS:
            self._draw_link(qp, link)
        qp.end()


# ───────────────────────── 클릭하면 커지는 사진 ─────────────────────────
class ImageDialog(QDialog):
    def __init__(self, path, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        lay = QVBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        lab = QLabel(); lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pm = QPixmap(path)
        scr = self.screen().availableGeometry() if self.screen() else None
        maxw = int(scr.width() * 0.85) if scr else 1200
        maxh = int(scr.height() * 0.8) if scr else 800
        if not pm.isNull():
            lab.setPixmap(pm.scaled(QSize(maxw, maxh),
                          Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation))
        scroll.setWidget(lab)
        lay.addWidget(scroll)
        hint = QLabel("아무 곳이나 클릭하거나 ESC로 닫기")
        hint.setObjectName("hint"); hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(hint)
        self.resize(min(maxw + 40, pm.width() + 40) if not pm.isNull() else 900,
                    min(maxh + 80, pm.height() + 80) if not pm.isNull() else 600)

    def mousePressEvent(self, _):
        self.accept()


class ClickableImage(QLabel):
    def __init__(self, fn, caption, thumb_w=240):
        super().__init__()
        self.path = os.path.join(MEDIA, fn)
        self.caption = caption
        pm = QPixmap(self.path)
        if not pm.isNull():
            self.setPixmap(pm.scaledToWidth(
                thumb_w, Qt.TransformationMode.SmoothTransformation))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"border:1px solid {S.GRID}; background:white; padding:2px;")
        self.setToolTip("클릭하면 크게 봅니다")

    def mousePressEvent(self, _):
        ImageDialog(self.path, self.caption, self).exec()


# ───────────────────────── 탭 본체 ─────────────────────────
class BoardTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(12)

        # 왼쪽: 블록도
        left = QVBoxLayout()
        title = QLabel("모터제어보드 신호·전력 흐름   (블록을 클릭하면 설명)")
        title.setObjectName("h2")
        left.addWidget(title)
        self.canvas = BoardCanvas()
        self.canvas.selected.connect(self._show)
        left.addWidget(self.canvas, 1)
        legend = QLabel(
            "<span style='color:#d1495b'>━━ 전력(큰 전류)</span> &nbsp;&nbsp; "
            "<span style='color:#2f5f8f'>━━ 제어(PWM)</span> &nbsp;&nbsp; "
            "<span style='color:#2e9e6b'>┈┈ 센싱(읽기)</span> &nbsp;&nbsp; "
            "<span style='color:#c0763a'>┈┈ 통신(양방향)</span>")
        legend.setObjectName("hint")
        left.addWidget(legend)
        lw = QWidget(); lw.setLayout(left)
        root.addWidget(lw, 3)

        # 오른쪽: 큰 사진 + 상세
        right = QVBoxLayout(); right.setSpacing(6)
        pc = QLabel("📷 실제 보드 사진  (클릭하면 전체화면으로 크게)")
        pc.setObjectName("h2")
        right.addWidget(pc)
        prow = QHBoxLayout(); prow.setSpacing(8)
        for fn, cap in [("board_3d.png", "3D 모습 (실제 PCB)"),
                        ("board_assembly.png", "부품 배치도 (Q=MOSFET 등)")]:
            col = QVBoxLayout(); col.setSpacing(2)
            img = ClickableImage(fn, cap, thumb_w=235)
            cl = QLabel(cap); cl.setObjectName("hint"); cl.setWordWrap(True)
            col.addWidget(img); col.addWidget(cl)
            prow.addLayout(col)
        right.addLayout(prow)

        self.head = QLabel(); self.head.setObjectName("h2")
        self.head.setWordWrap(True)
        right.addWidget(self.head)
        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(False)
        right.addWidget(self.detail, 1)
        rw = QWidget(); rw.setLayout(right)
        rw.setMinimumWidth(440)
        root.addWidget(rw, 2)

        self._show("mcu")

    def _show(self, key):
        c = COMPONENTS[key]
        self.head.setText(f"{c['title']}   ·   {c['part']}")
        self.detail.setHtml(
            f"<div style='font-family:{S.FONT_UI}; font-size:13.5px;"
            f" color:{S.INK}; line-height:1.55'>{c['html']}</div>")
        self.canvas.sel = key
        self.canvas.update()
