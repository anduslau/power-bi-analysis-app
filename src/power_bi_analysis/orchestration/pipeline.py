"""
Main orchestration pipeline for file analysis.
"""

import os
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from ..extractors import extract_metadata
from ..serializers.metadata_serializer import MetadataSerializer
from ..llm.factory import create_llm_client
from ..models import ReportMetadata, DiffReport
from ..comparison import compare_metadata
import yaml
import concurrent.futures

class AnalysisPipeline:
    """Main pipeline for analyzing files and generating outputs."""

    def __init__(
        self,
        llm_provider: str = "anthropic",
        llm_api_key: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_options: Optional[Dict[str, Any]] = None,
        generate_yaml: bool = False,
        generate_sql: bool = False,
        generate_dictionary: bool = False,
        parallel_generation: bool = True
    ):
        """
        Initialize the analysis pipeline.

        Args:
            llm_provider: LLM provider to use
            llm_api_key: API key for LLM provider
            llm_model: Specific model to use
            generate_yaml: Whether to generate Semantic YAML output
            generate_sql: Whether to generate SQL schema output
            generate_dictionary: Whether to generate data dictionary output
            parallel_generation: Whether to generate outputs in parallel (default: True)
        """
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.generate_yaml = generate_yaml
        self.generate_sql = generate_sql
        self.generate_dictionary = generate_dictionary
        self.parallel_generation = parallel_generation
        self.llm_options = llm_options or {}

        self.llm_client = None
        self.metadata: Optional[ReportMetadata] = None
        self.metadata_text: Optional[str] = None
        self.brd_output: Optional[str] = None
        self.yaml_output: Optional[str] = None
        self.sql_output: Optional[str] = None
        self.dictionary_output: Optional[str] = None
        self.errors: list = []
        self.stats: Dict[str, Any] = {}

    def _add_error(self, error: str, context: str = "") -> None:
        """
        Add an error message with optional context.

        Args:
            error: The error message
            context: Additional context about where the error occurred
        """
        if context:
            self.errors.append(f"[{context}] {error}")
        else:
            self.errors.append(error)

    def _validate_file(self, file_path: Path) -> bool:
        """
        Validate that the file exists, is readable, and has a supported extension.

        Args:
            file_path: Path to validate

        Returns:
            True if valid, False otherwise (errors added to self.errors)
        """
        from ..extractors import list_supported_extensions

        if not file_path.exists():
            self._add_error(f"File does not exist: {file_path}", "file_validation")
            return False

        if not file_path.is_file():
            self._add_error(f"Path is not a file: {file_path}", "file_validation")
            return False

        try:
            file_path.open('r').close()
        except PermissionError:
            self._add_error(f"Permission denied: {file_path}", "file_validation")
            return False
        except OSError as e:
            self._add_error(f"Cannot read file: {file_path} - {e}", "file_validation")
            return False

        # Check extension against supported extractors
        supported = list_supported_extensions()
        if file_path.suffix.lower() not in supported:
            self._add_error(
                f"Unsupported file extension: {file_path.suffix}. "
                f"Supported extensions: {', '.join(sorted(supported))}",
                "file_validation"
            )
            return False

        return True

    def _validate_api_key(self) -> bool:
        """
        Validate that an API key is available for the configured LLM provider.

        Returns:
            True if API key appears valid, False otherwise
        """
        # API key could be provided via parameter or environment variable
        # The LLM client factory will handle missing keys, but we can give early warning
        if self.llm_api_key:
            return True

        # Check environment variable based on provider
        provider_env_vars = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "deepseek": "OPENAI_API_KEY",  # DeepSeek uses OpenAI-compatible API
        }

        env_var = provider_env_vars.get(self.llm_provider)
        if env_var and os.environ.get(env_var):
            return True

        # If provider not in our mapping, we can't validate environment variable
        # Let the LLM factory handle missing key
        if self.llm_provider not in provider_env_vars:
            self._add_error(
                f"Unknown LLM provider '{self.llm_provider}'. "
                f"API key validation skipped; ensure API key is provided via parameter.",
                "api_validation"
            )
            return True  # Continue, let factory raise error if missing

        self._add_error(
            f"No API key provided for LLM provider '{self.llm_provider}'. "
            f"Set {env_var} environment variable or pass llm_api_key parameter.",
            "api_validation"
        )
        return False

    def _get_llm_client_params(self) -> Tuple[str, Optional[str], Optional[str], Dict[str, Any]]:
        """
        Get normalized LLM client parameters with provider mappings applied.

        Returns:
            Tuple of (provider, api_key, model, options)
        """
        from typing import Tuple, Optional, Dict, Any

        provider = self.llm_provider
        api_key = self.llm_api_key
        model = self.llm_model
        options = self.llm_options.copy() if self.llm_options else {}

        # Map deepseek to openai with default base URL
        if provider == "deepseek":
            provider = "openai"
            # Set default DeepSeek base URL if not already set
            if "base_url" not in options:
                options["base_url"] = "https://api.deepseek.com"
            # Set default DeepSeek model if not specified
            if model is None:
                model = "deepseek-chat"

        return provider, api_key, model, options

    def _validate_output_dir(self, output_dir: Path) -> bool:
        """
        Validate that output directory can be created or written to.

        Args:
            output_dir: Directory to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            # Test write permission
            test_file = output_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except PermissionError:
            self._add_error(f"Permission denied for output directory: {output_dir}", "output_validation")
            return False
        except OSError as e:
            self._add_error(f"Cannot create or write to output directory: {output_dir} - {e}", "output_validation")
            return False

    def _clean_yaml_output(self, yaml_text: str) -> str:
        """
        Clean YAML output by parsing and re-dumping to ensure valid YAML.
        This removes duplicate keys (keeping last occurrence) and fixes formatting.
        """
        try:
            data = yaml.safe_load(yaml_text)
            if data is None:
                return yaml_text
            # Dump with default flow style=False (block style)
            return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except yaml.YAMLError as e:
            # If YAML parsing fails, return original with error comment
            return f"# YAML parsing error: {e}\n{yaml_text}"
        except Exception:
            # Any other error, return original
            return yaml_text

    def analyze_file(self, file_path: Path) -> bool:
        """
        Analyze a file and generate outputs.

        Args:
            file_path: Path to the file to analyze

        Returns:
            True if analysis succeeded, False otherwise
        """
        self.errors.clear()
        self.stats.clear()
        start_time = time.time()

        # Early validation
        if not self._validate_file(file_path):
            return False
        if not self._validate_api_key():
            return False

        try:
            # Step 1: Extract metadata
            extract_start = time.time()
            try:
                self.metadata = extract_metadata(file_path)
            except Exception as e:
                self._add_error(f"Metadata extraction failed: {e}", "extraction")
                return False
            extract_time = time.time() - extract_start

            # Step 2: Serialize for LLM
            serialize_start = time.time()
            try:
                self.metadata_text = MetadataSerializer.to_compact_text(self.metadata)
            except Exception as e:
                self._add_error(f"Metadata serialization failed: {e}", "serialization")
                return False
            serialize_time = time.time() - serialize_start

            # Step 3: Initialize LLM client
            llm_init_start = time.time()
            try:
                # Handle provider mappings (e.g., deepseek -> openai with base URL)
                provider, api_key, model, options = self._get_llm_client_params()
                self.llm_client = create_llm_client(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    **options
                )
            except ValueError as e:
                self._add_error(f"LLM client initialization failed: {e}", "llm_init")
                return False
            except Exception as e:
                self._add_error(f"Unexpected error during LLM client initialization: {e}", "llm_init")
                return False
            llm_init_time = time.time() - llm_init_start

            # Step 4: Generate BRD
            brd_start = time.time()
            try:
                self.brd_output = self.llm_client.generate_brd(
                    self.metadata_text,
                    file_path.name
                )
                # Check for error messages in output (LLM clients may return error strings)
                if self.brd_output.startswith("Error generating BRD:"):
                    self._add_error(self.brd_output, "brd_generation")
                    return False
            except Exception as e:
                self._add_error(f"BRD generation failed: {e}", "brd_generation")
                return False
            brd_time = time.time() - brd_start

            # Step 5: Generate optional outputs (YAML, SQL, Dictionary)
            yaml_time = 0
            sql_time = 0
            dictionary_time = 0

            # Determine which outputs to generate
            tasks = []
            if self.generate_yaml:
                tasks.append(('yaml', self.llm_client.generate_sml_yaml))
            if self.generate_sql:
                tasks.append(('sql', self.llm_client.generate_sql_schema))
            if self.generate_dictionary:
                tasks.append(('dictionary', self.llm_client.generate_data_dictionary))

            if not tasks:
                # No optional outputs requested
                pass
            elif self.parallel_generation and len(tasks) > 1:
                # Parallel generation using ThreadPoolExecutor
                start_parallel = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
                    # Submit all tasks with individual start times
                    future_to_info = {}
                    for output_type, func in tasks:
                        future = executor.submit(func, self.metadata_text, file_path.name)
                        future_to_info[future] = {
                            'type': output_type,
                            'start': time.time()
                        }

                    # Collect results as they complete
                    for future in concurrent.futures.as_completed(future_to_info):
                        info = future_to_info[future]
                        output_type = info['type']
                        try:
                            result = future.result()
                            # Check for error messages (matching original LLM client error prefixes)
                            error_prefixes = {
                                'yaml': 'Error generating YAML:',
                                'sql': 'Error generating SQL schema:',
                                'dictionary': 'Error generating data dictionary:'
                            }
                            error_prefix = error_prefixes.get(output_type, f"Error generating {output_type}:")
                            if result.startswith(error_prefix):
                                self._add_error(result, f"{output_type}_generation")
                                # Cancel remaining futures
                                for f in future_to_info:
                                    f.cancel()
                                return False
                            # Store result
                            if output_type == 'yaml':
                                self.yaml_output = self._clean_yaml_output(result)
                            elif output_type == 'sql':
                                self.sql_output = result
                            elif output_type == 'dictionary':
                                self.dictionary_output = result
                            # Record individual task duration
                            task_duration = time.time() - info['start']
                            if output_type == 'yaml':
                                yaml_time = task_duration
                            elif output_type == 'sql':
                                sql_time = task_duration
                            elif output_type == 'dictionary':
                                dictionary_time = task_duration
                        except Exception as e:
                            self._add_error(f"{output_type} generation failed: {e}", f"{output_type}_generation")
                            # Cancel remaining futures
                            for f in future_to_info:
                                f.cancel()
                            return False

                    # Total parallel time (for reference)
                    parallel_time = time.time() - start_parallel
            else:
                # Sequential generation
                error_prefixes = {
                    'yaml': 'Error generating YAML:',
                    'sql': 'Error generating SQL schema:',
                    'dictionary': 'Error generating data dictionary:'
                }
                for output_type, func in tasks:
                    task_start = time.time()
                    try:
                        result = func(self.metadata_text, file_path.name)
                        error_prefix = error_prefixes.get(output_type, f"Error generating {output_type}:")
                        if result.startswith(error_prefix):
                            self._add_error(result, f"{output_type}_generation")
                            return False
                        # Store result
                        if output_type == 'yaml':
                            self.yaml_output = self._clean_yaml_output(result)
                        elif output_type == 'sql':
                            self.sql_output = result
                        elif output_type == 'dictionary':
                            self.dictionary_output = result
                    except Exception as e:
                        self._add_error(f"{output_type} generation failed: {e}", f"{output_type}_generation")
                        return False
                    task_time = time.time() - task_start
                    if output_type == 'yaml':
                        yaml_time = task_time
                    elif output_type == 'sql':
                        sql_time = task_time
                    elif output_type == 'dictionary':
                        dictionary_time = task_time

            total_time = time.time() - start_time

            # Collect statistics
            try:
                self.stats = {
                    "file_path": str(file_path),
                    "file_size": file_path.stat().st_size,
                    "file_type": self.metadata.file_type.value,
                    "extract_time": extract_time,
                    "serialize_time": serialize_time,
                    "llm_init_time": llm_init_time,
                    "brd_generation_time": brd_time,
                    "yaml_generation_time": yaml_time,
                    "sql_generation_time": sql_time,
                    "dictionary_generation_time": dictionary_time,
                    "total_time": total_time,
                    "metadata_tokens": self.llm_client.estimate_tokens(self.metadata_text),
                    "brd_length": len(self.brd_output) if self.brd_output else 0,
                    "yaml_length": len(self.yaml_output) if self.yaml_output else 0,
                    "sql_length": len(self.sql_output) if self.sql_output else 0,
                    "dictionary_length": len(self.dictionary_output) if self.dictionary_output else 0,
                    "extraction_errors": len(self.metadata.extraction_errors),
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                self._add_error(f"Failed to collect statistics: {e}", "statistics")
                # Continue - statistics are not critical

            return True

        except Exception as e:
            self._add_error(f"Unexpected error in analysis pipeline: {e}", "pipeline")
            return False

    def get_brd(self) -> Optional[str]:
        """Get the generated BRD."""
        return self.brd_output

    def get_yaml(self) -> Optional[str]:
        """Get the generated YAML."""
        return self.yaml_output

    def get_sql(self) -> Optional[str]:
        """Get the generated SQL schema."""
        return self.sql_output

    def get_dictionary(self) -> Optional[str]:
        """Get the generated data dictionary."""
        return self.dictionary_output

    def get_metadata_json(self, indent: int = 2) -> Optional[str]:
        """Get metadata as JSON string."""
        if self.metadata:
            return MetadataSerializer.to_json(self.metadata, indent)
        return None

    def get_metadata_text(self) -> Optional[str]:
        """Get the compact metadata text sent to LLM."""
        return self.metadata_text

    def get_stats(self) -> Dict[str, Any]:
        """Get analysis statistics."""
        return self.stats.copy()

    def get_errors(self) -> list:
        """Get any errors that occurred during analysis."""
        return self.errors.copy()

    def compare_with(self, baseline_path: Path, detect_renames: bool = True, similarity_threshold: float = 0.8) -> Optional[DiffReport]:
        """
        Compare current analysis with a baseline file.

        Args:
            baseline_path: Path to baseline file to compare against
            detect_renames: Whether to detect renamed elements
            similarity_threshold: Similarity threshold for rename detection (0.0-1.0)

        Returns:
            DiffReport if comparison successful, None if no metadata available
        """
        if not self.metadata:
            self._add_error("No metadata available. Run analyze_file first.", "comparison")
            return None

        if not baseline_path.exists():
            self._add_error(f"Baseline file not found: {baseline_path}", "comparison")
            return None

        try:
            # Extract metadata from baseline file
            baseline_metadata = extract_metadata(baseline_path)
            if not baseline_metadata:
                self._add_error(f"Failed to extract metadata from baseline file: {baseline_path}", "comparison")
                return None

            # Compare metadata
            diff_report = compare_metadata(
                baseline_metadata,
                self.metadata,
                detect_renames=detect_renames,
                similarity_threshold=similarity_threshold
            )

            return diff_report

        except Exception as e:
            self._add_error(f"Comparison failed: {e}", "comparison")
            return None

    def save_outputs(self, output_dir: Path) -> Tuple[Path, Optional[Path], Optional[Path], Optional[Path]]:
        """
        Save generated outputs to files.

        Args:
            output_dir: Directory to save files

        Returns:
            Tuple of (brd_path, yaml_path, sql_path, dictionary_path) - each path is None if not generated
        """
        if not self.brd_output:
            raise ValueError("No BRD generated. Run analyze_file first.")

        # Validate output directory
        if not self._validate_output_dir(output_dir):
            raise ValueError(f"Cannot write to output directory: {output_dir}. Errors: {self.errors[-1] if self.errors else 'Unknown'}")

        # Generate filename base from original file
        if self.metadata:
            file_stem = Path(self.metadata.file_path).stem
        else:
            file_stem = "analysis"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{file_stem}_{timestamp}"

        errors = []
        brd_path = yaml_path = sql_path = dictionary_path = None

        # Save BRD
        brd_path = output_dir / f"{base_name}_brd.md"
        brd_content = f"""# Business Requirements Document

## Source File
- **File:** {self.stats.get('file_path', 'Unknown')}
- **Type:** {self.stats.get('file_type', 'Unknown')}
- **Analyzed:** {self.stats.get('timestamp', 'Unknown')}
- **Analysis Time:** {self.stats.get('total_time', 0):.2f} seconds

---

{self.brd_output}
"""
        try:
            brd_path.write_text(brd_content, encoding="utf-8")
        except Exception as e:
            errors.append(f"Failed to save BRD: {e}")
            brd_path = None

        # Save YAML if generated
        if self.yaml_output:
            yaml_path = output_dir / f"{base_name}_semantic.yaml"
            try:
                yaml_path.write_text(self.yaml_output, encoding="utf-8")
            except Exception as e:
                errors.append(f"Failed to save YAML: {e}")
                yaml_path = None

        # Save SQL schema if generated
        if self.sql_output:
            sql_path = output_dir / f"{base_name}_schema.sql"
            try:
                sql_path.write_text(self.sql_output, encoding="utf-8")
            except Exception as e:
                errors.append(f"Failed to save SQL schema: {e}")
                sql_path = None

        # Save data dictionary if generated
        if self.dictionary_output:
            dictionary_path = output_dir / f"{base_name}_data_dictionary.md"
            try:
                dictionary_path.write_text(self.dictionary_output, encoding="utf-8")
            except Exception as e:
                errors.append(f"Failed to save data dictionary: {e}")
                dictionary_path = None

        # Save metadata as JSON for reference
        if self.metadata:
            metadata_path = output_dir / f"{base_name}_metadata.json"
            try:
                metadata_json = MetadataSerializer.to_json(self.metadata)
                metadata_path.write_text(metadata_json, encoding="utf-8")
            except Exception as e:
                errors.append(f"Failed to save metadata JSON: {e}")
                # Non-critical, continue

        # Save statistics
        stats_path = output_dir / f"{base_name}_stats.json"
        try:
            import json
            stats_path.write_text(json.dumps(self.stats, indent=2), encoding="utf-8")
        except Exception as e:
            errors.append(f"Failed to save statistics: {e}")
            # Non-critical, continue

        if errors:
            # Add errors to pipeline error list
            for error in errors:
                self._add_error(error, "save_outputs")
            # Raise exception summarizing failures
            raise ValueError(f"Failed to save some outputs: {'; '.join(errors)}")

        return brd_path, yaml_path, sql_path, dictionary_path