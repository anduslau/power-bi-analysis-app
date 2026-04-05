"""
Version comparison utilities for BI files.
"""

from .metadata_comparator import MetadataComparator, compare_metadata
from .diff_renderer import DiffRenderer, render_diff

__all__ = [
    "MetadataComparator",
    "compare_metadata",
    "DiffRenderer",
    "render_diff",
]