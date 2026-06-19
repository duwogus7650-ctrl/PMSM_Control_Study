# -*- coding: utf-8 -*-
"""탭 0: 학습. 레벨 슬라이더(1~10)로 같은 주제를 점점 깊게 본다.
.md 파일 안에서 `<!--LV n-->` 마커로 구간 난이도를 표시하고,
슬라이더 값 이하 레벨의 구간만 누적해서 보여준다 (1=입문 … 10=연구)."""
import os
import re
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QTextBrowser, QLabel, QButtonGroup, QSlider, QFrame)
from PyQt6.QtCore import Qt
import markdown as md

from . import style as S
from .learn_anim import ConceptAnim

DOC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "학습자료")

DOCS = [
    ("00", "전체지도 + 용어사전", "00_전체지도_그리고_용어사전.md"),
    ("01", "Interrupt & GPIO", "01_Interrupt_GPIO.md"),
    ("02", "ePWM (전압 만들기)", "02_ePWM.md"),
    ("03", "ADC (숫자로 읽기)", "03_ADC.md"),
    ("04", "PMSM 제어 (종합)", "04_PMSM제어.md"),
]

LEVEL_NAMES = {
    1: "직관·비유 (입문)", 2: "기본 동작 원리", 3: "정량 관계(공식·단위)",
    4: "설정·레지스터", 5: "코드 수준", 6: "수치 계산 예시",
    7: "비이상 효과", 8: "수식 유도", 9: "설계·튜닝", 10: "연구/고급",
}

LV_RE = re.compile(r'<!--\s*LV\s*(\d+)\s*-->')

CSS = f"""
<style>
body {{ font-family:"{S.FONT_UI}"; color:{S.INK}; font-size:14px; line-height:1.6; }}
h1 {{ color:{S.INK}; font-size:22px; border-bottom:3px solid {S.STEEL}; padding-bottom:6px; }}
h2 {{ color:{S.STEEL}; font-size:18px; margin-top:22px; border-left:5px solid {S.STEEL}; padding-left:8px; }}
h3 {{ color:{S.INK}; font-size:15px; margin-top:16px; }}
table {{ border-collapse:collapse; margin:10px 0; }}
th {{ background:{S.STEEL}; color:white; padding:7px 10px; text-align:left; }}
td {{ border:1px solid {S.GRID}; padding:6px 10px; }}
tr:nth-child(even) td {{ background:#eef1f5; }}
code {{ font-family:"{S.FONT_MONO}"; background:#eef1f5; color:{S.INK}; padding:1px 5px; border-radius:3px; }}
pre {{ background:#eef2f7; color:{S.INK}; padding:12px; border-radius:5px;
      border-left:4px solid {S.STEEL_LT}; font-family:"{S.FONT_MONO}";
      font-size:13px; line-height:1.5; }}
pre code {{ background:transparent; color:{S.INK}; padding:0; }}
blockquote {{ border-left:4px solid {S.AMBER}; background:#fbf4e8; margin:10px 0; padding:8px 14px; color:#5a4a2e; }}
strong {{ color:{S.INK}; }}
hr {{ border:none; border-top:1px solid {S.GRID}; margin:18px 0; }}
a {{ color:{S.STEEL}; }}
ul, ol {{ margin:6px 0 6px 4px; }}
li {{ margin:3px 0; }}
.lvtag {{ display:inline-block; background:{S.AMBER}; color:white; font-size:11px;
        padding:2px 8px; border-radius:10px; }}
</style>
"""


def parse_levels(text):
    """텍스트를 (level, chunk) 목록으로. 첫 마커 이전은 LV1."""
    parts = LV_RE.split(text)        # [chunk0, lv1, chunk1, lv2, chunk2, ...]
    out = [(1, parts[0])]
    for i in range(1, len(parts), 2):
        lvl = int(parts[i])
        chunk = parts[i + 1] if i + 1 < len(parts) else ""
        out.append((lvl, chunk))
    return out


class LearnTab(QWidget):
    def __init__(self, goto_sim=None):
        super().__init__()
        self.goto_sim = goto_sim
        self.cur_file = DOCS[0][2]
        self.level = 1
        self.raw_cache = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # ===== 왼쪽: 목차 + 레벨 슬라이더 =====
        left = QVBoxLayout(); left.setSpacing(6)
        title = QLabel("학습자료"); title.setObjectName("h2")
        left.addWidget(title)
        guide = QLabel("00 → 01 → 02 → 03 → 04 순서 추천")
        guide.setObjectName("hint"); left.addWidget(guide)

        self.group = QButtonGroup(self)
        self.btns = []
        for num, name, fn in DOCS:
            b = QPushButton(f"{num}. {name}")
            b.setObjectName("ghost"); b.setCheckable(True)
            b.setStyleSheet("text-align:left; padding:9px 12px;")
            b.clicked.connect(lambda _, f=fn: self._open(f))
            self.group.addButton(b); self.btns.append(b)
            left.addWidget(b)

        # 레벨 슬라이더 박스
        left.addSpacing(10)
        lvbox = QFrame()
        lvbox.setStyleSheet(f"background:white; border:1px solid {S.GRID}; border-radius:6px;")
        lvl = QVBoxLayout(lvbox); lvl.setContentsMargins(10, 10, 10, 10)
        lvhead = QLabel("난이도 레벨"); lvhead.setObjectName("h2")
        lvl.addWidget(lvhead)
        self.lvl_label = QLabel(); self.lvl_label.setObjectName("mono")
        self.lvl_label.setWordWrap(True)
        lvl.addWidget(self.lvl_label)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1); self.slider.setMaximum(10); self.slider.setValue(1)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self._on_level)
        lvl.addWidget(self.slider)
        scale = QLabel("1 입문  ←———→  10 전문가")
        scale.setObjectName("hint"); lvl.addWidget(scale)
        left.addWidget(lvbox)

        left.addSpacing(10)
        go = QPushButton("▶ 시뮬레이터로 가서 직접 해보기")
        go.setObjectName("amber")
        go.clicked.connect(lambda: self.goto_sim() if self.goto_sim else None)
        left.addWidget(go)
        left.addStretch(1)
        lw = QWidget(); lw.setLayout(left); lw.setFixedWidth(250)
        root.addWidget(lw)

        # ===== 오른쪽: 애니메이션 + 본문 =====
        right = QVBoxLayout(); right.setSpacing(8)
        at = QLabel("📺 개념 애니메이션 (문서에 맞춰 자동 전환)")
        at.setObjectName("hint"); right.addWidget(at)
        self.anim = ConceptAnim(); right.addWidget(self.anim)
        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(False)
        self.view.setSearchPaths([DOC_DIR])   # media/ 이미지 상대경로 해석
        self.view.setStyleSheet("padding:6px 18px;")
        right.addWidget(self.view, 1)
        rw = QWidget(); rw.setLayout(right)
        root.addWidget(rw, 1)

        self.btns[0].setChecked(True)
        self._update_level_label()
        self._open(DOCS[0][2])

    # ---------- 동작 ----------
    def _read(self, filename):
        if filename not in self.raw_cache:
            path = os.path.join(DOC_DIR, filename)
            try:
                with open(path, encoding="utf-8") as f:
                    self.raw_cache[filename] = f.read()
            except OSError as e:
                self.raw_cache[filename] = f"# 오류\n자료를 못 찾았습니다: {e}"
        return self.raw_cache[filename]

    def _open(self, filename):
        self.cur_file = filename
        self.raw_cache.pop(filename, None)   # 항상 최신 파일 반영
        self.anim.set_topic(filename[:2])
        self._render()

    def _on_level(self, v):
        self.level = v
        self._update_level_label()
        self._render()

    def _update_level_label(self):
        self.lvl_label.setText(f"Lv {self.level} · {LEVEL_NAMES[self.level]}")

    def _max_level_in(self, text):
        lvls = [int(x) for x in LV_RE.findall(text)]
        return max(lvls) if lvls else 1

    def _render(self):
        text = self._read(self.cur_file)
        chunks = parse_levels(text)
        shown = [c for (lv, c) in chunks if lv <= self.level]
        body = "".join(shown)
        maxlv = self._max_level_in(text)
        # 상단에 현재 레벨 안내 + 더 깊은 내용 존재 여부
        banner = (f'<p><span class="lvtag">레벨 {self.level} / {LEVEL_NAMES[self.level]}</span>')
        if self.level < maxlv:
            banner += (f' &nbsp;<span style="color:{S.MUTED};font-size:12px;">'
                       f'⬆ 슬라이더를 올리면 더 깊은 내용(최대 Lv{maxlv})이 추가됩니다</span>')
        elif maxlv > 1:
            banner += (f' &nbsp;<span style="color:{S.MUTED};font-size:12px;">'
                       f'(이 문서 최고 레벨)</span>')
        else:
            banner += (f' &nbsp;<span style="color:{S.MUTED};font-size:12px;">'
                       f'(이 문서는 아직 레벨 구분 없음 — 곧 추가됩니다)</span>')
        banner += "</p>\n"
        html = md.markdown(banner + body, extensions=["tables", "fenced_code", "nl2br"])
        self.view.setHtml(CSS + html)
        self.view.verticalScrollBar().setValue(0)
