# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation & Setup
```bash
# Install with development dependencies (recommended)
pip install -e ".[dev]"

# Install without development dependencies
pip install -e .

# Interactive configuration wizard
insight-fabric-configure
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_gui.py -v
pytest tests/test_cli.py -v
pytest tests/test_pipeline.py -v

# Run with coverage
pytest --cov=power_bi_analysis
```

### Using the Application
```bash
# Analyze any supported file
insight-fabric-analyze path/to/file.pbix --output-dir ./output

# RDL-specific analysis (no LLM required)
insight-fabric-rdl-analyze path/to/report.rdl --format json

# Launch GUI
insight-fabric-gui

# Compare two BI files
insight-fabric-compare file1.pbix file2.xlsx --output-format markdown

# List supported file extensions
insight-fabric-analyze --list-supported
```

### Code Quality
```bash
# Format code with black
black src/

# Lint with flake8
flake8 src/

# Type checking (if mypy is added)
mypy src/
```

### Helper Scripts
- `install.bat` / `install.sh` - Automated installation for Windows/Linux/Mac
- `run_test.bat` / `run_test.sh` - Run test suites

## Architecture Overview

The application follows a modular, plugin-based architecture with the following key components:

### Core Pipeline (`orchestration/pipeline.py`)
- `AnalysisPipeline` orchestrates the entire analysis workflow:
  1. File validation and metadata extraction via registered extractors
  2. Metadata serialization to compact text format
  3. LLM client initialization based on provider configuration
  4. BRD generation using the LLM
  5. Optional parallel generation of YAML, SQL, and data dictionary outputs
  6. Output saving with statistics collection

### Extractors (`extractors/`)
- Plugin system for different file formats (Power BI, Excel, RDL, CSV, JSON, Parquet)
- Each extractor implements `BaseExtractor` with `can_extract()` and `extract()` methods
- Registry pattern: extractors are registered in `extractors/__init__.py`
- New extractors can be added via `register_extractor()`

### LLM Clients (`llm/`)
- Provider-agnostic interface `BaseLLMClient` with methods for generating BRD, YAML, SQL, and data dictionary
- Supported providers: Anthropic, OpenAI, Gemini (optional)
- Factory pattern: `create_llm_client()` in `llm/factory.py` handles provider-specific initialization
- DeepSeek is supported via OpenAI-compatible endpoint mapping

### Serializers (`serializers/`)
- `MetadataSerializer` converts `ReportMetadata` objects to JSON and compact text formats
- Compact text format is optimized for LLM token usage

### Comparison (`comparison/`)
- `compare_metadata()` compares two `ReportMetadata` objects and produces a `DiffReport`
- Supports rename detection with configurable similarity threshold
- Used by `insight-fabric-compare` CLI

### GUI (`gui/`)
- PyQt6-based graphical interface
- `main_window.py` provides file browser, drag-and-drop, real-time logs, and progress indication

### Configuration (`config.py`)
- `Config` class manages user settings stored in `~/.insight-fabric/config.json`
- Supports multiple LLM providers with separate API keys and models
- Interactive configuration wizard via `insight-fabric-configure`

### Data Models (`models.py`)
- `ReportMetadata`: Structured representation of extracted metadata from any supported file
- `DiffReport`: Results of comparing two metadata sets

## Entry Points

The package provides five console scripts (defined in `setup.py`):
- `insight-fabric-analyze`: Main CLI for analyzing any supported file
- `insight-fabric-rdl-analyze`: Specialized CLI for RDL files (no LLM required)
- `insight-fabric-configure`: Interactive configuration wizard
- `insight-fabric-gui`: Launch the PyQt6 GUI
- `insight-fabric-compare`: Compare two BI files and generate diff report

## Configuration

- User configuration: `~/.insight-fabric/config.json`
- Environment variables for API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`
- DeepSeek configuration: Use `openai` provider with `base_url: "https://api.deepseek.com"` and model `deepseek-chat`

## Testing Strategy

- Unit tests for extractors, LLM clients, serializers, and comparison logic
- Integration tests for the pipeline
- GUI tests using `pytest-qt`
- Sample test files in `test_files/` directory
- Development dependencies include `pytest`, `pytest-qt`, `black`, `flake8`

## File Support

| Format | Extensions | Primary Extractor |
|--------|------------|-------------------|
| Power BI Desktop | `.pbix`, `.pbit`, `.pbip` | `PowerBIExtractor` |
| Excel Workbook | `.xlsx`, `.xlsm` | `ExcelExtractor` |
| RDL Report | `.rdl` | `RDLExtractor` |
| CSV Data | `.csv` | `CSVExtractor` |
| JSON Data | `.json` | `JSONExtractor` |
| Parquet Data | `.parquet` | `ParquetExtractor` |

## Adding New Components

### New Extractor
1. Create class inheriting from `BaseExtractor`
2. Implement `supported_extensions`, `can_extract()`, and `extract()`
3. Register via `register_extractor()` or add to `_EXTRACTORS` in `extractors/__init__.py`

### New LLM Provider
1. Create class inheriting from `BaseLLMClient`
2. Implement `generate_brd()`, `generate_sml_yaml()`, `generate_sql_schema()`, `generate_data_dictionary()`
3. Register via `register_llm_client()` in `llm/factory.py`

## Notes for Developers

- The pipeline supports parallel generation of optional outputs (YAML, SQL, dictionary) when `parallel_generation=True`
- Metadata serialization to compact text is critical for LLM token efficiency
- Error handling: Pipeline collects errors in `self.errors` and continues where possible
- Statistics collection helps monitor performance and token usage
- Comparison functionality is separate from analysis and can be used independently