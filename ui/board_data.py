# -*- coding: utf-8 -*-
"""모터제어보드 소자 설명 데이터 (실제 Cheap FOCer 2 / TI 28377D 보드 기준).

각 항목: key -> dict(
  title, part(실부품), color, rect(논리좌표 0~100), short(한줄),
  html(상세: 왜 필요/기능/신호흐름/TI자료 연결))
"""
from . import style as S

# 연결선: 블록 가장자리에서 출발해 '빈 공간'으로 직각 경로(꺾인 선)로 라우팅.
# pts = 논리좌표(0~100) 꺾임점들, label = 가운데 라벨, lpos = 라벨 좌표.
# kind: power(전력) / ctrl(제어PWM) / sense(센싱) / comm(통신, 양방향)
LINKS = [
    dict(pts=[(17, 50), (21, 50)], kind="power", label="DC", lpos=(17.5, 46)),
    dict(pts=[(34, 50), (40, 50)], kind="power", label="", lpos=None),
    dict(pts=[(56, 50), (62, 50)], kind="power", label="3상", lpos=(56.5, 46)),
    dict(pts=[(75, 50), (81, 50)], kind="power", label="U·V·W", lpos=(75, 46)),
    dict(pts=[(48, 26), (48, 34)], kind="ctrl", label="구동", lpos=(49.5, 30)),
    dict(pts=[(36, 76), (36, 17), (40, 17)], kind="ctrl",
         label="PWM 6채널", lpos=(36.5, 42)),
    dict(pts=[(68, 62), (68, 70), (34, 70), (34, 76)], kind="sense",
         label="전류 센싱(ADC)", lpos=(48, 68)),
    dict(pts=[(87, 76), (87, 73), (39, 73), (39, 76)], kind="sense",
         label="각도(SPI)", lpos=(62, 71)),
    dict(pts=[(40, 86), (46, 86)], kind="comm", label="명령/상태",
         lpos=(43, 75), bidir=True),
]

COMPONENTS = {
    "batt": dict(
        title="전원 / 배터리", part="J_PWR (XT/JST 커넥터)", color="#3b6fa0",
        rect=(3, 40, 14, 20), short="모터를 돌릴 큰 DC 전력을 공급",
        html=f"""
        <h3>전원 (DC 배터리/SMPS)</h3>
        <b>정체</b> : 모터 구동용 직류 전원 입력단 (예: 24V, 48V).<br>
        <b>왜 필요?</b> : 모터는 큰 전류·전력을 먹습니다. MCU의 3.3V 로직 전원과는
        완전히 별개의 '힘쓰는 전원'이 따로 있어야 합니다.<br>
        <b>기능</b> : 인버터(MOSFET 다리)에 DC 링크 전압을 공급. 이 전압을
        스위칭으로 잘라서 3상 교류를 만듭니다.<br>
        <b>주의</b> : 전원 +/- 역결선은 보드를 즉사시킵니다. 입력에 역결선 보호
        다이오드/퓨즈를 두는 이유입니다.<br>
        <span style='color:{S.MUTED}'>TI 자료 연결: 인버터에 들어가는 Vdc.
        DAC 페이지에서 'Vdc 받아오는 중'으로 등장.</span>
        """),
    "bulk": dict(
        title="벌크 커패시터", part="110µF 75V ×2 (C_BULK)", color="#5b86b3",
        rect=(21, 40, 13, 20), short="순간 전류 요동을 흡수해 전압을 안정화",
        html=f"""
        <h3>벌크(평활) 커패시터</h3>
        <b>정체</b> : DC 링크에 병렬로 붙은 큰 전해/세라믹 커패시터.<br>
        <b>왜 필요?</b> : MOSFET이 1초에 수만 번 ON/OFF 하면 전류가 확확
        튑니다. 전원선이 길면 인덕턴스 때문에 전압이 출렁이고 스파이크가 생겨
        소자가 파손됩니다.<br>
        <b>기능</b> : 스위칭 순간 필요한 전류를 '저수지'처럼 바로 공급/흡수해
        DC 전압을 평평하게 유지(리플 저감). MOSFET 바로 옆에 둬야 효과적.<br>
        <span style='color:{S.MUTED}'>핵심 감각: 스위칭 전원에는 '에너지 저장
        + 노이즈 억제'용 커패시터가 반드시 따라붙는다.</span>
        """),
    "bridge": dict(
        title="3상 인버터 (MOSFET ×6)", part="IPT007N06N ×6 (Q1~Q6)", color=S.STEEL,
        rect=(40, 34, 16, 32), short="DC를 잘라 3상 교류를 만드는 전력 스위치",
        html=f"""
        <h3>3상 인버터 = 전력 스위치 6개</h3>
        <b>정체</b> : 상(U/V/W)마다 위(High)·아래(Low) MOSFET 2개씩, 총 6개.
        '하프브리지 3개'라고 부릅니다.<br>
        <b>왜 필요?</b> : 모터는 3상 교류로 돌아가는데 전원은 DC입니다. DC를
        빠르게 켜고 꺼서(PWM) 평균적으로 원하는 3상 전압을 합성합니다.<br>
        <b>기능</b> : 각 상을 +Vdc 또는 0(GND)에 번갈아 연결. ON 시간 비율
        (듀티)을 바꾸면 상전압 크기가 정해집니다. → 이게 ePWM 의 역할.<br>
        <b>주의</b> : 같은 상의 위·아래를 동시에 켜면 전원이 단락(슛스루)되어
        폭발합니다. 그래서 둘 사이에 <b>데드타임</b>(둘 다 OFF 구간)을 넣습니다.<br>
        <span style='color:{S.MUTED}'>TI 자료 연결: ePWM의 Dead-Band(DB)
        submodule, CMPA/CMPB로 듀티 설정 (PDF 24·31p).</span>
        """),
    "gate": dict(
        title="게이트 드라이버", part="DRV8301 (U_DRV)", color="#7a5ea8",
        rect=(40, 8, 16, 18), short="MCU의 약한 신호로 큰 MOSFET을 빠르게 ON/OFF",
        html=f"""
        <h3>게이트 드라이버</h3>
        <b>정체</b> : MCU와 MOSFET 사이의 '힘 증폭기 + 통역사'.<br>
        <b>왜 필요?</b> : MCU PWM 핀은 3.3V·수mA 밖에 못 냅니다. 하지만 큰
        MOSFET을 빨리 켜려면 게이트 전하를 순간적으로 밀어넣을 수 A 단위 전류와
        높은 게이트 전압(10~15V)이 필요합니다. MCU가 직접 못 합니다.<br>
        <b>기능</b> : ① PWM 신호를 받아 게이트를 강하게 구동(빠른 스위칭=손실↓)
        ② High-side 구동용 부트스트랩/차지펌프 ③ 과전류·과열 보호 신호 출력.<br>
        <b>DRV8301</b> 은 게이트 드라이버 + 전류센스 앰프 + 강압 레귤레이터가
        합쳐진 칩이라 모터 보드에 많이 쓰입니다.<br>
        <span style='color:{S.MUTED}'>게이트 저항(10Ω ×6)은 스위칭 속도를
        조절해 링잉/노이즈를 억제합니다.</span>
        """),
    "shunt": dict(
        title="전류 센서 (션트저항)", part="0.5mΩ 1W ×3 + OP-AMP", color=S.GREEN,
        rect=(62, 38, 13, 24), short="전류를 전압으로 바꿔 측정 (FOC의 눈 ①)",
        html=f"""
        <h3>전류 센서 = 션트저항 + OP-AMP</h3>
        <b>정체</b> : 각 상 전류 경로에 직렬로 넣은 아주 작은 저항(0.5mΩ).<br>
        <b>왜 필요?</b> : FOC는 '지금 전류가 얼마인지'를 알아야 제어합니다.
        전류는 직접 못 읽으니 옴의 법칙(V=I·R)으로 전압으로 바꿔 측정합니다.<br>
        <b>왜 이렇게 작은 저항?</b> : 저항이 크면 열손실(I²R)과 전압강하가 커져
        모터 효율을 깎습니다. 그래서 0.5mΩ처럼 극히 작게 합니다. 대신 전압도
        매우 작아(수 mV) <b>OP-AMP로 증폭</b>해서 ADC 범위(0~3.3V)에 맞춥니다.<br>
        <b>기능</b> : 상전류 → 작은 전압 → 증폭 → MCU의 ADC로 입력.<br>
        <b>오프셋·스케일</b> : 0A인데도 ADC 값이 0이 아닐 수 있어(센서/앰프 바이어스)
        Calibration으로 0A 기준값(offset)을 빼고, 스케일을 곱해 실제 A로 환산.<br>
        <span style='color:{S.MUTED}'>TI 자료 연결: vScaleAdcValue,
        fADC2Offset, Calibration() (PDF 36·37·38p). 절연형(홀센서)도 대안.</span>
        """),
    "enc": dict(
        title="위치 센서 (엔코더)", part="AS5047P (U_ENC, SPI)", color=S.AMBER,
        rect=(78, 76, 19, 18), short="회전자(자석) 각도를 읽는다 (FOC의 눈 ②)",
        html=f"""
        <h3>위치 센서 = 자기식 엔코더</h3>
        <b>정체</b> : 회전축의 자석을 보고 절대 각도를 출력하는 칩(14bit).<br>
        <b>왜 필요?</b> : FOC의 Park 변환은 '회전자가 지금 몇 도인지(θe)'를
        알아야 전류를 d·q로 정확히 나눌 수 있습니다. 각도를 모르면 토크가 엉뚱한
        방향으로 나가 모터가 탈조합니다.<br>
        <b>기능</b> : 기계각 → (×극쌍수 P) → 전기각 θe 로 환산해 제어에 사용.<br>
        <b>센서리스 대안</b> : 엔코더 없이 전압·전류로 각도를 추정(관측기)하는
        방법도 있습니다. 이때 기동은 I/F로 하고 일정 속도 이상에서 전환합니다.<br>
        <span style='color:{S.MUTED}'>TI 자료 연결: AngleEstimation.C,
        '외부 측정각 받아와서 사용', 각도보상(연산·PWM 지연) (PDF 8p, 78p).</span>
        """),
    "mcu": dict(
        title="MCU (두뇌)", part="TI TMS320F28377D / STM32F405", color=S.INK,
        rect=(14, 76, 26, 20), short="센서를 읽고 제어 계산 후 PWM을 내보낸다",
        html=f"""
        <h3>MCU — 제어의 두뇌</h3>
        <b>정체</b> : 모든 측정·계산·명령을 담당하는 마이크로컨트롤러.
        TI 자료는 모터제어 특화 DSP인 <b>TMS320F28377D</b>(C2000)를 씁니다.<br>
        <b>왜 이 칩?</b> : 모터제어는 1초에 수만 번(예 20kHz) 반복되는 무거운
        실수 연산입니다. C2000은 FPU·삼각함수 가속기·전용 ePWM/ADC를 갖춰
        이 주기를 놓치지 않습니다.<br>
        <b>한 주기에 하는 일</b> :
        ① ADC로 전류 읽기 → ② Clarke/Park 변환 → ③ PI 전류제어 →
        ④ 역Park/SVPWM → ⑤ ePWM 듀티 출력. 이 전체가 인터럽트 안에서 돕니다.<br>
        <b>인터럽트</b> : ePWM 타이머가 정확한 주기로 '지금 계산해!' 신호(인터럽트)를
        주고, CPU는 하던 일을 멈추고 제어 루틴을 실행합니다.<br>
        <span style='color:{S.MUTED}'>TI 자료 연결: PIE 벡터테이블, IER/PIEIER,
        FsampInterrupt, TBPRD로 샘플링주파수 설정 (PDF 44~52p).</span>
        """),
    "can": dict(
        title="통신 (CAN 트랜시버)", part="TJA1051 (U_CAN)", color="#c0763a",
        rect=(46, 78, 18, 17), short="상위 제어기와 명령·상태를 주고받음",
        html=f"""
        <h3>통신 — CAN 트랜시버</h3>
        <b>정체</b> : MCU의 디지털 통신 신호를, 노이즈에 강한 차동 신호(CAN_H/CAN_L)로
        바꿔주는 칩.<br>
        <b>왜 필요?</b> : 모터 보드는 혼자 일하지 않습니다. 상위 컴퓨터/로봇 제어기가
        "300rpm으로 돌려"라고 명령하고, 보드는 "현재 속도·전류·온도·고장"을
        보고해야 합니다. 그 통로가 통신입니다.<br>
        <b>왜 CAN?</b> : 모터 옆은 전자기 노이즈가 심합니다. CAN은 두 선의 '차이'로
        신호를 읽어 노이즈에 강하고, 여러 장치를 한 버스에 연결·우선순위 관리가
        쉬워 차량·로봇에서 표준입니다.<br>
        <span style='color:{S.MUTED}'>자세한 비교(UART/SPI/CAN/I2C)는
        '3. 통신 방식' 탭에서. 엔코더는 보드 내부 고속통신용으로 SPI 사용.</span>
        """),
    "motor": dict(
        title="PMSM 모터", part="영구자석 동기전동기", color="#d1495b",
        rect=(81, 36, 16, 28), short="전기를 회전력으로 바꾸는 대상",
        html=f"""
        <h3>PMSM (영구자석 동기전동기)</h3>
        <b>정체</b> : 회전자에 영구자석이 박혀 있고, 고정자 3상 권선에 흐르는
        전류가 만드는 회전 자계에 자석이 '동기'되어 도는 모터.<br>
        <b>왜 제어가 필요?</b> : 그냥 전압을 주면 효율·토크가 들쭉날쭉합니다.
        FOC로 전류를 자석 방향(d)과 직각(q)으로 나눠, 토크를 만드는 q축 전류만
        키우면 적은 전류로 큰 토크를 정밀하게 냅니다.<br>
        <b>Id / Iq</b> : Id=자속(보통 0), Iq=토크. "Iq가 토크다"가 FOC 한 줄 요약.<br>
        <span style='color:{S.MUTED}'>시뮬레이터 탭에서 Iq를 키우면 토크·가속이
        커지는 걸 직접 확인하세요.</span>
        """),
}
