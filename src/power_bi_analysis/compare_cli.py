#!/usr/bin/env python3
"""
CLI for comparing two BI files and generating diff reports.
"""

import argparse
import sys
from pathlib import Path

from .extractors import extract_metadata
from .comparison import compare_metadata, render_diff


def main():
    parser = argparse.ArgumentParser(
        description="Compare two BI files (Power BI, Excel, RDL, etc.) and generate diff report."
    )
    parser.add_argument(
        "file1",
        type=Path,
        help="Path to baseline file (.rdl, .xlsx, .pbix, etc.)",
    )
    parser.add_argument(
        "file2",
        type=Path,
        help="Path to new file (.rdl, .xlsx, .pbix, etc.)",
    )
    parser.add_argument(
        "--output-format",
        "-f",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("./comparison_output"),
        help="Directory to save output file (default: ./comparison_output)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Specific output file path (overrides automatic naming)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show summary, not detailed changes (applies to markdown format)",
    )
    parser.add_argument(
        "--no-renames",
        action="store_true",
        help="Disable rename detection",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.8,
        help="Similarity threshold for rename detection (0.0-1.0, default: 0.8)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output",
    )

    args = parser.parse_args()

    # Validate files
    for file_path, label in [(args.file1, "baseline"), (args.file2, "new")]:
        if not file_path.exists():
            print(f"Error: {label} file '{file_path}' not found.", file=sys.stderr)
            sys.exit(1)

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.quiet:
        print("BI File Comparison Tool")
        print("======================")
        print(f"Baseline: {args.file1}")
        print(f"New: {args.file2}")
        print(f"Output format: {args.output_format}")
        print(f"Output directory: {args.output_dir}")
        if not args.no_renames:
            print(f"Rename detection: enabled (threshold: {args.similarity_threshold})")
        else:
            print(f"Rename detection: disabled")
        print()

    try:
        # Extract metadata from both files
        if not args.quiet:
            print("Extracting metadata from baseline file...")
        try:
            meta1 = extract_metadata(args.file1)
        except Exception as e:
            print(f"Error: Failed to extract metadata from {args.file1}: {e}", file=sys.stderr)
            sys.exit(1)
        if not meta1:
            print(f"Error: No metadata extracted from {args.file1}", file=sys.stderr)
            sys.exit(1)

        if not args.quiet:
            print("Extracting metadata from new file...")
        try:
            meta2 = extract_metadata(args.file2)
        except Exception as e:
            print(f"Error: Failed to extract metadata from {args.file2}: {e}", file=sys.stderr)
            sys.exit(1)
        if not meta2:
            print(f"Error: No metadata extracted from {args.file2}", file=sys.stderr)
            sys.exit(1)

        if not args.quiet:
            print("Comparing metadata...")

        # Compare metadata
        diff_report = compare_metadata(
            meta1,
            meta2,
            detect_renames=not args.no_renames,
            similarity_threshold=args.similarity_threshold
        )

        # Determine output file path
        if args.output_file:
            output_path = args.output_file
        else:
            # Generate automatic name: compare_{file1stem}_vs_{file2stem}.{ext}
            stem1 = args.file1.stem
            stem2 = args.file2.stem
            ext = {
                "markdown": "md",
                "json": "json",
                "html": "html"
            }[args.output_format]
            output_path = args.output_dir / f"compare_{stem1}_vs_{stem2}.{ext}"

        # Render diff
        if not args.quiet:
            print(f"Generating {args.output_format} report...")

        render_kwargs = {}
        if args.output_format == "markdown":
            render_kwargs["include_summary"] = True
            render_kwargs["include_details"] = not args.summary_only

        output_content = render_diff(diff_report, args.output_format, **render_kwargs)

        # Save to file
        output_path.write_text(output_content, encoding="utf-8")

        # Also print summary to console
        if not args.quiet:
            print()
            print("Comparison Summary")
            print("------------------")
            summary = diff_report.summary
            print(f"Total changes: {summary.get('total', 0)}")
            print(f"  Added: {summary.get('added', 0)}")
            print(f"  Removed: {summary.get('removed', 0)}")
            print(f"  Modified: {summary.get('modified', 0)}")

            # Print breakdown by element type
            element_types = set()
            for key in summary.keys():
                if '_' in key:
                    element_type, _ = key.split('_', 1)
                    element_types.add(element_type)

            if element_types:
                print("\nBreakdown by element type:")
                for element_type in sorted(element_types):
                    added = summary.get(f"{element_type}_added", 0)
                    removed = summary.get(f"{element_type}_removed", 0)
                    modified = summary.get(f"{element_type}_modified", 0)
                    total = added + removed + modified
                    if total > 0:
                        print(f"  {element_type.capitalize()}: {total} total "
                              f"(+{added}, -{removed}, ~{modified})")

            print()
            print(f"Report saved to: {output_path}")
            print("Comparison complete!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())