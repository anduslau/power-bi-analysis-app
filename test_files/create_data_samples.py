#!/usr/bin/env python3
"""
Create sample CSV, JSON, and Parquet files for testing extractors.
"""
import json
import csv
from pathlib import Path
import pandas as pd

def create_csv_sample(file_path: Path):
    """Create a sample CSV file."""
    data = [
        ["name", "age", "city", "salary"],
        ["John Doe", 30, "New York", 75000.50],
        ["Jane Smith", 25, "London", 65000.75],
        ["Bob Johnson", 35, "Tokyo", 82000.00],
        ["Alice Brown", 28, "Paris", 71000.25],
        ["Charlie Wilson", 42, "Berlin", 88000.50],
    ]

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)

    print(f"Created CSV sample: {file_path}")

def create_json_sample(file_path: Path):
    """Create a sample JSON file."""
    data = [
        {"id": 1, "name": "Product A", "price": 29.99, "category": "Electronics", "in_stock": True},
        {"id": 2, "name": "Product B", "price": 49.99, "category": "Home", "in_stock": False},
        {"id": 3, "name": "Product C", "price": 19.99, "category": "Books", "in_stock": True},
        {"id": 4, "name": "Product D", "price": 99.99, "category": "Electronics", "in_stock": True},
        {"id": 5, "name": "Product E", "price": 14.99, "category": "Toys", "in_stock": False},
    ]

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"Created JSON sample: {file_path}")

def create_parquet_sample(file_path: Path):
    """Create a sample Parquet file."""
    data = {
        "employee_id": [101, 102, 103, 104, 105],
        "first_name": ["John", "Jane", "Bob", "Alice", "Charlie"],
        "last_name": ["Doe", "Smith", "Johnson", "Brown", "Wilson"],
        "department": ["Engineering", "Sales", "Engineering", "HR", "Sales"],
        "salary": [85000.00, 72000.50, 91000.75, 68000.25, 77000.00],
        "start_date": pd.to_datetime(["2020-01-15", "2019-03-22", "2021-06-10", "2018-11-05", "2022-02-28"]),
        "active": [True, True, False, True, True]
    }

    df = pd.DataFrame(data)
    df.to_parquet(file_path, engine='pyarrow')

    print(f"Created Parquet sample: {file_path}")

def main():
    """Create all sample files."""
    test_dir = Path(__file__).parent

    # Create samples
    create_csv_sample(test_dir / "sample_data.csv")
    create_json_sample(test_dir / "sample_data.json")
    create_parquet_sample(test_dir / "sample_data.parquet")

    print("\nAll sample files created successfully!")

if __name__ == "__main__":
    main()