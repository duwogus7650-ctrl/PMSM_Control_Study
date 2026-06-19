//############################################################################
// EPwm_setup.c  —  ePWM 초기화 (PWM 출력 + 제어 인터럽트 발생원)
//----------------------------------------------------------------------------
// [학습자료 연결] 02_ePWM.md 전체.  특히 TB / CC / AQ / DB / ET 5개 모듈.
//
// 이 보드의 EPWM1 을 "제어 박자 시계"로 쓴다:
//   - PWM 캐리어 한 주기마다 ET 모듈이 인터럽트를 발생(자료02 E절)
//   - 그 인터럽트(=FsampInterrupt)에서 FOC 한 사이클 실행(자료01·04)
//############################################################################
#include "F28x_Project.h"
#include "GlobalVar.h"

// TBPRD 계산: 20kHz 만들기 (자료02 주파수 공식)
//   UpDown 모드: Fpwm = PWM_CLK / (2*TBPRD)  =>  TBPRD = PWM_CLK/(2*Fsamp)
volatile Uint16 uMaxCountSamp = 0;

void vInitEPwm(void)
{
    EALLOW;
    // 여러 ePWM의 클럭을 잠깐 멈춰두고 설정 (동기화 위해)
    CpuSysRegs.PCLKCR0.bit.TBCLKSYNC = 0;

    //==================================================================
    // ① TB (Time-Base) 모듈 : 캐리어(박자) 만들기  [자료02 C-①]
    //==================================================================
    uMaxCountSamp = (Uint16)(PWM_CLK / (2.0f * FSAMP));   // UpDown -> /2
    EPwm1Regs.TBPRD = uMaxCountSamp;             // 카운터 꼭대기 = 주파수 결정
    EPwm1Regs.TBCTL.bit.CTRMODE   = TB_COUNT_UPDOWN;  // 좌우대칭 캐리어
    EPwm1Regs.TBCTL.bit.PHSEN     = TB_DISABLE;  // 단독 사용(동기 안받음=Master)
    EPwm1Regs.TBCTL.bit.HSPCLKDIV = TB_DIV1;     // 분주 없음 -> TBCLK=PWM_CLK
    EPwm1Regs.TBCTL.bit.CLKDIV    = TB_DIV1;
    EPwm1Regs.TBCTR = 0;

    //==================================================================
    // ② CC (Counter-Compare) : 듀티 결정 + Shadow 모드  [자료02 C-②]
    //==================================================================
    EPwm1Regs.CMPA.bit.CMPA = uMaxCountSamp / 2; // 초기 듀티 0.5
    // Shadow 모드: 주기 중간에 CMPA 바꿔도 깨끗하게, 카운터=0 일 때 일괄 적용
    EPwm1Regs.CMPCTL.bit.SHDWAMODE = CC_SHADOW;
    EPwm1Regs.CMPCTL.bit.LOADAMODE = CC_CTR_ZERO;

    //==================================================================
    // ③ AQ (Action-Qualifier) : 언제 핀 High/Low?  [자료02 C-③]
    //   UpDown 모드 중심정렬 PWM: 올라갈때 CMPA 만나면 Low, 내려갈때 High
    //==================================================================
    EPwm1Regs.AQCTLA.bit.CAU = AQ_CLEAR;   // 카운터 ↑ 중 CMPA 도달 -> Low
    EPwm1Regs.AQCTLA.bit.CAD = AQ_SET;     // 카운터 ↓ 중 CMPA 도달 -> High

    //==================================================================
    // ④ DB (Dead-Band) : 상보동작 + 데드타임(안전!)  [자료02 C-④]
    //   위/아래 스위치 동시 ON(슛스루) 방지. EPWM1A=H측, EPWM1B=L측
    //==================================================================
    EPwm1Regs.DBCTL.bit.OUT_MODE = DB_FULL_ENABLE;  // A,B 둘 다 데드밴드 적용
    EPwm1Regs.DBCTL.bit.POLSEL   = DB_ACTV_HIC;     // B를 반전(상보)
    EPwm1Regs.DBCTL.bit.IN_MODE  = DBA_ALL;
    // 데드타임 2us = 2e-6 * PWM_CLK 카운트 (자료02 실습값)
    EPwm1Regs.DBRED.bit.DBRED = (Uint16)(2e-6f * PWM_CLK);  // 상승엣지 지연
    EPwm1Regs.DBFED.bit.DBFED = (Uint16)(2e-6f * PWM_CLK);  // 하강엣지 지연

    //==================================================================
    // ⑤ ET (Event-Trigger) : 제어 인터럽트 발생  [자료02 C-⑤ → 자료01]
    //==================================================================
    EPwm1Regs.ETSEL.bit.INTEN  = 1;            // 인터럽트 발생 켜기
    EPwm1Regs.ETSEL.bit.INTSEL = ET_CTR_ZERO;  // 카운터=0(주기시작)에서 발생
    EPwm1Regs.ETPS.bit.INTPRD  = ET_1ST;       // 매 주기마다(1번에 1번)
    EPwm1Regs.ETCLR.bit.INT    = 1;            // 이전 플래그 클리어

    // 클럭 다시 켜기 (모든 ePWM 동기 시작)
    CpuSysRegs.PCLKCR0.bit.TBCLKSYNC = 1;
    EDIS;
}

// 인터럽트 안에서 매 주기 호출: 계산된 듀티(0~1)를 CMPA 로 변환해 출력
void vSetPwmDuty(float da, float db, float dc)
{
    // da만 EPWM1 예시. 실제 3상은 EPWM1/2/3 각각에 da/db/dc 적용.
    EPwm1Regs.CMPA.bit.CMPA = (Uint16)(da * uMaxCountSamp);
    EPwm2Regs.CMPA.bit.CMPA = (Uint16)(db * uMaxCountSamp);
    EPwm3Regs.CMPA.bit.CMPA = (Uint16)(dc * uMaxCountSamp);
}
