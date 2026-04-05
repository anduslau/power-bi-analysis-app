"""
Extractor registry and factory.
"""

import importlib
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import BaseExtractor
from .rdl_extractor import RDLExtractor
from .excel_extractor import ExcelExtractor
from .powerbi_extractor import PowerBIExtractor
from .csv_extractor import CSVExtractor
from .json_extractor import JSONExtractor
from .parquet_extractor import ParquetExtractor
from ..models import ReportMetadata

# Registry of available extractors
_EXTRACTORS: Dict[str, Type[BaseExtractor]] = {
    'rdl': RDLExtractor,
    'excel': ExcelExtractor,
    'powerbi': PowerBIExtractor,
    'csv': CSVExtractor,
    'json': JSONExtractor,
    'parquet': ParquetExtractor,
}

def get_extractor_for_file(file_path: Path) -> Optional[BaseExtractor]:
    """
    Get an extractor instance for a given file.

    Args:
        file_path: Path to the file

    Returns:
        Extractor instance or None if no extractor found
    """
    for extractor_name, extractor_class in _EXTRACTORS.items():
        extractor = extractor_class()
        if extractor.can_extract(file_path):
            return extractor
    return None

def extract_metadata(file_path: Path) -> ReportMetadata:
    """
    Extract metadata from a file using the appropriate extractor.

    Args:
        file_path: Path to the file

    Returns:
        ReportMetadata object

    Raises:
        ValueError: If no extractor found for the file
    """
    extractor = get_extractor_for_file(file_path)
    if extractor is None:
        raise ValueError(f"No extractor found for file: {file_path}")

    return extractor.extract(file_path)

def register_extractor(name: str, extractor_class: Type[BaseExtractor]) -> None:
    """
    Register a new extractor class.

    Args:
        name: Unique name for the extractor
        extractor_class: Extractor class to register
    """
    _EXTRACTORS[name] = extractor_class

def list_supported_extensions() -> List[str]:
    """
    Get list of all supported file extensions.

    Returns:
        List of file extensions (including dot)
    """
    extensions = set()
    for extractor_class in _EXTRACTORS.values():
        extractor = extractor_class()
        extensions.update(extractor.supported_extensions)
    return sorted(extensions)