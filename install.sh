#!/bin/bash
echo "Report to Business Documents Application - Installation Script"
echo "==========================================="
echo

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.11+."
    exit 1
fi

PYVERSION=$(python3 --version | awk '{print $2}')
MAJOR=$(echo $PYVERSION | cut -d. -f1)
MINOR=$(echo $PYVERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ]; then
    echo "ERROR: Python 3.11+ required. Found Python $PYVERSION"
    exit 1
fi

if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]; then
    echo "ERROR: Python 3.11+ required. Found Python $PYVERSION"
    exit 1
fi

echo "Python $PYVERSION detected ✓"
echo

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
    echo
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created ✓"
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment."
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "WARNING: Failed to upgrade pip, continuing..."
else
    echo "Pip upgraded ✓"
fi
echo

# Install package in development mode
echo "Installing Report to Business Documents Application..."
pip install -e ".[dev]"
if [ $? -ne 0 ]; then
    echo "ERROR: Installation failed."
    echo
    echo "Troubleshooting steps:"
    echo "1. Check internet connection"
    echo "2. Try: pip install -e . (without dev dependencies)"
    echo "3. Check Python version compatibility"
    exit 1
fi
echo "Installation completed ✓"
echo

# Check if configuration already exists
CONFIG_FILE="$HOME/.power-bi-analysis/config.json"
if [ -f "$CONFIG_FILE" ]; then
    echo "Configuration file already exists at:"
    echo "  $CONFIG_FILE"
    echo
    read -p "Run configuration wizard anyway? (y/N): " RUN_CONFIG
    if [[ "$RUN_CONFIG" =~ ^[Yy]$ ]]; then
        RUN_CONFIG_WIZARD=1
    else
        RUN_CONFIG_WIZARD=0
    fi
else
    RUN_CONFIG_WIZARD=1
fi

if [ $RUN_CONFIG_WIZARD -eq 1 ]; then
    echo
    echo "Running configuration wizard..."
    echo "You'll need an API key for your chosen LLM provider."
    echo
    echo "Available providers:"
    echo "  1. OpenAI (requires OPENAI_API_KEY)"
    echo "  2. Anthropic Claude (requires ANTHROPIC_API_KEY)"
    echo "  3. Google Gemini (requires GEMINI_API_KEY)"
    echo
    echo "Press Ctrl+C to skip configuration (you can run 'power-bi-configure' later)"
    echo
    power-bi-configure
    if [ $? -ne 0 ]; then
        echo "WARNING: Configuration wizard failed or was cancelled."
        echo "You can run 'power-bi-configure' manually later."
    fi
else
    echo "Skipping configuration wizard."
    echo
fi

echo
echo "==========================================="
echo "Installation Complete!"
echo
echo "Next steps:"
echo "1. Test the installation: ./run_test.sh"
echo "2. Launch GUI: power-bi-gui"
echo "3. Analyze a file: power-bi-analyze test_files/sample.pbix"
echo "4. Run all tests: pytest"
echo
echo "Commands available:"
echo "  power-bi-analyze    - Analyze BI files with LLM"
echo "  power-bi-gui        - Launch graphical interface"
echo "  rdl-analyze         - Extract RDL metadata"
echo "  power-bi-configure  - Configure API keys and settings"
echo "  power-bi-compare    - Compare two BI files"
echo
echo "To activate the virtual environment in future sessions:"
echo "  source venv/bin/activate"
echo