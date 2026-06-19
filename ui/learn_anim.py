# -*- coding: utf-8 -*-
"""학습 탭용 개념 애니메이션 패널.
문서(00~04)를 고르면 그 주제에 맞는 움직이는 그림을 보여준다.
QTextBrowser는 애니메이션을 못 하므로 별도 QWidget + QTimer 로 직접 그린다.
"""
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPainterPath
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from . import style as S


class ConceptAnim(QWidget):
    CAPTIONS = {
        "00": "전체 흐름:  배터리(DC) → 스위칭으로 잘게 쪼갬 → 3상 → 모터 회전",
        "01": "인터럽트:  평소 메인 실행 → 알람! → ISR(제어 계산) → 복귀  (정확한 박자)",
        "02": "PWM:  삼각파가 기준선(CMP)보다 아래면 켬.  기준선 높이 = 듀티 = 평균전압",
        "03": "ADC:  출렁이는 신호를 일정 간격으로 콕 집어 → 가장 가까운 계단값(숫자)으로",
        "04": "FOC:  회전자(자석)와 함께 도는 d·q축.  q축 전류(초록)가 힘(토크)을 만든다",
    }

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(210)
        self.topic = "00"
        self.frame = 0
        self.timer = QTimer(self)
        self.timer.setInterval(33)          # ~30 fps
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def set_topic(self, key):
        self.topic = key if key in self.CAPTIONS else "00"
        self.frame = 0
        self.update()

    def _tick(self):
        self.frame += 1
        self.update()

    # ---------- 공통 헬퍼 ----------
    def _arrow(self, qp, x1, y1, x2, y2, color, w=2):
        qp.setPen(QPen(color, w))
        qp.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        ang = math.atan2(y2 - y1, x2 - x1)
        h = 7
        poly = QPolygonF([
            QPointF(x2, y2),
            QPointF(x2 - h * math.cos(ang - 0.5), y2 - h * math.sin(ang - 0.5)),
            QPointF(x2 - h * math.cos(ang + 0.5), y2 - h * math.sin(ang + 0.5)),
        ])
        qp.setBrush(QBrush(color)); qp.setPen(Qt.PenStyle.NoPen)
        qp.drawPolygon(poly)

    def _text(self, qp, x, y, s, color=None, size=10, bold=False, center=False):
        qp.setPen(QPen(QColor(color or S.INK)))
        f = QFont(S.FONT_UI, size, QFont.Weight.Bold if bold else QFont.Weight.Normal)
        qp.setFont(f)
        if center:
            qp.drawText(QRectF(x - 120, y - 10, 240, 20),
                        Qt.AlignmentFlag.AlignCenter, s)
        else:
            qp.drawText(QPointF(x, y), s)

    # ---------- 그리기 ----------
    def paintEvent(self, _):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        qp.fillRect(self.rect(), QColor("#fbfcfe"))
        qp.setPen(QPen(QColor(S.GRID)))
        qp.drawRect(0, 0, self.width() - 1, self.height() - 1)

        area = QRectF(0, 0, self.width(), self.height() - 26)
        {"00": self._draw_overview, "01": self._draw_interrupt,
         "02": self._draw_pwm, "03": self._draw_adc,
         "04": self._draw_foc}.get(self.topic, self._draw_overview)(qp, area)

        # 캡션 (하단)
        qp.fillRect(QRectF(0, self.height() - 26, self.width(), 26), QColor("#eef1f5"))
        self._text(qp, 12, self.height() - 9, self.CAPTIONS.get(self.topic, ""),
                   S.STEEL, 10, True)
        qp.end()

    # === 00. 전체 흐름 ===
    def _draw_overview(self, qp, a):
        cy = a.center().y()
        w = a.width()
        # 배터리
        bx = w * 0.10
        qp.setBrush(QBrush(QColor("#3b6fa0"))); qp.setPen(Qt.PenStyle.NoPen)
        qp.drawRoundedRect(QRectF(bx - 34, cy - 26, 68, 52), 6, 6)
        self._text(qp, bx, cy + 4, "배터리", "white", 10, True, True)
        self._text(qp, bx, cy + 40, "DC 일정", S.MUTED, 9, False, True)

        # 스위치(깜빡임 = 쪼갬)
        sx = w * 0.37
        on = (self.frame // 6) % 2 == 0
        qp.setBrush(QBrush(QColor(S.AMBER if on else "#d8d8d8")))
        qp.drawRoundedRect(QRectF(sx - 36, cy - 26, 72, 52), 6, 6)
        self._text(qp, sx, cy + 4, "스위칭", "white" if on else S.MUTED, 10, True, True)
        self._text(qp, sx, cy + 40, "잘게 쪼갬(PWM)", S.MUTED, 9, False, True)

        # 모터(회전)
        mx = w * 0.74
        ang = self.frame * 0.12
        qp.save(); qp.translate(mx, cy)
        qp.setBrush(QBrush(QColor("#eef1f5"))); qp.setPen(QPen(QColor(S.GRID), 2))
        qp.drawEllipse(QPointF(0, 0), 30, 30)
        qp.rotate(-math.degrees(ang))
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QBrush(QColor("#d1495b")))
        qp.drawPie(QRectF(-22, -22, 44, 44), -90 * 16, 180 * 16)
        qp.setBrush(QBrush(QColor("#3b6fa0")))
        qp.drawPie(QRectF(-22, -22, 44, 44), 90 * 16, 180 * 16)
        qp.restore()
        self._text(qp, mx, cy + 48, "모터 회전", S.MUTED, 9, False, True)

        # 화살표
        self._arrow(qp, bx + 36, cy, sx - 40, cy, QColor(S.RED), 3)
        self._arrow(qp, sx + 40, cy, mx - 34, cy, QColor(S.STEEL), 3)
        self._text(qp, (bx + sx) / 2, cy - 16, "전력", S.RED, 9, False, True)
        self._text(qp, (sx + mx) / 2, cy - 16, "3상 교류", S.STEEL, 9, False, True)

    # === 01. 인터럽트 타임라인 ===
    def _draw_interrupt(self, qp, a):
        w = a.width()
        x0, x1 = 40, w - 40
        y_main = a.center().y() - 30
        y_isr = a.center().y() + 36
        # 레인 배경
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QBrush(QColor("#eef4fb")))
        qp.drawRoundedRect(QRectF(x0, y_main - 16, x1 - x0, 32), 6, 6)
        qp.setBrush(QBrush(QColor("#fbf4e8")))
        qp.drawRoundedRect(QRectF(x0, y_isr - 16, x1 - x0, 32), 6, 6)
        self._text(qp, x0 + 8, y_main + 5, "메인 코드", S.STEEL, 10, True)
        self._text(qp, x0 + 8, y_isr + 5, "ISR (제어 계산)", S.AMBER, 10, True)

        period = 90
        p = (self.frame % period) / period       # 0~1
        # 진행 점 위치
        if p < 0.45:                              # 메인 실행
            x = x0 + (x1 - x0) * (p / 0.45) * 0.5
            y = y_main; lane = "main"
        elif p < 0.75:                            # ISR 처리
            x = x0 + (x1 - x0) * 0.5
            y = y_isr; lane = "isr"
        else:                                     # 메인 복귀
            x = x0 + (x1 - x0) * (0.5 + (p - 0.75) / 0.25 * 0.5)
            y = y_main; lane = "main"
        # ISR 진입/복귀 화살표
        midx = x0 + (x1 - x0) * 0.5
        if 0.4 <= p < 0.8:
            self._arrow(qp, midx, y_main + 16, midx, y_isr - 16,
                        QColor(S.RED), 2)
        if 0.45 <= p < 0.5:
            self._text(qp, midx, y_main - 26, "⚡ 인터럽트!", S.RED, 11, True, True)
        # 진행 점
        qp.setBrush(QBrush(QColor(S.GREEN if lane == "main" else S.AMBER)))
        qp.setPen(Qt.PenStyle.NoPen)
        qp.drawEllipse(QPointF(x, y), 9, 9)

    # === 02. PWM 파형 ===
    def _draw_pwm(self, qp, a):
        w = a.width()
        x0, x1 = 50, w - 20
        top = a.top() + 16
        midy = a.center().y() - 6
        amp = 42
        # 듀티(기준선)를 천천히 0.3~0.8 사이로
        duty = 0.55 + 0.25 * math.sin(self.frame * 0.03)
        cmp_y = midy - (duty - 0.5) * 2 * amp     # 기준선 y (높을수록 듀티↑)
        scroll = self.frame * 4
        period = 80
        # 삼각파 + 출력 계산
        carrier = QPainterPath(); out = QPainterPath()
        out_y0 = a.bottom() - 30
        first = True
        for i in range(int(x1 - x0)):
            x = x0 + i
            ph = ((i + scroll) % period) / period      # 0~1
            tri = 1 - abs(2 * ph - 1)                  # 0~1~0 삼각
            cy = midy + (0.5 - tri) * 2 * amp          # 화면좌표(위가 작음)
            duty_level = 1 - duty                      # tri 비교용
            high = tri < duty
            oy = out_y0 - (26 if high else 0)
            if first:
                carrier.moveTo(x, cy); out.moveTo(x, oy); first = False
            else:
                carrier.lineTo(x, cy); out.lineTo(x, oy)
        # 기준선(CMP)
        qp.setPen(QPen(QColor(S.RED), 2, Qt.PenStyle.DashLine))
        qp.drawLine(QPointF(x0, cmp_y), QPointF(x1, cmp_y))
        self._text(qp, x0 - 44, cmp_y + 4, "CMP", S.RED, 9, True)
        # 삼각파
        qp.setPen(QPen(QColor(S.STEEL), 2)); qp.drawPath(carrier)
        self._text(qp, x0 - 44, top + 10, "삼각파", S.STEEL, 9, True)
        # 출력
        qp.setPen(QPen(QColor(S.GREEN), 2)); qp.drawPath(out)
        self._text(qp, x0 - 44, out_y0 - 8, "출력", S.GREEN, 9, True)
        self._text(qp, x1 - 96, top + 10, f"듀티 ≈ {duty*100:4.0f}%", S.AMBER, 11, True)

    # === 03. ADC 샘플링 ===
    def _draw_adc(self, qp, a):
        w = a.width()
        x0, x1 = 40, w - 20
        midy = a.center().y()
        amp = 48
        # 양자화 계단(가로선)
        levels = 8
        qp.setPen(QPen(QColor(S.GRID), 1, Qt.PenStyle.DotLine))
        for k in range(levels + 1):
            y = midy - amp + (2 * amp) * k / levels
            qp.drawLine(QPointF(x0, y), QPointF(x1, y))
        # 사인파
        path = QPainterPath(); first = True
        phase = self.frame * 0.05
        def sine_y(x):
            t = (x - x0) / (x1 - x0)
            return midy - amp * math.sin(2 * math.pi * (t * 1.5) - phase)
        for i in range(int(x1 - x0)):
            x = x0 + i; y = sine_y(x)
            if first: path.moveTo(x, y); first = False
            else: path.lineTo(x, y)
        qp.setPen(QPen(QColor(S.STEEL_LT), 2)); qp.drawPath(path)
        # 샘플 점들 (일정 간격) + 양자화 스냅
        nsamp = 12
        for s in range(nsamp):
            x = x0 + (x1 - x0) * s / (nsamp - 1)
            y = sine_y(x)
            # 가장 가까운 계단으로 스냅
            rel = (y - (midy - amp)) / (2 * amp) * levels
            ql = round(rel)
            qy = midy - amp + (2 * amp) * ql / levels
            qp.setPen(QPen(QColor(S.GRID), 1))
            qp.drawLine(QPointF(x, midy + amp + 4), QPointF(x, qy))
            qp.setBrush(QBrush(QColor(S.AMBER))); qp.setPen(Qt.PenStyle.NoPen)
            qp.drawRect(QRectF(x - 3, qy - 3, 6, 6))
        # 움직이는 '현재 샘플' 강조
        cs = (self.frame // 4) % nsamp
        xx = x0 + (x1 - x0) * cs / (nsamp - 1)
        yy = sine_y(xx)
        rel = (yy - (midy - amp)) / (2 * amp) * levels
        num = max(0, min(levels, round(rel)))
        qp.setBrush(QBrush(QColor(S.GREEN))); qp.setPen(Qt.PenStyle.NoPen)
        qp.drawEllipse(QPointF(xx, yy), 6, 6)
        self._text(qp, x1 - 92, a.top() + 14, f"디지털값 = {levels-num}", S.GREEN, 11, True)

    # === 04. FOC 회전 dq ===
    def _draw_foc(self, qp, a):
        cx, cy = a.center().x(), a.center().y()
        R = min(a.width(), a.height()) * 0.40
        th = self.frame * 0.05
        # 고정자
        qp.setPen(QPen(QColor(S.GRID), 2)); qp.setBrush(QBrush(QColor("#eef1f5")))
        qp.drawEllipse(QPointF(cx, cy), R, R)
        # 회전자 자석
        qp.save(); qp.translate(cx, cy); qp.rotate(-math.degrees(th))
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QBrush(QColor("#d1495b")))
        qp.drawPie(QRectF(-R*0.55, -R*0.55, R*1.1, R*1.1), -90*16, 180*16)
        qp.setBrush(QBrush(QColor("#3b6fa0")))
        qp.drawPie(QRectF(-R*0.55, -R*0.55, R*1.1, R*1.1), 90*16, 180*16)
        qp.restore()
        # dq 축 + 전류벡터(q축)
        def arrow(angle, length, color, w, label):
            x = cx + length*math.cos(angle); y = cy - length*math.sin(angle)
            self._arrow(qp, cx, cy, x, y, color, w)
            self._text(qp, x+4, y-4, label, color, 10, True)
        qp.setPen(QPen(QColor(S.RED), 2, Qt.PenStyle.DashLine))
        qp.drawLine(QPointF(cx, cy),
                    QPointF(cx + R*0.95*math.cos(th), cy - R*0.95*math.sin(th)))
        self._text(qp, cx + R*0.95*math.cos(th)+4, cy - R*0.95*math.sin(th), "d", S.RED, 10, True)
        arrow(th + math.pi/2, R*0.9, QColor(S.AMBER), 2, "q")
        arrow(th + math.pi/2, R*0.78, QColor(S.GREEN), 4, "I (토크)")
        self._text(qp, cx, a.bottom()-6, "→ q축 전류 Iq 가 힘을 만든다", S.GREEN, 10, True, True)
