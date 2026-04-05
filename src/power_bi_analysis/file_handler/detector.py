"""
File type detection and routing.
"""

import zipfile
from pathlib import Path
from typing import Optional
from ..models import FileType

def detect_file_type(file_path: Path) -> FileType:
    """
    Detect the type of file based on extension and content.
    """
    suffix = file_path.suffix.lower()

    # Check by extension first
    if suffix == ".rdl":
        return FileType.RDL
    elif suffix in [".xlsx", ".xls"]:
        # Check if it contains PowerPivot model
        if _is_excel_with_powerpivot(file_path):
            return FileType.POWER_BI  # Excel with data model
        return FileType.EXCEL
    elif suffix == ".pbix":
        return FileType.POWER_BI
    elif suffix == ".pbit":
        return FileType.POWER_BI_TEMPLATE
    elif file_path.is_dir() and _is_pbip_folder(file_path):
        return FileType.POWER_BI_PROJECT
    else:
        return FileType.UNKNOWN

def _is_excel_with_powerpivot(file_path: Path) -> bool:
    """
    Check if an Excel file contains a PowerPivot data model.
    """
    try:
        # Excel files are zip archives
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Look for PowerPivot related files in the archive
            namelist = zip_ref.namelist()
            # PowerPivot data model is typically in xl/model
            return any('xl/model' in name for name in namelist)
    except (zipfile.BadZipFile, KeyError, OSError):
        return False

def _is_pbip_folder(folder_path: Path) -> bool:
    """
    Check if a folder is a Power BI Project (PBIP) folder.
    """
    # PBIP folder contains report.json, definition.pbir, etc.
    required_files = ["report.json", "definition.pbir"]
    return all((folder_path / file).exists() for file in required_files)

def get_extractor_for_file(file_path: Path) -> Optional[str]:
    """
    Return the name of the extractor module for a given file.
    """
    file_type = detect_file_type(file_path)

    mapping = {
        FileType.RDL: "rdl_extractor",
        FileType.EXCEL: "excel_extractor",
        FileType.POWER_BI: "powerbi_extractor",
        FileType.POWER_BI_TEMPLATE: "powerbi_extractor",
        FileType.POWER_BI_PROJECT: "powerbi_extractor",
    }

    return mapping.get(file_type)