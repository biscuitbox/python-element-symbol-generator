@echo off
chcp 65001 > nul
cd /d "%~dp0"
python gui.py
if %errorlevel% neq 0 (
    echo.
    echo === 오류가 발생했습니다 ===
    echo 위 메시지를 확인해 주세요.
    echo.
    pause
)
