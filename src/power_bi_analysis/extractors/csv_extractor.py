"""
CSV file extractor for .csv files.
Uses Python's built-in csv module.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseExtractor
from ..models import (
    ReportMetadata, FileType, DataSource, Column, Table,
    Parameter, Visual, Measure, Relationship
)


class CSVExtractor(BaseExtractor):
    """Extractor for CSV files."""

    def can_extract(self, file_path: Path) -> bool:
        """Check if file is a CSV file."""
        ext = file_path.suffix.lower()
        return ext == '.csv'

    @property
    def supported_extensions(self) -> List[str]:
        return ['.csv']

    def extract(self, file_path: Path) -> ReportMetadata:
        """Extract metadata from CSV file."""
        metadata = ReportMetadata(
            file_type=FileType.CSV,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            extracted_at=datetime.now().isoformat()
        )

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # Sniff dialect
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                has_header = sniffer.has_header(sample)

                reader = csv.reader(f, dialect)

                # Read header
                if has_header:
                    headers = next(reader)
                else:
                    # Generate default headers
                    # Need to know number of columns, read first row
                    first_row = next(reader)
                    headers = [f'Column{i+1}' for i in range(len(first_row))]
                    # Reset reader to start
                    f.seek(0)
                    reader = csv.reader(f, dialect)

                # Collect sample rows for type inference
                sample_rows = []
                row_count = 0
                for i, row in enumerate(reader):
                    if i >= 10:  # Sample first 10 rows for type inference
                        break
                    sample_rows.append(row)
                    row_count += 1

                # Continue counting rows
                row_count += sum(1 for _ in reader)

                # Infer column data types from sample rows
                columns = []
                if sample_rows:
                    num_cols = len(headers)
                    # Initialize type candidates for each column
                    for col_idx in range(num_cols):
                        col_name = headers[col_idx] if col_idx < len(headers) else f'Column{col_idx+1}'
                        col_samples = [row[col_idx] if col_idx < len(row) else '' for row in sample_rows]
                        inferred_type = self._infer_column_type(col_samples)
                        columns.append(Column(
                            name=col_name,
                            data_type=inferred_type,
                            description=f"Inferred from {len(col_samples)} sample rows"
                        ))

                # Create a single table representing the CSV
                metadata.tables = [Table(
                    name=file_path.stem,
                    columns=columns,
                    description=f"CSV file with {row_count} rows, {len(headers)} columns",
                    source=str(file_path),
                    row_count=row_count
                )]

                # No data sources, relationships, measures, parameters, visuals
                metadata.data_sources = []
                metadata.relationships = []
                metadata.measures = []
                metadata.parameters = []
                metadata.visuals = []

        except Exception as e:
            metadata.extraction_errors.append(f"CSV extraction error: {e}")

        return metadata

    def _infer_column_type(self, samples: List[str]) -> str:
        """Infer data type from sample values."""
        if not samples:
            return 'string'

        # Remove empty strings
        non_empty = [s for s in samples if s.strip() != '']
        if not non_empty:
            return 'string'

        # Check if all are integers
        try:
            [int(v) for v in non_empty]
            return 'integer'
        except ValueError:
            pass

        # Check if all are floats
        try:
            [float(v) for v in non_empty]
            return 'float'
        except ValueError:
            pass

        # Check for date/time patterns (simplistic)
        # Could be extended with dateutil
        date_patterns = ['-', '/', ':']
        for sample in non_empty:
            if any(pattern in sample for pattern in date_patterns):
                # Might be date
                return 'datetime'

        # Default to string
        return 'string'