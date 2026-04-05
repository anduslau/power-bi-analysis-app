"""
Power BI file extractor for .pbix, .pbit files and PBIP folders.
Uses pbixray for extraction.
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseExtractor
from ..models import (
    ReportMetadata, FileType, DataSource, Column, Table,
    Relationship, Measure, Parameter, Visual
)


class PowerBIExtractor(BaseExtractor):
    """Extractor for Power BI files."""

    def can_extract(self, file_path: Path) -> bool:
        """Check if file is a Power BI file."""
        # Support .pbix, .pbit, and PBIP folders (directory with .pbip extension)
        if file_path.is_dir():
            # Check if it's a PBIP folder (has a .pbip file inside?)
            # For now, treat any folder as potential PBIP (to be refined)
            return True
        ext = file_path.suffix.lower()
        return ext in ['.pbix', '.pbit', '.pbip']

    @property
    def supported_extensions(self) -> List[str]:
        return ['.pbix', '.pbit', '.pbip']

    def extract(self, file_path: Path) -> ReportMetadata:
        """Extract metadata from Power BI file."""
        metadata = ReportMetadata(
            file_type=FileType.POWER_BI,
            file_path=str(file_path),
            file_size=file_path.stat().st_size if file_path.is_file() else 0,
            extracted_at=datetime.now().isoformat()
        )

        try:
            # Import inside try block to avoid dependency issues
            import pbixray

            # Determine if it's a file or folder
            if file_path.is_file():
                # Use pbixray to analyze the .pbix/.pbit file
                analyzer = pbixray.PBIXRay(file_path)
                # Extract metadata
                self._extract_from_analyzer(analyzer, metadata)
            else:
                # PBIP folder - need to handle differently
                # For now, treat as unsupported
                metadata.extraction_errors.append(
                    f"PBIP folder extraction not yet implemented: {file_path}"
                )

        except ImportError as e:
            metadata.extraction_errors.append(
                f"pbixray library not available: {e}"
            )
        except Exception as e:
            metadata.extraction_errors.append(
                f"Power BI extraction error: {e}"
            )

        return metadata

    def _extract_from_analyzer(self, analyzer, metadata: ReportMetadata) -> None:
        """Extract metadata from pbixray analyzer and populate metadata."""
        # Extract tables and columns from schema
        metadata.tables = self._extract_tables(analyzer)

        # Extract measures
        metadata.measures = self._extract_measures(analyzer)

        # Extract relationships
        metadata.relationships = self._extract_relationships(analyzer)

        # Extract parameters
        metadata.parameters = self._extract_parameters(analyzer)

        # Extract data sources (from Power Query)
        metadata.data_sources = self._extract_data_sources(analyzer)

        # Extract queries (Power Query M expressions)
        metadata.queries = self._extract_queries(analyzer)

        # Extract visuals (not available in pbixray)
        metadata.visuals = []

    def _get_calculated_columns_set(self, analyzer) -> set:
        """Return set of (table_name, column_name) for calculated columns."""
        calculated = set()
        dax_cols_df = analyzer.dax_columns
        if not dax_cols_df.empty:
            for _, row in dax_cols_df.iterrows():
                calculated.add((row['TableName'], row['ColumnName']))
        return calculated

    def _extract_data_sources(self, analyzer) -> List[DataSource]:
        """Extract data source definitions."""
        # pbixray doesn't expose data sources directly
        # Could be derived from Power Query metadata
        return []

    def _extract_tables(self, analyzer) -> List[Table]:
        """Extract table definitions with columns."""
        tables = []

        # Get schema DataFrame
        schema_df = analyzer.schema
        if schema_df.empty:
            return tables

        # Get calculated columns set
        calculated_cols = self._get_calculated_columns_set(analyzer)

        # Get unique table names
        table_names = analyzer.tables
        for table_name in table_names:
            # Filter columns for this table
            table_cols = schema_df[schema_df['TableName'] == table_name]
            columns = []
            for _, row in table_cols.iterrows():
                col_name = row['ColumnName']
                data_type = row.get('PandasDataType', 'unknown')
                is_calculated = (table_name, col_name) in calculated_cols
                expression = None
                if is_calculated:
                    # Find expression from dax_columns
                    dax_cols_df = analyzer.dax_columns
                    if not dax_cols_df.empty:
                        match = dax_cols_df[(dax_cols_df['TableName'] == table_name) &
                                            (dax_cols_df['ColumnName'] == col_name)]
                        if not match.empty:
                            expression = match.iloc[0]['Expression']
                columns.append(Column(
                    name=col_name,
                    data_type=data_type,
                    is_calculated=is_calculated,
                    expression=expression
                ))

            # Check if table is a calculated table (DAX table)
            dax_tables_df = analyzer.dax_tables
            is_calculated_table = False
            expression = None
            if not dax_tables_df.empty:
                dax_table = dax_tables_df[dax_tables_df['TableName'] == table_name]
                if not dax_table.empty:
                    is_calculated_table = True
                    expression = dax_table.iloc[0]['Expression']

            tables.append(Table(
                name=table_name,
                columns=columns,
                description=f"Calculated table: {expression[:200]}..." if is_calculated_table else None,
                source=expression if is_calculated_table else None
            ))

        return tables

    def _extract_columns(self, analyzer) -> List[Column]:
        """Extract column definitions."""
        columns = []
        schema_df = analyzer.schema
        if schema_df.empty:
            return columns

        # Get calculated columns set
        calculated_cols = self._get_calculated_columns_set(analyzer)

        for _, row in schema_df.iterrows():
            table_name = row['TableName']
            col_name = row['ColumnName']
            data_type = row.get('PandasDataType', 'unknown')
            is_calculated = (table_name, col_name) in calculated_cols
            expression = None
            if is_calculated:
                # Find expression from dax_columns
                dax_cols_df = analyzer.dax_columns
                if not dax_cols_df.empty:
                    match = dax_cols_df[(dax_cols_df['TableName'] == table_name) &
                                        (dax_cols_df['ColumnName'] == col_name)]
                    if not match.empty:
                        expression = match.iloc[0]['Expression']

            columns.append(Column(
                name=col_name,
                data_type=data_type,
                is_calculated=is_calculated,
                expression=expression
            ))

        return columns

    def _extract_measures(self, analyzer) -> List[Measure]:
        """Extract DAX measure definitions."""
        measures = []
        df = analyzer.dax_measures
        if df.empty:
            return measures

        for _, row in df.iterrows():
            measures.append(Measure(
                name=row['Name'],
                expression=row['Expression'],
                description=row.get('Description'),
                format_string=None  # Not available in pbixray
            ))

        return measures

    def _extract_relationships(self, analyzer) -> List[Relationship]:
        """Extract relationship definitions."""
        relationships = []
        df = analyzer.relationships
        if df.empty:
            return relationships

        for _, row in df.iterrows():
            # Map cardinality to relationship_type
            cardinality = row.get('Cardinality', '1:1')
            if cardinality == '1:1':
                rel_type = 'one_to_one'
            elif cardinality == '1:M' or cardinality == 'M:1':
                rel_type = 'many_to_one'  # direction handled by from/to
            else:
                rel_type = 'many_to_many'

            relationships.append(Relationship(
                from_table=row['FromTableName'],
                from_column=row['FromColumnName'],
                to_table=row['ToTableName'],
                to_column=row['ToColumnName'],
                relationship_type=rel_type
            ))

        return relationships

    def _extract_parameters(self, analyzer) -> List[Parameter]:
        """Extract M parameters."""
        parameters = []
        df = analyzer.m_parameters
        if df.empty:
            return parameters

        for _, row in df.iterrows():
            parameters.append(Parameter(
                name=row['ParameterName'],
                data_type='string',  # M parameters are typically string
                default_value=None,
                prompt=row.get('Description'),
                values=[]
            ))

        return parameters

    def _extract_queries(self, analyzer) -> List[Dict[str, Any]]:
        """Extract Power Query M expressions."""
        queries = []
        df = analyzer.power_query
        if df.empty:
            return queries

        for _, row in df.iterrows():
            queries.append({
                'name': row['TableName'],
                'type': 'power_query',
                'expression': row['Expression']
            })

        return queries

    def _extract_visuals(self, analyzer) -> List[Visual]:
        """Extract visual/page definitions."""
        # Not available in pbixray
        return []