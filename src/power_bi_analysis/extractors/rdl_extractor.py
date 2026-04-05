"""
RDL (Report Definition Language) file extractor.
RDL files are XML-based report definitions used by SQL Server Reporting Services.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseExtractor
from ..models import (
    ReportMetadata, FileType, DataSource, Column, Table,
    Parameter, Visual, DataSource
)

class RDLExtractor(BaseExtractor):
    """Extractor for RDL files."""

    def __init__(self):
        self.namespaces = {
            'rd': 'http://schemas.microsoft.com/SQLServer/reporting/reportdesigner',
            '': 'http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition'
        }

    def can_extract(self, file_path: Path) -> bool:
        """Check if file is an RDL file."""
        return file_path.suffix.lower() == '.rdl'

    @property
    def supported_extensions(self) -> List[str]:
        return ['.rdl']

    def extract(self, file_path: Path) -> ReportMetadata:
        """Extract metadata from RDL file."""
        metadata = ReportMetadata(
            file_type=FileType.RDL,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            extracted_at=datetime.now().isoformat()
        )

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Register namespaces for easier searching
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)

            # Extract data sources
            metadata.data_sources = self._extract_data_sources(root)

            # Extract datasets (queries)
            metadata.tables = self._extract_datasets(root)

            # Extract parameters
            metadata.parameters = self._extract_parameters(root)

            # Extract report items (visuals)
            metadata.visuals = self._extract_report_items(root)

        except ET.ParseError as e:
            metadata.extraction_errors.append(f"XML parsing error: {e}")
        except Exception as e:
            metadata.extraction_errors.append(f"Extraction error: {e}")

        return metadata

    def _extract_data_sources(self, root: ET.Element) -> List[DataSource]:
        """Extract data source definitions."""
        data_sources = []

        # RDL 2016 namespace
        ns = self.namespaces['']

        for ds in root.findall(f'.//{{{ns}}}DataSource'):
            name_elem = ds.find(f'{{{ns}}}DataSourceReference')
            if name_elem is not None:
                name = name_elem.text or ds.get('Name', 'Unknown')
            else:
                name = ds.get('Name', 'Unknown')

            # Get connection properties
            conn_props = ds.find(f'.//{{{ns}}}ConnectionProperties')
            if conn_props is not None:
                conn_string_elem = conn_props.find(f'{{{ns}}}ConnectString')
                conn_string = conn_string_elem.text if conn_string_elem is not None else None

                data_provider_elem = conn_props.find(f'{{{ns}}}DataProvider')
                data_provider = data_provider_elem.text if data_provider_elem is not None else None
            else:
                conn_string = None
                data_provider = None

            data_sources.append(DataSource(
                name=name,
                connection_string=conn_string,
                data_provider=data_provider
            ))

        return data_sources

    def _extract_datasets(self, root: ET.Element) -> List[Table]:
        """Extract dataset definitions (queries)."""
        tables = []
        ns = self.namespaces['']

        for dataset in root.findall(f'.//{{{ns}}}DataSet'):
            name = dataset.get('Name', 'Unknown')

            # Get query
            query_elem = dataset.find(f'.//{{{ns}}}Query')
            if query_elem is not None:
                query_text_elem = query_elem.find(f'{{{ns}}}CommandText')
                query = query_text_elem.text if query_text_elem is not None else ''
            else:
                query = ''

            # Get fields
            columns = []
            fields_elem = dataset.find(f'.//{{{ns}}}Fields')
            if fields_elem is not None:
                for field in fields_elem.findall(f'{{{ns}}}Field'):
                    field_name = field.get('Name', 'Unknown')
                    data_type_elem = field.find(f'{{{ns}}}DataField')
                    data_type = data_type_elem.text if data_type_elem is not None else ''

                    columns.append(Column(
                        name=field_name,
                        data_type=data_type,
                        description=f"From query: {query[:100]}..." if query else None
                    ))

            tables.append(Table(
                name=name,
                columns=columns,
                description=f"Dataset query: {query[:200]}..." if query else None,
                source=query if query else None
            ))

        return tables

    def _extract_parameters(self, root: ET.Element) -> List[Parameter]:
        """Extract report parameters."""
        parameters = []
        ns = self.namespaces['']

        for param in root.findall(f'.//{{{ns}}}ReportParameter'):
            name = param.get('Name', 'Unknown')

            data_type_elem = param.find(f'{{{ns}}}DataType')
            data_type = data_type_elem.text if data_type_elem is not None else 'String'

            default_elem = param.find(f'{{{ns}}}DefaultValue')
            default_value = None
            if default_elem is not None:
                values_elem = default_elem.find(f'{{{ns}}}Values')
                if values_elem is not None:
                    value_elems = values_elem.findall(f'{{{ns}}}Value')
                    if value_elems:
                        default_value = value_elems[0].text

            prompt_elem = param.find(f'{{{ns}}}Prompt')
            prompt = prompt_elem.text if prompt_elem is not None else None

            # Get available values
            values = []
            valid_values_elem = param.find(f'.//{{{ns}}}ValidValues')
            if valid_values_elem is not None:
                for value in valid_values_elem.findall(f'.//{{{ns}}}Value'):
                    if value.text:
                        values.append(value.text)

            parameters.append(Parameter(
                name=name,
                data_type=data_type,
                default_value=default_value,
                prompt=prompt,
                values=values
            ))

        return parameters

    def _extract_report_items(self, root: ET.Element) -> List[Visual]:
        """Extract report items (tables, matrices, charts, etc.)."""
        visuals = []
        ns = self.namespaces['']

        # Common report item types
        item_types = ['Tablix', 'Table', 'Matrix', 'Chart', 'Gauge', 'Indicator']

        for item_type in item_types:
            for item in root.findall(f'.//{{{ns}}}{item_type}'):
                name = item.get('Name', f'{item_type}_{len(visuals)}')

                # Try to get data region name
                data_region_elem = item.find(f'.//{{{ns}}}DataRegionName')
                data_region = data_region_elem.text if data_region_elem is not None else name

                visuals.append(Visual(
                    name=name,
                    visual_type=item_type,
                    data_fields={},  # Would need more complex parsing
                    filters=[]  # Would need more complex parsing
                ))

        return visuals