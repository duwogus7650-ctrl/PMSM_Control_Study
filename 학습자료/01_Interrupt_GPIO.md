# 01. Interrupt & GPIO

원본: `001_28377D_MCU_Interrupt&GPIO_동현이형.pdf`

**한 줄 요약:** MCU에게 "이 핀 켜/꺼"(GPIO)와 "정확한 시간마다 이 일 해"(인터럽트)를 시키는 법.

---

## A. GPIO — 핀 하나 켜고 끄기

**GPIO**는 그냥 **전선 한 가닥**이라고 생각하세요. MCU가 이 전선에 전기를 주거나(켬) 안 주거나(끔) 합니다.

- **3.3V 나오면 = 켜짐(High, 1)**
- **0V = 꺼짐(Low, 0)**

딱 이 두 가지가 전부입니다. 쓰임새는 두 방향:

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#2f5f8f;">① 내보내기 (Output)</b><br>
MCU가 핀을 켜서 <b>LED를 켠다.</b> 예: "GPIO31 켜 → 초록 LED 점등"
</div>

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#2f5f8f;">② 읽어오기 (Input)</b><br>
바깥 <b>버튼이 눌렸는지</b> MCU가 확인한다. 예: "버튼 핀이 3.3V면 → 눌림"
</div>

> 🔎 **쉽게:** 청소기 버튼을 누르면(Input) MCU가 알아채고 모터를 돌리고, MCU가 표시등 핀을 켜면(Output) 불이 들어옵니다. GPIO는 **MCU의 손가락(켜기)과 눈(읽기)** 중 제일 단순한 것.

실습 보드에서는 **GPIO34 = 빨강 LED, GPIO31 = 초록 LED**. 첫 숙제는 "LED를 원하는 간격으로 깜빡이기"인데, **정확한 간격**으로 하려면 다음 주제인 인터럽트가 필요합니다.

---

## B. Interrupt — 정확한 타이밍의 비밀 (이 문서의 핵심)

### 인터럽트가 뭐야?
평소에 일하던 CPU를 **잠깐 멈추게 하고, 급한 일을 먼저 시킨 뒤, 원래 하던 곳으로 되돌려보내는** 것.

> 🔎 **쉽게:** 공부하다가 **알람이 울리면** 하던 걸 멈추고 약을 먹은 뒤, 다시 책으로 돌아오죠. 그 "알람"이 인터럽트입니다.

### 왜 모터 제어에 꼭 필요할까?
모터 제어는 **"정확히 일정한 간격으로"** 계산해야 합니다 (예: 1초에 2만 번).
그냥 평범한 반복문(`while`) 안에서 계산하면, 다른 코드 때문에 간격이 **들쭉날쭉**해집니다.
간격이 흔들리면 모터가 덜덜 떨거나 심하면 망가집니다.

> ✅ 그래서 **하드웨어 타이머(알람)** 가 "지금 계산해!" 하고 CPU를 **정확한 박자**로 깨웁니다. CPU가 뭘 하고 있든 상관없이 박자가 보장돼요.

### 인터럽트가 일어나는 순서 (4단계)

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#2f5f8f;">1단계 · 평소</b><br>CPU가 일반 코드를 차근차근 실행하는 중.
</div>
<p align="center" style="color:#9aa7b5;margin:2px 0;">▼ &nbsp;<span style="font-size:12px;">타이머가 "지금이야!" 하고 알람을 울림</span></p>
<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#2f5f8f;">2단계 · 멈춤</b><br>하던 일을 잠깐 멈추고, <b>"어디까지 했는지"</b> 위치를 기억해 둠.
</div>
<p align="center" style="color:#9aa7b5;margin:2px 0;">▼</p>
<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#c0763a;">3단계 · 급한 일 처리</b><br><b>여기서 모터 제어 계산</b>을 함 (전류 읽고 → 계산하고 → 전압 출력).
</div>
<p align="center" style="color:#9aa7b5;margin:2px 0;">▼</p>
<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#2f5f8f;">4단계 · 복귀</b><br>1단계에서 멈춘 자리로 <b>돌아가 이어서</b> 진행.
</div>

### 우선순위 (둘이 동시에 울리면?)
알람이 두 개 동시에 울리면 뭘 먼저? 예를 들어:

- 알람 A: "제어 계산해"
- 알람 B: "하드웨어 고장! 즉시 정지!"

당연히 **B(안전)** 가 먼저죠. 그래서 인터럽트엔 **우선순위(번호)** 가 있고, 번호가 낮을수록 먼저 처리합니다. (메인 PMSM 자료의 "PIE 벡터테이블"이 바로 이 우선순위 표예요.)

### 알람을 울리는 주인공
모터 제어에서 알람(인터럽트)을 울리는 건 보통 **ePWM 타이머**(다음 문서). PWM이 한 바퀴 돌 때마다 "제어해!" 하고 깨웁니다.

---

## C. CCS 프로젝트 만들 때 딱 하나만 주의

CCS(코드 작성·업로드 프로그램)에서 새 프로젝트를 만들 때:

> ⚠️ **폴더 경로에 한글이 있으면 안 됩니다!**
> `C:/User/새폴더/CCS` ❌ → `C:/CCS` ⭕. 한글 경로는 빌드 에러의 가장 흔한 원인.

나머지(Base 코드 풀기, 링커 파일, CPU 지정)는 외울 필요 없이 막히면 PDF 6~12쪽 순서대로 따라하면 됩니다.

---

## 30초 자가 점검
1. 핀에서 3.3V는 켜짐일까 꺼짐일까? → **켜짐(High)**
2. 인터럽트가 모터 제어에 꼭 필요한 이유 한 단어? → **타이밍(정확한 박자)**
3. 4단계 중 실제 제어 계산을 하는 단계? → **3단계**
4. "제어"와 "긴급정지"가 동시에 울리면? → **정지(우선순위 높음)부터**
5. CCS 폴더 경로 주의점? → **한글 금지**

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:12px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
• <b>GPIO</b> = 핀 켜기/끄기/읽기 (3.3V냐 0V냐).<br>
• <b>인터럽트</b> = 정확한 박자로 CPU를 깨워 제어를 시키는 알람.<br>
• 모터 제어는 보통 <b>ePWM 타이머 알람</b> 안에서 돈다.
</div>

➡️ 다음: **02_ePWM.md** (전압을 어떻게 만드나)

---

<!--LV 2-->
## Lv 2 · 기본 동작 원리 — 모드와 인터럽트 소스

레벨1에서 GPIO는 "전선 한 가닥"이라 했죠. 그런데 입력으로 쓸 때 **아무것도 안 연결된 핀**은 0V도 3.3V도 아닌 **둥둥 떠 있는(floating)** 상태가 됩니다. 잡음에 따라 0이 됐다 1이 됐다 제멋대로 읽혀요. 그래서 **풀업/풀다운 저항**으로 "기본값"을 정해 줍니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">풀업(Pull-Up)</b><br>핀을 약하게 3.3V 쪽으로 당겨 둠 → 평소 <b>1</b>, 버튼 누르면 0.</div>
<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">풀다운(Pull-Down)</b><br>핀을 약하게 0V 쪽으로 당겨 둠 → 평소 <b>0</b>, 버튼 누르면 1.</div>

> 🔎 **쉽게:** 풀업/풀다운은 "아무도 안 건드리면 이 값이야"라고 미리 정해 두는 **기본 자세**입니다.

**인터럽트는 어디서 울릴까?** 알람을 울리는 소스는 크게 3종류:

| 소스 | 예시 | 비유 |
|---|---|---|
| 주변장치(Peripheral) | ePWM 주기 끝, ADC 변환 완료 | 내부 부서가 "다 됐어요" 보고 |
| 외부 핀(External) | GPIO 핀에 신호 들어옴 | 바깥에서 누군가 초인종 |
| 소프트웨어(Software) | 코드가 직접 인터럽트 발생 | 내가 나한테 알람 설정 |

**폴링 vs 인터럽트** — 일을 알아채는 두 방식:

<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">폴링: 계속 들여다봄</span> → <span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">CPU 낭비·놓칠 수도</span> &nbsp;&nbsp; vs &nbsp;&nbsp; <span style="background:#e0922f;color:white;padding:5px 11px;border-radius:14px;">인터럽트: 일 생기면 알려줌</span> → <span style="background:#e0922f;color:white;padding:5px 11px;border-radius:14px;">효율적·정확</span>

> 🔎 **쉽게:** 폴링은 라면 익었나 1초마다 냄비 뚜껑 열어보기, 인터럽트는 타이머 맞춰 놓고 딴 일 하다 "띵!" 소리에 가기.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>입력 핀은 풀업/풀다운으로 기본값을 정한다. 인터럽트 소스는 주변장치·외부핀·소프트웨어 3종. 모터 제어는 폴링이 아니라 인터럽트로 한다.</div>

---

<!--LV 3-->
## Lv 3 · PIE 구조와 우선순위 (정량)

28377D는 인터럽트 소스가 **너무 많습니다**. CPU가 직접 받을 수 있는 줄(INT)은 한정돼 있는데 알람은 수백 개. 그래서 **PIE(Peripheral Interrupt Expansion, 주변장치 인터럽트 확장) 컨트롤러**가 비슷한 것끼리 **그룹으로 묶어** CPU에 전달합니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">규모</b><br><b>12개 그룹 × 각 16채널 = 최대 192개</b> 인터럽트를 정리. 12개 그룹은 CPU의 INT1~INT12로 연결됨.</div>

표로 보면 "그룹(행) × 채널(열)" 격자입니다:

| 그룹↓ \ 채널→ | 채널1 | 채널2 | … | 채널16 |
|---|---|---|---|---|
| **그룹1** | ADCA1 | … | | |
| **그룹2** | … | | | |
| **그룹3** | EPWM1_INT | EPWM2_INT | … | |
| … | | | | |
| **그룹12** | | | | |

**우선순위 규칙: 번호가 낮을수록 먼저.** 그룹끼리는 그룹1 > 그룹2 > …, 같은 그룹 안에서는 채널1 > 채널2 > ….

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">예시 위치</b><br>· <b>ADCA1</b> = 그룹1·채널1 (가장 높은 우선순위 쪽)<br>· <b>EPWM1_INT</b> = 그룹3·채널1</div>

> 🔎 **쉽게:** PIE는 192명 민원을 12개 창구로 묶어 CPU에 올리는 **민원실**. 창구 번호·대기 번호가 작을수록 먼저 처리.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>PIE = 192개 인터럽트를 12그룹×16채널로 묶는 정리함. 그룹·채널 번호가 낮을수록 우선순위 높음.</div>

---

<!--LV 4-->
## Lv 4 · 핵심 레지스터 — 인터럽트의 스위치들

인터럽트가 실제로 CPU에 도달하려면 **여러 단계의 허용 스위치**를 모두 켜야 합니다. 채널 → 그룹 → CPU → 전역 순서로 관문이 있어요.

| 레지스터 | 한 줄 설명 |
|---|---|
| `PIEIERx.bit.INTxn` | **PIE 레벨** — 그룹 x의 채널 n 하나를 허용 (가장 안쪽 관문) |
| `IER` | **CPU 레벨** — INT1~INT14 허용 (`M_INT3` 같은 마스크). 이 중 **INT1~INT12가 PIE 12그룹에 대응**(INT13/14는 PIE 안 거치는 타이머용) |
| `IFR` | **플래그** — 어떤 인터럽트가 대기 중인지 표시(읽기용) |
| `PIEACK` | 그룹 처리 끝났다고 알림 → **다음 인터럽트를 받기 위해** 비워줌 |
| `EINT` | **전역 ON** (ST1의 INTM=0). 이게 꺼져 있으면 다 막힘 |
| `EALLOW / EDIS` | 보호 레지스터 **잠금 해제 / 다시 잠금** |
| `ERTM` | 실시간 모드 활성화(디버깅 중에도 인터럽트 동작, Lv7에서 자세히) |

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">관문 순서 (다 열려야 통과)</b><br><span style="background:#2f5f8f;color:white;padding:4px 10px;border-radius:13px;">PIEIER (채널)</span> → <span style="background:#2f5f8f;color:white;padding:4px 10px;border-radius:13px;">IER (그룹)</span> → <span style="background:#2f5f8f;color:white;padding:4px 10px;border-radius:13px;">INTM=0 (EINT, 전역)</span></div>

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">PIEACK 안 비우면?</b><br>그 그룹의 다음 인터럽트가 영영 안 들어옵니다. ISR 끝에서 꼭 비워줘야 함.</div>

> 🔎 **쉽게:** 콘서트장 3중 게이트 — 좌석 검표(PIEIER), 구역 검표(IER), 정문(EINT). 셋 다 통과해야 입장. PIEACK는 "한 명 처리 끝, 다음 손님 받으세요" 종.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>PIEIER(채널)·IER(그룹)·EINT(전역) 3관문을 모두 열어야 인터럽트가 들어온다. ISR 끝엔 PIEACK 비우기, 보호 레지스터는 EALLOW로 연다.</div>

---

<!--LV 5-->
## Lv 5 · 코드 수준 — 연결부터 ISR 마무리까지

이제 실제 C 코드로 인터럽트를 거는 순서를 봅니다. (프로젝트의 `CCS_코드골격/main.c`, `FocInterrupt.c`와 그대로 연결되는 패턴)

**① 벡터테이블에 ISR 함수 연결** — 어떤 인터럽트가 울리면 어느 함수로 점프할지 등록:
```c
EALLOW;
PieVectTable.EPWM1_INT = &myISR;   // EPWM1 알람 → myISR로
EDIS;
```

**② main에서 허용 스위치 켜기 (순서 중요)** — 안쪽(채널)→그룹→전역:
```c
PieCtrlRegs.PIEIER3.bit.INTx1 = 1;  // 그룹3 채널1 (EPWM1) 허용
IER |= M_INT3;                      // CPU INT3(그룹3) 허용
EINT;                               // 전역 인터럽트 ON
```

**③ ISR 작성 — `interrupt` 키워드 필수** (컴파일러가 문맥 저장/복귀를 자동 생성):
```c
interrupt void myISR(void) {
    // ... 여기서 ADC 읽기 + FOC 계산 + PWM 출력 ...
    EPwm1Regs.ETCLR.bit.INT = 1;               // ePWM 인터럽트 플래그 클리어
    PieCtrlRegs.PIEACK.all = PIEACK_GROUP3;    // 그룹3 처리 끝 알림 → 다음 받기
}
```

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">ISR 끝 두 줄을 왜 꼭?</b><br>· <b>ETCLR.INT=1</b>: ePWM이 든 플래그를 안 지우면 같은 알람이 다시 안 울림.<br>· <b>PIEACK</b>: 그룹3 게이트를 다시 열어야 다음 50µs 알람이 들어옴.</div>

> 🔎 **쉽게:** ①은 "이 번호로 전화 오면 이 사람 바꿔줘" 전화번호부 등록, ②는 회선 켜기, ③은 통화 끝에 "다음 전화 받을게요" 정리.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>벡터연결(①) → PIEIER·IER·EINT 켜기(②) → ISR은 `interrupt void`, 끝에서 플래그 클리어 + PIEACK(③).</div>

---

<!--LV 6-->
## Lv 6 · 수치와 타이밍 — 50µs 시간 예산

레벨5의 ISR이 **얼마나 자주, 얼마 안에** 끝나야 하는지 숫자로 봅니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">제어 주파수 20kHz → 제어 주기 50µs</b><br>1초에 2만 번 = 0.00005초마다 한 번. ePWM 카운터가 한 주기 돌 때마다 인터럽트 1회 발생.</div>

즉 **50µs(50,000ns)마다** myISR이 깨어나고, 그 안에 아래를 전부 끝내야 합니다:

<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">① ADC 전류 읽기</span> → <span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">② FOC 계산(Clarke/Park/PI)</span> → <span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">③ PWM 듀티 출력</span>

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">시간 예산(Time Budget) 개념</b><br>①+②+③ 합이 <b>50µs를 넘으면</b> 다음 알람을 놓침 → 제어 깨짐. 50µs는 "이번 회차에 쓸 수 있는 전체 예산"이고, 계산은 그 안에 끝나야 한다.</div>

| 제어 주파수 | 제어 주기 | 비고 |
|---|---|---|
| 10 kHz | 100 µs | 여유 ↑ |
| **20 kHz** | **50 µs** | 흔한 PMSM 설정 |
| 40 kHz | 25 µs | 빠르지만 빡빡 |

> 🔎 **쉽게:** 50µs는 매 회차 받는 **용돈**. 계산이 이 용돈보다 비싸면 빚(밀림)이 생기고 제어가 무너집니다.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>20kHz = 50µs 주기. 이 50µs 안에 ADC읽기+계산+PWM출력을 전부 끝내야 한다(시간 예산).</div>

---

<!--LV 7-->
## Lv 7 · 비이상·실무 — ISR을 짧게 유지하라

이론상 50µs면 충분해 보여도, 실제로는 여러 문제가 끼어듭니다.

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">인터럽트 지터(Jitter)</b><br>알람이 매번 정확히 50µs가 아니라 미세하게 흔들림. 다른 인터럽트나 캐시·버스 경합이 원인. 제어에 잡음으로 작용.</div>
<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">중첩(Nesting)·재진입</b><br>ISR 처리 중 더 높은 우선순위 인터럽트가 끼어들 수 있음. 공유 변수를 잘못 다루면 재진입 버그 발생.</div>
<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">우선순위 역전</b><br>낮은 우선순위 작업이 자원을 쥐고 있어 높은 우선순위가 못 도는 현상.</div>

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">그래서 ISR은 무조건 짧게</b><br>ISR 안에서는 핵심 제어만. `printf`·긴 루프·블로킹 대기는 절대 금지. 무거운 일은 메인 루프로 미룬다.</div>

**디버깅 팁 — ERTM(실시간 모드):** 평소 디버거에서 코드를 멈추면(breakpoint) 인터럽트도 같이 멈춥니다. `ERTM`을 켜면 **CPU를 세워도 인터럽트(제어 루프)는 계속 돌아** 모터를 멈추지 않고 변수만 들여다볼 수 있습니다.

> 🔎 **쉽게:** ISR은 119 통화 — 용건만 짧게. 길게 수다 떨면 다음 신고(다음 50µs)를 못 받습니다.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>지터·중첩·우선순위 역전 때문에 ISR은 짧게 유지한다. 실시간 디버깅은 ERTM으로.</div>

---

<!--LV 8-->
## Lv 8 · (이론) 샘플링과 제어 주기

제어 주기 Ts(예: 50µs)는 단순한 "속도"가 아니라 **제어 성능의 상한선**을 정합니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">제어 대역폭 ≪ 1/Ts</b><br>제어기가 따라잡을 수 있는 응답 속도(대역폭)는 샘플링 주파수 1/Ts보다 훨씬 낮아야 함. 경험칙으로 <b>1/10 ~ 1/20</b> 수준.</div>

예: Ts=50µs → 1/Ts=20kHz → 전류 제어 대역폭은 보통 수백 Hz ~ 1kHz대로 잡습니다. (이 프로젝트 코드 `FocInterrupt.c`는 300Hz로 보수적으로 설정 — 04 자료 Lv6 참고.)

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">디지털 제어 지연 ≈ 1.5·Ts</b><br>· 연산 지연 ≈ <b>1·Ts</b> (이번에 읽은 값으로 계산한 출력은 다음 주기에 적용)<br>· ZOH(영차 홀드) 지연 ≈ <b>0.5·Ts</b> (출력이 한 주기 동안 유지됨)<br>→ 합쳐서 <b>약 1.5·Ts</b>의 지연이 생김. (자세한 건 04 자료 Lv7에서)</div>

> 🔎 **쉽게:** 사진을 50µs마다 한 장씩 찍어 세상을 본다면, 50µs보다 빨리 변하는 건 못 잡습니다. 그래서 제어 목표는 그보다 훨씬 느긋하게 잡아야 안정적.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>제어 대역폭은 1/Ts의 1/10~1/20 수준으로 잡는다. 디지털 제어엔 약 1.5·Ts 지연이 내재한다.</div>

---

<!--LV 9-->
## Lv 9 · 설계·튜닝 — CPU 점유율과 우선순위 배치

ISR이 50µs 안에 끝나는 것만으로는 부족합니다. **얼마나 여유가 있는지**가 안정성을 결정합니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">CPU 점유율 = ISR 실행시간 ÷ 제어 주기</b><br>예: ISR이 20µs 걸리면 20/50 = <b>40% 점유</b>. 나머지 60%는 메인 루프·통신·여유.</div>

| ISR 실행시간 | 점유율(50µs 기준) | 판정 |
|---|---|---|
| 15 µs | 30% | 여유 충분 |
| 30 µs | 60% | 보통 |
| 45 µs | 90% | 위험 (지터에 취약) |

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">평균이 아니라 WCET로 본다</b><br>최악 실행 시간(WCET, Worst-Case Execution Time) 기준으로 예산을 짜야 함. 평균만 보면 가끔 튀는 회차에서 주기를 넘겨 제어가 깨짐.</div>

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">우선순위 배치 전략</b><br>빠르게 돌아야 하는 <b>전류 제어 루프 → 높은 우선순위</b>, 느린 속도/위치 루프·통신·로깅 → 낮게. 빠른 루프가 절대 밀리지 않게.</div>

> 🔎 **쉽게:** 점유율은 50µs라는 그릇이 얼마나 찼나. 90% 채우면 조금만 흔들려도 넘칩니다. 항상 빈 공간을 남기세요.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>CPU 점유율(ISR시간/주기)은 WCET 기준으로 여유 있게. 빠른 제어 루프에 높은 우선순위를 준다.</div>

---

<!--LV 10-->
## Lv 10 · 연구·고급 — 멀티코어, CLA, 트립존 안전

28377D는 단순한 단일 CPU가 아닙니다. 제어를 **여러 일꾼에 분산**하고, 인터럽트보다 빠른 **하드웨어 보호**까지 갖췄습니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">듀얼 코어 + 가속기</b><br>C28x CPU <b>×2</b> + CLA(Control Law Accelerator, 제어 연산 전용 가속기) <b>×2</b>. 예: 코어1=전류 제어, 코어2=통신/감시, CLA=ADC 직후 초고속 전처리 — 식으로 분산.</div>

<span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">CPU1: 빠른 제어</span> → <span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">CPU2: 감시·통신</span> → <span style="background:#2f5f8f;color:white;padding:5px 11px;border-radius:14px;">CLA×2: 오프로드 연산</span>

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">트립존(TZ, Trip-Zone) — 인터럽트보다 빠른 보호</b><br>과전류·고장 신호가 들어오면 <b>소프트웨어(ISR)를 거치지 않고 하드웨어가 즉시 PWM을 차단</b>. 인터럽트는 ISR 진입까지 시간이 걸리지만, TZ는 게이트 신호를 직접 끊어 더 빠르고 확실하게 모터를 보호.</div>

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">기능 안전 관점</b><br>"제어가 멈춰도 안전하게 멈추는가"가 핵심. TZ 하드웨어 차단 + 코어 간 상호 감시(한 코어가 다른 코어 점검)로 단일 고장에도 안전 상태로 빠지게 설계. (구체 기능안전 등급은 문헌 확인 — 검증필요)</div>

> 🔎 **쉽게:** 인터럽트가 "사람이 비상벨 보고 달려가 차단기 내리는 것"이라면, 트립존은 "누전 시 두꺼비집이 스스로 탁 내려가는 것" — 사람을 안 거쳐 더 빠릅니다.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>28377D는 C28x×2 + CLA×2로 제어를 분산한다. 고장 시 트립존(TZ)이 ISR을 거치지 않고 하드웨어로 PWM을 즉시 차단한다(가장 빠른 보호).</div>
