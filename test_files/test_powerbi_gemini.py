#!/usr/bin/env python3
"""
Test the LLM pipeline with Power BI .pbix file using Gemini API.
Requires GOOGLE_API_KEY environment variable.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from power_bi_analysis.orchestration.pipeline import AnalysisPipeline

def test_powerbi_gemini():
    """Test LLM pipeline with Power BI file using Gemini."""

    # Sample Power BI file
    sample_file = Path(__file__).parent / "sample.pbix"
    if not sample_file.exists():
        print(f"ERROR: Sample file not found: {sample_file}")
        return False

    # Check for API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not set")
        print("Set it with: export GOOGLE_API_KEY=your_key")
        print("Skipping actual LLM test, only testing extraction...")
        api_key = None

    print(f"Testing LLM pipeline with Power BI file: {sample_file}")
    print(f"File size: {sample_file.stat().st_size:,} bytes")
    print(f"Using provider: {'gemini' if api_key else 'gemini (no API key)'}")

    # Initialize pipeline
    pipeline = AnalysisPipeline(
        llm_provider="gemini",
        llm_api_key=api_key,
        llm_model=None,  # Use default
        generate_yaml=False,
        generate_sql=False,
        generate_dictionary=False
    )

    print("\nRunning analysis...")
    success = pipeline.analyze_file(sample_file)

    if not success:
        errors = pipeline.get_errors()
        print(f"\nAnalysis failed. Errors:")
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
                if not api_key:
                    print("\n[NOTE] Test completed without API key. Extraction works.")
                    return True
                else:
                    print("\n[ERROR] Analysis failed even with API key.")
                    return False
            else:
                print(f"\n[ERROR] File type mismatch")
                return False
        else:
            print(f"\n[ERROR] Metadata extraction also failed.")
            return False
    else:
        # Analysis succeeded!
        print("\n[SUCCESS] Analysis succeeded with Gemini API!")
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
    print("=== Power BI LLM Pipeline Test with Gemini ===\n")
    success = test_powerbi_gemini()
    sys.exit(0 if success else 1)