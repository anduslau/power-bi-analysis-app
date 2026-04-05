#!/usr/bin/env python3
"""
Test Power BI extractor with a dummy file.
"""
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from power_bi_analysis.extractors import extract_metadata

def test_powerbi_extractor():
    # Create a dummy file path with .pbix extension
    dummy_path = Path(__file__).parent / "dummy.pbix"
    # Ensure it doesn't exist (clean up if it does)
    if dummy_path.exists():
        dummy_path.unlink()

    # Create an empty file
    dummy_path.touch()

    print(f"Testing extractor on {dummy_path}")

    try:
        metadata = extract_metadata(dummy_path)
        print(f"Extracted metadata:")
        print(f"  File type: {metadata.file_type}")
        print(f"  File size: {metadata.file_size}")
        print(f"  Tables count: {len(metadata.tables)}")
        print(f"  Measures count: {len(metadata.measures)}")
        print(f"  Relationships count: {len(metadata.relationships)}")
        print(f"  Parameters count: {len(metadata.parameters)}")
        print(f"  Queries count: {len(metadata.queries)}")
        print(f"  Extraction errors: {metadata.extraction_errors}")
        if metadata.extraction_errors:
            for err in metadata.extraction_errors:
                print(f"    - {err}")
    finally:
        # Clean up dummy file
        if dummy_path.exists():
            dummy_path.unlink()

if __name__ == "__main__":
    test_powerbi_extractor()