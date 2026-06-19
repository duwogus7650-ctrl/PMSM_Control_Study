# -*- coding: utf-8 -*-
"""AI 강사 음성 가이드 엔진.
- Narrator: Windows 한국어 음성(SAPI, Heami)으로 말한다.
- GuideBar: ▶/⏸/⏭/⏮ + 강의 선택 + 자막. 강의 step을 따라가며 화면을 조작하고
  음성으로 설명하고, 말이 끝나면 자동으로 다음 step으로 넘어간다.

step = dict(say="할 말", do=callable_or_None)
  do()는 탭 전환·슬라이더 이동·블록 선택 등 '프로그램 조작'을 수행한다.
lesson = dict(name="강의명", steps=[step, ...])
"""
import xml.sax.saxutils as _su
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from . import style as S

try:
    import win32com.client as _w
    _HAS_SAPI = True
except Exception:
    _HAS_SAPI = False


class Narrator:
    """SAPI 한국어 음성 래퍼. 음성 없으면 조용히 무시(자막만)."""
    def __init__(self):
        self.voice = None
        self.ok = False
        if not _HAS_SAPI:
            return
        try:
            self.voice = _w.Dispatch("SAPI.SpVoice")
            for t in self.voice.GetVoices():
                if "Korean" in t.GetDescription():
                    self.voice.Voice = t
                    break
            self.voice.Rate = 2           # 일타 강사처럼 빠르고 활기차게
            self.voice.Volume = 100       # 음량 최대
            self.ok = True
        except Exception:
            self.voice = None
            self.ok = False

    def speak(self, text):
        if not self.ok:
            return
        try:
            # 피치를 살짝 올려 생기있게. XML 모드라 특수문자는 이스케이프.
            safe = _su.escape(text)
            xml = f'<pitch absmiddle="3">{safe}</pitch>'
            # 1=Async, 2=PurgeBeforeSpeak, 8=IsXML  → 11
            self.voice.Speak(xml, 11)
        except Exception:
            try:
                self.voice.Speak(text, 3)   # XML 실패 시 일반 모드 폴백
            except Exception:
                pass

    def stop(self):
        if not self.ok:
            return
        try:
            self.voice.Speak("", 3)       # purge
        except Exception:
            pass

    def busy(self):
        if not self.ok:
            return False
        try:
            return self.voice.Status.RunningState == 2   # 2 = 말하는 중
        except Exception:
            return False


class GuideBar(QWidget):
    """하단 강의 컨트롤 바 + 자막."""
    def __init__(self, lessons):
        super().__init__()
        self.lessons = lessons            # [{name, steps}]
        self.narrator = Narrator()
        self.steps = []
        self.idx = -1
        self.playing = False
        self._seen = False                # 현재 step에서 음성이 시작된 적 있나
        self._ticks = 0                   # 현재 step 경과 tick(150ms)
        self._build()

        self.timer = QTimer(self)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _build(self):
        self.setFixedHeight(78)
        self.setStyleSheet(
            f"background:{S.INK}; border-top:2px solid {S.AMBER};")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 6, 12, 6)
        root.setSpacing(4)

        top = QHBoxLayout(); top.setSpacing(8)
        tag = QLabel("🎓 AI 강사")
        tag.setStyleSheet(f"color:{S.AMBER}; font-weight:bold; font-size:14px;")
        top.addWidget(tag)

        self.combo = QComboBox()
        for L in self.lessons:
            self.combo.addItem(L["name"])
        self.combo.setStyleSheet(
            "QComboBox{background:white; padding:4px 8px; border-radius:4px;}")
        self.combo.setMinimumWidth(260)
        top.addWidget(self.combo)

        self.btn_play = QPushButton("▶ 강의 시작")
        self.btn_play.setObjectName("amber")
        self.btn_play.clicked.connect(self._toggle)
        self.btn_prev = QPushButton("⏮")
        self.btn_prev.clicked.connect(self.prev)
        self.btn_next = QPushButton("⏭")
        self.btn_next.clicked.connect(self.next)
        for b in (self.btn_play, self.btn_prev, self.btn_next):
            top.addWidget(b)

        self.chk_mute = QCheckBox("음소거")
        self.chk_mute.setStyleSheet("color:#cdd8e4;")
        if not self.narrator.ok:
            self.chk_mute.setChecked(True)
            self.chk_mute.setText("음소거 (음성 엔진 없음)")
            self.chk_mute.setEnabled(False)
        top.addWidget(self.chk_mute)
        top.addStretch(1)
        self.lbl_prog = QLabel("")
        self.lbl_prog.setStyleSheet("color:#9fb3c8;")
        top.addWidget(self.lbl_prog)
        root.addLayout(top)

        self.subtitle = QLabel("강의를 선택하고 ▶ 를 누르세요. AI 강사가 화면을 "
                               "직접 조작하며 한국어로 설명합니다.")
        self.subtitle.setWordWrap(True)
        self.subtitle.setStyleSheet("color:white; font-size:13px;")
        root.addWidget(self.subtitle)

    # ---------- 동작 ----------
    def _toggle(self):
        if self.playing:
            self.pause()
        else:
            self.start()

    def start(self):
        if self.idx < 0:
            self.steps = self.lessons[self.combo.currentIndex()]["steps"]
            self.idx = -1
            self.next()
        self.playing = True
        self.btn_play.setText("⏸ 일시정지")

    def pause(self):
        self.playing = False
        self.narrator.stop()
        self.btn_play.setText("▶ 이어서")

    def _enter(self, i):
        self.idx = i
        step = self.steps[i]
        self._seen = False
        self._ticks = 0
        do = step.get("do")
        if do:
            try:
                do()
            except Exception as e:
                print("guide do() error:", e)
        say = step.get("say", "")
        self.subtitle.setText(say)
        self.lbl_prog.setText(f"{i+1} / {len(self.steps)}")
        if not self.chk_mute.isChecked():
            self.narrator.speak(say)

    def next(self):
        if not self.steps:
            self.steps = self.lessons[self.combo.currentIndex()]["steps"]
            self.idx = -1
        if self.idx + 1 < len(self.steps):
            self._enter(self.idx + 1)
        else:
            self.pause()
            self.subtitle.setText("강의가 끝났습니다. 다른 강의를 골라 보세요!")
            self.idx = -1
            self.steps = []

    def prev(self):
        if self.steps and self.idx > 0:
            self._enter(self.idx - 1)

    def _reading_ticks(self, text):
        # 음소거 시 자막 읽을 시간 추정 (150ms tick 기준)
        return max(20, int(len(text) * 0.42))

    def _tick(self):
        if not self.playing or self.idx < 0 or not self.steps:
            return
        self._ticks += 1
        if self.chk_mute.isChecked():
            if self._ticks >= self._reading_ticks(self.steps[self.idx].get("say", "")):
                self.next()
            return
        # 음성 모드: 말이 끝나면(또는 시작조차 안 하면 유예 후) 다음
        if self.narrator.busy():
            self._seen = True
            return
        if self._seen or self._ticks >= 14:      # 끝남, 또는 ~2.1s 내 미시작
            self.next()
