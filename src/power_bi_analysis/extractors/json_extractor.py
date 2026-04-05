"""
JSON file extractor for .json files.
Uses Python's built-in json module.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime

from .base import BaseExtractor
from ..models import (
    ReportMetadata, FileType, DataSource, Column, Table,
    Parameter, Visual, Measure, Relationship
)


class JSONExtractor(BaseExtractor):
    """Extractor for JSON files."""

    def can_extract(self, file_path: Path) -> bool:
        """Check if file is a JSON file."""
        ext = file_path.suffix.lower()
        return ext == '.json'

    @property
    def supported_extensions(self) -> List[str]:
        return ['.json']

    def extract(self, file_path: Path) -> ReportMetadata:
        """Extract metadata from JSON file."""
        metadata = ReportMetadata(
            file_type=FileType.JSON,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            extracted_at=datetime.now().isoformat()
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Determine JSON structure
            if isinstance(data, list):
                # Array of objects (rows)
                if not data:
                    # Empty array
                    metadata.tables = [Table(
                        name=file_path.stem,
                        columns=[],
                        description="Empty JSON array",
                        source=str(file_path),
                        row_count=0
                    )]
                else:
                    # Infer schema from first object
                    first = data[0]
                    if isinstance(first, dict):
                        columns = self._infer_columns_from_dict(first)
                        # Count rows
                        row_count = len(data)
                        metadata.tables = [Table(
                            name=file_path.stem,
                            columns=columns,
                            description=f"JSON array with {row_count} objects",
                            source=str(file_path),
                            row_count=row_count
                        )]
                    else:
                        # Array of primitives
                        col_type = self._infer_type_from_value(first)
                        columns = [Column(
                            name='value',
                            data_type=col_type,
                            description="Array of primitive values"
                        )]
                        metadata.tables = [Table(
                            name=file_path.stem,
                            columns=columns,
                            description=f"JSON array with {len(data)} primitive values",
                            source=str(file_path),
                            row_count=len(data)
                        )]

            elif isinstance(data, dict):
                # Single object, treat as table with one row
                columns = self._infer_columns_from_dict(data)
                metadata.tables = [Table(
                    name=file_path.stem,
                    columns=columns,
                    description="JSON object",
                    source=str(file_path),
                    row_count=1
                )]
                # Could also extract nested structures as separate tables?
                # For now, keep simple.
            else:
                # Primitive value (string, number, bool, null)
                col_type = self._infer_type_from_value(data)
                columns = [Column(
                    name='value',
                    data_type=col_type,
                    description="Primitive JSON value"
                )]
                metadata.tables = [Table(
                    name=file_path.stem,
                    columns=columns,
                    description="Primitive JSON value",
                    source=str(file_path),
                    row_count=1
                )]

            # No data sources, relationships, measures, parameters, visuals
            metadata.data_sources = []
            metadata.relationships = []
            metadata.measures = []
            metadata.parameters = []
            metadata.visuals = []

        except json.JSONDecodeError as e:
            metadata.extraction_errors.append(f"JSON parsing error: {e}")
        except Exception as e:
            metadata.extraction_errors.append(f"JSON extraction error: {e}")

        return metadata

    def _infer_columns_from_dict(self, obj: Dict[str, Any]) -> List[Column]:
        """Infer column definitions from a dictionary object."""
        columns = []
        for key, value in obj.items():
            col_type = self._infer_type_from_value(value)
            columns.append(Column(
                name=key,
                data_type=col_type,
                description=f"From JSON object key"
            ))
        return columns

    def _infer_type_from_value(self, value: Any) -> str:
        """Infer data type from a JSON value."""
        if isinstance(value, str):
            return 'string'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, list):
            # Could be array type
            if value:
                element_type = self._infer_type_from_value(value[0])
                return f'array[{element_type}]'
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        elif value is None:
            return 'null'
        else:
            return 'unknown'