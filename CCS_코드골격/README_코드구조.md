# CCS C코드 골격 — 학습자료와 1:1 대응

TMS320F28377D + CCS 에서 PMSM을 FOC로 돌리는 코드의 **뼈대**입니다.
실제 동작 코드가 아니라 **"어떤 파일이 어떤 일을 하고, 어떤 순서로 도는지"** 를
학습자료(00~04)와 짝지어 익히는 용도입니다.

> ⚠️ **이 코드는 그대로 빌드되지 않습니다.** TI의 `C2000Ware` / `F2837xD` 헤더
> (`F28x_Project.h` 등)와 연구실 Base 코드가 있어야 컴파일됩니다. 레지스터 이름·
> 흐름은 28377D 실제 구조를 따릅니다. 목적은 **구조 이해**.

---

## 파일 ↔ 학습자료 대응표

| 파일 | 하는 일 | 학습자료 |
|---|---|---|
| `main.c` | 클록·PIE·인터럽트·주변장치 초기화 → 인터럽트 허용 → 대기 | **01** (PIE/IER/EINT) |
| `Gpio_setup.c` | LED 핀 설정·토글 | **01** (GPIO) |
| `EPwm_setup.c` | PWM 캐리어·듀티·데드타임·인터럽트 발생 | **02** (TB/CC/AQ/DB/ET) |
| `Adc_setup.c` | 전류 읽기·스케일·오프셋 교정 | **03** (SAR/Scale/Offset) |
| `Encoder.c` | 회전자 각도 읽기(SPI) | **04** + 통신탭(SPI) |
| `foc_lib.c/.h` | Clarke/Park/역Park/PI | **04** (좌표변환·PI) |
| `FocInterrupt.c` | ★제어 본체(20kHz) — 자료 4개가 만나는 곳 | **01·02·03·04 전부** |
| `GlobalVar.h` | 파라미터·전역상태·구조체 | **04** |

---

## 프로그램이 도는 순서 (실행 흐름)

```
[전원 ON]
   │
   ▼  main.c
 ① InitSysCtrl()            클록 공급                      (자료01)
 ② DINT/PIE/IER/IFR/벡터    인터럽트 표 만들기              (자료01)
 ③ PieVectTable.EPWM1_INT = &vFsampInterrupt   인터럽트↔함수 연결 (자료01)
 ④ vInitGpioLed/Adc/EPwm    주변장치 초기화          (자료01/03/02)
 ⑤ vInitController/Calibrate 제어기·오프셋 준비       (자료04/03)
 ⑥ IER|=M_INT3; PIEIER3.INTx1=1; EINT; ERTM;  인터럽트 ON (자료01)
   │
   ▼  while(1)  ← CPU는 여기서 (거의) 논다
        ▲
        │  20kHz마다 ePWM ET가 인터럽트 발생 (자료02 → 자료01)
        ▼
   ★ vFsampInterrupt()   ← 50us마다 자동 실행 (FocInterrupt.c)
        ① ADC 전류 읽기                         (자료03)
        ② 엔코더 각도 θe                        (자료04)
        ③ Clarke (3상→2상)                      (자료04)
        ④ 모드별 제어 V/F·I/F·Vector·Speed      (자료04)
        ⑤ 역Clarke → 듀티                       (자료04→02)
        ⑥ ePWM CMPA 출력                        (자료02)
        ⑦ 플래그 클리어 + PIEACK                (자료01)
```

이 그림의 **★ 부분이 프로그램 "1. 제어 시뮬레이터" 탭에서 눈으로 보던 바로 그 루프**입니다.
시뮬레이터의 `core/motor.py` 와 이 `FocInterrupt.c` 는 **같은 수식·같은 순서**예요.

---

## 시뮬레이터(Python) ↔ 실코드(C) 비교

| 개념 | 시뮬레이터 (`core/motor.py`) | 실코드 (CCS) |
|---|---|---|
| 제어 1스텝 | `PMSM.step(dt)` | `vFsampInterrupt()` |
| Clarke/Park | `clarke()/park()` | `foc_lib.c` 동일 |
| PI 제어 | `class PI` | `pi_update()` |
| 전류 측정 | 모델이 계산 | `vScaleAdcValue()` (ADC) |
| 각도 | 모델 적분 | `vReadEncoderTheta()` (엔코더) |
| 전압 출력 | 모델에 직접 | `vSetPwmDuty()` → CMPA |

> 즉, **Python 시뮬레이터로 원리를 이해 → 이 C골격으로 실제 MCU 구현을 매핑**하면
> PLECS→CCS 로 넘어가는 자료04 D절의 워크플로우를 그대로 따라가는 셈입니다.

---

## 실제로 보드에 올리려면 (다음 단계)
1. CCS에서 연구실 **Base 코드**로 프로젝트 생성 (자료01 C절, 한글경로 금지).
2. 이 파일들의 **함수 본체를 Base 코드의 해당 위치에 이식**.
3. `SCALE_ADC_CURRENT`, 모터 파라미터(`GlobalVar.h`)를 **실제 보드/모터 값으로 교정**.
4. 자료04 순서대로 검증: **V/F → I/F → Vector → Speed**, 그리고 PLECS/RT-BOX 먼저.
5. CCS **Expression 창**에 `g`(FocState)를 등록해 id/iq/θe/duty 를 실시간 관찰.
