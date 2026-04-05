@echo off
echo Launching Report to Business Documents Application GUI...
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found.
    echo Please run install.bat first or activate your environment manually.
    echo.
)

REM Launch GUI
power-bi-gui