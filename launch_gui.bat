@echo off
echo Launching Insight Fabric GUI...
echo.

REM Check if GUI executable exists
if exist venv\Scripts\insight-fabric-gui.exe (
    echo Starting GUI...
    venv\Scripts\insight-fabric-gui.exe
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