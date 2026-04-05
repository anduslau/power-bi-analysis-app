"""
Serialize metadata for LLM consumption.
"""

import json
from typing import Dict, Any
from ..models import ReportMetadata

class MetadataSerializer:
    """Serialize metadata to various formats."""

    @staticmethod
    def to_dict(metadata: ReportMetadata) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "file_type": metadata.file_type.value,
            "file_path": metadata.file_path,
            "file_size": metadata.file_size,
            "data_sources": [
                {
                    "name": ds.name,
                    "connection_string": ds.connection_string,
                    "data_provider": ds.data_provider,
                }
                for ds in metadata.data_sources
            ],
            "tables": [
                {
                    "name": table.name,
                    "description": table.description,
                    "source": table.source,
                    "row_count": table.row_count,
                    "columns": [
                        {
                            "name": col.name,
                            "data_type": col.data_type,
                            "description": col.description,
                            "is_measure": col.is_measure,
                            "is_calculated": col.is_calculated,
                            "expression": col.expression,
                        }
                        for col in table.columns
                    ]
                }
                for table in metadata.tables
            ],
            "relationships": [
                {
                    "from_table": rel.from_table,
                    "from_column": rel.from_column,
                    "to_table": rel.to_table,
                    "to_column": rel.to_column,
                    "relationship_type": rel.relationship_type,
                }
                for rel in metadata.relationships
            ],
            "measures": [
                {
                    "name": measure.name,
                    "expression": measure.expression,
                    "description": measure.description,
                    "format_string": measure.format_string,
                }
                for measure in metadata.measures
            ],
            "parameters": [
                {
                    "name": param.name,
                    "data_type": param.data_type,
                    "default_value": param.default_value,
                    "prompt": param.prompt,
                    "values": param.values,
                }
                for param in metadata.parameters
            ],
            "visuals": [
                {
                    "name": visual.name,
                    "visual_type": visual.visual_type,
                    "data_fields": visual.data_fields,
                    "filters": visual.filters,
                }
                for visual in metadata.visuals
            ],
            "extraction_errors": metadata.extraction_errors,
            "extracted_at": metadata.extracted_at,
        }

    @staticmethod
    def to_json(metadata: ReportMetadata, indent: int = 2) -> str:
        """Convert metadata to JSON string."""
        return json.dumps(MetadataSerializer.to_dict(metadata), indent=indent)

    @staticmethod
    def to_compact_text(metadata: ReportMetadata, max_tokens: int = 150000) -> str:
        """
        Convert metadata to compact text for LLM context.

        Args:
            metadata: Metadata to serialize
            max_tokens: Approximate token limit (Claude 3.5 Sonnet has ~200K context)

        Returns:
            Compact text representation
        """
        lines = []

        # File info
        lines.append(f"# FILE ANALYSIS: {metadata.file_path}")
        lines.append(f"File Type: {metadata.file_type.value}")
        lines.append(f"File Size: {metadata.file_size:,} bytes")
        lines.append(f"Extracted: {metadata.extracted_at}")
        lines.append("")

        # Data Sources
        if metadata.data_sources:
            lines.append("## DATA SOURCES")
            for ds in metadata.data_sources:
                lines.append(f"- {ds.name}")
                if ds.data_provider:
                    lines.append(f"  Provider: {ds.data_provider}")
                if ds.connection_string:
                    # Truncate connection string for security/privacy
                    conn_str = ds.connection_string
                    if len(conn_str) > 100:
                        conn_str = conn_str[:100] + "..."
                    lines.append(f"  Connection: {conn_str}")
            lines.append("")

        # Tables/Datasets
        if metadata.tables:
            lines.append("## TABLES/DATASETS")
            for table in metadata.tables:
                lines.append(f"### {table.name}")
                if table.description:
                    lines.append(f"{table.description}")
                if table.source:
                    lines.append(f"Source/Query: {table.source}")
                lines.append("Columns:")
                for col in table.columns:
                    col_line = f"  - {col.name}"
                    if col.data_type:
                        col_line += f" ({col.data_type})"
                    if col.description:
                        col_line += f": {col.description}"
                    lines.append(col_line)
                lines.append("")

        # Parameters
        if metadata.parameters:
            lines.append("## PARAMETERS")
            for param in metadata.parameters:
                param_line = f"- {param.name} ({param.data_type})"
                if param.default_value:
                    param_line += f" [Default: {param.default_value}]"
                if param.prompt:
                    param_line += f" - {param.prompt}"
                lines.append(param_line)
                if param.values:
                    lines.append(f"  Allowed values: {', '.join(param.values[:10])}")
                    if len(param.values) > 10:
                        lines.append(f"  ... and {len(param.values) - 10} more")
            lines.append("")

        # Measures (DAX)
        if metadata.measures:
            lines.append("## MEASURES (DAX)")
            for measure in metadata.measures:
                lines.append(f"### {measure.name}")
                if measure.description:
                    lines.append(f"{measure.description}")
                lines.append(f"Expression: {measure.expression}")
                if measure.format_string:
                    lines.append(f"Format: {measure.format_string}")
                lines.append("")

        # Relationships
        if metadata.relationships:
            lines.append("## RELATIONSHIPS")
            for rel in metadata.relationships:
                lines.append(f"- {rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column} ({rel.relationship_type})")
            lines.append("")

        # Visuals/Report Items
        if metadata.visuals:
            lines.append("## VISUALS/REPORT ITEMS")
            for visual in metadata.visuals:
                lines.append(f"- {visual.name} ({visual.visual_type})")
            lines.append("")

        # Errors
        if metadata.extraction_errors:
            lines.append("## EXTRACTION ERRORS")
            for error in metadata.extraction_errors:
                lines.append(f"- {error}")
            lines.append("")

        text = "\n".join(lines)

        # Simple token estimation (roughly 1 token ≈ 4 characters for English)
        approx_tokens = len(text) // 4
        if approx_tokens > max_tokens:
            # Truncate if too large
            chars_to_keep = max_tokens * 4
            text = text[:chars_to_keep] + f"\n\n[TRUNCATED: Original was ~{approx_tokens:,} tokens, kept ~{max_tokens:,}]"

        return text