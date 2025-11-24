@echo off
chcp 65001 >nul
echo ===============================================
echo   캠핑 예약 자동화 시스템 서버 시작
echo ===============================================
echo.

REM 현재 디렉토리를 배치 파일의 위치로 변경
cd /d "%~dp0"

REM 현재 디렉토리 확인
echo [정보] 현재 위치: %CD%
echo.

REM 백엔드 서버 시작 (포트 5001)
echo [1/2] Flask 백엔드 서버 시작 중... (포트: 5001)
start "Flask Backend Server" cmd /k "cd /d "%~dp0backend" && venv\Scripts\python.exe run.py"
timeout /t 3 /nobreak >nul
echo ✓ 백엔드 서버 시작됨
echo.

REM 프론트엔드 서버 시작 (포트 4000)
echo [2/2] React 프론트엔드 서버 시작 중... (포트: 4000)
start "React Frontend Server" cmd /k "cd /d "%~dp0frontend" && npm run dev"
timeout /t 3 /nobreak >nul
echo ✓ 프론트엔드 서버 시작됨
echo.

echo ===============================================
echo   서버 시작 완료!
echo ===============================================
echo.
echo   • 프론트엔드: http://localhost:4000
echo   • 백엔드 API: http://localhost:5001/api
echo.
echo   서버를 종료하려면 각 창에서 Ctrl+C를 누르세요.
echo ===============================================
echo.
pause
