#!/usr/bin/env python3
"""
Basic CLI for RDL file analysis.
Extracts metadata from RDL files and outputs JSON or human-readable text.
No LLM dependencies.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .extractors.rdl_extractor import RDLExtractor
from .serializers.metadata_serializer import MetadataSerializer

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract metadata from RDL files (SQL Server Reporting Services)."
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Path to RDL file (.rdl)"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Directory to save output files (default: print to stdout)"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "text", "compact"],
        default="text",
        help="Output format: json, text (human-readable), compact (LLM-ready text) (default: text)"
    )
    parser.add_argument(
        "--list-supported",
        action="store_true",
        help="List supported file extensions and exit"
    )
    return parser.parse_args()

def list_supported():
    """List supported file extensions."""
    extractor = RDLExtractor()
    print("Supported file extensions:")
    for ext in extractor.supported_extensions:
        print(f"  {ext}")
    return 0

def ensure_output_dir(path: Optional[Path]) -> Optional[Path]:
    """Ensure output directory exists if provided."""
    if path is None:
        return None
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_output(content: str, output_dir: Path, base_name: str, suffix: str):
    """Save content to file in output directory."""
    output_path = output_dir / f"{base_name}{suffix}"
    output_path.write_text(content, encoding="utf-8")
    print(f"Saved: {output_path}")
    return output_path

def main():
    args = parse_args()

    if args.list_supported:
        return list_supported()

    if args.file is None:
        print("Error: No file specified. Provide a RDL file path.", file=sys.stderr)
        sys.exit(1)

    # Validate file
    if not args.file.exists():
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.file.suffix.lower() != ".rdl":
        print(f"Warning: File extension is not .rdl. Attempting extraction anyway.")

    # Extract metadata
    print(f"Analyzing RDL file: {args.file}", file=sys.stderr)
    extractor = RDLExtractor()
    try:
        metadata = extractor.extract(args.file)
    except Exception as e:
        print(f"Extraction error: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate output based on format
    if args.format == "json":
        output = MetadataSerializer.to_json(metadata, indent=2)
        suffix = "_metadata.json"
    elif args.format == "compact":
        output = MetadataSerializer.to_compact_text(metadata)
        suffix = "_metadata.txt"
    else:  # text
        # Create a simple human-readable summary
        lines = []
        lines.append(f"RDL Analysis: {args.file}")
        lines.append(f"File Size: {metadata.file_size:,} bytes")
        lines.append(f"Extracted: {metadata.extracted_at}")
        lines.append("")
        if metadata.data_sources:
            lines.append("Data Sources:")
            for ds in metadata.data_sources:
                lines.append(f"  - {ds.name}")
                if ds.data_provider:
                    lines.append(f"    Provider: {ds.data_provider}")
                if ds.connection_string:
                    # Truncate for security
                    conn = ds.connection_string
                    if len(conn) > 80:
                        conn = conn[:80] + "..."
                    lines.append(f"    Connection: {conn}")
            lines.append("")
        if metadata.tables:
            lines.append("Datasets:")
            for table in metadata.tables:
                lines.append(f"  - {table.name}")
                if table.description:
                    lines.append(f"    Description: {table.description}")
                if table.columns:
                    lines.append(f"    Columns: {len(table.columns)}")
                    for col in table.columns[:5]:  # Show first 5 columns
                        col_line = f"      * {col.name}"
                        if col.data_type:
                            col_line += f" ({col.data_type})"
                        lines.append(col_line)
                    if len(table.columns) > 5:
                        lines.append(f"      ... and {len(table.columns) - 5} more")
                lines.append("")
        if metadata.parameters:
            lines.append("Parameters:")
            for param in metadata.parameters:
                param_line = f"  - {param.name} ({param.data_type})"
                if param.default_value:
                    param_line += f" [Default: {param.default_value}]"
                if param.prompt:
                    param_line += f" - {param.prompt}"
                lines.append(param_line)
            lines.append("")
        if metadata.visuals:
            lines.append("Visuals:")
            for visual in metadata.visuals:
                lines.append(f"  - {visual.name} ({visual.visual_type})")
            lines.append("")
        if metadata.extraction_errors:
            lines.append("Extraction Errors:")
            for error in metadata.extraction_errors:
                lines.append(f"  - {error}")
            lines.append("")
        output = "\n".join(lines)
        suffix = "_summary.txt"

    # Output or save
    if args.output_dir is None:
        print(output)
    else:
        ensure_output_dir(args.output_dir)
        base_name = args.file.stem
        save_output(output, args.output_dir, base_name, suffix)
        # Also save raw JSON for reference
        json_output = MetadataSerializer.to_json(metadata, indent=2)
        save_output(json_output, args.output_dir, base_name, "_metadata.json")
        print(f"\nAnalysis complete. Files saved to {args.output_dir}", file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main())