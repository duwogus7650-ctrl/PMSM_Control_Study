//############################################################################
// FocInterrupt.c  —  제어 인터럽트 (★자료 4개가 전부 만나는 곳)
//----------------------------------------------------------------------------
// [학습자료 연결]
//   - 언제 도는가      : 01_Interrupt_GPIO.md (ePWM 인터럽트가 깨움)
//   - 박자(20kHz)      : 02_ePWM.md (ET 모듈이 발생)
//   - 전류 읽기        : 03_ADC.md
//   - 제어 계산        : 04_PMSM제어.md (Clarke/Park/PI/역Park)
//
// 한 사이클(50us)에 하는 일:  자료04 B절의 ①~⑥ 순서 그대로.
//############################################################################
#include "F28x_Project.h"
#include "GlobalVar.h"
#include "foc_lib.h"

FocState g;   // 전역 상태 (Expression 창에서 관찰)

// 외부(Adc_setup.c)에서 계산된 측정 전류와 함수들
extern float fIo[3];
extern void  vScaleAdcValue(void);
extern void  vSetPwmDuty(float, float, float);
extern float vReadEncoderTheta(void);   // 엔코더 각도 읽기(SPI) — Encoder.c에 구현

//------------------------------------------------------------------
// 제어기 초기화 (main 에서 1회 호출)
//------------------------------------------------------------------
void vInitController(void)
{
    // 전류루프 표준 튜닝: Kp=wc*L, Ki=wc*R  (wc=대역폭, 자료04)
    float wc = TWO_PI * 300.0f;            // 300Hz
    g.pi_id.Kp = wc*LD;  g.pi_id.Ki = wc*RS;  g.pi_id.out_max = VMAX;
    g.pi_iq.Kp = wc*LQ;  g.pi_iq.Ki = wc*RS;  g.pi_iq.out_max = VMAX;
    // 속도루프: 전류루프보다 훨씬 느리게(~10Hz). 출력=iq 지령.
    // Python 시뮬(core/motor.py)과 동일한 표준식: Kp=J*wc/Kt, Ki=B*wc/Kt(+적분여유).
    g.pi_speed.Kp = J_INERTIA * WC_SPEED / KT_CONST;
    g.pi_speed.Ki = B_VISC    * WC_SPEED / KT_CONST + 0.05f;
    g.pi_speed.out_max = IQ_LIMIT;
    pi_reset(&g.pi_id); pi_reset(&g.pi_iq); pi_reset(&g.pi_speed);

    g.mode = MODE_VECTOR;
    g.id_ref = 0.0f; g.iq_ref = 1.0f; g.speed_ref_rpm = 0.0f;
    g.theta_c = 0.0f;
}

//------------------------------------------------------------------
// ★ 제어 인터럽트 본체 (EPWM1_INT). 20kHz로 자동 호출됨.
//   PieVectTable.EPWM1_INT = &vFsampInterrupt;  (main.c 에서 연결)
//------------------------------------------------------------------
interrupt void vFsampInterrupt(void)
{
    float dt = TSAMP;
    float we_ref = POLE_PAIRS * (g.speed_ref_rpm * TWO_PI / 60.0f); // 전기 각속도 지령

    // ── ① ADC: 상전류 읽기 + 스케일/오프셋 (자료03) ──────────────
    vScaleAdcValue();
    g.ia = fIo[0]; g.ib = fIo[1]; g.ic = fIo[2];

    // ── ② 회전자 전기각 읽기 (엔코더, 자료04) ────────────────────
    g.theta_e = vReadEncoderTheta();

    // ── ③ Clarke (3상 -> 2상) ────────────────────────────────────
    clarke(g.ia, g.ib, g.ic, &g.ialpha, &g.ibeta);

    // ── ④ 모드별 제어 (자료04 C절: 제어 4단계) ───────────────────
    switch (g.mode)
    {
    case MODE_VF:   // V/F: 개루프. 명령각 적분 + 주파수 비례 전압
        g.theta_c = wrap_angle(g.theta_c + we_ref*dt);
        {
            float vmag = 0.02f * we_ref;       // V/F 기울기
            if (vmag >  VMAX) vmag =  VMAX;
            if (vmag < -VMAX) vmag = -VMAX;
            inv_park(0.0f, vmag, g.theta_c, &g.valpha, &g.vbeta);
        }
        break;

    case MODE_IF:   // I/F: 명령각 좌표에서 전류제어 (자료04)
        g.theta_c = wrap_angle(g.theta_c + we_ref*dt);
        {
            float idc, iqc;
            park(g.ialpha, g.ibeta, g.theta_c, &idc, &iqc);
            g.vd = pi_update(&g.pi_id, g.id_ref - idc, dt);
            g.vq = pi_update(&g.pi_iq, 0.0f      - iqc, dt);
            inv_park(g.vd, g.vq, g.theta_c, &g.valpha, &g.vbeta);
        }
        break;

    case MODE_VECTOR:  // FOC: 실제 회전자각으로 dq 제어 (자료04 핵심)
        park(g.ialpha, g.ibeta, g.theta_e, &g.id, &g.iq);
        g.vd = pi_update(&g.pi_id, g.id_ref - g.id, dt);
        g.vq = pi_update(&g.pi_iq, g.iq_ref - g.iq, dt);   // iq가 토크!
        inv_park(g.vd, g.vq, g.theta_e, &g.valpha, &g.vbeta);
        break;

    case MODE_SPEED:   // 이중 루프: 속도루프 -> iq지령 -> 전류루프 (자료04)
        park(g.ialpha, g.ibeta, g.theta_e, &g.id, &g.iq);
        {
            float w_ref = g.speed_ref_rpm * TWO_PI / 60.0f;
            float iq_cmd = pi_update(&g.pi_speed, w_ref - g.wm, dt); // 바깥 루프
            g.vd = pi_update(&g.pi_id, g.id_ref - g.id, dt);
            g.vq = pi_update(&g.pi_iq, iq_cmd  - g.iq, dt);          // 안쪽 루프
        }
        inv_park(g.vd, g.vq, g.theta_e, &g.valpha, &g.vbeta);
        break;
    }

    // ── ⑤ 역Clarke -> 듀티 (자료04 → 자료02) ─────────────────────
    inv_clarke_to_duty(g.valpha, g.vbeta, VDC_NOM, &g.duty_a, &g.duty_b, &g.duty_c);

    // ── ⑥ ePWM 듀티 출력 (자료02: CMPA) ──────────────────────────
    vSetPwmDuty(g.duty_a, g.duty_b, g.duty_c);

    // ── 인터럽트 마무리 (자료01: 플래그 클리어 + ACK) ────────────
    EPwm1Regs.ETCLR.bit.INT = 1;                   // ePWM 인터럽트 플래그 클리어
    PieCtrlRegs.PIEACK.all  = PIEACK_GROUP3;       // 그룹3 ACK -> 다음 인터럽트 허용
}
