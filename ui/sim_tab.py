# -*- coding: utf-8 -*-
"""탭 1: PMSM 제어 시뮬레이터. V/F -> I/F -> Vector -> Speed 를 직접 돌려본다."""
import math
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QSlider, QFrame
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg

from core.motor import PMSM, MotorParams, clarke, TWO_PI
from . import style as S
from .motor_view import MotorView

pg.setConfigOptions(antialias=True, background=S.PANEL, foreground=S.INK)

MODE_INFO = {
    "VF": ("V/F 제어 (개루프)",
           "주파수 지령에 비례해 전압을 키워 모터를 억지로 돌립니다. 가장 원시적·"
           "제어 없음. 인버터가 3상 전압을 제대로 내는지 확인하는 1단계."),
    "IF": ("I/F 제어 (전류 개루프)",
           "전류 크기는 제어하되 각도는 지령으로 천천히 돌립니다. 회전자가 고정자 "
           "자속에 끌려옴. 기동·저속 구동 검증용 2단계."),
    "VECTOR": ("Vector 제어 / FOC (전류 폐루프)",
               "★핵심. 실제 회전자 각도로 전류를 d(자속)·q(토크)로 분리 제어. "
               "Iq가 토크를 만든다. 3단계."),
    "SPEED": ("Speed 제어 (이중 루프)",
              "바깥 속도제어기가 Iq 지령을 만들고, 안쪽 전류제어기가 추종. "
              "지령 속도를 정확히 맞추는 4단계."),
}


class Slider(QWidget):
    """라벨 + 슬라이더 + 값표시 묶음. 실수값을 정수 슬라이더로 다룸."""
    def __init__(self, name, unit, vmin, vmax, vinit, scale=1.0, color=S.STEEL):
        super().__init__()
        self.scale = scale
        self.unit = unit
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(2)
        top = QHBoxLayout()
        self.lbl = QLabel(name)
        self.val = QLabel()
        self.val.setObjectName("mono")
        self.val.setStyleSheet(f"color:{color};")
        self.val.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(self.lbl)
        top.addWidget(self.val)
        lay.addLayout(top)
        self.sld = QSlider(Qt.Orientation.Horizontal)
        self.sld.setMinimum(int(vmin / scale))
        self.sld.setMaximum(int(vmax / scale))
        self.sld.setValue(int(vinit / scale))
        self.sld.valueChanged.connect(self._show)
        lay.addWidget(self.sld)
        self._show()

    def _show(self):
        self.val.setText(f"{self.value():+.2f} {self.unit}")

    def value(self):
        return self.sld.value() * self.scale

    def set_enabled(self, en):
        self.sld.setEnabled(en)
        self.lbl.setStyleSheet("" if en else f"color:{S.MUTED};")


class SimTab(QWidget):
    def __init__(self):
        super().__init__()
        self.motor = PMSM(MotorParams())
        self.DT = 1e-5                 # 내부 적분 스텝 [s]
        self.sim_ms_per_frame = 4.0    # 한 프레임당 흘려보낼 시뮬 시간 [ms]
        self.sim_time = 0.0
        self.running = False

        # 그래프 버퍼
        N = 1600
        self.buf_t = deque(maxlen=N)
        self.buf = {k: deque(maxlen=N) for k in
                    ("ia", "ib", "ic", "id", "iq", "idr", "iqr", "spd", "spdr")}

        self._build()
        self.timer = QTimer(self)
        self.timer.setInterval(25)     # 40 fps
        self.timer.timeout.connect(self._on_frame)
        self._apply_mode()

    # ---------------- UI 구성 ----------------
    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- 왼쪽: 컨트롤 ---
        left = QVBoxLayout()
        left.setSpacing(10)

        # 모드 선택
        gb_mode = QGroupBox("제어 단계 선택")
        ml = QVBoxLayout(gb_mode)
        self.mode_group = QButtonGroup(self)
        self.mode_btns = {}
        for key in PMSM.MODES:
            rb = QRadioButton(MODE_INFO[key][0])
            self.mode_btns[key] = rb
            self.mode_group.addButton(rb)
            ml.addWidget(rb)
            rb.toggled.connect(self._apply_mode)
        self.mode_desc = QLabel()
        self.mode_desc.setObjectName("hint")
        self.mode_desc.setWordWrap(True)
        ml.addWidget(self.mode_desc)
        left.addWidget(gb_mode)

        # 지령 슬라이더
        gb_cmd = QGroupBox("지령 / 부하")
        cl = QVBoxLayout(gb_cmd)
        self.s_speed = Slider("속도 지령 ω*", "rpm", -1000, 1000, 300, 10, S.C_SPEED)
        self.s_id = Slider("Id 지령 (자속전류)", "A", -3, 3, 0, 0.1, S.C_ID)
        self.s_iq = Slider("Iq 지령 (토크전류)", "A", -5, 5, 1, 0.1, S.C_IQ)
        self.s_load = Slider("부하 토크 TL", "mN·m", -100, 100, 0, 1, S.RED)
        for s in (self.s_speed, self.s_id, self.s_iq, self.s_load):
            cl.addWidget(s)
        left.addWidget(gb_cmd)

        # 튜닝
        gb_set = QGroupBox("표시 설정")
        sl = QVBoxLayout(gb_set)
        self.s_slow = Slider("시뮬 배속 (작을수록 느림)", "ms/frame", 1, 20, 4, 1, S.MUTED)
        sl.addWidget(self.s_slow)
        left.addWidget(gb_set)

        # 버튼
        btns = QHBoxLayout()
        self.btn_run = QPushButton("▶ 시작")
        self.btn_run.clicked.connect(self._toggle)
        self.btn_reset = QPushButton("↺ 리셋")
        self.btn_reset.setObjectName("ghost")
        self.btn_reset.clicked.connect(self._reset)
        btns.addWidget(self.btn_run)
        btns.addWidget(self.btn_reset)
        left.addLayout(btns)
        left.addStretch(1)

        lw = QWidget()
        lw.setLayout(left)
        lw.setFixedWidth(290)
        root.addWidget(lw)

        # --- 가운데: 모터 뷰 + 수치 ---
        mid = QVBoxLayout()
        mid.setSpacing(8)
        title = QLabel("모터 단면 & 공간벡터 (전기각 기준)")
        title.setObjectName("h2")
        mid.addWidget(title)
        self.motor_view = MotorView()
        mid.addWidget(self.motor_view, 1)

        legend = QLabel(
            "<span style='color:#d1495b'>━ d축(자석)</span>  "
            "<span style='color:#e0922f'>━ q축(토크)</span>  "
            "<span style='color:#2e9e6b'>→ 전류벡터</span>  "
            "<span style='color:#2f5f8f'>→ 전압벡터</span>  "
            "<span style='color:#5b86b3'>┈ Vmax 한계</span>")
        legend.setObjectName("hint")
        mid.addWidget(legend)

        self.readout = QLabel()
        self.readout.setObjectName("mono")
        self.readout.setStyleSheet(
            f"background:{S.INK}; color:#dfe8f2; padding:8px; border-radius:4px;")
        self.readout.setTextFormat(Qt.TextFormat.RichText)
        mid.addWidget(self.readout)

        mw = QWidget()
        mw.setLayout(mid)
        mw.setFixedWidth(400)
        root.addWidget(mw)

        # --- 오른쪽: 그래프 ---
        right = QVBoxLayout()
        right.setSpacing(6)
        self.p_abc = self._plot("3상 전류 [A]", "ia/ib/ic")
        self.p_dq = self._plot("dq 전류 [A]  (실선=측정, 점선=지령)", "id/iq")
        self.p_spd = self._plot("속도 [rpm]  (실선=측정, 점선=지령)", "rpm")
        self.c_ia = self.p_abc.plot(pen=pg.mkPen(S.C_IA, width=2), name="ia")
        self.c_ib = self.p_abc.plot(pen=pg.mkPen(S.C_IB, width=2), name="ib")
        self.c_ic = self.p_abc.plot(pen=pg.mkPen(S.C_IC, width=2), name="ic")
        self.c_id = self.p_dq.plot(pen=pg.mkPen(S.C_ID, width=2), name="id")
        self.c_iq = self.p_dq.plot(pen=pg.mkPen(S.C_IQ, width=2), name="iq")
        self.c_idr = self.p_dq.plot(pen=pg.mkPen(S.C_ID, width=1, style=Qt.PenStyle.DashLine))
        self.c_iqr = self.p_dq.plot(pen=pg.mkPen(S.C_IQ, width=1, style=Qt.PenStyle.DashLine))
        self.c_spd = self.p_spd.plot(pen=pg.mkPen(S.C_SPEED, width=2))
        self.c_spdr = self.p_spd.plot(pen=pg.mkPen(S.AMBER, width=1, style=Qt.PenStyle.DashLine))
        for p in (self.p_abc, self.p_dq, self.p_spd):
            right.addWidget(p)
        root.addLayout(right, 1)

        # 모든 위젯 생성이 끝난 뒤 초기 모드 선택 (슬라이더 활성화 처리 포함)
        self.mode_btns["VECTOR"].setChecked(True)

    def _plot(self, title, ylabel):
        p = pg.PlotWidget(title=title)
        p.showGrid(x=True, y=True, alpha=0.25)
        p.setLabel("bottom", "시간", units="s")
        p.setLabel("left", ylabel)
        p.setMinimumHeight(150)
        return p

    # ---------------- 동작 ----------------
    def _apply_mode(self):
        for key, rb in self.mode_btns.items():
            if rb.isChecked():
                self.motor.mode = key
                self.mode_desc.setText(MODE_INFO[key][1])
                break
        m = self.motor.mode
        # 슬라이더 활성/비활성: 모드별로 의미 있는 것만
        self.s_speed.set_enabled(m in ("VF", "IF", "SPEED"))
        self.s_id.set_enabled(m in ("IF", "VECTOR", "SPEED"))
        self.s_iq.set_enabled(m == "VECTOR")
        self.motor.pi_id.reset()
        self.motor.pi_iq.reset()
        self.motor.pi_spd.reset()

    def _toggle(self):
        self.running = not self.running
        if self.running:
            self.timer.start()
            self.btn_run.setText("⏸ 일시정지")
            self.btn_run.setObjectName("amber")
        else:
            self.timer.stop()
            self.btn_run.setText("▶ 시작")
            self.btn_run.setObjectName("")
        self.btn_run.style().unpolish(self.btn_run)
        self.btn_run.style().polish(self.btn_run)

    def _reset(self):
        self.motor.reset()
        self.sim_time = 0.0
        self.buf_t.clear()
        for d in self.buf.values():
            d.clear()
        self._refresh_view()
        self._refresh_plots()

    def _push_commands(self):
        self.motor.speed_ref_rpm = self.s_speed.value()
        self.motor.id_ref = self.s_id.value()
        self.motor.iq_ref = self.s_iq.value()
        self.motor.load_torque = self.s_load.value() / 1000.0  # mN·m -> N·m
        self.sim_ms_per_frame = self.s_slow.value()

    def _on_frame(self):
        self._push_commands()
        steps = max(1, int((self.sim_ms_per_frame * 1e-3) / self.DT))
        m = self.motor
        for _ in range(steps):
            m.step(self.DT)
            self.sim_time += self.DT
        # 샘플 1점 기록
        s = m.s
        self.buf_t.append(self.sim_time)
        self.buf["ia"].append(s.ia); self.buf["ib"].append(s.ib); self.buf["ic"].append(s.ic)
        self.buf["id"].append(s.id); self.buf["iq"].append(s.iq)
        self.buf["idr"].append(m.id_ref)
        self.buf["iqr"].append(m.iq_ref if m.mode == "VECTOR" else float("nan"))
        self.buf["spd"].append(m.speed_rpm)
        self.buf["spdr"].append(m.speed_ref_rpm if m.mode in ("VF", "IF", "SPEED")
                                else float("nan"))
        self._refresh_view()
        self._refresh_plots()

    def _refresh_view(self):
        s = self.motor.s
        ialpha, ibeta = clarke(s.ia, s.ib, s.ic)
        self.motor_view.update_state(
            s.theta_e, ialpha, ibeta, s.valpha, s.vbeta,
            self.motor.p.Vmax, 6.0)
        self.readout.setText(
            f"속도 ω : <b>{self.motor.speed_rpm:8.1f}</b> rpm<br>"
            f"토크 Te: <b>{s.Te*1000:8.2f}</b> mN·m<br>"
            f"id / iq: <b>{s.id:6.2f}</b> / <b>{s.iq:6.2f}</b> A<br>"
            f"전기각 θe: <b>{math.degrees(s.theta_e):7.1f}</b>°&nbsp;&nbsp;"
            f"|V|: <b>{math.hypot(s.valpha,s.vbeta):.2f}</b>/{self.motor.p.Vmax:.1f} V")

    def _refresh_plots(self):
        if not self.buf_t:
            return
        t = list(self.buf_t)
        self.c_ia.setData(t, list(self.buf["ia"]))
        self.c_ib.setData(t, list(self.buf["ib"]))
        self.c_ic.setData(t, list(self.buf["ic"]))
        self.c_id.setData(t, list(self.buf["id"]))
        self.c_iq.setData(t, list(self.buf["iq"]))
        self.c_idr.setData(t, list(self.buf["idr"]))
        self.c_iqr.setData(t, list(self.buf["iqr"]))
        self.c_spd.setData(t, list(self.buf["spd"]))
        self.c_spdr.setData(t, list(self.buf["spdr"]))
