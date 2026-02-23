@echo off

echo.
echo === Rebuilding plugin ===
calibre-customize -b .

echo.
echo === Restarting Calibre ===
taskkill /IM calibre.exe /F >nul 2>&1

timeout /t 1 >nul

start "" "C:\Program Files\Calibre2\calibre.exe"

echo.
echo Done.
pause