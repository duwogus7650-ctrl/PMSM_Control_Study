@echo off
rem PMSM 학습툴 — Windows 더블클릭 실행 런처
chcp 65001 >nul
cd /d "%~dp0"

rem py 런처가 있으면 우선 사용, 없으면 python 사용
where py >nul 2>nul
if %errorlevel%==0 (
    py run.py
) else (
    python run.py
)

rem 오류(패키지 없음 등)로 끝나면 메시지를 읽도록 창을 멈춤
if errorlevel 1 pause
