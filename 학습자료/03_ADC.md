# 03. ADC — 바깥 세상을 숫자로 읽기

원본: `003_28377D_MCU_ADC_정빈이.pdf`

**한 줄 요약:** 전류·전압 같은 "아날로그 신호"를 MCU가 계산할 수 있는 "숫자"로 바꾼다.

---

## A. ADC가 뭐야?

**ADC** = 아날로그(전압) → 디지털(숫자) 변환기.

> 🔎 **쉽게:** 체온계와 같아요. 몸의 온도(아날로그)를 **"36.5"라는 숫자**로 바꿔주죠.
> ADC는 전선의 전압을 숫자로 바꿔줍니다. MCU는 숫자만 계산할 수 있으니까요.

변환은 3걸음으로 이뤄집니다:

<p style="line-height:2.4;">
<span style="background:#2f5f8f;color:white;padding:5px 12px;border-radius:14px;">① 표본화</span> →
<span style="background:#2e9e6b;color:white;padding:5px 12px;border-radius:14px;">② 양자화</span> →
<span style="background:#e0922f;color:white;padding:5px 12px;border-radius:14px;">③ 부호화</span>
</p>

- **① 표본화(Sampling):** 출렁이는 신호를 **일정 간격으로 콕콕 집기.**
- **② 양자화(Quantization):** 집은 값을 **가장 가까운 계단값으로** 맞추기.
  계단이 촘촘할수록 정밀 → 28377D는 **12비트 = 4096계단**.
- **③ 부호화(Encoding):** 그 계단 번호를 컴퓨터 숫자(2진수)로 적기.

---

## B. ADC 안에서 숫자를 찾는 법 (스무고개)

28377D의 ADC는 **"업/다운 게임"** 처럼 절반씩 좁혀가며 값을 찾습니다 (이름: SAR).

**예시:** 0~5V를 4비트로 읽는데 입력이 1V라면 —

| 질문 | 추측 | 입력(1V)과 비교 | 결과 |
|---|---|---|---|
| 1차 | 2.5V? | 너무 큼 | 아래로 |
| 2차 | 1.25V? | 큼 | 아래로 |
| 3차 | 0.625V? | 작음 | 위로 |
| 4차 | 0.9375V? | 거의 맞음 | **확정** |

→ 최종 **0.9375V** (1V에 가장 근접). 4비트라 4번 만에 끝.

> ⚠️ **Hold time(잡아두는 시간):** 게임 도중에 입력 전압이 흔들리면 답이 틀리겠죠?
> 그래서 ADC는 입력을 **잠깐 붙잡아 고정**한 뒤 게임을 합니다. 그 붙잡는 시간이 필요해요.

---

## C. 28377D에서 ADC 설정 (이름만 가볍게)

A·B·C·D 4개의 ADC가 있습니다. 설정에서 **딱 두 가지만** 기억하세요:

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#c0763a;">① 전원 켜기 (필수!)</b><br>
<code>ADCPWDNZ = 1</code> — 이걸 안 하면 ADC가 아예 작동 안 합니다. 초보자가 제일 많이 빠뜨리는 것.
</div>
<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#2f5f8f;">② 어느 핀을 읽을지</b><br>
<code>CHSEL</code> — 여러 입력 핀 중 몇 번을 읽을지 고름 (예: CHSEL=2 → ADCINA2 핀).
</div>

**흐름 용어 2개:**
- **SOC** ("변환 시작!") — 보통 **PWM이 정확한 타이밍에** 이 신호를 쏴서 전류를 잽니다.
- **EOC** ("변환 끝!") — 변환이 끝난 이때 인터럽트를 걸어 그 값을 제어에 씁니다.

> ⚠️ 변환이 **끝나기 전에** 값을 쓰면 **이전 값**을 쓰게 돼 제어가 흔들립니다. 그래서 "끝난 뒤(EOC)"에 씁니다.

---

## D. ★제일 중요 — 숫자를 진짜 전류(A)로 바꾸기

ADC가 주는 건 그냥 **0~4095 사이의 맨숫자**일 뿐, "몇 A"인지는 아직 모릅니다.
두 가지 손질이 필요해요:

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#2f5f8f;">Scale (배율 곱하기)</b><br>
맨숫자에 정해진 배율을 곱해 실제 단위(A, V)로 변환. 입력 3.3V를 4096칸에 나눈 비율 + 센서 배율 고려.
</div>
<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:8px 0;border-radius:6px;">
<b style="color:#c0763a;">Offset (영점 빼기)</b><br>
전류가 <b>진짜 0A인데도</b> ADC가 0이 아니라 50, 120 같은 찌꺼기 값을 냅니다(부품 특성).
이대로 쓰면 "항상 약간 흐른다"고 착각하죠.
</div>

**해결 = 영점 잡기(Calibration):** 모터를 안 돌린 0A 상태에서 ADC 값을 **여러 번 읽어 평균** →
그게 "0A일 때의 기준값". 이후 측정마다 그 기준값을 빼줍니다.

> 공식 한 줄: **실제 전류 = 배율 × (맨숫자 − 영점)**
>
> 🔎 체중계로 비유하면: 아무것도 안 올렸는데 0.3kg이 떠 있으면, 그 0.3을 "영점"으로
> 빼주고 재야 정확하죠. ADC도 똑같습니다.

> 💡 **자료의 실제 버그 사례:** 계산을 정수로 해서 값이 깨졌던 적이 있어요.
> → **제어 계산은 무조건 소수(float)로** 하세요.

---

## E. 전류는 왜 "전압으로 바꿔서" 읽나
ADC는 **전압만** 읽을 수 있어요. 전류는 직접 못 재니까:
- **아주 작은 저항(션트)** 에 전류를 흘려 `전압 = 전류 × 저항`으로 바꿔 잰 뒤, 키워서(증폭) ADC로.

(부품 자세한 설명은 프로그램 **"2. 보드·소자 구조" → 전류센서** 참고)

---

## 30초 자가 점검
1. ADC 3걸음? → **표본화 → 양자화 → 부호화**
2. 12비트면 계단 몇 칸? → **4096**
3. ADC가 작동 안 할 때 제일 먼저 의심? → **전원(ADCPWDNZ) 안 켰나**
4. 0A인데 숫자가 0이 아니면? → **영점(offset) 빼주기 = Calibration**
5. 실제 전류 공식? → **배율 × (맨숫자 − 영점)**

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:12px 0;">
<b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
• ADC = <b>전압 → 숫자(0~4095)</b>.<br>
• 맨숫자는 <b>배율 곱하고 영점 빼야</b> 진짜 전류/전압이 된다.<br>
• 계산은 꼭 <b>소수(float)</b>로.
</div>

➡️ 다음: **04_PMSM제어.md** (드디어 합쳐서 모터 돌리기)

---

<!--LV 2-->
## Lv 2 · 표본화·양자화·부호화 자세히 + S/H

레벨1의 3걸음을 한 단계 더 깊게 봅니다.

| 단계 | 하는 일 | 비유 |
|---|---|---|
| 표본화(Sampling) | 시간을 잘게 끊어 그 순간 값만 집음 | 영상의 **프레임 사진** |
| 양자화(Quantization) | 집은 값을 가장 가까운 계단으로 반올림 | 자에 눈금이 1mm뿐 |
| 부호화(Encoding) | 계단 번호를 2진수로 적음 | 17번 → `10001` |

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">S/H (샘플 앤 홀드)의 역할</b><br>
변환(스무고개)이 진행되는 동안 입력이 흔들리면 답이 틀립니다. 그래서 ADC 앞에는 작은 콘덴서(Cap)가 있어 <b>그 순간 전압을 충전해 붙잡아 둡니다.</b> 충전 → 잡아둠 → 그 고정값으로 변환.</div>

> 🔎 **쉽게:** 움직이는 새를 그리려면 먼저 **사진을 찍어 멈춰 둬야** 하죠. S/H가 그 사진 역할.

**Single-ended vs Differential 입력**

| 방식 | 측정 기준 | 특징 |
|---|---|---|
| Single-ended(단일) | 핀 전압을 **접지(0V) 기준**으로 잼 | 핀 1개, 간단함. 공통잡음에 약함 |
| Differential(차동) | 두 핀의 **차이**를 잼 | 핀 2개. 두 선에 똑같이 낀 잡음은 빼면서 사라짐 → 잡음에 강함 |

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
S/H는 변환 도중 입력을 <b>붙잡아 고정</b>하는 콘덴서. 차동입력은 두 핀의 <b>차이</b>를 재서 공통잡음에 강하다.</div>

---

<!--LV 3-->
## Lv 3 · 해상도와 양자화 오차 (정량)

12비트 = **2¹² = 4096계단**. 0~4095 사이 숫자가 나옵니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">1 LSB = 한 칸의 크기</b><br>
<b>1 LSB = Vref / 4096</b><br>
Vref = 3.3V 이면 → 3.3 / 4096 ≈ <b>0.806 mV</b><br>
즉 숫자 1칸이 약 0.8mV. 그보다 작은 변화는 못 봅니다.</div>

> 🔎 **쉽게:** LSB(Least Significant Bit)는 자의 **가장 작은 눈금 한 칸**. 눈금이 0.8mV 간격이면 0.4mV 차이는 같은 칸으로 보입니다.

**양자화 오차(Quantization error)**

반올림하므로 참값과 최대 **±0.5 LSB**(≈ ±0.4mV) 어긋날 수 있습니다. 이건 ADC 원리상 피할 수 없는 한계.

| 비트수 | 계단 수 | 1 LSB (Vref=3.3V) |
|---|---|---|
| 8비트 | 256 | 12.9 mV |
| 10비트 | 1024 | 3.22 mV |
| 12비트 | 4096 | 0.806 mV |
| 16비트 | 65536 | 50.3 µV |

해상도↑(비트↑) = 계단이 더 촘촘 = 더 미세한 변화도 구분.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
12비트 = 4096칸. <b>1 LSB = Vref/4096 ≈ 0.806mV</b>(3.3V 기준). 양자화 오차는 <b>±0.5 LSB</b>.</div>

---

<!--LV 4-->
## Lv 4 · 핵심 레지스터와 타이밍 공식

ADC 속도와 "잡아두는 시간"을 정하는 공식 2개부터.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">① ADC 클럭</b><br>
<b>ADCCLK = SYSCLK / PRESCALE</b><br>
시스템 클럭을 나눠서 ADC가 쓸 속도를 만듭니다.</div>
<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">② 획득시간 (Acquisition window)</b><br>
<b>획득시간 = (ACQPS + 1) × (1 / SYSCLK)</b><br>
⚠️ 주의: 이 카운터는 <b>ADCCLK가 아니라 SYSCLK(시스템 클럭)</b>로 셉니다 (흔한 실수 포인트). S/H 콘덴서를 충전하는 시간으로, 센서 출력저항·내부 Cap이 클수록 더 길게 필요. <b>28377D 12비트는 최소 ~75ns</b> 확보해야 정확.</div>

> 🔎 **쉽게:** 양동이(Cap)에 물(전압)을 채우는 시간. 호스가 얇으면(저항↑) 더 오래 부어야 가득 참.

**꼭 아는 레지스터**

| 레지스터 / 비트 | 역할 |
|---|---|
| `ADCCTL1.ADCPWDNZ` | ADC **전원** ON (1로). 안 켜면 무동작 |
| `ADCCTL2.PRESCALE` | ADCCLK 분주비 설정 |
| `ADCSOCxCTL.CHSEL` | 이 SOC가 **읽을 채널(핀)** 선택 |
| `ADCSOCxCTL.ACQPS` | **획득시간** 길이(샘플 유지창) |
| `ADCSOCxCTL.TRIGSEL` | **트리거원** = 누가 변환 시작? (보통 EPWM SOC) |
| `ADCINTSELxNy` | **EOC → 인터럽트** 연결 |

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">주의</b><br>
ACQPS를 너무 짧게 잡으면 Cap이 덜 차서 측정값이 <b>실제보다 작게</b> 나옵니다. 센서 임피던스가 크면 ACQPS를 넉넉히.</div>

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
ADCCLK = SYSCLK/PRESCALE(변환 속도용). 획득시간 = (ACQPS+1)/<b>SYSCLK</b>(최소 ~75ns). SOC = CHSEL·ACQPS·TRIGSEL로 구성.</div>

---

<!--LV 5-->
## Lv 5 · 코드 수준 (실제 함수 구조)

프로젝트 `CCS_코드골격/Adc_setup.c`의 함수 흐름을 봅니다.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">vInitAdc() — 설정 순서</b><br>
① 전원 ON (<code>ADCPWDNZ=1</code>) → ② <code>PRESCALE</code> 설정 → ③ SOC 구성(<code>CHSEL</code> 채널 / <code>ACQPS</code> 획득시간 / <code>TRIGSEL</code> = EPWM SOC) → ④ <code>INTSEL</code>로 EOC→인터럽트 연결.</div>

```c
// 읽을 때: 하위 12비트만 추출
raw = AdcaResultRegs.ADCRESULT0 & 0x0FFF;   // 0~4095

// 맨숫자 → 실제 전류
float vScaleAdcValue(int raw) {
    return SCALE * (float)(raw - offset);    // fIo = SCALE*(raw - offset)
}

// 영점 잡기: 0A 상태에서 N회 평균
void vCalibrateOffset(void) {
    long sum = 0;
    for (int i = 0; i < N; i++) sum += (readAdc() & 0x0FFF);
    offset = sum / N;
}
```

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">왜 <code>& 0x0FFF</code>?</b><br>
결과 레지스터에 잡것이 섞일 수 있어 <b>하위 12비트(0xFFF)만</b> 마스킹해 순수 변환값을 뽑습니다.</div>

> 🔎 **쉽게:** `vCalibrateOffset`은 체중계의 "영점(Tare)" 버튼. 모터 끄고 0A일 때 여러 번 재서 평균을 기준으로 저장.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
초기화는 <b>전원→PRESCALE→SOC→INTSEL</b> 순. 읽으면 <code>&0x0FFF</code>, 변환은 <b>SCALE×(raw−offset)</b>, offset은 0A에서 평균.</div>

---

<!--LV 6-->
## Lv 6 · 수치 계산 직접 해보기

실제 숫자를 넣어 손으로 풀어봅니다. (예시 값, 보드별 다름)

**① ADCCLK 산출** — SYSCLK = 200MHz, PRESCALE = 4 라면
> ADCCLK = 200MHz / 4 = **50MHz** (주기 = 20ns)

**② 획득시간** — ACQPS = 14 라면 (★SYSCLK로 셈, ADCCLK 아님!)
> 획득시간 = (14+1) × (1/200MHz) = 15 × 5ns = **75ns**
> → 12비트 최소치(~75ns)에 **딱 맞음** (여유 없음! 센서 임피던스가 크면 ACQPS를 더 키워야 함)

**③ raw → 전압** — raw = 2048 일 때
> V = raw × 3.3 / 4096 = 2048 × 0.000806 ≈ **1.65V** (정확히 중간값)

**④ 분압회로 역산** — ADC핀이 1.65V인데 앞단에 10:1 분압이 있었다면
> 실제 측정점 전압 = 1.65V × 10 = **16.5V**

| 입력 raw | ADC핀 전압 (×3.3/4096) | 분압 10:1 환산 |
|---|---|---|
| 0 | 0 V | 0 V |
| 1024 | 0.825 V | 8.25 V |
| 2048 | 1.650 V | 16.5 V |
| 4095 | 3.299 V | 32.99 V |

> 🔎 **쉽게:** 분압은 큰 전압을 ADC가 견디는 3.3V 이하로 "줄여서" 넣은 것. 그래서 읽고 나서 **나눈 비율만큼 다시 곱해** 원래 전압을 복원.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
ADCCLK=SYSCLK/PRESCALE(변환용), 획득시간=(ACQPS+1)/<b>SYSCLK</b>(최소 75ns). <b>V = raw×3.3/4096</b>, 분압이 있으면 분압비만큼 <b>되곱</b>한다.</div>

---

<!--LV 7-->
## Lv 7 · 비이상·실무 (드리프트·노이즈·동기샘플링)

이상적 공식 너머, 현장에서 값을 망치는 것들.

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">오프셋·게인 드리프트 (온도)</b><br>
센서·증폭기는 온도가 오르면 영점과 배율이 조금씩 변합니다. 시동 시 잡은 offset이 운전 중 어긋날 수 있음 → 주기적 재보정 고려.</div>

**노이즈 줄이기 — 평균의 힘**

- **오버샘플링:** 같은 값을 여러 번 빠르게 읽어 평균. 랜덤 잡음은 √N배로 줄어듦.
- **이동평균(Moving average) 필터:** 최근 N개 평균을 계속 갱신해 출렁임을 매끈하게.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">★ PWM과 동기 샘플링</b><br>
PWM 스위칭으로 전류엔 톱니 같은 리플이 끼어 있습니다. <b>PWM 캐리어가 0(골) 또는 꼭대기(피크)인 순간</b>에 샘플하면 리플의 한가운데(평균 지점)를 잡아 <b>평균전류</b>를 깔끔히 읽습니다.</div>

> 🔎 **쉽게:** 그네가 위아래로 흔들릴 때, **딱 가운데를 지나는 순간** 키를 재면 평균 위치가 나오죠. 동기 샘플링이 그 타이밍.

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">EOC 후에 쓰기</b><br>
변환완료(EOC) 전에 결과를 읽으면 <b>이전 변환값</b>을 쓰게 됩니다. 반드시 EOC 인터럽트에서 사용.</div>

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
드리프트는 재보정, 잡음은 오버샘플링/이동평균. PWM <b>골·피크에서 동기 샘플</b>하면 리플을 피해 평균전류를 읽는다.</div>

---

<!--LV 8-->
## Lv 8 · (이론) 샘플링 정리와 에일리어싱

왜 동기 샘플링이 옳은지 신호처리 이론으로.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">나이퀴스트 정리</b><br>
신호를 잃지 않고 복원하려면 <b>샘플링 주파수 fs &gt; 2 × fmax</b> (신호 최고주파수의 2배 초과). 못 지키면 가짜 저주파가 생김.</div>

**에일리어싱(Aliasing)** = 너무 드물게 샘플해서 빠른 신호가 **느린 가짜 신호로 둔갑**하는 현상.

> 🔎 **쉽게:** 영화에서 빠르게 도는 바퀴가 **거꾸로 도는 것처럼** 보이는 것. 카메라(샘플)가 바퀴(신호)를 못 따라잡아 생긴 착시.

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">동기 샘플링이 에일리어싱을 피하는 원리</b><br>
전류 리플의 주성분은 PWM 주파수에 있습니다. <b>PWM과 같은 주파수로(골·피크에) 동기 샘플</b>하면, 리플 성분이 항상 같은 위상에서 잡혀 <b>0Hz(DC=평균)로 정렬</b>됩니다. 즉 리플이 가짜 저주파로 접히지 않고 평균전류만 남습니다.</div>

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
<b>fs &gt; 2·fmax</b>(나이퀴스트). 못 지키면 에일리어싱(가짜 저주파). PWM 동기 샘플은 리플을 평균(DC)으로 정렬해 이를 피한다.</div>

---

<!--LV 9-->
## Lv 9 · 센서·회로 설계

전류를 전압으로 바꾸는 앞단 회로를 설계 관점에서.

| 방식 | 원리 | 장점 | 단점 |
|---|---|---|---|
| 션트저항 | `V=I·R`, 작은 저항의 전압강하 측정 | 싸고 정확, 빠름 | 절연 안 됨, 손실(I²R) |
| 홀센서(절연형) | 자기장으로 전류 감지 | **절연**, 큰 전류 OK | 비싸고 대역·정밀도 한계 |

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">션트 = 작게 vs 신호 키우기</b><br>
션트저항을 작게 하면 손실(I²R)과 발열이 줄지만 전압신호도 작아집니다. 그래서 <b>OP-AMP로 증폭</b>해 ADC 범위(3.3V)에 맞춥니다. 단, OP-AMP의 <b>입력 임피던스/부하효과</b>와 <b>대역폭</b>이 측정 정확도·속도를 좌우.</div>

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">안티에일리어싱 RC 필터</b><br>
ADC 앞에 저역통과 RC 필터를 둬 고주파 잡음이 접히는 것을 막습니다. 차단주파수 <b>fc = 1/(2πRC)</b>. 신호 대역은 통과시키되 fs/2 위 성분은 충분히 줄이도록 설계. 단 R이 너무 크면 획득시간(ACQPS) 부담↑.</div>

> 🔎 **쉽게:** 션트는 "얇은 저울추"라 신호가 작아서 **돋보기(OP-AMP)** 로 키워 봅니다. RC 필터는 그 앞에 낀 잔떨림을 걸러주는 체.

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
션트(싸고 비절연·OP-AMP 증폭) vs 홀센서(절연·고전류). 앞단 <b>RC 안티에일리어싱(fc=1/2πRC)</b> 필요, R↑은 획득시간 부담.</div>

---

<!--LV 10-->
## Lv 10 · 고급/연구 — 상전류 재구성

3상 모터의 전류를 몇 개의 션트로 알아내는 기술.

<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">3션트</b><br>
세 상(a,b,c) 각각에 션트. 가장 정확·단순하지만 부품·채널이 많고, 동기 샘플 타이밍 관리 필요.</div>
<div style="background:#eef4fb;border-left:6px solid #2f5f8f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#2f5f8f;">2션트</b><br>
두 상만 재고 나머지는 키르히호프 법칙으로 계산: <b>ia + ib + ic = 0 → ic = −ia − ib</b>. 션트 1개·채널 1개 절약.</div>
<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">1션트 (DC링크 전류 재구성)</b><br>
DC링크(인버터 입력)에 션트 1개만. PWM 한 주기 안에서 스위칭 상태가 바뀌므로, <b>구간별로 두 번 샘플</b>하면 그 순간 DC링크에 흐르는 전류가 어느 상 전류인지가 정해져 상전류를 복원. 가장 저비용·절연 단순. <b>단 측정창 제약</b>이 큼.</div>

> 🔎 **쉽게:** 1션트는 좁은 문 하나로 사람을 세는 것 — **한 명씩 지나가는 짧은 순간**에만 셀 수 있어, 두 사람이 거의 동시에 지나가면(측정창 부족) 못 셉니다.

<div style="background:#fbf4e8;border-left:6px solid #e0922f;padding:10px 14px;margin:7px 0;border-radius:6px;"><b style="color:#c0763a;">오버모듈레이션 시 측정창 부족 (검증필요)</b><br>
듀티가 100%에 가깝거나 두 상 듀티가 비슷하면 특정 스위칭 구간이 너무 짧아 S/H 획득시간을 못 채웁니다. → 보상기법(최소펄스 삽입, 측정용 PWM 변형) 필요. 1션트의 핵심 난제.</div>

<div style="background:#e8f5ee;border:1px solid #2e9e6b;border-radius:6px;padding:10px 14px;margin:10px 0;"><b style="color:#2e9e6b;">✔ 이것만 기억</b><br>
3션트(정확) → 2션트(<b>ic=−ia−ib</b>) → 1션트(DC링크, 최저비용이나 <b>측정창 제약</b>). 저비용일수록 타이밍 설계가 까다롭다.</div>
