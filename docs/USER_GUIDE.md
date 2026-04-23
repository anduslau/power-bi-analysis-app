# Insight Fabric - User Guide

## Introduction

Insight Fabric automates the documentation process for business intelligence assets. It extracts metadata from Power BI, Excel, and RDL files, then uses AI to generate comprehensive documentation including Business Requirements Documents (BRDs), semantic data models, SQL schemas, and data dictionaries.

## Quick Start

### Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/anduslau/insight-fabric-app.git
cd insight-fabric-app

# Install the tool
pip install -e .
```

### Step 2: Configuration

Run the interactive configuration wizard:

```bash
insight-fabric-configure
```

Follow the prompts to:
- Select your preferred LLM provider (OpenAI, Anthropic, Gemini, DeepSeek)
- Enter your API key (stored locally in `~/.insight-fabric/config.json`)
- Set default output directory (recommended: `./analysis_output`)
- Choose whether to generate YAML by default

### Step 3: Analyze Your First File

```bash
# Analyze a Power BI file
insight-fabric-analyze path/to/your_report.pbix

# Analyze an Excel file with all outputs
insight-fabric-analyze data/workbook.xlsx \
  --generate-yaml \
  --generate-sql \
  --generate-dictionary

# Extract RDL metadata (no LLM required)
insight-fabric-rdl-analyze reports/dashboard.rdl --format json --output-dir ./rdl_output
```

### Step 4: Review Results

Check the output directory (default: `./analysis_output`) for generated files:
- `{filename}_brd.md` - Complete Business Requirements Document
- `{filename}_semantic.yaml` - Semantic data model
- `{filename}_schema.sql` - SQL schema definition
- `{filename}_dictionary.md` - Data dictionary

## Detailed Usage

### Command Line Interface

#### Basic Syntax
```bash
insight-fabric-analyze [FILE] [OPTIONS]
```

#### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir`, `-o` | Output directory | `./analysis_output` |
| `--generate-yaml`, `-y` | Generate semantic YAML | From config |
| `--no-yaml` | Skip YAML generation | False |
| `--generate-sql` | Generate SQL schema | False |
| `--generate-dictionary` | Generate data dictionary | False |
| `--llm-provider` | LLM provider (`openai`, `anthropic`, `gemini`, `deepseek`) | From config |
| `--model` | Specific model name | Provider default |
| `--api-key` | API key (overrides config) | From config |
| `--list-supported` | List supported file extensions | N/A |

#### Examples

**Analyze Power BI with custom settings:**
```bash
insight-fabric-analyze sales.pbix \
  --output-dir ./sales_docs \
  --llm-provider anthropic \
  --model claude-3-5-sonnet-20241022 \
  --generate-yaml \
  --generate-sql
```

**Quick Excel analysis:**
```bash
insight-fabric-analyze budget.xlsx --no-yaml
```

**Check supported formats:**
```bash
insight-fabric-analyze --list-supported
```

### Graphical User Interface

Launch the GUI:
```bash
insight-fabric-gui
```

#### GUI Workflow

1. **Select File**: Click "Browse..." or drag-and-drop a supported file
2. **Configure Options**:
   - Choose LLM provider from dropdown
   - Enter API key (optional, uses config if omitted)
   - Select output directory
   - Check desired outputs (YAML, SQL, Dictionary)
3. **Run Analysis**: Click "Run Analysis" button
4. **Monitor Progress**: Watch real-time log messages
5. **Review Results**: Output files are saved to selected directory

#### GUI Features
- **File Browser**: Supports all file types with filter
- **Real-time Logging**: See extraction and generation progress
- **Progress Indicator**: Visual feedback during analysis
- **Log Management**: Clear log button for fresh sessions

### RDL-Specific Tool

For SQL Server Reporting Services (RDL) files:
```bash
insight-fabric-rdl-analyze report.rdl [OPTIONS]
```

**RDL Options:**
- `--format`: `json`, `text`, or `compact` (LLM-ready text)
- `--output-dir`: Save to directory (default: print to stdout)

**Example:**
```bash
# Extract JSON metadata
insight-fabric-rdl-analyze report.rdl --format json --output-dir ./metadata

# Generate compact text for LLM processing
insight-fabric-rdl-analyze report.rdl --format compact --output-dir ./llm_input
```

## Output Files Explained

### Business Requirements Document (BRD)

A comprehensive markdown document containing:

**Structure:**
1. **Executive Summary**: High-level overview
2. **Business Context**: Purpose and objectives
3. **Data Sources**: Connections and queries
4. **Key Metrics**: Calculations and measures
5. **Visualizations**: Charts, tables, dashboards
6. **User Stories**: Functional requirements
7. **Technical Notes**: Dependencies and considerations

**Usage**: Share with stakeholders, use as project documentation, inform development teams.

### Semantic YAML Definition

Structured data model in YAML format:

**Contents:**
- **Entities**: Tables, views, and their relationships
- **Measures**: Calculations with DAX/Excel formulas
- **Dimensions**: Hierarchies and categorization
- **Business Rules**: Validation and transformation logic

**Usage**: Import into data modeling tools, generate data warehouse designs, document business logic.

### SQL Schema

Ready-to-use SQL Data Definition Language:

**Includes:**
- `CREATE TABLE` statements with proper data types
- Primary and foreign key constraints
- Indexes for performance
- View definitions for common queries

**Usage**: Execute in database, use as blueprint for data warehouse, document existing schemas.

### Data Dictionary

Detailed column-level documentation:

**For each column:**
- Name and data type
- Description and business meaning
- Source table and transformation
- Validation rules and constraints
- Sample values and patterns

**Usage**: Data governance, onboarding new team members, documentation for data consumers.

## Configuration Details

### Configuration File Location

The tool stores configuration in:
```
~/.insight-fabric/config.json
```

### Manual Configuration Example

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
      },
      "anthropic": {
        "api_key": "your-api-key-here",
        "model": "claude-3-5-sonnet-20241022"
      }
    }
  },
  "output": {
    "default_dir": "./analysis_output",
    "generate_yaml": true
  },
  "extraction": {
    "max_file_size_mb": 100,
    "timeout_seconds": 30
  }
}
```

### Environment Variables

Set API keys via environment variables (overrides config file):

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-key-here"

# Linux/macOS Bash
export OPENAI_API_KEY="your-key-here"
```

Supported variables:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `DEEPSEEK_API_KEY`

## Troubleshooting

### Common Issues

#### "API key not found"
**Solution:**
1. Run `insight-fabric-configure` to set API key
2. Or set environment variable: `export OPENAI_API_KEY="your-key"`
3. Or edit `~/.insight-fabric/config.json` directly

#### "File type not supported"
**Solution:**
- Check file extension with `insight-fabric-analyze --list-supported`
- Ensure file is not corrupted
- Try opening file in native application first

#### "Analysis failed with LLM error"
**Solution:**
- Verify API key has sufficient credits
- Check network connectivity to LLM provider
- Try a different LLM provider or model
- Reduce file size if very large

#### "Slow performance"
**Solution:**
- Large files (>100MB) take longer to process
- Skip unnecessary outputs with `--no-yaml`
- Consider splitting large Power BI files
- Use faster LLM model (e.g., GPT-3.5-turbo instead of GPT-4)

### Getting Help

1. **Check Logs**: GUI shows detailed logs; CLI outputs errors to console
2. **Review Metadata**: Examine `{filename}_metadata.json` for extraction issues
3. **Enable Debug**: Set environment variable `POWER_BI_DEBUG=1` for verbose output
4. **File Issues**: Check file permissions and corruption

## Best Practices

### For Power BI Files
1. **Remove sensitive data** before analysis
2. **Use .pbit templates** for sharing (no embedded data)
3. **Split large reports** into smaller focused files
4. **Document data sources** in Power Query first

### For Excel Files
1. **Use named ranges** and tables for better extraction
2. **Document Power Query steps** with meaningful names
3. **Separate data and presentation** sheets
4. **Use consistent formatting** for headers

### For RDL Files
1. **Validate data source connections** are documented
2. **Use meaningful parameter names**
3. **Organize datasets** with clear naming
4. **Test extraction** with `insight-fabric-rdl-analyze` first

### Output Management
1. **Version control** generated documentation
2. **Review BRDs** with business stakeholders
3. **Update documentation** when files change
4. **Use semantic YAML** for data governance

## Advanced Topics

### Custom LLM Providers

For OpenAI-compatible endpoints (LocalAI, Ollama, etc.):

1. Select "openai" as provider
2. Set base URL in configuration:
   ```bash
   insight-fabric-configure
   # When prompted for base URL, enter: http://localhost:8080/v1
   ```
3. Specify model name (as recognized by your endpoint)

### Python API Integration

Use the tool programmatically:

```python
from power_bi_analysis.orchestration.pipeline import AnalysisPipeline

pipeline = AnalysisPipeline(
    llm_provider="openai",
    llm_api_key="your-key",
    generate_yaml=True
)

success = pipeline.analyze_file("report.pbix")
if success:
    outputs = pipeline.save_outputs("./output")
    stats = pipeline.get_stats()
```

### Batch Processing

Script for multiple files:

```bash
#!/bin/bash
for file in ./reports/*.pbix; do
    echo "Analyzing $file..."
    insight-fabric-analyze "$file" --output-dir "./docs"
done
```

## Support

- **Documentation**: See README.md for latest updates
- **Issues**: Report bugs on GitHub issue tracker
- **Contributing**: Pull requests welcome for enhancements
- **Questions**: Contact maintainers through GitHub discussions

---

*Last Updated: April 2026*