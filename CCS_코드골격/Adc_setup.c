//############################################################################
// Adc_setup.c  —  ADC 초기화 + 전류/전압 측정(스케일·오프셋)
//----------------------------------------------------------------------------
// [학습자료 연결] 03_ADC.md 전체.  C절(28377D 설정), D절(Scale/Offset)
//############################################################################
#include "F28x_Project.h"
#include "GlobalVar.h"

// 측정 결과 (다른 파일에서 사용)
float fIo[3]      = {0,0,0};   // 실제 전류 [A] (자료03 D절)
float fAdcOffset[3] = {0,0,0}; // 0A 일때 ADC 기준값 (자료03: Calibration)

#define SCALE_ADC_CURRENT  0.01f   // (raw-offset) -> A 환산 배율. ★보드에 맞게 교정
#define ADC_RESULT_MASK    0x0FFFu // 12bit 만 취함 (자료03 과제 주의)

//------------------------------------------------------------------
// ADCA 초기화 (자료03 C절: vInitAdc)
//------------------------------------------------------------------
void vInitAdc(void)
{
    EALLOW;
    // ADC 클럭 = SYSCLK / PRESCALE (자료03: ADCCTL2.PRESCALE)
    AdcaRegs.ADCCTL2.bit.PRESCALE   = 6;   // /4
    // 인터럽트 펄스를 "변환 끝(EOC)"에 발생 (자료03: 타이밍 함정 방지)
    AdcaRegs.ADCCTL1.bit.INTPULSEPOS = 1;
    // ADC 아날로그 회로 전원 ON — 이거 안하면 ADC 작동 안함! (자료03 필수)
    AdcaRegs.ADCCTL1.bit.ADCPWDNZ    = 1;
    DELAY_US(1000);   // 전원 안정화 대기

    // SOC0 설정 (자료03: CHSEL, ACQPS)
    AdcaRegs.ADCSOC0CTL.bit.CHSEL  = 0;    // 채널0 = ADCINA0 (U상 전류 등)
    AdcaRegs.ADCSOC0CTL.bit.ACQPS  = 14;   // 샘플 홀드 시간(최소 75ns 이상)
    AdcaRegs.ADCSOC0CTL.bit.TRIGSEL = 5;   // 트리거원 = EPWM1 SOCA (자료02 ET)

    // SOC1 (V상 등)
    AdcaRegs.ADCSOC1CTL.bit.CHSEL  = 1;
    AdcaRegs.ADCSOC1CTL.bit.ACQPS  = 14;
    AdcaRegs.ADCSOC1CTL.bit.TRIGSEL = 5;

    // 변환 끝(EOC1)에서 ADCINT1 발생하도록
    AdcaRegs.ADCINTSEL1N2.bit.INT1SEL = 1;   // EOC1 -> ADCINT1
    AdcaRegs.ADCINTSEL1N2.bit.INT1E   = 1;
    AdcaRegs.ADCINTFLGCLR.bit.ADCINT1 = 1;   // 플래그 클리어
    EDIS;
}

//------------------------------------------------------------------
// raw 읽고 -> offset 빼고 -> scale 곱해 실제 전류로 (자료03 D절 핵심식)
//   fIo = SCALE * (raw - offset)
//------------------------------------------------------------------
void vScaleAdcValue(void)
{
    Uint16 raw0 = AdcaResultRegs.ADCRESULT0 & ADC_RESULT_MASK;
    Uint16 raw1 = AdcaResultRegs.ADCRESULT1 & ADC_RESULT_MASK;

    fIo[0] = SCALE_ADC_CURRENT * ((float)raw0 - fAdcOffset[0]);  // ia
    fIo[1] = SCALE_ADC_CURRENT * ((float)raw1 - fAdcOffset[1]);  // ib
    fIo[2] = -(fIo[0] + fIo[1]);   // ic = -(ia+ib)  (3상 합=0 가정)
}

//------------------------------------------------------------------
// 오프셋 교정: 0A 상태에서 ADC 값을 N번 평균 (자료03 Calibration)
//   - 기동 전 모터 무전류 상태에서 한 번 호출해 fAdcOffset 채움
//------------------------------------------------------------------
void vCalibrateOffset(void)
{
    const int N = 1000;
    long acc0 = 0, acc1 = 0;
    int i;
    for (i = 0; i < N; i++) {
        // 실제로는 ADCINT1 플래그를 폴링하며 변환완료를 기다려야 함
        while (AdcaRegs.ADCINTFLG.bit.ADCINT1 == 0) { }
        AdcaRegs.ADCINTFLGCLR.bit.ADCINT1 = 1;
        acc0 += (AdcaResultRegs.ADCRESULT0 & ADC_RESULT_MASK);
        acc1 += (AdcaResultRegs.ADCRESULT1 & ADC_RESULT_MASK);
    }
    fAdcOffset[0] = (float)acc0 / N;   // ≈ 0A 일 때 ADC 기본값
    fAdcOffset[1] = (float)acc1 / N;
}
