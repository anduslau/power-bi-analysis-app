@echo off
echo Report to Business Documents Application - Installation Script
echo ===========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ and add to PATH.
    pause
    exit /b 1
)

REM Check Python version >= 3.11
for /f "tokens=2" %%i in ('python --version') do set PYVERSION=%%i
for /f "tokens=1,2 delims=." %%a in ("%PYVERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo ERROR: Python 3.11+ required. Found Python %PYVERSION%
    pause
    exit /b 1
)

if %MAJOR% EQU 3 (
    if %MINOR% LSS 11 (
        echo ERROR: Python 3.11+ required. Found Python %PYVERSION%
        pause
        exit /b 1
    )
)

echo Python %PYVERSION% detected ✓
echo.

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo Virtual environment already exists.
    echo.
) else (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created ✓
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing...
) else (
    echo Pip upgraded ✓
)
echo.

REM Install package in development mode
echo Installing Report to Business Documents Application...
pip install -e ".[dev]"
if errorlevel 1 (
    echo ERROR: Installation failed.
    echo.
    echo Troubleshooting steps:
    echo 1. Check internet connection
    echo 2. Try: pip install -e . (without dev dependencies)
    echo 3. Check Python version compatibility
    pause
    exit /b 1
)
echo Installation completed ✓
echo.

REM Check if configuration already exists
set CONFIG_FILE=%USERPROFILE%\.power-bi-analysis\config.json
if exist "%CONFIG_FILE%" (
    echo Configuration file already exists at:
    echo   %CONFIG_FILE%
    echo.
    set /p RUN_CONFIG="Run configuration wizard anyway? (y/N): "
    if /i "%RUN_CONFIG%"=="y" (
        goto run_config
    ) else (
        goto skip_config
    )
) else (
    goto run_config
)

:run_config
echo.
echo Running configuration wizard...
echo You'll need an API key for your chosen LLM provider.
echo.
echo Available providers:
echo   1. OpenAI (requires OPENAI_API_KEY)
echo   2. Anthropic Claude (requires ANTHROPIC_API_KEY)
echo   3. Google Gemini (requires GEMINI_API_KEY)
echo.
echo Press Ctrl+C to skip configuration (you can run 'power-bi-configure' later)
echo.
power-bi-configure
if errorlevel 1 (
    echo WARNING: Configuration wizard failed or was cancelled.
    echo You can run 'power-bi-configure' manually later.
)
goto after_config

:skip_config
echo Skipping configuration wizard.
echo.

:after_config
echo.
echo ===========================================
echo Installation Complete!
echo.
echo Next steps:
echo 1. Test the installation: run_test.bat
echo 2. Launch GUI: power-bi-gui
echo 3. Analyze a file: power-bi-analyze test_files\sample.pbix
echo 4. Run all tests: pytest
echo.
echo Commands available:
echo   power-bi-analyze    - Analyze BI files with LLM
echo   power-bi-gui        - Launch graphical interface
echo   rdl-analyze         - Extract RDL metadata
echo   power-bi-configure  - Configure API keys and settings
echo   power-bi-compare    - Compare two BI files
echo.
echo To activate the virtual environment in future sessions:
echo   venv\Scripts\activate.bat
echo.
pause