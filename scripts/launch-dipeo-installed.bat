@echo off
echo Starting DiPeO...
echo.

rem Start Backend Server
echo Starting Backend Server...
start "DiPeO Backend" /B "%~dp0dipeo-server.exe"

rem Wait a moment for the backend to start
timeout /t 3 /nobreak > nul

rem Start Frontend
echo Starting Frontend...
start "DiPeO Frontend" /B "%~dp0dipeo-frontend.exe"

echo.
echo DiPeO is now running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop all services...
pause > nul

rem Stop all services
echo.
echo Stopping DiPeO services...
taskkill /FI "WINDOWTITLE eq DiPeO Backend" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq DiPeO Frontend" /F > nul 2>&1
taskkill /IM dipeo-server.exe /F > nul 2>&1
taskkill /IM dipeo-frontend.exe /F > nul 2>&1
echo DiPeO services stopped.