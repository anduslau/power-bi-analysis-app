#!/usr/bin/env python3
"""
Test Power BI extractor with real sample file.
"""
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from power_bi_analysis.extractors import extract_metadata

def test_real_pbix():
    sample_path = Path(__file__).parent / "sample.pbix"
    if not sample_path.exists():
        print(f"Error: sample.pbix not found.")
        sys.exit(1)

    print(f"Testing extractor on {sample_path}")
    print(f"File size: {sample_path.stat().st_size} bytes")

    metadata = extract_metadata(sample_path)
    print(f"\nExtracted metadata:")
    print(f"  File type: {metadata.file_type}")
    print(f"  File size: {metadata.file_size}")
    print(f"  Tables count: {len(metadata.tables)}")
    for table in metadata.tables:
        print(f"    - {table.name}: {len(table.columns)} columns")
        if table.description:
            print(f"      description: {table.description[:100]}...")
    print(f"  Measures count: {len(metadata.measures)}")
    for measure in metadata.measures[:5]:  # limit output
        print(f"    - {measure.name}: {measure.expression[:100]}...")
    if len(metadata.measures) > 5:
        print(f"      ... and {len(metadata.measures) - 5} more")
    print(f"  Relationships count: {len(metadata.relationships)}")
    for rel in metadata.relationships[:5]:
        print(f"    - {rel.from_table}.{rel.from_column} -> {rel.to_table}.{rel.to_column} ({rel.relationship_type})")
    print(f"  Parameters count: {len(metadata.parameters)}")
    for param in metadata.parameters[:5]:
        print(f"    - {param.name}: {param.data_type}")
    print(f"  Queries count: {len(metadata.queries)}")
    for query in metadata.queries[:5]:
        print(f"    - {query['name']}: {query['type']}")
    print(f"  Data sources count: {len(metadata.data_sources)}")
    print(f"  Extraction errors: {metadata.extraction_errors}")
    if metadata.extraction_errors:
        for err in metadata.extraction_errors:
            print(f"    - {err}")

if __name__ == "__main__":
    test_real_pbix()