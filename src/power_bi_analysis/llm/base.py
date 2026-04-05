"""
Base LLM client interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_brd(self, metadata_text: str, file_name: str) -> str:
        """
        Generate a Business Requirements Document from metadata.

        Args:
            metadata_text: Compact text representation of metadata
            file_name: Name of the file being analyzed

        Returns:
            Generated BRD as markdown text
        """
        pass

    @abstractmethod
    def generate_sml_yaml(self, metadata_text: str, file_name: str) -> str:
        """
        Generate Semantic YAML (dbt Semantic Layer) from metadata.

        Args:
            metadata_text: Compact text representation of metadata
            file_name: Name of the file being analyzed

        Returns:
            Generated YAML as text
        """
        pass

    @abstractmethod
    def generate_sql_schema(self, metadata_text: str, file_name: str) -> str:
        """
        Generate SQL schema (DDL) from metadata.

        Args:
            metadata_text: Compact text representation of metadata
            file_name: Name of the file being analyzed

        Returns:
            Generated SQL DDL as text
        """
        pass

    @abstractmethod
    def generate_data_dictionary(self, metadata_text: str, file_name: str) -> str:
        """
        Generate data dictionary from metadata.

        Args:
            metadata_text: Compact text representation of metadata
            file_name: Name of the file being analyzed

        Returns:
            Generated data dictionary as markdown text
        """
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the LLM provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the model being used."""
        pass

    @property
    @abstractmethod
    def max_context_tokens(self) -> int:
        """Maximum context window size in tokens."""
        pass