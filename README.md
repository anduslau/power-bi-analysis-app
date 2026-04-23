<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/304b3230-c059-4d0a-a587-000c2394b210" />

# Insight Fabric

An AI-powered tool that analyzes Power BI (.pbix), Excel (.xlsx), and RDL (.rdl) files to automatically generate Business Requirements Documents (BRDs), Semantic YAML definitions, SQL schemas, and data dictionaries using Large Language Models.

## Features

- **Multi-format support**: Analyze Power BI (.pbix/.pbit/.pbip), Excel (.xlsx/.xlsm), RDL (.rdl), and data files (.csv/.json/.parquet)
- **AI-powered analysis**: Uses LLMs (OpenAI, Anthropic Claude, Google Gemini, DeepSeek) to generate comprehensive BRDs
- **Multiple outputs**:
  - Business Requirements Document (BRD) in Markdown format
  - Semantic YAML definition for data modeling
  - SQL schema definitions
  - Data dictionary with column-level documentation
- **Flexible interfaces**:
  - Command-line interface (CLI) for automation
  - Graphical user interface (GUI) with PyQt6
  - Interactive configuration wizard
- **Extensible architecture**: Plugin-based extractors and serializers

## Installation

### Prerequisites

- Python 3.11 or higher
- Git (optional, for development)

### Quick Install

1. Clone or download the repository:
   ```bash
   git clone https://github.com/anduslau/insight-fabric-app.git
   cd insight-fabric-app
   ```

2. Install the package with pip:
   ```bash
   pip install -e .
   ```

3. For development with testing capabilities:
   ```bash
   pip install -e ".[dev]"
   ```

### Dependencies

The tool automatically installs required packages:
- `pbixray` - Power BI file extraction
- `openpyxl` - Excel file support
- `pandas` & `pyarrow` - Data file processing
- `PyQt6` - GUI interface
- LLM providers: `anthropic`, `openai`, `google-generativeai`
- Output formats: `pyyaml`, `python-docx`, `markdown`

## Configuration

Before using the tool, configure your LLM provider and API keys:

### Interactive Configuration

Run the configuration wizard:
```bash
insight-fabric-configure
```

Follow the prompts to:
1. Select LLM provider (OpenAI, Anthropic, Gemini, DeepSeek)
2. Enter API key (stored securely in `~/.insight-fabric/config.json`)
3. Specify default model
4. Set output directory (default: `./analysis_output`)
5. Configure YAML generation preference

### Manual Configuration

Edit the configuration file at `~/.insight-fabric/config.json`:
```json
{
  "llm": {
    "provider": "openai",
    "api_key": "your-api-key-here",
    "model": "gpt-4-turbo-preview",
    "providers": {
      "openai": {
        "api_key": "your-api-key-here",
        "model": "gpt-4-turbo-preview",
        "base_url": null
      }
    }
  },
  "output": {
    "default_dir": "./analysis_output",
    "generate_yaml": true
  }
}
```

### Environment Variables

Alternatively, set API keys via environment variables:
- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Anthropic Claude
- `GEMINI_API_KEY` for Google Gemini
- `DEEPSEEK_API_KEY` for DeepSeek

## Usage

### Command Line Interface (CLI)

#### Analyze any supported file:
```bash
insight-fabric-analyze path/to/your/file.pbix
```

#### Advanced options:
```bash
insight-fabric-analyze path/to/report.pbix \
  --output-dir ./output \
  --generate-yaml \
  --generate-sql \
  --generate-dictionary \
  --llm-provider anthropic \
  --model claude-3-5-sonnet-20241022
```

#### List supported file extensions:
```bash
insight-fabric-analyze --list-supported
```

#### RDL-specific analysis (no LLM required):
```bash
insight-fabric-rdl-analyze path/to/report.rdl --format json --output-dir ./rdl_output
```

### Graphical User Interface (GUI)

Launch the GUI application:
```bash
insight-fabric-gui
```

Or run directly:
```bash
python -m power_bi_analysis.gui.main_window
```

<img width="799" height="745" alt="image" src="https://github.com/user-attachments/assets/1d3f4c17-2dd6-41b9-a0fe-b9689083a9ff" />


**GUI Features:**
- File browser with drag-and-drop support
- Real-time log display
- Progress indication
- One-click analysis with configurable options
- Clear log and output management

### Python API

Use the tool programmatically:
```python
from power_bi_analysis.orchestration.pipeline import AnalysisPipeline

# Create pipeline with configuration
pipeline = AnalysisPipeline(
    llm_provider="openai",
    llm_api_key="your-api-key",
    generate_yaml=True,
    generate_sql=False,
    generate_dictionary=True
)

# Analyze file
success = pipeline.analyze_file("report.pbix")

if success:
    # Save outputs
    brd_path, yaml_path, sql_path, dict_path = pipeline.save_outputs("./output")
    
    # Get statistics
    stats = pipeline.get_stats()
    print(f"Analysis completed in {stats['total_time']:.2f}s")
```

## Output Files

The tool generates the following files in the output directory:

### 1. Business Requirements Document (BRD)
- `{filename}_brd.md` - Comprehensive markdown document containing:
  - Executive summary
  - Business context and objectives
  - Data sources and connections
  - Key metrics and calculations
  - Visualizations and dashboard layout
  - User stories and requirements
  - Technical considerations

### 2. Semantic YAML Definition
- `{filename}_semantic.yaml` - Structured data model definition:
  - Entities and relationships
  - Measures and calculations
  - Hierarchies and dimensions
  - Business logic and rules

### 3. SQL Schema
- `{filename}_schema.sql` - SQL DDL statements:
  - Table definitions with data types
  - Primary and foreign keys
  - Indexes and constraints
  - View definitions

### 4. Data Dictionary
- `{filename}_dictionary.md` - Detailed column documentation:
  - Column names, data types, and descriptions
  - Source tables and transformations
  - Business rules and validation
  - Sample values and patterns

### 5. Metadata Files
- `{filename}_metadata.json` - Raw extracted metadata
- `{filename}_stats.json` - Performance statistics

## Supported File Types

| Format | Extension | Description |
|--------|-----------|-------------|
| Power BI Desktop | `.pbix` | Complete Power BI reports with data |
| Power BI Template | `.pbit` | Template files without data |
| Power BI Project | `.pbip` | Project format for Power BI Desktop |
| Excel Workbook | `.xlsx` | Excel files with data and Power Query |
| Excel Macro-enabled | `.xlsm` | Excel with macros and Power Query |
| RDL Report | `.rdl` | SQL Server Reporting Services reports |
| Comma-Separated Values | `.csv` | Tabular data files |
| JSON Data | `.json` | JSON-structured data |
| Parquet | `.parquet` | Columnar storage format |

## LLM Providers

The tool supports multiple LLM providers:

| Provider | Default Model | Environment Variable |
|----------|---------------|----------------------|
| OpenAI | `gpt-4-turbo-preview` | `OPENAI_API_KEY` |
| Anthropic Claude | `claude-3-5-sonnet-20241022` | `ANTHROPIC_API_KEY` |
| Google Gemini | `gemini-2.0-flash-exp` | `GEMINI_API_KEY` |
| DeepSeek | `deepseek-chat` | `DEEPSEEK_API_KEY` |

### Custom Models and Endpoints

For OpenAI-compatible providers (like DeepSeek, LocalAI, Ollama):
1. Select "openai" as provider
2. Set `--model` to your model name
3. Configure base URL in interactive config or set `base_url` in config file

## Examples

### Example 1: Quick Power BI Analysis
```bash
insight-fabric-analyze sales_dashboard.pbix --output-dir ./sales_analysis
```

### Example 2: Excel File with All Outputs
```bash
insight-fabric-analyze financial_data.xlsx \
  --generate-yaml \
  --generate-sql \
  --generate-dictionary \
  --llm-provider gemini
```

### Example 3: RDL Metadata Extraction
```bash
insight-fabric-rdl-analyze report.rdl --format compact --output-dir ./rdl_metadata
```

## Troubleshooting

### Common Issues

**"API key not found" error**
- Run `insight-fabric-configure` to set API key
- Set environment variable: `export OPENAI_API_KEY="your-key"`
- Check config file permissions

**"File not supported" error**
- Use `--list-supported` to see all extensions
- Ensure file has correct extension
- Check file is not corrupted

**"LLM provider not available" error**
- Install missing provider package: `pip install openai`
- Check API key is valid and has sufficient credits
- Verify network connectivity to provider API

**Slow performance with large files**
- The tool extracts and processes file contents fully
- Consider splitting large Power BI files (>100MB)
- Use `--no-yaml` to skip YAML generation if not needed

### Logging and Debugging

Enable verbose output:
```bash
insight-fabric-analyze file.pbix --verbose  # If implemented
```

Check generated metadata files for extraction issues:
```bash
cat output/filename_metadata.json | jq .  # Use jq for pretty printing
```

## Development

### Project Structure
```
insight-fabric-app/
├── src/power_bi_analysis/
│   ├── extractors/          # File format extractors
│   ├── llm/                # LLM provider implementations
│   ├── orchestration/      # Pipeline and coordination
│   ├── serializers/        # Output format generators
│   ├── gui/               # PyQt6 graphical interface
│   ├── config.py          # Configuration management
│   └── cli.py             # Command-line interface
├── tests/                  # Unit and integration tests
├── setup.py               # Package configuration
└── README.md              # This file
```

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run GUI tests specifically
pytest tests/test_gui.py -v

# Run with coverage
pytest --cov=power_bi_analysis
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Specify license - e.g., MIT License]

## Acknowledgments

- Built with `pbixray` for Power BI file extraction
- Uses multiple LLM providers for intelligent analysis
- PyQt6 for cross-platform GUI
- Inspired by the need for automated documentation in BI workflows

---

**Note**: This tool processes sensitive business data. Ensure you have appropriate permissions and comply with data governance policies when analyzing files.
