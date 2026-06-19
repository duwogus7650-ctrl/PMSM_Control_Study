//############################################################################
// foc_lib.h  —  FOC 수학 라이브러리 (좌표변환 + PI 제어기)
//----------------------------------------------------------------------------
// [학습자료 연결] 04_PMSM제어.md  B절(Clarke/Park), C절(PI)
//############################################################################
#ifndef FOC_LIB_H_
#define FOC_LIB_H_

#include "GlobalVar.h"

// 3상(abc) -> 2상 고정좌표(alpha-beta)  [자료04: Clarke]
void clarke(float ia, float ib, float ic, float *alpha, float *beta);

// 고정좌표(alpha-beta) -> 회전좌표(dq)   [자료04: Park]
void park(float alpha, float beta, float theta, float *d, float *q);

// 회전좌표(dq) -> 고정좌표(alpha-beta)    [자료04: 역Park]
void inv_park(float d, float q, float theta, float *alpha, float *beta);

// 2상(alpha-beta) -> 3상 듀티(0~1)  (자료02 ePWM CMPA 로 들어감)
void inv_clarke_to_duty(float alpha, float beta, float vdc,
                        float *da, float *db, float *dc);

// PI 제어기 한 스텝  [자료04: PI]
float pi_update(PI_t *pi, float error, float dt);
void  pi_reset(PI_t *pi);

// 각도 -pi~+pi 정규화
float wrap_angle(float a);

#endif /* FOC_LIB_H_ */
