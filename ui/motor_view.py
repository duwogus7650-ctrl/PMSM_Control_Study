# -*- coding: utf-8 -*-
"""모터 단면 + 공간벡터 시각화 위젯.

전기각 기준으로 그립니다(FOC 설명에 자연스러움):
  - 고정자(stator): 3상 코일 a/b/c (0/120/240도)
  - 회전자(rotor): N-S 영구자석. d축 = 회전자 방향
  - dq축: d(빨강, 자석방향) / q(앰버, 90도 앞). dq가 회전자와 같이 돈다 = FOC 핵심
  - 전류 공간벡터(초록): 측정 전류 (i_alpha, i_beta)
  - 전압 공간벡터(스틸): 인가 전압 (v_alpha, v_beta)
"""
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QRectF
from . import style as S


class MotorView(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(360, 360)
        self.theta_e = 0.0
        self.ialpha = self.ibeta = 0.0
        self.valpha = self.vbeta = 0.0
        self.vmax = 13.85
        self.imax = 6.0

    def update_state(self, theta_e, ialpha, ibeta, valpha, vbeta, vmax, imax):
        self.theta_e = theta_e
        self.ialpha, self.ibeta = ialpha, ibeta
        self.valpha, self.vbeta = valpha, vbeta
        self.vmax = max(vmax, 1e-3)
        self.imax = max(imax, 1e-3)
        self.update()

    def _arrow(self, qp, cx, cy, ang, length, color, width, label=None, dash=False):
        x = cx + length * math.cos(ang)
        y = cy - length * math.sin(ang)   # 화면 y는 아래로 증가하므로 반전
        pen = QPen(color, width)
        if dash:
            pen.setStyle(Qt.PenStyle.DashLine)
        qp.setPen(pen)
        qp.drawLine(QPointF(cx, cy), QPointF(x, y))
        if not dash and length > 8:
            # 화살촉
            head = 10
            a1 = ang + math.radians(150)
            a2 = ang - math.radians(150)
            p = QPolygonF([
                QPointF(x, y),
                QPointF(x + head * math.cos(a1), y - head * math.sin(a1)),
                QPointF(x + head * math.cos(a2), y - head * math.sin(a2)),
            ])
            qp.setBrush(QBrush(color))
            qp.setPen(Qt.PenStyle.NoPen)
            qp.drawPolygon(p)
        if label:
            qp.setPen(QPen(color))
            f = QFont(S.FONT_MONO, 10, QFont.Weight.Bold)
            qp.setFont(f)
            qp.drawText(QPointF(x + 6, y - 4), label)

    def paintEvent(self, _):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        qp.fillRect(self.rect(), QColor(S.PANEL))
        cx, cy = w / 2, h / 2
        R = min(w, h) * 0.40         # 고정자 외경
        Rr = R * 0.55                # 회전자 반경

        # 고정자 하우징
        qp.setPen(QPen(QColor(S.GRID), 2))
        qp.setBrush(QBrush(QColor("#eef1f5")))
        qp.drawEllipse(QPointF(cx, cy), R, R)

        # 3상 코일 위치 (a=0, b=120, c=240도) — 전기각 평면
        for ang_deg, col, name in [(0, S.C_IA, "A"), (120, S.C_IB, "B"), (240, S.C_IC, "C")]:
            a = math.radians(ang_deg)
            px = cx + R * 0.86 * math.cos(a)
            py = cy - R * 0.86 * math.sin(a)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(QBrush(QColor(col)))
            qp.drawEllipse(QPointF(px, py), 9, 9)
            qp.setPen(QPen(QColor("white")))
            qp.setFont(QFont(S.FONT_UI, 8, QFont.Weight.Bold))
            qp.drawText(QRectF(px - 9, py - 9, 18, 18),
                        Qt.AlignmentFlag.AlignCenter, name)

        # 회전자 (자석): d축 = theta_e 방향. N(빨강 반쪽)/S(파랑 반쪽)
        th = self.theta_e
        qp.save()
        qp.translate(cx, cy)
        qp.rotate(-math.degrees(th))   # 화면 좌표계 회전
        # N극 반원 (오른쪽=+d)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QBrush(QColor("#d1495b")))
        qp.drawPie(QRectF(-Rr, -Rr, 2 * Rr, 2 * Rr), -90 * 16, 180 * 16)
        qp.setBrush(QBrush(QColor("#3b6fa0")))
        qp.drawPie(QRectF(-Rr, -Rr, 2 * Rr, 2 * Rr), 90 * 16, 180 * 16)
        qp.setPen(QPen(QColor("white"), 1))
        qp.setFont(QFont(S.FONT_UI, 10, QFont.Weight.Bold))
        qp.drawText(QRectF(Rr * 0.2, -Rr * 0.35, Rr * 0.8, Rr * 0.7),
                    Qt.AlignmentFlag.AlignCenter, "N")
        qp.drawText(QRectF(-Rr, -Rr * 0.35, Rr * 0.8, Rr * 0.7),
                    Qt.AlignmentFlag.AlignCenter, "S")
        qp.restore()

        # dq 축 (회전자와 함께 회전)
        self._arrow(qp, cx, cy, th, R * 0.95, QColor(S.RED), 2, "d", dash=True)
        self._arrow(qp, cx, cy, th + math.pi / 2, R * 0.95, QColor(S.AMBER), 2, "q", dash=True)

        # 전류 공간벡터 (초록): 크기 정규화
        imag = math.hypot(self.ialpha, self.ibeta)
        if imag > 1e-4:
            iang = math.atan2(self.ibeta, self.ialpha)
            L = min(imag / self.imax, 1.0) * R * 0.9
            self._arrow(qp, cx, cy, iang, L, QColor(S.GREEN), 3, "I")

        # 전압 공간벡터 (스틸): 점선 원(=Vmax 한계)과 함께
        qp.setPen(QPen(QColor(S.STEEL_LT), 1, Qt.PenStyle.DotLine))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        qp.drawEllipse(QPointF(cx, cy), R * 0.9, R * 0.9)
        vmag = math.hypot(self.valpha, self.vbeta)
        if vmag > 1e-4:
            vang = math.atan2(self.vbeta, self.valpha)
            L = min(vmag / self.vmax, 1.0) * R * 0.9
            self._arrow(qp, cx, cy, vang, L, QColor(S.STEEL), 2, "V")

        # 중심점
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QBrush(QColor(S.INK)))
        qp.drawEllipse(QPointF(cx, cy), 4, 4)
        qp.end()
