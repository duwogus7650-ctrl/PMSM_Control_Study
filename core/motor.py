# -*- coding: utf-8 -*-
"""
PMSM (영구자석 동기모터) 물리 엔진 + FOC 제어기.

초보자 설명:
  - 이 파일은 '진짜 모터'를 컴퓨터 안에서 흉내 내는 수식 덩어리입니다.
  - 모터는 dq(회전자 기준) 좌표계에서 모델링합니다. dq가 뭔지는
    제어 시뮬레이터 탭에서 그림으로 설명합니다.
  - 제어기(Controller)는 V/F -> I/F -> Vector(FOC) -> Speed 4단계를
    모두 구현했습니다. PDF 5페이지의 '제어 4단계'와 1:1로 대응됩니다.

핵심 수식 (회전자 dq 좌표계):
  d(id)/dt = (Vd - Rs*id + we*Lq*iq) / Ld
  d(iq)/dt = (Vq - Rs*iq - we*Ld*id - we*λ) / Lq
  Te = 1.5 * P * (λ*iq + (Ld - Lq)*id*iq)        # 발생 토크
  d(wm)/dt = (Te - TL - B*wm) / J                 # 뉴턴의 회전 운동방정식
  we = P * wm                                      # 전기각속도 = 극쌍수 * 기계각속도
"""

import math
from dataclasses import dataclass, field

TWO_PI = 2.0 * math.pi


def wrap_angle(a):
    """각도를 -pi ~ +pi 범위로 정규화."""
    a = math.fmod(a, TWO_PI)
    if a > math.pi:
        a -= TWO_PI
    elif a < -math.pi:
        a += TWO_PI
    return a


@dataclass
class MotorParams:
    """소형 24V PMSM의 대표 파라미터 (교육용 기본값)."""
    P: int = 4              # 극쌍수 (pole pairs). 실제 극수 = 2*P = 8극
    Rs: float = 0.30        # 상저항 [Ohm]
    Ld: float = 2.0e-4      # d축 인덕턴스 [H]
    Lq: float = 2.0e-4      # q축 인덕턴스 [H] (표면부착형이면 Ld=Lq)
    lam: float = 6.4e-3     # 영구자석 쇄교자속 λ [Wb]
    J: float = 2.0e-5       # 회전 관성 [kg*m^2]
    B: float = 5.0e-5       # 점성 마찰계수 [N*m*s]
    Vdc: float = 24.0       # DC 링크 전압 [V]

    @property
    def Vmax(self):
        """선형 변조(SVPWM) 영역에서 낼 수 있는 상전압 벡터 크기 한계."""
        return self.Vdc / math.sqrt(3.0)

    @property
    def Kt(self):
        """토크 상수 Te/iq (Ld=Lq일 때) = 1.5*P*λ [N*m/A]."""
        return 1.5 * self.P * self.lam


class PI:
    """간단한 PI 제어기 (적분 와인드업 방지 포함).

    초보자 설명: '목표값 - 현재값(오차)'을 받아서, 오차에 비례(P)하는 양과
    오차를 시간으로 누적(I)한 양을 더해 '얼마나 세게 밀어줄지'를 출력합니다.
    """

    def __init__(self, kp, ki, out_limit):
        self.kp = kp
        self.ki = ki
        self.out_limit = out_limit
        self.integ = 0.0

    def reset(self):
        self.integ = 0.0

    def update(self, error, dt):
        self.integ += error * dt
        # 적분 와인드업 방지: 적분항이 출력 한계를 넘지 않게 제한
        i_limit = self.out_limit / self.ki if self.ki > 1e-9 else 0.0
        if self.integ > i_limit:
            self.integ = i_limit
        elif self.integ < -i_limit:
            self.integ = -i_limit
        out = self.kp * error + self.ki * self.integ
        if out > self.out_limit:
            out = self.out_limit
        elif out < -self.out_limit:
            out = -self.out_limit
        return out


# ---- 좌표 변환 (FOC의 핵심) -------------------------------------------------

def clarke(ia, ib, ic):
    """3상(abc) -> 2상 고정좌표(alpha-beta). 진폭 불변형."""
    ialpha = (2.0 * ia - ib - ic) / 3.0
    ibeta = (ib - ic) / math.sqrt(3.0)
    return ialpha, ibeta


def park(ialpha, ibeta, theta):
    """고정좌표(alpha-beta) -> 회전좌표(dq). theta = 기준 전기각."""
    c, s = math.cos(theta), math.sin(theta)
    d = ialpha * c + ibeta * s
    q = -ialpha * s + ibeta * c
    return d, q


def inv_park(d, q, theta):
    """회전좌표(dq) -> 고정좌표(alpha-beta)."""
    c, s = math.cos(theta), math.sin(theta)
    alpha = d * c - q * s
    beta = d * s + q * c
    return alpha, beta


def inv_clarke(alpha, beta):
    """2상(alpha-beta) -> 3상(abc) 전압."""
    va = alpha
    vb = -0.5 * alpha + (math.sqrt(3.0) / 2.0) * beta
    vc = -0.5 * alpha - (math.sqrt(3.0) / 2.0) * beta
    return va, vb, vc


@dataclass
class SimState:
    id: float = 0.0
    iq: float = 0.0
    wm: float = 0.0          # 기계 각속도 [rad/s]
    theta_m: float = 0.0     # 기계각 [rad]
    theta_e: float = 0.0     # 전기각 [rad]
    theta_c: float = 0.0     # 제어기가 만든 명령각 (V/F, I/F용)
    Te: float = 0.0          # 발생 토크 [N*m]
    # 마지막으로 인가한 전압/측정 전류 (시각화용)
    valpha: float = 0.0
    vbeta: float = 0.0
    ia: float = 0.0
    ib: float = 0.0
    ic: float = 0.0


class PMSM:
    """PMSM 모터 + 인버터 + FOC 제어기 통합 시뮬레이터."""

    MODES = ("VF", "IF", "VECTOR", "SPEED")

    def __init__(self, params: MotorParams = None):
        self.p = params or MotorParams()
        self.s = SimState()
        self.mode = "VECTOR"

        # 지령값 (사용자가 슬라이더로 바꿈)
        self.speed_ref_rpm = 0.0     # 속도 지령 [rpm]
        self.id_ref = 0.0            # d축 전류 지령 [A]
        self.iq_ref = 0.0            # q축 전류 지령 [A] (VECTOR 모드)
        self.load_torque = 0.0       # 부하 토크 [N*m]
        self.vf_gain = 0.02          # V/F 기울기 [V / (rad/s 전기각)]

        self._make_controllers()

    # --- 제어기 게인 설정 ---------------------------------------------------
    def _make_controllers(self):
        p = self.p
        # 전류 루프: 대역폭 wc_i 기준으로 Kp=wc*L, Ki=wc*R (표준 튜닝)
        wc_i = TWO_PI * 300.0   # 전류제어 대역폭 ~300Hz
        self.pi_id = PI(kp=wc_i * p.Ld, ki=wc_i * p.Rs, out_limit=p.Vmax)
        self.pi_iq = PI(kp=wc_i * p.Lq, ki=wc_i * p.Rs, out_limit=p.Vmax)
        # 속도 루프: 전류루프보다 훨씬 느리게 (~10Hz). 출력 = iq 지령
        self.iq_limit = 8.0
        self.pi_spd = PI(kp=p.J * TWO_PI * 10.0 / p.Kt,
                         ki=p.B * TWO_PI * 10.0 / p.Kt + 0.05,
                         out_limit=self.iq_limit)

    def set_gains(self, kp_i=None, ki_i=None, kp_s=None, ki_s=None):
        if kp_i is not None:
            self.pi_id.kp = self.pi_iq.kp = kp_i
        if ki_i is not None:
            self.pi_id.ki = self.pi_iq.ki = ki_i
        if kp_s is not None:
            self.pi_spd.kp = kp_s
        if ki_s is not None:
            self.pi_spd.ki = ki_s

    def reset(self):
        self.s = SimState()
        self.pi_id.reset()
        self.pi_iq.reset()
        self.pi_spd.reset()

    # --- 단위 변환 헬퍼 -----------------------------------------------------
    @property
    def speed_rpm(self):
        return self.s.wm * 60.0 / TWO_PI

    @property
    def speed_ref_rad(self):
        """기계 각속도 지령 [rad/s]."""
        return self.speed_ref_rpm * TWO_PI / 60.0

    # --- 제어기: 모드별로 인가할 (Valpha, Vbeta)를 계산 --------------------
    def _controller(self, dt):
        p, s = self.p, self.s
        we_ref = p.P * self.speed_ref_rad   # 전기 각속도 지령

        if self.mode == "VF":
            # 개루프: 명령각을 적분으로 만들고, 주파수에 비례해 전압 크기 증가
            s.theta_c = wrap_angle(s.theta_c + we_ref * dt)
            vmag = min(abs(self.vf_gain * we_ref), p.Vmax)
            # 전압을 명령각보다 90도 앞선 q축 방향으로 인가(회전자속 견인)
            valpha, vbeta = inv_park(0.0, vmag, s.theta_c)
            return valpha, vbeta

        if self.mode == "IF":
            # 명령각을 개루프로 돌리되, 그 좌표계에서 전류제어 (id->Id_ref, iq->0)
            s.theta_c = wrap_angle(s.theta_c + we_ref * dt)
            ialpha, ibeta = clarke(s.ia, s.ib, s.ic)
            id_c, iq_c = park(ialpha, ibeta, s.theta_c)
            vd = self.pi_id.update(self.id_ref - id_c, dt)
            vq = self.pi_iq.update(0.0 - iq_c, dt)
            return inv_park(vd, vq, s.theta_c)

        if self.mode in ("VECTOR", "SPEED"):
            # 실제 회전자 전기각을 사용한 진짜 벡터제어(FOC)
            ialpha, ibeta = clarke(s.ia, s.ib, s.ic)
            id_m, iq_m = park(ialpha, ibeta, s.theta_e)
            if self.mode == "SPEED":
                # 바깥 속도루프가 iq 지령을 생성 (이중 루프)
                iq_cmd = self.pi_spd.update(self.speed_ref_rad - s.wm, dt)
            else:
                iq_cmd = self.iq_ref
            vd = self.pi_id.update(self.id_ref - id_m, dt)
            vq = self.pi_iq.update(iq_cmd - iq_m, dt)
            return inv_park(vd, vq, s.theta_e)

        return 0.0, 0.0

    # --- 모터 1스텝 적분 (전진 오일러) -------------------------------------
    def step(self, dt):
        p, s = self.p, self.s
        valpha, vbeta = self._controller(dt)
        s.valpha, s.vbeta = valpha, vbeta

        # 인가 전압을 회전자 dq로 변환
        vd = valpha * math.cos(s.theta_e) + vbeta * math.sin(s.theta_e)
        vq = -valpha * math.sin(s.theta_e) + vbeta * math.cos(s.theta_e)

        we = p.P * s.wm
        did = (vd - p.Rs * s.id + we * p.Lq * s.iq) / p.Ld
        diq = (vq - p.Rs * s.iq - we * p.Ld * s.id - we * p.lam) / p.Lq
        s.id += did * dt
        s.iq += diq * dt

        s.Te = 1.5 * p.P * (p.lam * s.iq + (p.Ld - p.Lq) * s.id * s.iq)
        dwm = (s.Te - self.load_torque - p.B * s.wm) / p.J
        s.wm += dwm * dt
        s.theta_m = wrap_angle(s.theta_m + s.wm * dt)
        s.theta_e = wrap_angle(p.P * s.theta_m)

        # 측정 전류(시각화용): dq -> alpha,beta -> abc
        ialpha = s.id * math.cos(s.theta_e) - s.iq * math.sin(s.theta_e)
        ibeta = s.id * math.sin(s.theta_e) + s.iq * math.cos(s.theta_e)
        s.ia, s.ib, s.ic = inv_clarke(ialpha, ibeta)
        return s
