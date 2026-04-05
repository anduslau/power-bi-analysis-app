#!/usr/bin/env python3
"""
Test RDL extraction.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from power_bi_analysis.extractors import extract_metadata

sample_file = Path(__file__).parent / "sample.rdl"
if not sample_file.exists():
    print(f"ERROR: Sample file not found: {sample_file}")
    sys.exit(1)

print(f"Testing extractor on {sample_file}")
metadata = extract_metadata(sample_file)

print(f"Extractor class: {metadata.file_type}")
print(f"File size: {metadata.file_size}")
print(f"Data sources: {len(metadata.data_sources)}")
for ds in metadata.data_sources:
    print(f"  - {ds.name}: {ds.data_provider}")
print(f"Tables: {len(metadata.tables)}")
for tbl in metadata.tables:
    print(f"  - {tbl.name}: {len(tbl.columns)} columns")
print(f"Parameters: {len(metadata.parameters)}")
for param in metadata.parameters:
    print(f"  - {param.name}: {param.data_type}")
print(f"Visuals: {len(metadata.visuals)}")
print(f"Extraction errors: {metadata.extraction_errors}")
if metadata.extraction_errors:
    for err in metadata.extraction_errors:
        print(f"  - {err}")