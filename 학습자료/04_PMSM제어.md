# 04. PMSM 제어 — 합쳐서 모터 돌리기 (종합)

원본: `PMSM_TI 구현_임세영.pdf`

**한 줄 요약:** 앞의 세 블록(읽기·만들기·박자)을 합쳐서 모터를 원하는 대로 돌린다.
이 문서는 프로그램 **"1. 제어 시뮬레이터"** 탭과 같이 보면 제일 빨리 이해됩니다.

### 📷 우리가 다루는 게 실제로는 이런 물건입니다

지금 배우는 모든 내용은 결국 **이런 모터 제어보드 한 장** 위에서 돕니다.

<img src="media/board_3d.png" width="380" alt="실제 모터제어보드 3D">

<img src="media/board_assembly.png" width="600" alt="보드 부품 배치도">

위 배치도에서 **Q1~Q6 = 전력 스위치(MOSFET)**, **C_BULK = 큰 커패시터**,
**R_SH = 전류 측정 저항(션트)**, **U_DRV = 게이트 드라이버**, **U_MCU = 두뇌(MCU)**,
**U_ENC = 각도 센서(엔코더)**, **U_CAN = 통신** 입니다.
(각 부품 설명은 프로그램 **"2. 보드·소자 구조"** 탭에서 클릭으로 볼 수 있어요.)

---

## A. PMSM이 어떤 모터야?

회전하는 부분(회전자)에 **영구자석**이 박혀 있는 모터입니다.

> 🔎 **쉽게:** 손에 막대자석을 쥐고, 바깥에서 다른 자석을 빙글빙글 돌리면 손의 자석도
> 따라 돕니다. PMSM이 딱 이래요. 바깥 자석(고정자 자기장)을 **얼마나 세게, 어느 방향으로
> 돌리느냐**가 제어의 전부입니다. 그 바깥 자기장은 코일에 흐르는 **전류**로 만듭니다.

---

## B. FOC의 핵심 아이디어 (이거 하나면 80%)

모터에 흐르는 3상 전류는 **계속 출렁이는 물결(sin파)** 이라 직접 다루기 어렵습니다.
그래서 **보는 시점을 바꿉니다.**

> 🔎 **쉽게:** 회전목마를 땅에서 보면 말들이 빙빙 돌아 어지럽죠. 그런데 **회전목마에
> 같이 올라타서 보면** 말들이 가만히 멈춰 보입니다. 전류도 **회전자와 같이 도는 시점**에서
> 보면 출렁임이 사라지고 **가만히 있는 값**처럼 보입니다. 그러면 제어가 훨씬 쉬워져요.

이렇게 "같이 타서 본" 전류를 두 가지로 나눕니다:

<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#7a3f9e;">Id = 자석 방향 전류</b> → 토크를 못 만듦. 그래서 보통 <b>0</b>으로 둡니다.
</div>
<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#c0763a;">Iq = 자석과 직각 방향 전류</b> → <b>이게 힘(토크)을 만듭니다.</b>
</div>

> ✅ **"Iq가 토크다."** FOC를 한마디로 줄이면 이겁니다. Iq를 키우면 힘이 세지고 빨라져요.
> 프로그램 Vector 모드에서 Iq 슬라이더를 올려 직접 확인해 보세요.

---

## C. 한 박자에 하는 일 (앞 자료 3개가 여기서 만남)

알람(인터럽트)이 울릴 때마다, 1/20000초 안에 아래를 순서대로 합니다:

<p style="line-height:2.6;">
<span style="background:#2e9e6b;color:white;padding:5px 11px;border-radius:14px;">① 전류 읽기</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#e0922f;color:white;padding:5px 11px;border-radius:14px;">② 각도 읽기</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">③ 회전목마에 올라타기(좌표변환)</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#7a3f9e;color:white;padding:5px 11px;border-radius:14px;">④ 계산(PI)</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">⑤ 다시 3상으로</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#d1495b;color:white;padding:5px 11px;border-radius:14px;">⑥ PWM 출력</span>
</p>

| 단계 | 하는 일 | 어느 자료 |
|---|---|---|
| ① | 전류 읽기 (ADC) | 03 |
| ② | 회전자 각도 읽기 (엔코더) | 04 |
| ③ | "회전목마 올라타기" = 좌표변환(Clarke·Park) | 04 |
| ④ | 목표와 비교해 전압 계산 (PI) | 04 |
| ⑤ | 전압을 다시 3상으로 (역변환) | 04 |
| ⑥ | PWM 듀티로 출력 (ePWM) | 02 |

> ✅ **이게 프로그램 "제어 시뮬레이터"에서 눈으로 보던 그 루프**입니다. 시뮬레이터 속
> 계산과 실제 MCU 코드가 **똑같은 순서**예요.

---

## D. 제어 4단계 — 쉬운 것부터 차근차근

한 번에 정밀 제어로 안 갑니다. **검증 가능한 작은 단계부터** 올라가요.
(프로그램에서 라디오버튼으로 하나씩 눌러 보세요.)

<div style="background:#eef4fb;border-left:6px solid #5b86b3;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2f5f8f;">1단계 · V/F</b> — 제어랄 게 없음. 그냥 주파수 올리며 전압도 같이 올려 <b>억지로</b> 돌림.
<br><span style="color:#6b7888;font-size:12.5px;">→ 인버터가 3상 전압을 제대로 내는지 점검용.</span>
</div>
<div style="background:#eef4fb;border-left:6px solid #5b86b3;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2f5f8f;">2단계 · I/F</b> — 전류 크기는 정해놓고, 각도를 천천히 돌림. 자석이 <b>끌려와</b> 따라 돎.
<br><span style="color:#6b7888;font-size:12.5px;">→ 처음 기동·아주 느린 속도에 유용.</span>
</div>
<div style="background:#e8f5ee;border-left:6px solid #2e9e6b;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2e9e6b;">3단계 · Vector (FOC) ★</b> — 진짜 각도를 알기에 <b>Iq로 토크를 정밀하게</b> 만듦.
<br><span style="color:#6b7888;font-size:12.5px;">→ 핵심. "Iq가 토크."</span>
</div>
<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">4단계 · Speed</b> — 속도를 직접 못 만드니, "속도가 모자라면 <b>Iq를 더 줘</b>"라고 시킴.
<br><span style="color:#6b7888;font-size:12.5px;">→ 속도제어기(바깥) + 전류제어기(안). 이중 구조.</span>
</div>

> 🔎 **이중 구조가 왜?** 자동차로 치면 "속도가 느리다 → 그러니 액셀(토크)을 더 밟아라"
> 순서예요. 속도를 보고 **필요한 힘(Iq)** 을 정하고, 그 힘을 전류제어기가 만들어 냅니다.

---

## E. 실제로는 이렇게 단계별로 안전하게 검증

진짜 모터를 처음부터 돌리지 않습니다. 망가지면 위험하고 비싸니까요.

<p style="line-height:2.4;">
<span style="background:#5b86b3;color:white;padding:5px 11px;border-radius:14px;">PLECS (PC 시뮬)</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">CCS + TI 보드</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#e0922f;color:white;padding:5px 11px;border-radius:14px;">RT-BOX (가짜 모터)</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#d1495b;color:white;padding:5px 11px;border-radius:14px;">진짜 모터</span>
</p>

> ✅ **이 학습 프로그램이 바로 맨 앞 "PC 시뮬" 단계의 쉬운 버전**입니다. 수식으로 모터를
> 흉내 내며 4단계를 눈으로 보는 것. 실제로는 그다음 CCS로 넘어갑니다.

---

## F. 초보자가 자주 터지는 곳 (미리 알면 안 당함)

- **계산을 정수로 해서 값이 깨짐** → 제어 계산은 **무조건 소수(float)** 로.
- **갑작스런 부하에 모터가 휘청** → 전류제어만으론 부족, **속도제어(4단계)** 를 붙이면 안정.
- **속도를 너무 올리면 파형이 떨림** → 전압엔 한계가 있어 무한정 못 올림.
  프로그램에서 속도를 올리면 **전압벡터가 바깥 점선 원(한계)에 닿는** 걸 보세요.

---

## G. 프로그램으로 5분 체험 (그대로 따라하기)

> **"1. 제어 시뮬레이터"** 탭에서:

1. **Vector** 고르고 시작 → Iq를 0에서 2A로 → *힘·속도가 커진다 = "Iq가 토크".*
2. Iq 고정하고 **부하 토크**를 올려보기 → *속도가 떨어진다(혼자선 못 버팀).*
3. **Speed**로 바꾸고 속도 300rpm + 부하 올리기 → *Iq가 알아서 늘어 속도 유지.* (이중 구조의 힘)
4. **V/F**로 바꿔보기 → *제어 없이도 돌지만 거칠다.* 가장 원시적 단계 체감.
5. 모터 그림에서 **빨강(d)·주황(q) 축이 회전자와 같이 돌고**, 초록 전류 화살표가
   주황(q) 쪽을 향하면 → FOC가 잘 되고 있다는 뜻.

---

## 30초 자가 점검
1. 힘(토크)을 만드는 전류는? → **Iq**
2. 전류가 "가만히" 보이게 만드는 비유? → **회전목마에 같이 올라타기**
3. 제어 4단계 순서? → **V/F → I/F → Vector → Speed**
4. Speed가 이중 구조인 이유? → **속도 보고 필요한 Iq를 정하고, 전류제어기가 만듦**
5. 속도를 무한정 못 올리는 이유? → **전압 한계**

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:12px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
• FOC = 전류를 <b>회전목마 위 시점</b>으로 바꿔, 힘 만드는 <b>Iq</b>만 키우는 것.<br>
• 한 박자: <b>전류읽기 → 각도 → 변환 → 계산 → 다시 3상 → PWM</b> (전부 알람 안에서).<br>
• 단계는 <b>V/F→I/F→Vector→Speed</b>, 검증은 <b>PC시뮬→보드→가짜모터→진짜모터</b>.
</div>

---

### 더 깊이 가려면
- 보드 부품: 프로그램 **"2. 보드·소자 구조"** 탭
- 통신 선택: 프로그램 **"3. 통신 방식"** 탭
- 실제 C코드: `CCS_코드골격/` 폴더 (이 자료와 1:1로 짝지어 둠)

---

<!--LV 2-->
## Lv 2 · 좌표계 3개 — 어디서 전류를 바라볼까

레벨1에서 "회전목마에 올라타면 전류가 멈춰 보인다"고 했죠. 그 "시점 바꾸기"는 사실
**좌표계 3개**를 차례로 갈아타는 일입니다.

<p style="line-height:2.6;">
<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">abc · 3상</span>
<span style="color:#9aa7b5;">→ Clarke →</span>
<span style="background:#e0922f;color:white;padding:5px 11px;border-radius:14px;">αβ · 2상 고정</span>
<span style="color:#9aa7b5;">→ Park →</span>
<span style="background:#9b59b6;color:white;padding:5px 11px;border-radius:14px;">dq · 회전</span>
</p>

| 좌표계 | 축 | 보는 사람 | 전류 모양 |
|---|---|---|---|
| **abc** | 3개(120° 간격) | 땅에 선 사람 | 출렁이는 sin파 3개 |
| **αβ** | 2개(직각, 고정) | 땅에 선 사람 | 출렁이는 sin파 2개 |
| **dq** | 2개(직각, 회전자와 같이 돎) | **회전목마 탑승자** | 멈춘 직류값 (id, iq) |

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2f5f8f;">Clarke 변환</b><br>
3상(abc)을 직각 2축(αβ)으로 줄이기. 평형 3상(ia+ib+ic=0)에서는 정보 손실 없이 좌표만 바꾼 것.
</div>
<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">Park 변환 = "회전목마 올라타기"</b><br>
고정된 αβ축을 <b>회전자 각도 θe만큼 돌려서</b> dq축으로. 이때부터 전류가 멈춰 보입니다.
</div>

이걸 한 박자 안에서 앞뒤로 합니다(레벨1 C절의 ①~⑥을 변환 이름으로 정리):

<p style="line-height:2.6;">
<span style="background:#2e9e6b;color:white;padding:5px 11px;border-radius:14px;">측정(ia,ib,ic)</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">Clarke</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#9b59b6;color:white;padding:5px 11px;border-radius:14px;">Park</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#7a3f9e;color:white;padding:5px 11px;border-radius:14px;">PI</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#9b59b6;color:white;padding:5px 11px;border-radius:14px;">역Park</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#d1495b;color:white;padding:5px 11px;border-radius:14px;">SVPWM</span>
</p>

가는 길(측정→dq)은 **Clarke·Park**, 오는 길(dq전압→3상)은 **역Park·SVPWM**. PI는 멈춰 보이는
dq값 위에서만 계산합니다. 직류값을 PI로 다루니 쉬워요.

> 🔎 **쉽게:** abc는 "땅에서 보기", αβ는 "땅에서 보되 축만 2개로 정리", dq는 "회전목마에
> 올라타서 보기". 올라타려면 회전목마가 지금 어느 각도인지(θe)를 알아야 합니다 — 그래서
> 각도 센서가 필수예요.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
좌표계는 <b>abc → αβ → dq</b> 순으로 갈아탄다. <b>Clarke</b>는 3상→2상,
<b>Park</b>은 회전목마 올라타기(θe로 회전). dq에서는 전류가 <b>직류</b>처럼 멈춰 보여 제어가 쉽다.
</div>

---

<!--LV 3-->
## Lv 3 · 변환식과 토크식 — 숫자로 정확히

레벨2의 "갈아타기"를 실제 수식으로 씁니다. θe는 **회전자 전기각**입니다.

<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">Clarke (진폭불변형)</b><br>
<code>iα = (2·ia − ib − ic) / 3</code><br>
<code>iβ = (ib − ic) / √3</code>
</div>
<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">Park (αβ → dq, 측정 전류용)</b><br>
<code>id =  iα·cos θe + iβ·sin θe</code><br>
<code>iq = −iα·sin θe + iβ·cos θe</code>
</div>
<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">역Park (dq → αβ, 출력 전압용)</b><br>
<code>vα = vd·cos θe − vq·sin θe</code><br>
<code>vβ = vd·sin θe + vq·cos θe</code>
</div>

**"진폭불변형"** 이란 3상 전류 진폭이 1A면 변환 후 iα 진폭도 1A가 되도록 1/3, 1/√3 계수를
맞춘 것입니다. 그래서 슬라이더의 "2A"가 실제 dq에서도 2A로 직관적으로 읽혀요.

### 토크식 (힘이 어디서 나오는가)

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">일반(IPM 포함)</b><br>
<code>Te = 1.5 · P · ( λ·iq + (Ld − Lq)·id·iq )</code>
</div>

- `P` = 극쌍수(pole pairs), `λ` = 영구자석 쇄교자속, `Ld·Lq` = d·q축 인덕턴스.
- 첫 항 `λ·iq` = **자석 토크**(iq에 비례 → "Iq가 토크"의 정체).
- 둘째 항 `(Ld−Lq)·id·iq` = **릴럭턴스 토크**(자기저항 차이에서 나옴, IPM에서만 큼).

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">표면부착형 SPM (Ld = Lq)</b><br>
둘째 항이 0 → <code>Te = 1.5 · P · λ · iq</code>. 그래서 SPM은 <b>id*=0</b>이 최적.
</div>

기계 회전과 전기 회전의 관계(극쌍수만큼 전기각이 빨리 돕니다):
`ωe = P · ωm` (ωm = 기계 각속도[rad/s]).

> 🔎 **쉽게:** 극쌍수 P=4인 모터는 회전자가 한 바퀴(기계 360°) 돌 때 전기적으로는
> 4바퀴(전기 1440°) 돈 셈. Park에 넣는 θe는 항상 **전기각**입니다.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
SPM은 <code>Te = 1.5·P·λ·iq</code> — 토크는 iq에 정비례. IPM은 릴럭턴스 항
<code>(Ld−Lq)·id·iq</code>가 더해진다(Lv10 MTPA의 씨앗). Park/역Park에는 항상 <b>전기각 θe</b>를 쓴다.
</div>

---

<!--LV 4-->
## Lv 4 · 전압방정식과 전류제어 블록도

PI는 "전류를 맞추려면 전압을 얼마나 줘야 하나"를 계산합니다. 그 근거가 **dq 전압방정식**입니다.

<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">회전자 dq 좌표 전압방정식</b><br>
<code>vd = Rs·id + Ld·(did/dt) − ωe·Lq·iq</code><br>
<code>vq = Rs·iq + Lq·(diq/dt) + ωe·(Ld·id + λ)</code>
</div>

각 항의 뜻:
- `Rs·i` = 저항에서 깎이는 전압(열).
- `L·(di/dt)` = 인덕턴스가 전류 변화에 저항(이게 PI로 제어하려는 핵심 동특성).
- `−ωe·Lq·iq`, `+ωe·Ld·id` = **교차결합 항**(d↔q가 서로 간섭. Lv7에서 상쇄).
- `+ωe·λ` = **역기전력(back-EMF)**. 속도가 빠를수록 커지는 "맞바람".

### 전류제어 블록도 (한 축 기준, d축·q축 각각 동일 구조)

| 신호 | 내용 |
|---|---|
| 지령 | `id* , iq*` (위에서 내려줌. SPM이면 id*=0) |
| 오차 | `e_d = id* − id` , `e_q = iq* − iq` |
| PI | `vd = Kp·e_d + Ki·∫e_d dt` (q도 동일) |
| 출력 변환 | (vd, vq) → 역Park → (vα, vβ) → **SVPWM** |
| 출력 | 3상 듀티 → ePWM → 인버터 → 모터 |

<p style="line-height:2.6;">
<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">id*,iq*</span>
<span style="color:#9aa7b5;">→ (−) →</span>
<span style="background:#9b59b6;color:white;padding:5px 11px;border-radius:14px;">PI</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#9b59b6;color:white;padding:5px 11px;border-radius:14px;">vd,vq</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#e0922f;color:white;padding:5px 11px;border-radius:14px;">역Park</span>
<span style="color:#9aa7b5;">→</span>
<span style="background:#d1495b;color:white;padding:5px 11px;border-radius:14px;">SVPWM</span>
<span style="color:#9aa7b5;">↺ 측정전류 되먹임</span>
</p>

<img src="../media/board_assembly.png" width="600" alt="제어보드 부품 배치">

위 블록도의 마지막 "인버터→모터"가 바로 이 보드의 **Q1~Q6 스위치**에서 일어납니다.
PI가 만든 vd,vq는 결국 이 6개 스위치의 ON/OFF 시간(듀티)으로 변신해요.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
dq 전압식 = <b>저항항 + 인덕턴스항 + 교차결합 + 역기전력</b>. 전류제어기는 d·q
<b>두 개의 똑같은 PI</b>가 각자 <code>오차→vd/vq</code>를 만들고, 역Park·SVPWM으로 3상에 뿌린다.
</div>

---

<!--LV 5-->
## Lv 5 · 코드 한 사이클 — 인터럽트 안에서 벌어지는 일

레벨1~4의 흐름을 실제 펌웨어 한 사이클(50µs, 20kHz)의 의사코드로 봅니다.
프로젝트 `CCS_코드골격/FocInterrupt.c`의 `vFsampInterrupt()`, 변환·PI 함수는
`CCS_코드골격/foc_lib.c`에 **1:1로** 들어 있습니다.

```c
interrupt void vFsampInterrupt(void)        // 20kHz로 자동 호출
{
    // 1) ADC: 상전류 읽기 + 스케일/오프셋          (자료03)
    vScaleAdcValue();
    ia = fIo[0]; ib = fIo[1]; ic = fIo[2];

    // 2) 회전자 전기각 읽기 (엔코더 SPI)            (자료04 Lv2)
    theta_e = vReadEncoderTheta();

    // 3) Clarke: 3상 -> αβ                          (Lv3 식)
    clarke(ia, ib, ic, &ialpha, &ibeta);

    // 4) Park: αβ -> dq  (회전목마 올라타기)         (Lv3 식)
    park(ialpha, ibeta, theta_e, &id, &iq);

    // 5) PI 전류제어: 오차 -> vd, vq                 (Lv4 블록도)
    vd = pi_calc(&pi_id, id_ref - id);   // d축
    vq = pi_calc(&pi_iq, iq_ref - iq);   // q축

    // 6) 역Park: dq전압 -> αβ전압                    (Lv3 식)
    inv_park(vd, vq, theta_e, &valpha, &vbeta);

    // 7) SVPWM -> CMPA(듀티) 출력                    (자료02 ePWM)
    svpwm(valpha, vbeta, &da, &db, &dc);
    vSetPwmDuty(da, db, dc);
}
```

> 참고: 제공된 골격 코드 `foc_lib.c`는 이해를 위해 7)을 단순 **역Clarke**(`inv_clarke_to_duty`)로 구현했습니다. 실제 구현은 여기에 **SVPWM**(자료02 Lv8)을 넣어 전압을 15% 더 활용합니다. 구조·자리는 동일합니다.

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">⚠ 계산은 반드시 float</b><br>
모든 변환·PI 변수는 <b>소수(float)</b>로. 정수로 하면 sin/cos·나눗셈에서 값이 깨지고
(레벨1 F절) 토크가 엉뚱하게 나옵니다. C2000은 FPU/CLA로 float를 빠르게 처리합니다.
</div>

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2f5f8f;">타이밍이 생명</b><br>
이 7단계가 <b>한 PWM 주기(50µs) 안에</b> 끝나야 다음 박자에 늦지 않습니다. 그래서 함수는
가볍게, sin/cos는 룩업/하드웨어로 빠르게. 못 끝내면 제어가 무너져요.
</div>

> 🔎 **쉽게:** 시뮬레이터에서 보던 흐름이 코드에선 함수 호출 일곱 줄. 시뮬과 펌웨어가
> **같은 순서**라는 게 핵심입니다.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
한 인터럽트 = <b>ADC → θe → clarke → park → PI → inv_park → SVPWM</b>. 전부
<code>FocInterrupt.c</code>/<code>foc_lib.c</code>에 있고, 한 주기(50µs) 안에 끝내야 하며, 계산은 전부 <b>float</b>.
</div>

---

<!--LV 6-->
## Lv 6 · PI 게인 계산 — 추측 말고 식으로

PI의 Kp, Ki를 감으로 돌리지 않습니다. **내부모델제어(IMC)·극영점 상쇄** 방식이면
모터 파라미터(R, L)와 원하는 대역폭 하나로 딱 떨어집니다.

<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">전류루프 표준 튜닝식</b><br>
<code>Kp = ωc · L</code><br>
<code>Ki = ωc · R</code><br>
(ωc = 전류루프 목표 대역폭 [rad/s])
</div>

**원리:** PI 제로(`Ki/Kp = R/L`)를 모터 극(`R/L`)에 **딱 겹치게**(극영점 상쇄) 두면,
닫힌 루프가 1차 시스템처럼 깔끔해지고 대역폭이 정확히 ωc가 됩니다.

### 예제 (d축 = q축, L 같다고 가정)

주어진 값: `ωc = 2π·300 = 1885 rad/s`, `L = 0.2 mH = 0.0002 H`, `R = 0.3 Ω`.

| 게인 | 계산 | 값 |
|---|---|---|
| **Kp** | 1885 × 0.0002 | **≈ 0.377 V/A** |
| **Ki** | 1885 × 0.3 | **≈ 565.5 V/(A·s)** |

IPM이라 Ld≠Lq면 **축별로 따로** 계산합니다:
- d축: `Kp_d = ωc·Ld`, `Ki_d = ωc·R`
- q축: `Kp_q = ωc·Lq`, `Ki_q = ωc·R`

예로 Ld=0.2mH, Lq=0.5mH면 Kp_q=1885×0.0005 ≈ **0.943**, Ki는 둘 다 ≈565.5(R 공통).

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">⚠ 디지털 PI는 Ki에 dt를 곱해 적분</b><br>
코드의 적분 항은 <code>integ += Ki·error·dt</code> 형태(dt=Tsamp). 위 Ki는 연속시간 값이니
구현 시 샘플시간을 곱하는 걸 잊지 마세요. <code>FocInterrupt.c</code>도 <code>wc·L</code>, <code>wc·R</code>로 둡니다.
</div>

> 🔎 **쉽게:** 대역폭 ωc는 "전류가 얼마나 빨리 지령을 따라잡나"의 속도. 크게 잡으면
> 빠르지만, 샘플링·잡음·전압한계에 막힙니다(상한은 Lv9). 보통 스위칭의 1/10 이하로.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
전류루프 게인은 <code>Kp=ωc·L</code>, <code>Ki=ωc·R</code> — 원리는 <b>극영점 상쇄</b>.
IPM은 d·q 축의 L이 달라 <b>Kp를 따로</b> 계산한다. ωc 하나만 정하면 게인이 나온다.
</div>

---

<!--LV 7-->
## Lv 7 · 비이상 보상 — 교차결합·디지털 지연 (실무 핵심)

Lv4 식대로만 PI를 돌리면 두 가지가 성능을 갉아먹습니다. 실무에서 반드시 잡는 두 보상입니다.

### 1) 교차결합 전향보상 (decoupling feedforward)

전압식의 `−ωe·Lq·iq`, `+ωe·(Ld·id+λ)` 항 때문에 d축과 q축이 서로 간섭합니다(속도가
빠를수록 심함). 이걸 PI 출력에 **미리 더해(feedforward)** 상쇄합니다.

<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">보상 후 출력 전압</b><br>
<code>vd = PI_d(id*−id) − ωe·Lq·iq</code><br>
<code>vq = PI_q(iq*−iq) + ωe·(Ld·id + λ)</code>
</div>

전향항을 더하면 PI 입장에서 d·q가 **독립된 1차계**처럼 보여, Lv6 게인식이 그대로 잘 맞습니다.

> 🔎 **쉽게:** d축과 q축이 서로 밀치는 힘을 PI가 뒤늦게 따라잡으려 애쓰는 대신,
> "지금 속도·전류면 이만큼 밀릴 것"을 미리 계산해 **선수 쳐서** 더해주는 것.

### 2) 디지털 지연(각도) 보상

디지털 제어에는 두 가지 지연이 겹칩니다 — 연산 지연 **1·Ts**(이번 박자에 측정→다음 박자에
전압 출력) + ZOH(PWM 유지) **0.5·Ts**. 합쳐 약 **1.5·Tsamp** 지연.

그동안 회전자는 계속 돌므로, 출력 전압을 낼 시점의 각도는 측정 각도보다 앞서 있습니다.
그래서 **역Park에 쓰는 각도를 미리 보정**합니다:

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">각도 보상</b><br>
<code>θe_보정 = θe + ωe · 1.5 · Tsamp</code><br>
(원본 PDF 8p "각도보상 1.5Tsamp"와 일치)
</div>

보정 안 하면 고속에서 전압벡터가 **실제보다 뒤처진 각도**로 나가, 토크가 줄고 d·q가 서로
새어 들어옵니다(고속일수록 ωe가 크니 오차도 커짐).

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
실무 두 보상: (1) <b>교차결합 전향보상</b> — <code>±ωe·L·i</code>, <code>+ωe·λ</code>를 vd/vq에 더해 d·q 분리.
(2) <b>지연 보상</b> — 디지털 ≈<b>1.5·Ts</b> 지연이라 역Park 각도를 <code>θe+ωe·1.5·Ts</code>로 앞당긴다.
</div>

---

<!--LV 8-->
## Lv 8 · dq 모델 유도 — 그 식은 어디서 왔나 (이론)

Lv4의 dq 전압방정식이 하늘에서 떨어진 게 아닙니다. **정지좌표 → 회전변환**으로 유도됩니다.

### 유도 흐름 (개략)

1. **정지좌표(αβ) 전압식** — 모터를 코일로 보면:
   `v_αβ = Rs·i_αβ + d(ψ_αβ)/dt`, 여기서 쇄교자속 `ψ_αβ`에는 인덕턴스 전류항과
   회전하는 영구자석 자속(`λ·e^{jθe}` 형태)이 섞여 있어 **각도 의존**이라 다루기 어렵습니다.
2. **회전변환 적용** — αβ값에 `e^{−jθe}`를 곱해 dq로 보냅니다(= Park). 미분에 곱의 미분을
   쓰면 `d/dt(e^{jθe}·x_dq) = e^{jθe}(dx_dq/dt + jωe·x_dq)`에서 **`jωe` 항**이 튀어나옵니다.
3. 이 `jωe` 항이 바로 Lv4의 **교차결합(±ωe·L·i)과 역기전력(+ωe·λ)** 의 출처입니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2f5f8f;">결과 (Lv4와 동일)</b><br>
<code>vd = Rs·id + Ld·(did/dt) − ωe·Lq·iq</code><br>
<code>vq = Rs·iq + Lq·(diq/dt) + ωe·(Ld·id + λ)</code>
</div>

### 왜 dq에서 직류가 되나

회전변환이 "회전자와 같은 속도로 도는 좌표"로 옮기기 때문입니다. 정상상태에서 전류 벡터는
회전자와 **같은 속도로 함께 도므로**, 그 위에 올라타서 보면(=dq) 더 이상 회전이 없어
`did/dt = diq/dt = 0`인 **상수(직류)**가 됩니다. 미분항이 사라지니 정상상태식은
`vd=Rs·id−ωe·Lq·iq`, `vq=Rs·iq+ωe·(Ld·id+λ)`로 간단해져요.

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">안티와인드업 (anti-windup) 개념</b><br>
전압이 한계(Vmax)에 막히면 실제 출력은 못 커지는데 PI 적분기는 계속 쌓입니다(windup).
포화가 풀리면 그 쌓인 값 때문에 크게 출렁(overshoot). 그래서 <b>포화 시 적분을 멈추거나
(클램핑) 되돌리는(백캘큘레이션)</b> 장치를 답니다. 자세한 설계는 Lv9.
</div>

> 🔎 **쉽게:** "회전하는 세상"을 식으로 쓰면 미분에서 `jωe`라는 회전 보정이 자동으로 끼어들고,
> 그게 교차결합·역기전력의 정체입니다. 일단 dq로 옮기면 정상상태가 직류라 PI로 다루기 쉬워요.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
dq식은 정지좌표 전압식에 <b>회전변환(e^{−jθe})</b>을 적용해 얻고, 미분의 <code>jωe</code> 항이
<b>교차결합·역기전력</b>이 된다. 회전좌표라 정상상태가 <b>직류</b>. 포화 시엔 <b>안티와인드업</b> 필수.
</div>

---

<!--LV 9-->
## Lv 9 · 루프 설계와 안정성 — 캐스케이드·포화·와인드업

속도제어(레벨1 4단계)는 **이중(캐스케이드) 구조**입니다. 그 설계 규칙과 안정성 장치를 봅니다.

### 대역폭 분리 규칙

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2f5f8f;">내부(전류) ≫ 외부(속도)</b><br>
내부 전류루프 대역폭을 외부 속도루프보다 <b>5~10배 빠르게</b> 둔다. 그래야 속도루프가
"전류는 즉시 따라온다"고 가정할 수 있어 두 루프를 따로 설계 가능.
</div>

| 루프 | 출력 | 입력 | 대역폭(예) |
|---|---|---|---|
| 외부 · 속도 PI | iq 지령(iq*) | 속도오차 | 느림 (예 30~60Hz) |
| 내부 · 전류 PI | vd, vq | 전류오차 | 빠름 (예 300Hz) |

속도 PI: `iq* = Kp_s·(ω*−ω) + Ki_s·∫(ω*−ω)dt`. 출력 iq*는 반드시 **전류 한계로 클램핑**
(과전류 방지 = 레벨1의 "필요한 힘만큼 Iq").

### 안정성 3종 세트

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">① 적분 와인드업 방지</b><br>
출력이 한계에 닿으면 적분 정지(<b>클램핑</b>) 또는 초과분을 적분기에서 빼주는
(<b>백캘큘레이션</b>). 부하 급변·포화 복귀 시 오버슈트를 막음.
</div>
<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">② 전압 포화 한계</b><br>
<code>√(vd² + vq²) ≤ Vmax = Vdc / √3</code><br>
(SVPWM 선형영역의 상전압 최대. 이 원을 넘으면 파형이 찌그러지고 제어가 무너짐 —
레벨1 F절의 "점선 원에 닿는" 그것.)
</div>
<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2f5f8f;">③ 샘플링이 대역폭 상한</b><br>
디지털 제어는 샘플주파수(=PWM 주파수)가 대역폭의 천장. 보통 전류루프 대역폭은
샘플주파수의 <b>1/10 이하</b>로(20kHz면 ~2kHz 이하, 실무는 더 보수적). 04 Lv8·01 Lv8 연결.
</div>

전압이 포화에 닿았는데 더 빠르게 돌려야 하면? → d축에 음의 전류를 줘 한계를 넓히는
**약계자**로 넘어갑니다(Lv10).

> 🔎 **쉽게:** 속도루프는 "얼마나 세게 밟을지(iq*)"를 정하는 운전자, 전류루프는 그 명령을
> 실제 페달 깊이(전압)로 빠르게 만드는 다리. 다리가 훨씬 빨라야 운전자가 편하게 운전합니다.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
캐스케이드: <b>전류루프를 속도루프보다 5~10배 빠르게</b>. 안정성은 <b>안티와인드업 +
전압포화 √(vd²+vq²)≤Vdc/√3 + 샘플링 상한(대역폭은 fs의 1/10 이하)</b>으로 지킨다.
</div>

---

<!--LV 10-->
## Lv 10 · 연구·고급 — MTPA·약계자·센서리스·고장진단

여기서부터는 시뮬레이터의 한계를 넘는 연구 주제입니다(원본 PDF 76~78p 연계).

### 1) MTPA — 전류당 최대 토크 (IPM)

Lv3 토크식의 릴럭턴스 항 `(Ld−Lq)·id·iq`를 **활용**합니다. IPM은 보통 Lq>Ld라
이 항이 양의 토크가 되려면 **id를 음수**로 줘야 합니다. 같은 전류 크기(|i|=√(id²+iq²))에서
토크를 최대로 만드는 (id, iq) 조합을 찾는 것이 MTPA.

<div style="background:#f3eef9;border-left:6px solid #9b59b6;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#7a3f9e;">MTPA 조건 (개략)</b><br>
<code>id = ( λ − √(λ² + 8·(Lq−Ld)²·iq²) ) / ( 4·(Lq−Ld) )</code> &nbsp;(IPM, id&lt;0)<br>
SPM(Ld=Lq)은 릴럭턴스 항이 0이라 <b>id* = 0</b>이 그대로 MTPA.
</div>

> 🔎 **쉽게:** IPM에서는 "자석을 약간 옆에서 당기는(음의 id)" 보조 힘(릴럭턴스 토크)을 더해
> 같은 전류로 더 큰 토크를 짜냅니다. SPM은 그 보조 힘이 없어 id=0이 최선.

### 2) 약계자 (Field Weakening)

기저속도 이상에서 역기전력(`ωe·λ`)이 커져 전압한계 `√(vd²+vq²)≤Vmax`에 막히면 더 못 빨라집니다.
이때 **음의 id**로 자석 자속을 상쇄(약화)시켜 필요한 전압을 낮추고 속도를 더 올립니다.

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#c0763a;">동작</b><br>
전압포화를 감지하면 id를 점점 더 음으로 → 유효 자속 <code>(λ + Ld·id)</code> 감소 → 같은 전압으로
더 높은 속도. 단, 토크는 줄고 약자속 영역(정출력)으로 들어감. 시뮬레이터에서 속도를
기저속도 이상으로 올려 약계자 동작(전압벡터가 한계 원에 붙고 id가 음으로 가는 것)을 확인 가능.
</div>

### 3) 센서리스 (sensorless)

엔코더 없이 θe를 **추정**합니다. 역기전력/자속 관측기(observer, 예: 슬라이딩모드·확장
칼만필터 — 세부 알고리즘은 검증필요)로 추정하되, **저속·정지에서는 역기전력이 작아** 부정확합니다.
그래서 기동은 **I/F**(레벨1 2단계)로 강제로 끌고 가다가, 일정 속도 이상에서 관측기 추정값으로
**전환(handover)** 합니다(PDF 78p).

### 4) 고장진단 (fault diagnosis)

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;">
<b style="color:#2f5f8f;">전압각 지표</b><br>
<code>δ = −tan⁻¹(Vd / Vq)</code><br>
정상 대비 이 전압각 δ의 변화로 고장을 진단(PDF 76p). 고장 유형: <b>편심</b>(회전자 치우침),
<b>감자</b>(자석 약화), <b>권선 단락</b>(턴 쇼트), <b>베어링 고장</b> 등이 각기 다른 특성 변화를 남김.
</div>

### 시뮬레이터·연구 연결

| 고급 주제 | 어디서 확인/확장 |
|---|---|
| MTPA | 시뮬레이터에서 IPM 파라미터로 id<0 토크 이득 비교 |
| 약계자 | 기저속도 이상 + 전압한계 원에 붙는 동작 관찰 |
| 센서리스 | I/F 기동 → 관측기 전환 알고리즘 추가(연구 주제) |
| 고장진단 | δ=−tan⁻¹(Vd/Vq) 모니터링, 고장 모드별 패턴 학습 |

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
고급 4종: <b>MTPA</b>(IPM은 id&lt;0로 릴럭턴스 토크 활용, SPM은 id=0), <b>약계자</b>(전압한계에
막히면 음의 id로 자속 약화), <b>센서리스</b>(관측기로 θe 추정·I/F로 기동 후 전환),
<b>고장진단</b>(전압각 <code>δ=−tan⁻¹(Vd/Vq)</code> 변화로 편심·감자·단락·베어링 판별).
</div>
