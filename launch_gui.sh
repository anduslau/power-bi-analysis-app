#!/bin/bash
echo "Launching Report to Business Documents Application GUI..."
echo

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "WARNING: Virtual environment not found."
    echo "Please run install.sh first or activate your environment manually."
    echo
fi

# Launch GUI
power-bi-gui