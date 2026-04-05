"""
Google Gemini API client.
"""

import os
from typing import Optional, Dict, Any
import google.genai as genai
from .base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """LLM client for Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini client.

        Args:
            api_key: Google AI API key (default: from GOOGLE_API_KEY env var)
            model: Gemini model to use
        """
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Google API key not provided. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        self._model = model
        self._client = genai.Client(api_key=self._api_key)

        # Model context window sizes (approximate)
        self._context_windows = {
            "gemini-2.0-flash-exp": 1048576,
            "gemini-2.0-flash": 1048576,
            "gemini-1.5-flash": 1048576,
            "gemini-1.5-pro": 1048576,
            "gemini-1.0-pro": 30720,
        }

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def max_context_tokens(self) -> int:
        return self._context_windows.get(self._model, 30720)

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count using Gemini's tokenizer.
        Falls back to character count if not available.
        """
        try:
            # Try to use Gemini's count_tokens method
            response = self._client.models.count_tokens(
                model=self._model,
                contents=text
            )
            return response.total_tokens
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 chars for English)
            return len(text) // 4

    def generate_brd(self, metadata_text: str, file_name: str) -> str:
        """
        Generate Business Requirements Document using Gemini.
        """
        prompt = self._create_brd_prompt(metadata_text, file_name)

        try:
            config = genai.types.GenerateContentConfig(
                system_instruction=self._get_system_prompt(),
                temperature=0.2,
                max_output_tokens=4096,
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            return f"Error generating BRD: {str(e)}"

    def generate_sml_yaml(self, metadata_text: str, file_name: str) -> str:
        """
        Generate Semantic YAML using Gemini.
        """
        prompt = self._create_sml_prompt(metadata_text, file_name)

        try:
            config = genai.types.GenerateContentConfig(
                system_instruction=self._get_sml_system_prompt(),
                temperature=0.1,
                max_output_tokens=4096,
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            return f"Error generating YAML: {str(e)}"

    def generate_sql_schema(self, metadata_text: str, file_name: str) -> str:
        """
        Generate SQL schema (DDL) using Gemini.
        """
        prompt = self._create_sql_schema_prompt(metadata_text, file_name)

        try:
            config = genai.types.GenerateContentConfig(
                system_instruction=self._get_sql_schema_system_prompt(),
                temperature=0.1,
                max_output_tokens=4096,
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            return f"Error generating SQL schema: {str(e)}"

    def generate_data_dictionary(self, metadata_text: str, file_name: str) -> str:
        """
        Generate data dictionary using Gemini.
        """
        prompt = self._create_data_dictionary_prompt(metadata_text, file_name)

        try:
            config = genai.types.GenerateContentConfig(
                system_instruction=self._get_data_dictionary_system_prompt(),
                temperature=0.2,
                max_output_tokens=4096,
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            return f"Error generating data dictionary: {str(e)}"

    def _get_system_prompt(self) -> str:
        """System prompt for BRD generation."""
        return """You are a business analyst specializing in data and reporting systems.
Your task is to analyze metadata from a business intelligence file (Power BI, Excel, RDL) and generate a comprehensive Business Requirements Document (BRD).

The BRD should be written for business stakeholders (non-technical) and should explain:
1. What the report/dashboard is for (purpose, business context)
2. What data sources it uses
3. What key metrics and calculations it includes
4. How data is structured (tables, relationships)
5. What parameters/filters are available
6. Any business rules embedded in calculations
7. Recommendations for improvements or potential issues

Write in clear, professional business language. Use markdown formatting with appropriate headings.
Focus on the "why" not just the "what" - explain business meaning behind technical elements."""

    def _get_sml_system_prompt(self) -> str:
        """System prompt for Semantic YAML generation."""
        return """You are a data engineer specializing in semantic layers.
Your task is to convert metadata from a business intelligence file into a dbt Semantic Layer YAML specification.

The YAML should follow the dbt Semantic Layer specification (version 2.0).
Include:
1. Semantic models (tables)
2. Dimensions (columns)
3. Measures (calculations)
4. Entities (for relationships)

Output ONLY valid YAML. No explanations, no markdown formatting.
Ensure the YAML is syntactically correct and follows dbt's semantic layer schema.
Ensure all YAML keys are unique (no duplicate keys)."""

    def _create_brd_prompt(self, metadata_text: str, file_name: str) -> str:
        """Create prompt for BRD generation."""
        return f"""Analyze the following metadata from the file '{file_name}' and generate a Business Requirements Document.

METADATA:
{metadata_text}

Please generate a comprehensive BRD covering:
1. Executive Summary
2. Business Purpose & Context
3. Data Sources Analysis
4. Data Model Overview (Tables, Relationships)
5. Key Metrics & Calculations
6. Parameters & Filters
7. Report Components/Visuals
8. Business Rules & Logic
9. Recommendations & Considerations
10. Glossary of Terms

Format the BRD using markdown with clear headings and bullet points where appropriate."""

    def _create_sml_prompt(self, metadata_text: str, file_name: str) -> str:
        """Create prompt for Semantic YAML generation."""
        return f"""Convert the following metadata from '{file_name}' into a dbt Semantic Layer YAML specification.

METADATA:
{metadata_text}

Generate YAML that follows the dbt Semantic Layer schema (version 2.0).
Focus on:
- Semantic models (tables with descriptions)
- Dimensions (columns with data types)
- Measures (calculations with expressions)
- Entities (for table relationships)
- Time dimensions where appropriate

Only output the YAML content, no other text."""

    def _get_sql_schema_system_prompt(self) -> str:
        """System prompt for SQL schema generation."""
        return """You are a database architect specializing in SQL schema design.
Your task is to convert metadata from a business intelligence file into a SQL Data Definition Language (DDL) schema.

The SQL should be compatible with a modern SQL database (PostgreSQL dialect preferred).
Include:
1. CREATE TABLE statements with appropriate data types
2. Primary key and foreign key constraints where relationships exist
3. Column comments/descriptions
4. Indexes on foreign keys and frequently queried columns
5. Appropriate schema name (use 'analytics' or a suitable schema)

Output ONLY the SQL DDL statements. No explanations, no markdown formatting.
Ensure SQL syntax is valid and follows best practices."""

    def _create_sql_schema_prompt(self, metadata_text: str, file_name: str) -> str:
        """Create prompt for SQL schema generation."""
        return f"""Convert the following metadata from '{file_name}' into a SQL DDL schema.

METADATA:
{metadata_text}

Generate CREATE TABLE statements with appropriate data types, primary keys, foreign keys, and indexes.
Include column comments to document each column's purpose.
Use PostgreSQL-compatible syntax.
If there are relationships between tables, add FOREIGN KEY constraints.
Name the schema 'analytics' or choose an appropriate schema name.

Output only the SQL statements, no additional text."""

    def _get_data_dictionary_system_prompt(self) -> str:
        """System prompt for data dictionary generation."""
        return """You are a data governance specialist.
Your task is to create a comprehensive data dictionary from metadata.

The data dictionary should include:
1. Table name and description
2. Column names, data types, and descriptions
3. Relationships between tables
4. Business definitions of key metrics and calculations
5. Data lineage and source information
6. Data quality rules and constraints

Format the output as a well-structured markdown document with clear sections.
Use tables for column listings where appropriate.
Write for a mixed audience of business and technical stakeholders."""

    def _create_data_dictionary_prompt(self, metadata_text: str, file_name: str) -> str:
        """Create prompt for data dictionary generation."""
        return f"""Create a comprehensive data dictionary from the following metadata of '{file_name}'.

METADATA:
{metadata_text}

The data dictionary should include:
1. Overview of the dataset/report
2. Table-level descriptions
3. Column-level details (name, data type, description, business meaning)
4. Relationships between tables
5. Key metrics and calculations with business definitions
6. Data sources and lineage
7. Data quality notes and constraints

Format as a markdown document with clear headings, tables, and bullet points.
Aim for clarity and completeness to serve both business and technical users."""
