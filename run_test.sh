#!/bin/bash
echo "Insight Fabric - Test Runner"
echo "==================================="
echo

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "WARNING: Virtual environment not found."
    echo "Please run install.sh first or activate your environment manually."
    echo
fi

# Run pytest
echo "Running tests..."
echo
pytest -v
if [ $? -ne 0 ]; then
    echo
    echo "WARNING: Some tests failed."
    echo "Check the output above for details."
else
    echo
    echo "All tests passed ✓"
fi

echo
echo "==================================="
echo "Test Summary"
echo
echo "To run specific test groups:"
echo "  pytest tests/test_gui.py -v"
echo "  pytest tests/test_cli.py -v"
echo "  pytest tests/test_pipeline.py -v"
echo
echo "To run with coverage:"
echo "  pytest --cov=power_bi_analysis"
echo