# -*- coding: utf-8 -*-
"""모터 물리 엔진 자가검증 (GUI 붙이기 전에 숫자가 맞는지 확인)."""
import io, sys, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.motor import PMSM, MotorParams, clarke, park, inv_park, TWO_PI

DT = 1e-5

def run(m, seconds):
    n = int(seconds / DT)
    for _ in range(n):
        m.step(DT)

def check(name, cond, detail):
    tag = "PASS" if cond else "**FAIL**"
    print(f"[{tag}] {name}: {detail}")
    return cond

ok = True

# 0) Clarke/Park 왕복 변환이 원래 값으로 돌아오는지 (수학 검증)
ia, ib, ic = 1.0, -0.5, -0.5
al, be = clarke(ia, ib, ic)
d, q = park(al, be, 0.7)
al2, be2 = inv_park(d, q, 0.7)
ok &= check("Clarke/Park 왕복", abs(al-al2) < 1e-9 and abs(be-be2) < 1e-9,
            f"alpha {al:.4f}->{al2:.4f}, beta {be:.4f}->{be2:.4f}")

# 1) VECTOR 모드: iq_ref=2A, 무부하 -> 초기에 iq가 지령을 추종하는지
m = PMSM()
m.mode = "VECTOR"
m.id_ref, m.iq_ref, m.load_torque = 0.0, 2.0, 0.0
run(m, 0.003)  # 3ms (전기 시정수 0.67ms의 ~4.5배)
ok &= check("전류제어 추종(iq)", abs(m.s.iq - 2.0) < 0.3,
            f"iq={m.s.iq:.3f}A (목표 2.0A)")
ok &= check("d축 분리(id~0)", abs(m.s.id) < 0.3, f"id={m.s.id:.3f}A (목표 0)")

# 2) 토크 부호: +iq -> +회전
ok &= check("토크/회전 부호", m.s.Te > 0 and m.s.wm > 0,
            f"Te={m.s.Te*1000:.2f}mN·m, wm={m.s.wm:.2f}rad/s (양수여야 함)")

# 3) 토크 상수 검증: Te ≈ Kt*iq
Kt = m.p.Kt
ok &= check("토크상수 Te=Kt*iq", abs(m.s.Te - Kt*m.s.iq) < 1e-4,
            f"Te={m.s.Te:.5f}, Kt*iq={Kt*m.s.iq:.5f}")

# 4) SPEED 모드: 400rpm 지령 + 소부하 -> 정상상태에서 속도 추종
m2 = PMSM()
m2.mode = "SPEED"
m2.id_ref = 0.0
m2.speed_ref_rpm = 400.0
m2.load_torque = 0.03  # 30 mN·m 부하
run(m2, 1.5)  # 1.5초 -> 정착
err = abs(m2.speed_rpm - 400.0)
ok &= check("속도제어 추종(400rpm)", err < 15.0,
            f"속도={m2.speed_rpm:.1f}rpm (오차 {err:.1f}rpm)")
# 정상상태 토크 균형: Te ≈ TL + B*wm
bal = m2.s.Te - (m2.load_torque + m2.p.B * m2.s.wm)
ok &= check("정상상태 토크균형", abs(bal) < 5e-3,
            f"Te-(TL+B*wm)={bal*1000:.3f} mN·m (≈0이어야)")

# 5) 부하 토크 반대로 주면(발전 영역) iq 부호 반전 확인
m3 = PMSM()
m3.mode = "SPEED"
m3.speed_ref_rpm = 300.0
m3.load_torque = -0.03  # 모터를 떠미는 방향
run(m3, 1.5)
ok &= check("음(-)부하시 iq 음수", m3.s.iq < 0,
            f"iq={m3.s.iq:.3f}A (음수여야)")

# 6) NaN/발산 안 하는지 (수치 안정성)
finite = all(math.isfinite(x) for x in (m2.s.id, m2.s.iq, m2.s.wm, m2.s.Te))
ok &= check("수치 안정성(발산X)", finite, "모든 상태값 유한")

print("\n" + ("== 모든 검증 통과 ==" if ok else "== 일부 실패: 모델 수정 필요 =="))
sys.exit(0 if ok else 1)
