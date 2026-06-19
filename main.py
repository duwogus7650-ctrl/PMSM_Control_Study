# -*- coding: utf-8 -*-
"""
PMSM 제어 + 보드 학습툴 (초보자용)
==================================
0. 학습 / 1. 제어 시뮬레이터 / 2. 보드·소자 / 3. 통신  + 하단 'AI 강사' 음성 가이드.
실행:  python main.py
"""
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QLabel,
                             QWidget, QVBoxLayout)
from PyQt6.QtCore import Qt

from ui import style as S
from ui.sim_tab import SimTab
from ui.learn_tab import LearnTab, DOCS
from ui.board_tab import BoardTab
from ui.comm_tab import CommTab
from ui.board_data import COMPONENTS
from ui.guide import GuideBar
from ui.guide_scripts import LEVEL_NARRATION, TOUR, SIM_DEMO


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PMSM 제어 · 보드 학습툴  —  AI 강사 음성 가이드 포함")
        self.resize(1340, 900)

        tabs = QTabWidget()
        self.tabs = tabs
        learn = LearnTab(goto_sim=lambda: tabs.setCurrentIndex(1))
        sim = SimTab()
        board = BoardTab()
        comm = CommTab()
        tabs.addTab(learn, "0. 학습")
        tabs.addTab(sim, "1. 제어 시뮬레이터")
        tabs.addTab(board, "2. 보드 · 소자 구조")
        tabs.addTab(comm, "3. 통신 방식")

        lessons = self._build_lessons(tabs, learn, sim, board, comm)
        self.guide = GuideBar(lessons)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(tabs, 1)
        lay.addWidget(self.guide)
        self.setCentralWidget(central)

    # ---------------- 강의 구성 ----------------
    def _build_lessons(self, tabs, learn, sim, board, comm):
        lessons = []

        # 1) 전체 둘러보기
        tour_do = [None,
                   lambda: tabs.setCurrentIndex(0),
                   lambda: tabs.setCurrentIndex(1),
                   lambda: tabs.setCurrentIndex(2),
                   lambda: tabs.setCurrentIndex(3),
                   lambda: tabs.setCurrentIndex(0)]
        lessons.append(dict(name="🧭 전체 둘러보기 (처음이라면 여기)",
                            steps=[dict(say=t, do=d) for t, d in zip(TOUR, tour_do)]))

        # 2) 시뮬레이터 실습
        def ensure_run():
            if not sim.running:
                sim._toggle()
        sim_do = [
            lambda: tabs.setCurrentIndex(1),
            lambda: (tabs.setCurrentIndex(1), sim.mode_btns["VECTOR"].setChecked(True),
                     sim.s_load.sld.setValue(0), sim.s_id.sld.setValue(0),
                     sim.s_iq.sld.setValue(10), ensure_run()),
            lambda: sim.s_iq.sld.setValue(30),
            lambda: sim.s_load.sld.setValue(60),
            lambda: (sim.mode_btns["SPEED"].setChecked(True),
                     sim.s_speed.sld.setValue(30), sim.s_load.sld.setValue(60)),
            None,
        ]
        lessons.append(dict(name="🎮 시뮬레이터 실습 (직접 돌려보기)",
                            steps=[dict(say=t, do=d) for t, d in zip(SIM_DEMO, sim_do)]))

        # 3) 보드 구조 둘러보기 (블록을 하나씩 짚으며)
        order = ["batt", "bulk", "bridge", "gate", "shunt",
                 "motor", "mcu", "enc", "can"]
        bsteps = [dict(say="보드 구조 탭입니다. 블록을 하나씩 짚으며 설명할게요. "
                           "오른쪽 실제 사진은 클릭하면 크게 볼 수 있어요.",
                       do=lambda: tabs.setCurrentIndex(2))]
        for k in order:
            c = COMPONENTS[k]
            bsteps.append(dict(
                say=f"{c['title']}. {c['short']}.",
                do=(lambda kk=k: (tabs.setCurrentIndex(2), board._show(kk)))))
        lessons.append(dict(name="🔧 보드 · 소자 구조 둘러보기", steps=bsteps))

        # 4) 통신 비교
        comm_say = [
            ("table", "통신이 왜 필요한지부터 봅니다. 모터 보드는 상위 제어기와 "
                      "명령과 상태를 주고받아야 해요."),
            ("uart", "UART는 가장 단순한 1대1 시리얼입니다. 개발 중 디버깅과 로그에 좋아요."),
            ("spi", "SPI는 보드 안 칩끼리의 고속 통신이에요. 엔코더 각도를 매 주기 빠르게 읽습니다."),
            ("i2c", "I2C는 선 두 개로 여러 저속 센서를 붙일 때 씁니다."),
            ("can", "CAN은 노이즈에 강하고 여러 장치를 한 버스에 묶기 좋아, "
                    "모터와 상위 제어기 사이 메인 통신으로 권장됩니다."),
            ("pick", "정리하면, 엔코더는 SPI, 상위 제어는 CAN, 개발은 UART. "
                     "연결마다 알맞은 걸 씁니다."),
        ]
        csteps = [dict(say=s, do=(lambda kk=k: (tabs.setCurrentIndex(3), comm._show(kk))))
                  for k, s in comm_say]
        lessons.append(dict(name="📡 통신 방식 비교", steps=csteps))

        # 5) 학습자료 레벨별 강의 (문서마다 레벨 1→10)
        def mk_step(fn, lvl, text):
            def do():
                tabs.setCurrentIndex(0)
                if learn.cur_file != fn:
                    learn._open(fn)
                learn.slider.setValue(lvl)
            return dict(say=text, do=do)

        for num, name, fn in DOCS:
            narr = LEVEL_NARRATION.get(num)
            if not narr:
                continue
            steps = [mk_step(fn, i + 1, narr[i]) for i in range(len(narr))]
            lessons.append(dict(name=f"📚 학습 {num}: {name} — 레벨 1→10",
                                steps=steps))

        return lessons


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(S.QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
