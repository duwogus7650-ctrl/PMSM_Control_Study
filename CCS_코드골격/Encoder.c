//############################################################################
// Encoder.c  —  회전자 각도 읽기 (자기식 엔코더, SPI)
//----------------------------------------------------------------------------
// [학습자료 연결] 04_PMSM제어.md(각도가 왜 필요한지) + 프로그램 "통신 탭"(SPI)
//
// AS5047P 같은 엔코더는 SPI로 기계각(0~2pi)을 준다.
// FOC는 "전기각 θe = 극쌍수 × 기계각" 이 필요하다(자료04).
//############################################################################
#include "F28x_Project.h"
#include "GlobalVar.h"

static float theta_m_offset = 0.0f;  // 기계각 영점 (정렬 시 보정)

// SPI로 엔코더 raw 읽기 — 보드/칩에 맞게 구현 (여기선 형태만)
static Uint16 spi_read_encoder_raw(void)
{
    // 실제: SpiaRegs.SPITXBUF = 0xFFFF; while(!RX준비); return SpiaRegs.SPIRXBUF;
    return 0;   // 스텁
}

// 전기각 반환 [rad], -pi~+pi
float vReadEncoderTheta(void)
{
    Uint16 raw = spi_read_encoder_raw();          // 14bit (0~16383)
    float theta_m = ((float)raw / 16384.0f) * TWO_PI - theta_m_offset; // 기계각
    float theta_e = POLE_PAIRS * theta_m;         // 전기각 = P × 기계각
    while (theta_e >  PI_F) theta_e -= TWO_PI;
    while (theta_e < -PI_F) theta_e += TWO_PI;
    return theta_e;
}
