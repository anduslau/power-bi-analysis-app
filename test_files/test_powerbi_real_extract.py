#!/usr/bin/env python3
"""
Test Power BI extractor with real sample.pbix file.
"""
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from power_bi_analysis.extractors import extract_metadata

def test_powerbi_real():
    import os
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script file: {__file__}")
    sample_path = Path(__file__).parent / "sample.pbix"
    print(f"Sample path: {sample_path}")
    print(f"Parent exists: {Path(__file__).parent.exists()}")
    if not sample_path.exists():
        print(f"ERROR: Sample file not found: {sample_path}")
        return False

    print(f"Testing extractor on {sample_path}")
    print(f"File size: {sample_path.stat().st_size} bytes")

    metadata = extract_metadata(sample_path)
    print(f"Extracted metadata:")
    print(f"  File type: {metadata.file_type}")
    print(f"  File size: {metadata.file_size}")
    print(f"  Tables count: {len(metadata.tables)}")
    print(f"  Measures count: {len(metadata.measures)}")
    print(f"  Relationships count: {len(metadata.relationships)}")
    print(f"  Parameters count: {len(metadata.parameters)}")
    print(f"  Queries count: {len(metadata.queries)}")
    print(f"  Extraction errors: {len(metadata.extraction_errors)}")
    if metadata.extraction_errors:
        for err in metadata.extraction_errors:
            print(f"    - {err}")

    # Print some table details
    for i, table in enumerate(metadata.tables[:5]):  # limit to first 5
        print(f"  Table {i}: {table.name} ({len(table.columns)} columns)")
        for col in table.columns[:3]:  # first 3 columns
            print(f"    - {col.name}: {col.data_type}")
    if len(metadata.tables) > 5:
        print(f"  ... and {len(metadata.tables) - 5} more tables")

    return len(metadata.extraction_errors) == 0

if __name__ == "__main__":
    success = test_powerbi_real()
    sys.exit(0 if success else 1)