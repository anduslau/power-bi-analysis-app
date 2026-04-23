@echo off
echo Insight Fabric - Test Runner
echo ====================================
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found.
    echo Please run install.bat first or activate your environment manually.
    echo.
)

REM Run pytest
echo Running tests...
echo.
pytest -v
if errorlevel 1 (
    echo.
    echo WARNING: Some tests failed.
    echo Check the output above for details.
) else (
    echo.
    echo All tests passed ✓
)

echo.
echo ====================================
echo Test Summary
echo.
echo To run specific test groups:
echo   pytest tests/test_gui.py -v
echo   pytest tests/test_cli.py -v
echo   pytest tests/test_pipeline.py -v
echo.
echo To run with coverage:
echo   pytest --cov=power_bi_analysis
echo.
pause