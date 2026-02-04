@echo off
echo.
echo ========================================
echo Restarting MATRIYA Backend Server
echo ========================================
echo.
echo Please stop the current server (Ctrl+C) if it's running
echo Then press any key to start the server...
pause >nul
echo.
cd back
python main.py
