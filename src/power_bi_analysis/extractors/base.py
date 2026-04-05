"""
Base classes for file extractors.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from ..models import ReportMetadata

class BaseExtractor(ABC):
    """Abstract base class for file extractors."""

    @abstractmethod
    def extract(self, file_path: Path) -> ReportMetadata:
        """
        Extract metadata from a file.

        Args:
            file_path: Path to the file to extract

        Returns:
            ReportMetadata object with extracted information
        """
        pass

    @abstractmethod
    def can_extract(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle the given file.

        Args:
            file_path: Path to check

        Returns:
            True if this extractor can handle the file
        """
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        List of file extensions supported by this extractor.
        """
        pass