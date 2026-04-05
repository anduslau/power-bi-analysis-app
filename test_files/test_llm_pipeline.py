#!/usr/bin/env python3
"""
Test the LLM pipeline with DeepSeek API.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from power_bi_analysis.orchestration.pipeline import AnalysisPipeline

def test_deepseek_excel():
    """Test LLM pipeline with Excel file using DeepSeek."""

    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Set it with your DeepSeek API token: export OPENAI_API_KEY=sk-...")
        return False

    # Sample Excel file
    sample_file = Path(__file__).parent / "sample.xlsx"
    if not sample_file.exists():
        print(f"ERROR: Sample file not found: {sample_file}")
        return False

    print(f"Testing LLM pipeline with file: {sample_file}")
    print(f"Using provider: openai with DeepSeek endpoint")

    # Initialize pipeline with DeepSeek configuration
    pipeline = AnalysisPipeline(
        llm_provider="openai",
        llm_api_key=api_key,
        llm_model="deepseek-chat",
        generate_yaml=True,
        llm_options={
            "base_url": "https://api.deepseek.com"
        }
    )

    # Run analysis
    print("Running analysis...")
    success = pipeline.analyze_file(sample_file)

    if not success:
        print("Analysis failed with errors:")
        for error in pipeline.get_errors():
            print(f"  - {error}")
        return False

    print("Analysis succeeded!")

    # Display stats
    stats = pipeline.get_stats()
    print("\nStatistics:")
    for key, value in stats.items():
        if key not in ['file_path', 'timestamp']:
            print(f"  {key}: {value}")

    # Show BRD preview
    brd = pipeline.get_brd()
    if brd:
        print(f"\nBRD preview (first 500 chars):")
        print(brd[:500] + "..." if len(brd) > 500 else brd)

    # Show YAML preview
    yaml = pipeline.get_yaml()
    if yaml:
        print(f"\nYAML preview (first 500 chars):")
        print(yaml[:500] + "..." if len(yaml) > 500 else yaml)

    # Save outputs
    output_dir = Path(__file__).parent / "output"
    brd_path, yaml_path, sql_path, dict_path = pipeline.save_outputs(output_dir)
    print(f"\nOutputs saved:")
    print(f"  BRD: {brd_path}")
    if yaml_path:
        print(f"  YAML: {yaml_path}")

    return True

if __name__ == "__main__":
    print("=== LLM Pipeline Test with DeepSeek ===\n")
    success = test_deepseek_excel()
    sys.exit(0 if success else 1)