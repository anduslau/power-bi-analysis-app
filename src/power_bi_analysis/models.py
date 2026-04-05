"""
Data models for extracted metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class FileType(Enum):
    """Supported file types."""
    RDL = "rdl"
    EXCEL = "excel"
    POWER_BI = "power_bi"
    POWER_BI_TEMPLATE = "power_bi_template"
    POWER_BI_PROJECT = "power_bi_project"
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    UNKNOWN = "unknown"

@dataclass
class DataSource:
    """Data source definition."""
    name: str
    connection_string: Optional[str] = None
    data_provider: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None

@dataclass
class Column:
    """Column/field definition."""
    name: str
    data_type: Optional[str] = None
    description: Optional[str] = None
    is_measure: bool = False
    is_calculated: bool = False
    expression: Optional[str] = None

@dataclass
class Table:
    """Table definition."""
    name: str
    columns: List[Column] = field(default_factory=list)
    description: Optional[str] = None
    source: Optional[str] = None
    row_count: Optional[int] = None

@dataclass
class Relationship:
    """Relationship between tables."""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str = "many_to_one"  # or "one_to_one", "many_to_many"

@dataclass
class Measure:
    """DAX measure definition."""
    name: str
    expression: str
    description: Optional[str] = None
    format_string: Optional[str] = None

@dataclass
class Parameter:
    """Report parameter."""
    name: str
    data_type: str
    default_value: Optional[str] = None
    prompt: Optional[str] = None
    values: List[str] = field(default_factory=list)

@dataclass
class Visual:
    """Report visual/page element."""
    name: str
    visual_type: str
    data_fields: Dict[str, List[str]] = field(default_factory=dict)
    filters: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ReportMetadata:
    """Complete metadata extracted from a file."""
    file_type: FileType
    file_path: str
    file_size: int

    # Common metadata
    data_sources: List[DataSource] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    measures: List[Measure] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    visuals: List[Visual] = field(default_factory=list)

    # File-specific metadata
    worksheets: List[str] = field(default_factory=list)  # For Excel
    queries: List[Dict[str, Any]] = field(default_factory=list)  # For Power Query
    report_items: List[Dict[str, Any]] = field(default_factory=list)  # For RDL

    # Extraction info
    extraction_errors: List[str] = field(default_factory=list)
    extracted_at: str = ""


@dataclass
class Change:
    """Represent a change between two versions of a BI file."""
    change_type: str  # "added", "removed", "modified", "unchanged"
    element_type: str  # "table", "column", "measure", "relationship", "parameter", "visual", "data_source"
    element_name: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiffReport:
    """Report of changes between two ReportMetadata objects."""
    file1: str
    file2: str
    comparison_date: str
    changes: List[Change] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)  # counts by change type and element type