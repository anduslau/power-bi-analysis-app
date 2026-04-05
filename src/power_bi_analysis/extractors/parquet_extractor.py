"""
Parquet file extractor for .parquet files.
Uses pyarrow or pandas to read schema.
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseExtractor
from ..models import (
    ReportMetadata, FileType, DataSource, Column, Table,
    Parameter, Visual, Measure, Relationship
)


class ParquetExtractor(BaseExtractor):
    """Extractor for Parquet files."""

    def can_extract(self, file_path: Path) -> bool:
        """Check if file is a Parquet file."""
        ext = file_path.suffix.lower()
        return ext == '.parquet'

    @property
    def supported_extensions(self) -> List[str]:
        return ['.parquet']

    def extract(self, file_path: Path) -> ReportMetadata:
        """Extract metadata from Parquet file."""
        metadata = ReportMetadata(
            file_type=FileType.PARQUET,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            extracted_at=datetime.now().isoformat()
        )

        try:
            # Try to read Parquet metadata
            columns, row_count = self._extract_parquet_metadata(file_path)

            metadata.tables = [Table(
                name=file_path.stem,
                columns=columns,
                description=f"Parquet file with {row_count} rows, {len(columns)} columns",
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
            metadata.extraction_errors.append(f"Parquet extraction error: {e}")

        return metadata

    def _extract_parquet_metadata(self, file_path: Path):
        """Extract column schema and row count from Parquet file."""
        # Try pyarrow first
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(file_path)
            schema = table.schema
            row_count = table.num_rows

            columns = []
            for field in schema:
                col_type = str(field.type)
                # Simplify type name
                if col_type.startswith('int'):
                    data_type = 'integer'
                elif col_type.startswith('float') or col_type.startswith('double'):
                    data_type = 'float'
                elif col_type.startswith('bool'):
                    data_type = 'boolean'
                elif col_type.startswith('string') or col_type.startswith('utf8'):
                    data_type = 'string'
                elif col_type.startswith('timestamp') or col_type.startswith('date'):
                    data_type = 'datetime'
                else:
                    data_type = col_type

                columns.append(Column(
                    name=field.name,
                    data_type=data_type,
                    description=f"Parquet type: {col_type}"
                ))

            return columns, row_count
        except ImportError:
            pass

        # Fallback to pandas
        try:
            import pandas as pd
            # Read only schema to avoid loading full data
            # pandas read_parquet requires engine; default 'auto' uses pyarrow or fastparquet
            # We'll read just first row to get column names and types
            df = pd.read_parquet(file_path, nrows=1)
            row_count = None  # Cannot get row count without reading entire file
            # Infer row count via metadata? Skip for now.
            columns = []
            for col_name in df.columns:
                col_type = str(df[col_name].dtype)
                # Map pandas dtypes
                if col_type.startswith('int'):
                    data_type = 'integer'
                elif col_type.startswith('float'):
                    data_type = 'float'
                elif col_type.startswith('bool'):
                    data_type = 'boolean'
                elif col_type.startswith('object') or col_type.startswith('string'):
                    data_type = 'string'
                elif col_type.startswith('datetime'):
                    data_type = 'datetime'
                else:
                    data_type = col_type

                columns.append(Column(
                    name=col_name,
                    data_type=data_type,
                    description=f"Pandas dtype: {col_type}"
                ))

            # Try to get row count using pyarrow again or read metadata file
            # For now, we can read the whole file but that's heavy.
            # We'll leave row_count as None.
            return columns, row_count
        except ImportError:
            raise ImportError(
                "Neither pyarrow nor pandas is installed. "
                "Please install pyarrow or pandas to extract Parquet metadata."
            )