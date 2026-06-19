//############################################################################
// Gpio_setup.c  —  GPIO 초기화 (LED) + 토글 예제
//----------------------------------------------------------------------------
// [학습자료 연결] 01_Interrupt_GPIO.md  A절(GPIO)
// 28377D Dock 보드: GPIO34 = RED LED, GPIO31 = GREEN LED
//############################################################################
#include "F28x_Project.h"   // TI F2837xD 기본 헤더 (Base 코드에 포함)

void vInitGpioLed(void)
{
    EALLOW;   // 보호 레지스터 쓰기 허용 (28377D는 중요 레지스터가 잠겨있음)

    // --- GPIO34 (RED) ---
    GpioCtrlRegs.GPBMUX1.bit.GPIO34 = 0;   // 0 = 일반 GPIO 기능 (자료01: 범용핀)
    GpioCtrlRegs.GPBDIR.bit.GPIO34  = 1;   // 1 = 출력(Output)
    GpioDataRegs.GPBSET.bit.GPIO34  = 1;   // 처음엔 끔(공통캐소드 기준 High=Off)

    // --- GPIO31 (GREEN) ---
    GpioCtrlRegs.GPAMUX2.bit.GPIO31 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO31  = 1;
    GpioDataRegs.GPASET.bit.GPIO31  = 1;

    EDIS;     // 보호 레지스터 쓰기 잠금
}

// LED 토글: 핀 상태를 뒤집는다 (3.3V<->0V). 자료01의 "GPIO Write".
// 보통 제어 인터럽트보다 느린 주기(예: 1ms)로 호출해 깜빡임을 눈으로 본다.
void vToggleGreenLed(void)
{
    GpioDataRegs.GPATOGGLE.bit.GPIO31 = 1;   // TOGGLE 레지스터 = 한 번에 반전
}
