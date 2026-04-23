# Insight Fabric - Installation and Testing Guide

This guide covers installation, configuration, and testing of Insight Fabric.

## Prerequisites

- **Python 3.11 or higher** - Download from [python.org](https://python.org)
- **Git** (optional, for development) - Download from [git-scm.com](https://git-scm.com)
- **LLM API Key** (optional for testing) - Get from your preferred provider:
  - [OpenAI](https://platform.openai.com/api-keys)
  - [Anthropic](https://console.anthropic.com/)
  - [Google AI Studio](https://makersuite.google.com/app/apikey)

## Quick Installation (Automated)

### Windows
1. Open Command Prompt or PowerShell in the project directory
2. Run: `install.bat`
3. Follow the prompts to configure your API key

### Linux/Mac
1. Open Terminal in the project directory
2. Make script executable: `chmod +x install.sh`
3. Run: `./install.sh`
4. Follow the prompts to configure your API key

## Manual Installation

### 1. Clone or Download
```bash
git clone https://github.com/anduslau/insight-fabric-app.git
cd insight-fabric-app
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv
```

### 3. Activate Virtual Environment
```bash
# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

### 4. Install Package
```bash
# Install with development dependencies (recommended)
pip install -e ".[dev]"

# Or without development dependencies
pip install -e .
```

### 5. Configure the Tool
```bash
# Run interactive configuration wizard
insight-fabric-configure

# Or set API key via environment variable
# Windows
set OPENAI_API_KEY=your-key-here

# Linux/Mac
export OPENAI_API_KEY=your-key-here
```

## Testing the Installation

### Run All Tests
```bash
# Using the test scripts
./run_test.bat      # Windows
./run_test.sh       # Linux/Mac

# Or manually
pytest -v
```

### Test Specific Components
```bash
# GUI tests
pytest tests/test_gui.py -v

# CLI tests
pytest tests/test_cli.py -v

# Pipeline tests
pytest tests/test_pipeline.py -v

# Comparison functionality tests
pytest tests/test_comparison.py -v  # If exists
```

### Quick Smoke Tests
```bash
# Check command availability
insight-fabric-analyze --help
insight-fabric-rdl-analyze --help
insight-fabric-gui --help
insight-fabric-compare --help

# List supported file formats
insight-fabric-analyze --list-supported

# Extract metadata from sample files (no LLM required)
insight-fabric-rdl-analyze test_files/sample.rdl --format json
```

## Using the Tool

### Command Line Interface
```bash
# Analyze a Power BI file
insight-fabric-analyze test_files/sample.pbix --output-dir ./output

# Analyze Excel file with all outputs
insight-fabric-analyze test_files/sample.xlsx \
  --generate-yaml \
  --generate-sql \
  --generate-dictionary \
  --llm-provider openai

# Compare two BI files
insight-fabric-compare test_files/sample.pbix test_files/sample.xlsx \
  --output-format markdown \
  --similarity-threshold 0.8
```

### Graphical User Interface
```bash
# Launch the GUI
insight-fabric-gui
```

**GUI Features:**
- File browser with drag-and-drop support
- Real-time log display
- Progress indication
- Comparison functionality
- One-click analysis with configurable options

### Python API
```python
from power_bi_analysis.orchestration.pipeline import AnalysisPipeline

# Create pipeline
pipeline = AnalysisPipeline(
    llm_provider="openai",
    llm_api_key="your-key",
    generate_yaml=True
)

# Analyze file
success = pipeline.analyze_file("report.pbix")

if success:
    # Save outputs
    brd_path, yaml_path, sql_path, dict_path = pipeline.save_outputs("./output")
```

## Sample Files

The `test_files/` directory contains sample files for testing:

- `sample.pbix` - Power BI Desktop file
- `sample.rdl` - SQL Server Reporting Services report
- `sample.xlsx` - Excel workbook
- `sample_data.csv` - CSV data file
- `sample_data.json` - JSON data file
- `sample_data.parquet` - Parquet data file

## Troubleshooting

### Common Issues

**"Python not found" error**
- Ensure Python 3.11+ is installed and in PATH
- Check with `python --version` or `python3 --version`

**Virtual environment activation fails**
- On Windows PowerShell, you may need to set execution policy:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

**"Module not found" errors**
- Ensure virtual environment is activated
- Re-run `pip install -e .`

**LLM API errors**
- Verify API key is correct and has sufficient credits
- Check network connectivity to provider API
- Try setting environment variable instead of config file

**Test failures**
- Ensure all dependencies are installed: `pip install -e ".[dev]"`
- Check Python version compatibility
- Run tests with `-v` flag for detailed output

### Getting Help

- Check the [README.md](README.md) for detailed documentation
- Run `insight-fabric-analyze --help` for CLI options
- Examine generated metadata files for extraction issues
- Enable verbose logging with `--verbose` flag (if implemented)

## Next Steps

1. **Analyze your own files** - Try with actual Power BI, Excel, or RDL files
2. **Explore outputs** - Check generated BRD, YAML, SQL, and dictionary files
3. **Customize configuration** - Edit `~/.insight-fabric/config.json`
4. **Extend the tool** - Add new extractors or serializers
5. **Contribute** - Submit issues or pull requests on GitHub

## Uninstallation

To remove the tool:

1. Delete the virtual environment: `rm -rf venv` (Linux/Mac) or `rmdir /s venv` (Windows)
2. Remove configuration: `rm -rf ~/.insight-fabric` (Linux/Mac) or `rmdir /s %USERPROFILE%\.insight-fabric` (Windows)
3. Uninstall package: `pip uninstall insight-fabric`

---

**Note**: This tool processes sensitive business data. Ensure you have appropriate permissions and comply with data governance policies when analyzing files.