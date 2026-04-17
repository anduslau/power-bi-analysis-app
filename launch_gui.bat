@echo off
echo Launching Report to Business Documents Application GUI...
echo.

REM Check if GUI executable exists
if exist venv\Scripts\power-bi-gui.exe (
    echo Starting GUI...
    venv\Scripts\power-bi-gui.exe
    if %ERRORLEVEL% neq 0 (
        echo.
        echo GUI exited with error code %ERRORLEVEL%.
        echo If the GUI window didn't appear, check for error messages above.
        pause
    )
) else (
    echo ERROR: GUI executable not found.
    echo Please run install.bat first to install the application.
    echo.
    pause
    exit /b 1
)