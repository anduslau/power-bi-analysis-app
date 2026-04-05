#!/usr/bin/env python3
"""
Test CSV, JSON, and Parquet extractors.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from power_bi_analysis.extractors import extract_metadata, get_extractor_for_file

def test_csv_extractor():
    """Test CSV extractor."""
    print("\n=== Testing CSV Extractor ===")
    sample_file = Path(__file__).parent / "sample_data.csv"
    if not sample_file.exists():
        print(f"ERROR: Sample file not found: {sample_file}")
        return False

    print(f"Testing CSV file: {sample_file}")

    # Get extractor
    extractor = get_extractor_for_file(sample_file)
    if extractor is None:
        print("ERROR: No extractor found for CSV file")
        return False

    print(f"Extractor class: {extractor.__class__.__name__}")
    print(f"Can extract: {extractor.can_extract(sample_file)}")
    print(f"Supported extensions: {extractor.supported_extensions}")

    # Extract metadata
    metadata = extract_metadata(sample_file)

    # Verify metadata
    if metadata.file_type.value != "csv":
        print(f"ERROR: Expected file_type 'csv', got '{metadata.file_type.value}'")
        return False

    print(f"File type: {metadata.file_type}")
    print(f"File size: {metadata.file_size:,} bytes")
    print(f"Tables: {len(metadata.tables)}")

    if len(metadata.tables) != 1:
        print(f"ERROR: Expected 1 table, got {len(metadata.tables)}")
        return False

    table = metadata.tables[0]
    print(f"Table name: {table.name}")
    print(f"Table columns: {len(table.columns)}")
    print(f"Table row count: {table.row_count}")

    # Verify column count
    expected_columns = 4  # name, age, city, salary
    if len(table.columns) != expected_columns:
        print(f"ERROR: Expected {expected_columns} columns, got {len(table.columns)}")
        return False

    # Verify column names
    expected_col_names = ["name", "age", "city", "salary"]
    actual_col_names = [col.name for col in table.columns]
    for expected in expected_col_names:
        if expected not in actual_col_names:
            print(f"ERROR: Expected column '{expected}' not found")
            return False

    print("[SUCCESS] CSV extractor test passed!")
    return True

def test_json_extractor():
    """Test JSON extractor."""
    print("\n=== Testing JSON Extractor ===")
    sample_file = Path(__file__).parent / "sample_data.json"
    if not sample_file.exists():
        print(f"ERROR: Sample file not found: {sample_file}")
        return False

    print(f"Testing JSON file: {sample_file}")

    # Get extractor
    extractor = get_extractor_for_file(sample_file)
    if extractor is None:
        print("ERROR: No extractor found for JSON file")
        return False

    print(f"Extractor class: {extractor.__class__.__name__}")
    print(f"Can extract: {extractor.can_extract(sample_file)}")
    print(f"Supported extensions: {extractor.supported_extensions}")

    # Extract metadata
    metadata = extract_metadata(sample_file)

    # Verify metadata
    if metadata.file_type.value != "json":
        print(f"ERROR: Expected file_type 'json', got '{metadata.file_type.value}'")
        return False

    print(f"File type: {metadata.file_type}")
    print(f"File size: {metadata.file_size:,} bytes")
    print(f"Tables: {len(metadata.tables)}")

    if len(metadata.tables) != 1:
        print(f"ERROR: Expected 1 table, got {len(metadata.tables)}")
        return False

    table = metadata.tables[0]
    print(f"Table name: {table.name}")
    print(f"Table columns: {len(table.columns)}")
    print(f"Table row count: {table.row_count}")

    # Verify column count
    expected_columns = 5  # id, name, price, category, in_stock
    if len(table.columns) != expected_columns:
        print(f"ERROR: Expected {expected_columns} columns, got {len(table.columns)}")
        return False

    # Verify column names
    expected_col_names = ["id", "name", "price", "category", "in_stock"]
    actual_col_names = [col.name for col in table.columns]
    for expected in expected_col_names:
        if expected not in actual_col_names:
            print(f"ERROR: Expected column '{expected}' not found")
            return False

    print("[SUCCESS] JSON extractor test passed!")
    return True

def test_parquet_extractor():
    """Test Parquet extractor."""
    print("\n=== Testing Parquet Extractor ===")
    sample_file = Path(__file__).parent / "sample_data.parquet"
    if not sample_file.exists():
        print(f"ERROR: Sample file not found: {sample_file}")
        return False

    print(f"Testing Parquet file: {sample_file}")

    # Get extractor
    extractor = get_extractor_for_file(sample_file)
    if extractor is None:
        print("ERROR: No extractor found for Parquet file")
        return False

    print(f"Extractor class: {extractor.__class__.__name__}")
    print(f"Can extract: {extractor.can_extract(sample_file)}")
    print(f"Supported extensions: {extractor.supported_extensions}")

    # Extract metadata
    metadata = extract_metadata(sample_file)

    # Verify metadata
    if metadata.file_type.value != "parquet":
        print(f"ERROR: Expected file_type 'parquet', got '{metadata.file_type.value}'")
        return False

    print(f"File type: {metadata.file_type}")
    print(f"File size: {metadata.file_size:,} bytes")
    print(f"Tables: {len(metadata.tables)}")

    if len(metadata.tables) != 1:
        print(f"ERROR: Expected 1 table, got {len(metadata.tables)}")
        return False

    table = metadata.tables[0]
    print(f"Table name: {table.name}")
    print(f"Table columns: {len(table.columns)}")
    print(f"Table row count: {table.row_count}")

    # Verify column count
    expected_columns = 7  # employee_id, first_name, last_name, department, salary, start_date, active
    if len(table.columns) != expected_columns:
        print(f"ERROR: Expected {expected_columns} columns, got {len(table.columns)}")
        return False

    # Verify column names
    expected_col_names = ["employee_id", "first_name", "last_name", "department", "salary", "start_date", "active"]
    actual_col_names = [col.name for col in table.columns]
    for expected in expected_col_names:
        if expected not in actual_col_names:
            print(f"ERROR: Expected column '{expected}' not found")
            return False

    print("[SUCCESS] Parquet extractor test passed!")
    return True

def main():
    """Run all data extractor tests."""
    print("=== Data File Extractor Tests ===\n")

    success = True

    # Run tests
    if not test_csv_extractor():
        success = False

    if not test_json_extractor():
        success = False

    if not test_parquet_extractor():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] All data extractor tests passed!")
    else:
        print("[ERROR] Some tests failed.")

    return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1)