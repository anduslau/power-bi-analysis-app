#!/usr/bin/env python3
"""
Test the Excel extractor on the sample file.
"""
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from power_bi_analysis.extractors import extract_metadata, get_extractor_for_file

def test_excel_extractor():
    sample_path = Path(__file__).parent / "sample.xlsx"
    if not sample_path.exists():
        print("Error: sample.xlsx not found. Run create_sample.py first.")
        sys.exit(1)

    print(f"Testing extractor on {sample_path}")

    # Get extractor
    extractor = get_extractor_for_file(sample_path)
    if extractor is None:
        print("No extractor found for file.")
        return

    print(f"Extractor class: {extractor.__class__.__name__}")
    print(f"Can extract: {extractor.can_extract(sample_path)}")
    print(f"Supported extensions: {extractor.supported_extensions}")

    # Extract metadata
    metadata = extract_metadata(sample_path)
    print(f"\nExtracted metadata:")
    print(f"  File type: {metadata.file_type}")
    print(f"  File size: {metadata.file_size}")
    print(f"  Worksheets: {metadata.worksheets}")
    print(f"  Tables count: {len(metadata.tables)}")
    for table in metadata.tables:
        print(f"    - {table.name}: {table.description}")
    print(f"  Queries count: {len(metadata.queries)}")
    for query in metadata.queries:
        print(f"    - {query['name']}: {query['type']} ({query['reference']})")
    print(f"  Data sources count: {len(metadata.data_sources)}")
    print(f"  Extraction errors: {metadata.extraction_errors}")
    print(f"  Extracted at: {metadata.extracted_at}")

if __name__ == "__main__":
    test_excel_extractor()