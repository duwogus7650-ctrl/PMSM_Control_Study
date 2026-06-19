//############################################################################
// foc_lib.c  —  FOC 수학 라이브러리 구현
//----------------------------------------------------------------------------
// [학습자료 연결] 04_PMSM제어.md
// ★ 핵심 교훈(자료04 E절): 제어 계산은 반드시 float 로! (정수연산 버그 주의)
//############################################################################
#include "foc_lib.h"

float wrap_angle(float a)
{
    while (a >  PI_F) a -= TWO_PI;
    while (a < -PI_F) a += TWO_PI;
    return a;
}

// --- Clarke: 3상 -> 2상 (진폭 불변형) -------------------------------------
void clarke(float ia, float ib, float ic, float *alpha, float *beta)
{
    *alpha = (2.0f*ia - ib - ic) / 3.0f;
    *beta  = (ib - ic) / SQRT3;
}

// --- Park: 고정좌표 -> 회전(dq)좌표 ---------------------------------------
// theta = 회전자 전기각. 회전자와 같이 도는 시점에서 보면 전류가 직류처럼 보인다.
void park(float alpha, float beta, float theta, float *d, float *q)
{
    float c = cosf(theta), s = sinf(theta);
    *d =  alpha*c + beta*s;
    *q = -alpha*s + beta*c;
}

// --- inv Park: 회전(dq) -> 고정좌표 ---------------------------------------
void inv_park(float d, float q, float theta, float *alpha, float *beta)
{
    float c = cosf(theta), s = sinf(theta);
    *alpha = d*c - q*s;
    *beta  = d*s + q*c;
}

// --- inv Clarke + 듀티 환산 ------------------------------------------------
// alpha-beta 전압 -> 3상 전압 -> 0~1 듀티.
// 여기서는 이해를 위한 단순 변환. 실제 연구실 코드는 SVPWM(공간벡터)을 써서
// 전압 활용도를 ~15% 높인다(자료04). 구조는 동일: "전압 -> 듀티 -> CMPA".
void inv_clarke_to_duty(float alpha, float beta, float vdc,
                        float *da, float *db, float *dc)
{
    float va = alpha;
    float vb = -0.5f*alpha + (SQRT3/2.0f)*beta;
    float vc = -0.5f*alpha - (SQRT3/2.0f)*beta;
    // 상전압(-vdc/2 ~ +vdc/2)을 듀티(0~1)로: 0.5 중심에 매핑
    *da = 0.5f + va / vdc;
    *db = 0.5f + vb / vdc;
    *dc = 0.5f + vc / vdc;
    // 포화
    if (*da > 1.0f) *da = 1.0f; if (*da < 0.0f) *da = 0.0f;
    if (*db > 1.0f) *db = 1.0f; if (*db < 0.0f) *db = 0.0f;
    if (*dc > 1.0f) *dc = 1.0f; if (*dc < 0.0f) *dc = 0.0f;
}

// --- PI 제어기 (적분 와인드업 방지) ---------------------------------------
float pi_update(PI_t *pi, float error, float dt)
{
    pi->integ += error * dt;
    // 적분항이 출력 한계를 넘지 않도록 제한 (anti-windup)
    float i_lim = (pi->Ki > 1e-9f) ? (pi->out_max / pi->Ki) : 0.0f;
    if (pi->integ >  i_lim) pi->integ =  i_lim;
    if (pi->integ < -i_lim) pi->integ = -i_lim;

    float out = pi->Kp*error + pi->Ki*pi->integ;
    if (out >  pi->out_max) out =  pi->out_max;
    if (out < -pi->out_max) out = -pi->out_max;
    return out;
}

void pi_reset(PI_t *pi) { pi->integ = 0.0f; }
