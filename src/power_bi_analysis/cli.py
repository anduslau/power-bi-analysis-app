#!/usr/bin/env python3
"""
CLI entry point for Insight Fabric.
"""

import argparse
import sys
from pathlib import Path

from .orchestration.pipeline import AnalysisPipeline
from .extractors import list_supported_extensions
from .config import Config
from .llm.factory import list_supported_providers

def main():
    # Load configuration
    config = Config()

    parser = argparse.ArgumentParser(
        description="Analyze Power BI, Excel, and RDL files to generate BRDs and Semantic YAML."
    )
    parser.add_argument(
        "file",
        type=Path,
        nargs='?',
        help="Path to the file to analyze (.rdl, .xlsx, .pbix, etc.)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=config.get_output_dir(),
        help="Directory to save output files (default: ./analysis_output)",
    )
    parser.add_argument(
        "--generate-yaml",
        "-y",
        action="store_true",
        help="Generate Semantic YAML output in addition to BRD",
    )
    parser.add_argument(
        "--no-yaml",
        action="store_true",
        help="Do not generate Semantic YAML output (overrides config default)",
    )
    parser.add_argument(
        "--generate-sql",
        action="store_true",
        help="Generate SQL schema output in addition to BRD",
    )
    parser.add_argument(
        "--generate-dictionary",
        action="store_true",
        help="Generate data dictionary output in addition to BRD",
    )
    parser.add_argument(
        "--llm-provider",
        choices=list_supported_providers(),
        default=config.get_llm_provider(),
        help=f"LLM provider to use (default: {config.get_llm_provider()})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=config.get_llm_model(),
        help="Specific model to use (default: from configuration)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=config.get_llm_api_key(),
        help="API key for LLM provider (default: from configuration)",
    )
    parser.add_argument(
        "--list-supported",
        action="store_true",
        help="List supported file extensions and exit",
    )

    args = parser.parse_args()

    if args.list_supported:
        print("Supported file extensions:")
        for ext in list_supported_extensions():
            print(f"  {ext}")
        return 0

    # Determine YAML generation preference
    if args.no_yaml:
        generate_yaml = False
    elif args.generate_yaml:
        generate_yaml = True
    else:
        generate_yaml = config.get_generate_yaml()

    # Basic validation
    if args.file is None:
        print("Error: No file specified. Use --list-supported to see supported extensions.")
        sys.exit(1)
    if not args.file.exists():
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    print(f"Insight Fabric")
    print(f"=============================")
    print(f"File: {args.file}")
    print(f"Output directory: {args.output_dir}")
    print(f"Generate YAML: {generate_yaml}")
    print(f"Generate SQL: {args.generate_sql}")
    print(f"Generate Dictionary: {args.generate_dictionary}")
    print(f"LLM Provider: {args.llm_provider}")
    if args.model:
        print(f"Model: {args.model}")
    print()

    try:
        # Create and run pipeline
        pipeline = AnalysisPipeline(
            llm_provider=args.llm_provider,
            llm_api_key=args.api_key,
            llm_model=args.model,
            generate_yaml=generate_yaml,
            generate_sql=args.generate_sql,
            generate_dictionary=args.generate_dictionary
        )

        print("Starting analysis...")
        success = pipeline.analyze_file(args.file)

        if not success:
            print("\n[ERROR] Analysis failed with errors:")
            for error in pipeline.get_errors():
                print(f"  - {error}")
            sys.exit(1)

        # Get results
        stats = pipeline.get_stats()

        print("\n[SUCCESS] Analysis completed successfully!")
        print(f"\nStatistics:")
        print(f"  File type: {stats.get('file_type', 'Unknown')}")
        print(f"  File size: {stats.get('file_size', 0):,} bytes")
        print(f"  Extraction time: {stats.get('extract_time', 0):.2f}s")
        print(f"  Metadata tokens: {stats.get('metadata_tokens', 0):,}")
        print(f"  BRD generation time: {stats.get('brd_generation_time', 0):.2f}s")
        if args.generate_yaml:
            print(f"  YAML generation time: {stats.get('yaml_generation_time', 0):.2f}s")
        if args.generate_sql:
            print(f"  SQL generation time: {stats.get('sql_generation_time', 0):.2f}s")
        if args.generate_dictionary:
            print(f"  Dictionary generation time: {stats.get('dictionary_generation_time', 0):.2f}s")
        print(f"  Total time: {stats.get('total_time', 0):.2f}s")

        # Save outputs
        print(f"\n[Saving] Saving outputs to {args.output_dir}...")
        brd_path, yaml_path, sql_path, dictionary_path = pipeline.save_outputs(args.output_dir)

        print(f"\n[Files] Generated files:")
        print(f"  BRD: {brd_path}")
        if yaml_path:
            print(f"  Semantic YAML: {yaml_path}")
        if sql_path:
            print(f"  SQL Schema: {sql_path}")
        if dictionary_path:
            print(f"  Data Dictionary: {dictionary_path}")
        print(f"  Metadata: {args.output_dir / brd_path.stem.replace('_brd', '_metadata.json')}")
        print(f"  Statistics: {args.output_dir / brd_path.stem.replace('_brd', '_stats.json')}")

        print(f"\n[Complete] Analysis complete! Check the output directory for results.")

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

    return 0

if __name__ == "__main__":
    sys.exit(main())