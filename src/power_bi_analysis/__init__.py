"""
Report to Business Documents Application

A desktop application that analyzes Power BI, Excel, and RDL files
to generate Business Requirements Documents and Semantic YAML files.
"""

__version__ = "0.1.0"
__author__ = "Report to Business Documents Application Team"

from .cli import main
from .extractors import (
    extract_metadata,
    get_extractor_for_file,
    list_supported_extensions,
    register_extractor
)
from .llm.factory import (
    create_llm_client,
    list_supported_providers,
    register_llm_client
)
from .orchestration.pipeline import AnalysisPipeline

# Public API
__all__ = [
    "main",
    "extract_metadata",
    "get_extractor_for_file",
    "list_supported_extensions",
    "register_extractor",
    "create_llm_client",
    "list_supported_providers",
    "register_llm_client",
    "AnalysisPipeline",
]