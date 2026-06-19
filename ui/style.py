# -*- coding: utf-8 -*-
"""엔지니어링 팔레트 (블루프린트 스틸 + 앰버 액센트). 초보자 학습툴 공통 테마."""

# 색상
BG = "#f7f8fa"          # 쿨 그레이 배경
PANEL = "#ffffff"        # 패널
INK = "#1d3f63"          # 진한 블루프린트
STEEL = "#2f5f8f"        # 스틸 블루 (주 색상)
STEEL_LT = "#5b86b3"
AMBER = "#e0922f"        # 기능 액센트 (경고/동작/지령)
GREEN = "#2e9e6b"        # 측정/정상
RED = "#d1495b"          # 위험/고장
GRID = "#d9dee5"
MUTED = "#6b7888"

# 신호별 고정 색 (그래프 일관성)
C_IA, C_IB, C_IC = "#d1495b", "#2e9e6b", "#2f5f8f"
C_ID, C_IQ = "#9b59b6", "#e0922f"
C_REF = "#1d3f63"
C_SPEED = "#2f5f8f"

# 폰트
FONT_UI = "Malgun Gothic"       # 한글 UI
FONT_MONO = "Consolas"          # 숫자/코드

QSS = f"""
QWidget {{
    background: {BG};
    color: {INK};
    font-family: "{FONT_UI}";
    font-size: 13px;
}}
QTabWidget::pane {{ border: 1px solid {GRID}; background: {BG}; }}
QTabBar::tab {{
    background: #e7ebf0; color: {MUTED};
    padding: 9px 20px; margin-right: 2px;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
    font-weight: bold;
}}
QTabBar::tab:selected {{ background: {STEEL}; color: white; }}
QTabBar::tab:hover:!selected {{ background: #d3dae2; }}

QGroupBox {{
    background: {PANEL};
    border: 1px solid {GRID}; border-radius: 4px;
    margin-top: 14px; padding: 10px 10px 10px 10px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 10px; padding: 0 5px;
    color: {STEEL};
}}
QPushButton {{
    background: {STEEL}; color: white; border: none;
    border-radius: 4px; padding: 7px 16px; font-weight: bold;
}}
QPushButton:hover {{ background: {STEEL_LT}; }}
QPushButton:pressed {{ background: {INK}; }}
QPushButton:disabled {{ background: #b8c2cf; color: #eef; }}
QPushButton#amber {{ background: {AMBER}; }}
QPushButton#amber:hover {{ background: #eaa44f; }}
QPushButton#ghost {{ background: #e7ebf0; color: {INK}; }}
QPushButton#ghost:hover {{ background: #d3dae2; }}

QRadioButton {{ spacing: 7px; padding: 3px; }}
QRadioButton::indicator {{ width: 15px; height: 15px; }}

QSlider::groove:horizontal {{
    height: 5px; background: {GRID}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {STEEL}; width: 15px; margin: -6px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{ background: {STEEL_LT}; border-radius: 2px; }}

QLabel#h1 {{ font-size: 19px; font-weight: bold; color: {INK}; }}
QLabel#h2 {{ font-size: 15px; font-weight: bold; color: {STEEL}; }}
QLabel#mono {{ font-family: "{FONT_MONO}"; font-size: 14px; color: {INK}; }}
QLabel#hint {{ color: {MUTED}; font-size: 12px; }}

QScrollArea {{ border: none; background: {BG}; }}
QTextBrowser {{
    background: {PANEL}; border: 1px solid {GRID}; border-radius: 4px;
    padding: 8px;
}}
"""
