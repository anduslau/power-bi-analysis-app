#!/usr/bin/env python3
"""
Test Power BI extractor registration and basic functionality.
"""
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from power_bi_analysis.extractors import (
    PowerBIExtractor, get_extractor_for_file, list_supported_extensions
)

def test_extractor_registration():
    print("Testing PowerBIExtractor registration...")

    # Check that PowerBIExtractor is in registry
    extractor = PowerBIExtractor()
    print(f"Extractor class: {extractor.__class__.__name__}")
    print(f"Supported extensions: {extractor.supported_extensions}")

    # Test can_extract with dummy paths
    test_paths = [
        Path("dummy.pbix"),
        Path("dummy.pbit"),
        Path("dummy.pbip"),
        Path("folder"),  # directory
    ]
    for path in test_paths:
        # Note: we don't create actual files, just test extension detection
        if path.suffix:
            print(f"  {path.suffix}: {extractor.can_extract(path)}")
        else:
            print(f"  directory: {extractor.can_extract(path)}")

    # Test get_extractor_for_file with .pbix extension
    dummy_pbix = Path("test.pbix")
    extractor_found = get_extractor_for_file(dummy_pbix)
    if extractor_found:
        print(f"Extractor found for .pbix: {extractor_found.__class__.__name__}")
    else:
        print("ERROR: No extractor found for .pbix")
        sys.exit(1)

    # Check list_supported_extensions includes .pbix
    extensions = list_supported_extensions()
    if '.pbix' in extensions:
        print(f"Supported extensions list includes .pbix: {extensions}")
    else:
        print(f"ERROR: .pbix missing from supported extensions: {extensions}")
        sys.exit(1)

    print("All registration tests passed.")

def test_pbixray_available():
    print("\nTesting pbixray availability...")
    try:
        import pbixray
        print(f"pbixray version: {pbixray.__version__ if hasattr(pbixray, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        print(f"WARNING: pbixray not available: {e}")
        print("Extraction will fail but registration works.")
        return False

if __name__ == "__main__":
    test_extractor_registration()
    test_pbixray_available()
    print("\nPower BI Extractor implementation complete.")