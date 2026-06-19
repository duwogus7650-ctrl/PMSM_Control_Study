# -*- coding: utf-8 -*-
"""탭 3: 통신 방식. 왜 통신이 필요한가 + UART/SPI/I2C/CAN 비교 + 무엇을 쓸지."""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QTextBrowser, QLabel, QButtonGroup)
from . import style as S

INTRO = f"""
<div style='font-family:{S.FONT_UI}; color:{S.INK}; line-height:1.6'>
<b>통신은 왜 필요할까?</b><br>
모터 제어보드는 혼자 동작하지 않습니다. 상위 장치(PC·로봇 메인보드·PLC)가
<b>"300rpm으로 돌려", "토크 0.5N·m로"</b> 같은 <b>명령</b>을 보내고, 보드는
<b>"현재 속도·전류·온도·고장 유무"</b> 같은 <b>상태</b>를 되돌려줘야 합니다.
이 양방향 통로가 통신입니다. 또 보드 <b>내부</b>에서도 MCU가 엔코더·게이트
드라이버 같은 칩과 데이터를 주고받아야 합니다. 용도에 따라 알맞은 방식을 고릅니다.
</div>
"""

DATA = {
    "table": dict(
        title="한눈 비교표",
        html=f"""
        <h3>통신 방식 비교</h3>
        <table border='1' cellspacing='0' cellpadding='6'
               style='border-collapse:collapse; font-size:12.5px;'>
        <tr style='background:{S.STEEL}; color:white;'>
          <th>방식</th><th>선 수</th><th>속도</th><th>거리/노이즈</th>
          <th>연결 수</th><th>주 용도</th></tr>
        <tr><td><b>UART</b></td><td>2 (TX/RX)</td><td>~1Mbps</td>
          <td>짧음/약함</td><td>1:1</td><td>디버깅·간단 명령</td></tr>
        <tr style='background:#eef1f5'><td><b>SPI</b></td><td>4 (+CS)</td>
          <td>매우 빠름(수십Mbps)</td><td>매우 짧음(보드 내)</td><td>1:N(CS별)</td>
          <td>엔코더·ADC·드라이버칩</td></tr>
        <tr><td><b>I2C</b></td><td>2 (SDA/SCL)</td><td>~400kbps~</td>
          <td>짧음</td><td>다수(주소)</td><td>저속 센서·EEPROM</td></tr>
        <tr style='background:#fbf2e6'><td><b>CAN</b></td><td>2 (차동 H/L)</td>
          <td>~1Mbps(CAN FD↑)</td><td><b>김/매우 강함</b></td><td><b>다수(버스)</b></td>
          <td><b>모터↔상위제어기</b></td></tr>
        </table>
        <p style='color:{S.MUTED}; font-size:12px'>핵심: '보드 안 칩끼리 고속' = SPI,
        '노이즈 심한 곳에서 장치들 묶기' = CAN, '그냥 PC와 간단히' = UART.</p>
        """),
    "uart": dict(
        title="UART (시리얼)",
        html=f"""
        <h3>UART — 가장 단순한 1:1 시리얼</h3>
        <b>구조</b> : TX(보냄)·RX(받음) 2선을 서로 엇갈려 연결. 클럭선이 없어
        양쪽이 같은 속도(baud, 예 115200)를 미리 약속합니다(비동기).<br>
        <b>장점</b> : 가장 간단, 거의 모든 MCU·PC가 지원. 디버깅·로그·간단한
        명령 전송에 최고.<br>
        <b>단점</b> : 기본 1:1, 노이즈·거리에 약함(전압 레벨 통신).
        멀리/여럿 연결하려면 RS-485 같은 차동 변환이 필요.<br>
        <b>이 프로젝트에서</b> : 개발 중 PC로 변수 모니터링·파라미터 튜닝 채널로
        흔히 사용. (CCS의 Expression 창 대신 실시간 텍스트 로그용)
        """),
    "spi": dict(
        title="SPI (고속 보드 내부)",
        html=f"""
        <h3>SPI — 보드 안 칩끼리 고속 통신</h3>
        <b>구조</b> : 4선 — SCLK(클럭), MOSI(주→종), MISO(종→주), CS(칩 선택).
        클럭선이 있어 매우 빠르고 정확(동기). 칩마다 CS를 따로 둬 여러 개 연결.<br>
        <b>장점</b> : 수십 Mbps로 매우 빠름, 구현 단순, 전이중(동시 송수신).<br>
        <b>단점</b> : 선이 많고 거리 짧음(같은 보드 위 수 cm). 장치마다 CS 필요.<br>
        <b>이 프로젝트에서</b> : <b>엔코더 AS5047P</b>가 SPI로 회전자 각도를
        매 제어주기(수십 µs)마다 빠르게 넘겨줍니다. 각도는 늦으면 안 되는
        데이터라 고속 SPI가 적합. 게이트드라이버(DRV8301) 설정도 SPI로 합니다.
        """),
    "i2c": dict(
        title="I2C (저속 다수 센서)",
        html=f"""
        <h3>I2C — 적은 선으로 여러 저속 장치</h3>
        <b>구조</b> : SDA(데이터)·SCL(클럭) 단 2선에 여러 장치를 매달고, 각
        장치를 <b>주소</b>로 구분. 동기식.<br>
        <b>장점</b> : 선이 2개뿐, 장치 여러 개를 주소로 관리. 온도센서·EEPROM·
        전력관리칩 등 '가끔 조금' 읽는 용도에 좋음.<br>
        <b>단점</b> : 속도 느림, 거리 짧음, 풀업저항 필요, 버스 점유 충돌 관리.<br>
        <b>이 프로젝트에서</b> : 보드 온도센서나 설정 저장용 EEPROM 같은
        부가 장치 연결에 쓰일 수 있음(필수는 아님).
        """),
    "can": dict(
        title="CAN (모터↔상위제어기) ★권장",
        html=f"""
        <h3>CAN — 노이즈 심한 현장의 표준</h3>
        <b>구조</b> : CAN_H / CAN_L 두 선의 <b>전압 차이</b>로 0/1을 읽는 차동
        신호. 트랜시버 칩(TJA1051)이 MCU 신호를 이 차동 신호로 변환. 양 끝에
        120Ω 종단저항.<br>
        <b>왜 모터에 CAN?</b><br>
        ① <b>노이즈 내성</b>: 두 선에 같이 실린 잡음은 '차이'를 빼면 사라짐 →
        모터·인버터의 강한 전자기 노이즈 속에서도 안정.<br>
        ② <b>멀티드롭 버스</b>: 한 쌍의 선에 여러 보드(여러 모터축)를 주렁주렁
        연결. 로봇 관절마다 모터가 있을 때 배선이 깔끔.<br>
        ③ <b>메시지 우선순위·오류검출</b>: ID로 중요한 메시지가 먼저 가고,
        하드웨어가 오류를 자동 검출·재전송.<br>
        <b>이 프로젝트에서</b> : 보드의 <b>TJA1051</b>이 바로 이 역할. 상위
        제어기와 속도·토크 명령 / 상태·고장 보고를 주고받는 메인 통신으로 권장.
        고장진단 데이터를 상위로 올리는 데도 적합.<br>
        <span style='color:{S.MUTED}'>TI 자료의 '인버터 통신 프로토콜 분석/
        제어 플랫폼 구축'(PDF 76p)과 직접 연결됩니다.</span>
        """),
    "pick": dict(
        title="그래서 무엇을 쓸까? (정리)",
        html=f"""
        <h3>용도별 선택 가이드</h3>
        <ul style='line-height:1.7'>
        <li><b>보드 내부, 빠르고 시간 민감</b> (엔코더 각도, 드라이버 설정)
            → <b>SPI</b></li>
        <li><b>보드 내부, 느리고 가끔</b> (온도, 설정 저장) → <b>I2C</b></li>
        <li><b>PC와 개발·디버깅·로그</b> → <b>UART</b> (필요시 RS-485)</li>
        <li><b>상위 제어기와 본 통신, 노이즈·다축</b> → <b>CAN</b> ★</li>
        </ul>
        <p style='color:{S.MUTED}'>한 보드 안에서 여러 방식을 <b>동시에</b> 씁니다:
        엔코더는 SPI로 읽고, 상위와는 CAN으로 말하고, 개발 중엔 UART로 들여다보는
        식입니다. "하나만 고른다"가 아니라 "각 연결마다 알맞은 걸 쓴다"가 정답.</p>
        """),
}

ORDER = ["table", "uart", "spi", "i2c", "can", "pick"]


class CommTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        intro = QTextBrowser()
        intro.setHtml(INTRO)
        intro.setMaximumHeight(120)
        root.addWidget(intro)

        body = QHBoxLayout()
        body.setSpacing(10)
        # 왼쪽 버튼
        col = QVBoxLayout()
        col.setSpacing(6)
        self.group = QButtonGroup(self)
        self.btns = {}
        for key in ORDER:
            b = QPushButton(DATA[key]["title"])
            b.setObjectName("ghost")
            b.setCheckable(True)
            b.clicked.connect(lambda _, k=key: self._show(k))
            self.group.addButton(b)
            self.btns[key] = b
            col.addWidget(b)
        col.addStretch(1)
        cw = QWidget(); cw.setLayout(col); cw.setFixedWidth(220)
        body.addWidget(cw)

        self.detail = QTextBrowser()
        body.addWidget(self.detail, 1)
        root.addLayout(body, 1)

        self.btns["table"].setChecked(True)
        self._show("table")

    def _show(self, key):
        self.btns[key].setChecked(True)
        self.detail.setHtml(
            f"<div style='font-family:{S.FONT_UI}; font-size:13.5px;"
            f" color:{S.INK}; line-height:1.55'>{DATA[key]['html']}</div>")
