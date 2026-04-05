#!/usr/bin/env python3
"""
Test the LLM pipeline with Power BI .pbix file.
This test verifies that the pipeline can extract metadata from Power BI files
and handle LLM integration (will fail with API key error if no key is set).
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from power_bi_analysis.orchestration.pipeline import AnalysisPipeline

def test_powerbi_pipeline():
    """Test LLM pipeline with Power BI file."""

    # Sample Power BI file
    sample_file = Path(__file__).parent / "sample.pbix"
    if not sample_file.exists():
        print(f"ERROR: Sample file not found: {sample_file}")
        return False

    print(f"Testing LLM pipeline with Power BI file: {sample_file}")
    print(f"File size: {sample_file.stat().st_size:,} bytes")

    # Initialize pipeline - will try to use OpenAI (default) without API key
    # This should fail gracefully during LLM call
    pipeline = AnalysisPipeline(
        llm_provider="openai",  # Default provider
        llm_api_key=None,  # No API key provided
        llm_model=None,  # Use default
        generate_yaml=False,  # Skip YAML for faster test
        generate_sql=False,
        generate_dictionary=False
    )

    print("\nRunning analysis...")
    print("Note: This will fail with API key error if OPENAI_API_KEY is not set.")
    print("      That's expected - we're testing pipeline integration, not LLM calls.")

    success = pipeline.analyze_file(sample_file)

    if not success:
        errors = pipeline.get_errors()
        print(f"\nAnalysis failed (as expected without API key). Errors:")
        for error in errors:
            print(f"  - {error}")

        # Check if metadata was extracted despite LLM failure
        if pipeline.metadata:
            print(f"\n[SUCCESS] Metadata extraction succeeded!")
            print(f"  File type: {pipeline.metadata.file_type}")
            print(f"  Tables: {len(pipeline.metadata.tables)}")
            print(f"  Measures: {len(pipeline.metadata.measures)}")
            print(f"  Relationships: {len(pipeline.metadata.relationships)}")

            # Verify this is a Power BI file
            if pipeline.metadata.file_type.value == "power_bi":
                print(f"\n[SUCCESS] Power BI file correctly identified!")
                return True
            else:
                print(f"\n[ERROR] File type mismatch: expected 'power_bi', got {pipeline.metadata.file_type} (value: {pipeline.metadata.file_type.value})")
                return False
        else:
            print(f"\n❌ Metadata extraction also failed.")
            return False
    else:
        # If analysis succeeded (API key was set), print stats
        print("\n✅ Analysis succeeded (API key was available)!")
        stats = pipeline.get_stats()
        print(f"\nStatistics:")
        for key, value in stats.items():
            if key not in ['file_path', 'timestamp']:
                print(f"  {key}: {value}")

        # Show BRD preview
        brd = pipeline.get_brd()
        if brd:
            print(f"\nBRD preview (first 500 chars):")
            print(brd[:500] + "..." if len(brd) > 500 else brd)

        return True

if __name__ == "__main__":
    print("=== Power BI LLM Pipeline Test ===\n")
    success = test_powerbi_pipeline()
    sys.exit(0 if success else 1)