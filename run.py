# -*- coding: utf-8 -*-
"""PMSM 학습툴 오프라인 실행 런처.

하는 일:
  1) Python 버전과 필수 패키지가 갖춰졌는지 먼저 확인한다.
  2) 빠진 게 있으면 '무엇을 어떻게 설치하면 되는지' 친절히 안내하고 멈춘다.
  3) 다 갖춰졌으면 GUI(main.py)를 실행한다.

사용법:
  python run.py            # 일반 실행
  python run.py --check    # 환경만 점검(설치/CI용). OK면 종료코드 0.
  (Windows 는 run.bat 더블클릭으로도 실행)
"""
import sys

MIN_PY = (3, 9)

# (import 이름, pip 패키지 이름)
REQUIRED = [
    ("PyQt6", "PyQt6"),
    ("pyqtgraph", "pyqtgraph"),
    ("markdown", "Markdown"),
]
OPTIONAL = [
    ("win32com", "pywin32"),   # AI 강사 음성(Windows). 없으면 자막만 표시.
]


def check_env(verbose=True):
    """환경 점검. 필수 충족 시 True."""
    if sys.version_info < MIN_PY:
        if verbose:
            print(f"[오류] Python {MIN_PY[0]}.{MIN_PY[1]}+ 필요 "
                  f"(현재 {sys.version.split()[0]})")
        return False

    missing = []
    for mod, pkg in REQUIRED:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)

    if missing:
        if verbose:
            print("[필수 패키지 없음] :", ", ".join(missing))
            print("  온라인 설치 :  python -m pip install -r requirements.txt")
            print("  오프라인 설치:  python -m pip install --no-index "
                  "--find-links=wheels -r requirements.txt")
        return False

    if verbose:
        for mod, pkg in OPTIONAL:
            try:
                __import__(mod)
            except ImportError:
                print(f"[안내] 선택 패키지 '{pkg}' 없음 → "
                      f"AI 강사 음성 꺼짐(자막은 정상 동작).")
    return True


def main():
    if "--check" in sys.argv:
        ok = check_env(verbose=True)
        print("ENV_OK" if ok else "ENV_MISSING")
        sys.exit(0 if ok else 1)

    if not check_env(verbose=True):
        sys.exit(1)

    from main import main as run_app
    run_app()


if __name__ == "__main__":
    main()
