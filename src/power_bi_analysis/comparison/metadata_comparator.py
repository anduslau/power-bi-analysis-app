"""
Core comparison algorithm for ReportMetadata objects.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict
import difflib

from ..models import ReportMetadata, Change, DiffReport, Table, Column, Measure, Relationship, DataSource, Parameter, Visual


class MetadataComparator:
    """Compare two ReportMetadata objects and generate diff report."""

    def __init__(self, detect_renames: bool = True, similarity_threshold: float = 0.8):
        """
        Initialize comparator.

        Args:
            detect_renames: Whether to attempt detection of renamed elements
            similarity_threshold: Similarity score threshold for rename detection (0.0-1.0)
        """
        self.detect_renames = detect_renames
        self.similarity_threshold = similarity_threshold

    def compare(self, metadata1: ReportMetadata, metadata2: ReportMetadata) -> DiffReport:
        """
        Compare two ReportMetadata objects and return DiffReport.

        Args:
            metadata1: Baseline metadata
            metadata2: New metadata

        Returns:
            DiffReport with all changes
        """
        changes: List[Change] = []

        # Compare different element types
        changes.extend(self._compare_tables(metadata1.tables, metadata2.tables))
        changes.extend(self._compare_measures(metadata1.measures, metadata2.measures))
        changes.extend(self._compare_relationships(metadata1.relationships, metadata2.relationships))
        changes.extend(self._compare_data_sources(metadata1.data_sources, metadata2.data_sources))
        changes.extend(self._compare_parameters(metadata1.parameters, metadata2.parameters))
        changes.extend(self._compare_visuals(metadata1.visuals, metadata2.visuals))

        # Build summary counts
        summary = self._build_summary(changes)

        return DiffReport(
            file1=metadata1.file_path,
            file2=metadata2.file_path,
            comparison_date=datetime.now().isoformat(),
            changes=changes,
            summary=summary
        )

    def _compare_tables(self, tables1: List[Table], tables2: List[Table]) -> List[Change]:
        """Compare tables between two versions."""
        changes = []

        # Build maps for efficient lookup
        tables1_map = {table.name: table for table in tables1}
        tables2_map = {table.name: table for table in tables2}

        # Find added and removed tables
        added_tables = tables2_map.keys() - tables1_map.keys()
        removed_tables = tables1_map.keys() - tables2_map.keys()

        # Handle potential renames if enabled
        if self.detect_renames and added_tables and removed_tables:
            added_tables, removed_tables, rename_changes = self._detect_renames(
                added_tables, removed_tables, tables1_map, tables2_map, "table"
            )
            changes.extend(rename_changes)

        # Report added tables
        for table_name in added_tables:
            changes.append(Change(
                change_type="added",
                element_type="table",
                element_name=table_name,
                new_value=tables2_map[table_name].description
            ))

        # Report removed tables
        for table_name in removed_tables:
            changes.append(Change(
                change_type="removed",
                element_type="table",
                element_name=table_name,
                old_value=tables1_map[table_name].description
            ))

        # Compare common tables
        common_tables = tables1_map.keys() & tables2_map.keys()
        for table_name in common_tables:
            table1 = tables1_map[table_name]
            table2 = tables2_map[table_name]

            # Compare table attributes
            table_changes = self._compare_table_details(table1, table2)
            changes.extend(table_changes)

        return changes

    def _compare_table_details(self, table1: Table, table2: Table) -> List[Change]:
        """Compare details within a table (columns, description, etc.)."""
        changes = []

        # Compare table description
        if table1.description != table2.description:
            changes.append(Change(
                change_type="modified",
                element_type="table",
                element_name=table1.name,
                old_value=table1.description,
                new_value=table2.description,
                details={"attribute": "description"}
            ))

        # Compare columns
        cols1_map = {col.name: col for col in table1.columns}
        cols2_map = {col.name: col for col in table2.columns}

        added_cols = cols2_map.keys() - cols1_map.keys()
        removed_cols = cols1_map.keys() - cols2_map.keys()

        # Handle column renames
        if self.detect_renames and added_cols and removed_cols:
            added_cols, removed_cols, rename_changes = self._detect_renames(
                added_cols, removed_cols, cols1_map, cols2_map, "column",
                parent_name=table1.name
            )
            changes.extend(rename_changes)

        # Report added columns
        for col_name in added_cols:
            col = cols2_map[col_name]
            changes.append(Change(
                change_type="added",
                element_type="column",
                element_name=f"{table1.name}.{col_name}",
                new_value=col.description
            ))

        # Report removed columns
        for col_name in removed_cols:
            col = cols1_map[col_name]
            changes.append(Change(
                change_type="removed",
                element_type="column",
                element_name=f"{table1.name}.{col_name}",
                old_value=col.description
            ))

        # Compare common columns
        common_cols = cols1_map.keys() & cols2_map.keys()
        for col_name in common_cols:
            col1 = cols1_map[col_name]
            col2 = cols2_map[col_name]

            col_changes = self._compare_column_details(col1, col2, table1.name)
            changes.extend(col_changes)

        return changes

    def _compare_column_details(self, col1: Column, col2: Column, table_name: str) -> List[Change]:
        """Compare column details."""
        changes = []
        col_id = f"{table_name}.{col1.name}"

        # Compare data type
        if col1.data_type != col2.data_type:
            changes.append(Change(
                change_type="modified",
                element_type="column",
                element_name=col_id,
                old_value=col1.data_type,
                new_value=col2.data_type,
                details={"attribute": "data_type"}
            ))

        # Compare description
        if col1.description != col2.description:
            changes.append(Change(
                change_type="modified",
                element_type="column",
                element_name=col_id,
                old_value=col1.description,
                new_value=col2.description,
                details={"attribute": "description"}
            ))

        # Compare is_measure flag
        if col1.is_measure != col2.is_measure:
            changes.append(Change(
                change_type="modified",
                element_type="column",
                element_name=col_id,
                old_value=str(col1.is_measure),
                new_value=str(col2.is_measure),
                details={"attribute": "is_measure"}
            ))

        # Compare expression for calculated columns
        if col1.expression != col2.expression:
            changes.append(Change(
                change_type="modified",
                element_type="column",
                element_name=col_id,
                old_value=col1.expression,
                new_value=col2.expression,
                details={"attribute": "expression"}
            ))

        return changes

    def _compare_measures(self, measures1: List[Measure], measures2: List[Measure]) -> List[Change]:
        """Compare measures between versions."""
        changes = []

        measures1_map = {m.name: m for m in measures1}
        measures2_map = {m.name: m for m in measures2}

        added = measures2_map.keys() - measures1_map.keys()
        removed = measures1_map.keys() - measures2_map.keys()

        # Handle measure renames
        if self.detect_renames and added and removed:
            added, removed, rename_changes = self._detect_renames(
                added, removed, measures1_map, measures2_map, "measure"
            )
            changes.extend(rename_changes)

        # Report added measures
        for name in added:
            measure = measures2_map[name]
            changes.append(Change(
                change_type="added",
                element_type="measure",
                element_name=name,
                new_value=measure.expression
            ))

        # Report removed measures
        for name in removed:
            measure = measures1_map[name]
            changes.append(Change(
                change_type="removed",
                element_type="measure",
                element_name=name,
                old_value=measure.expression
            ))

        # Compare common measures
        common = measures1_map.keys() & measures2_map.keys()
        for name in common:
            m1 = measures1_map[name]
            m2 = measures2_map[name]

            if m1.expression != m2.expression:
                changes.append(Change(
                    change_type="modified",
                    element_type="measure",
                    element_name=name,
                    old_value=m1.expression,
                    new_value=m2.expression,
                    details={"attribute": "expression"}
                ))

            if m1.description != m2.description:
                changes.append(Change(
                    change_type="modified",
                    element_type="measure",
                    element_name=name,
                    old_value=m1.description,
                    new_value=m2.description,
                    details={"attribute": "description"}
                ))

            if m1.format_string != m2.format_string:
                changes.append(Change(
                    change_type="modified",
                    element_type="measure",
                    element_name=name,
                    old_value=m1.format_string,
                    new_value=m2.format_string,
                    details={"attribute": "format_string"}
                ))

        return changes

    def _compare_relationships(self, rels1: List[Relationship], rels2: List[Relationship]) -> List[Change]:
        """Compare relationships between versions."""
        changes = []

        # Create unique keys for relationships
        def rel_key(rel):
            return f"{rel.from_table}.{rel.from_column}->{rel.to_table}.{rel.to_column}"

        rels1_map = {rel_key(rel): rel for rel in rels1}
        rels2_map = {rel_key(rel): rel for rel in rels2}

        added = rels2_map.keys() - rels1_map.keys()
        removed = rels1_map.keys() - rels2_map.keys()

        # Report added relationships
        for key in added:
            rel = rels2_map[key]
            changes.append(Change(
                change_type="added",
                element_type="relationship",
                element_name=key,
                new_value=rel.relationship_type
            ))

        # Report removed relationships
        for key in removed:
            rel = rels1_map[key]
            changes.append(Change(
                change_type="removed",
                element_type="relationship",
                element_name=key,
                old_value=rel.relationship_type
            ))

        # Compare common relationships
        common = rels1_map.keys() & rels2_map.keys()
        for key in common:
            r1 = rels1_map[key]
            r2 = rels2_map[key]

            if r1.relationship_type != r2.relationship_type:
                changes.append(Change(
                    change_type="modified",
                    element_type="relationship",
                    element_name=key,
                    old_value=r1.relationship_type,
                    new_value=r2.relationship_type,
                    details={"attribute": "relationship_type"}
                ))

        return changes

    def _compare_data_sources(self, sources1: List[DataSource], sources2: List[DataSource]) -> List[Change]:
        """Compare data sources."""
        changes = []

        sources1_map = {s.name: s for s in sources1}
        sources2_map = {s.name: s for s in sources2}

        added = sources2_map.keys() - sources1_map.keys()
        removed = sources1_map.keys() - sources2_map.keys()

        # Report added data sources
        for name in added:
            changes.append(Change(
                change_type="added",
                element_type="data_source",
                element_name=name
            ))

        # Report removed data sources
        for name in removed:
            changes.append(Change(
                change_type="removed",
                element_type="data_source",
                element_name=name
            ))

        # Compare common data sources (simplified - just name matching)
        # Could be extended to compare connection strings, etc.

        return changes

    def _compare_parameters(self, params1: List[Parameter], params2: List[Parameter]) -> List[Change]:
        """Compare parameters."""
        changes = []

        params1_map = {p.name: p for p in params1}
        params2_map = {p.name: p for p in params2}

        added = params2_map.keys() - params1_map.keys()
        removed = params1_map.keys() - params2_map.keys()

        # Report added parameters
        for name in added:
            changes.append(Change(
                change_type="added",
                element_type="parameter",
                element_name=name
            ))

        # Report removed parameters
        for name in removed:
            changes.append(Change(
                change_type="removed",
                element_type="parameter",
                element_name=name
            ))

        # Compare common parameters
        common = params1_map.keys() & params2_map.keys()
        for name in common:
            p1 = params1_map[name]
            p2 = params2_map[name]

            if p1.data_type != p2.data_type:
                changes.append(Change(
                    change_type="modified",
                    element_type="parameter",
                    element_name=name,
                    old_value=p1.data_type,
                    new_value=p2.data_type,
                    details={"attribute": "data_type"}
                ))

            if p1.default_value != p2.default_value:
                changes.append(Change(
                    change_type="modified",
                    element_type="parameter",
                    element_name=name,
                    old_value=p1.default_value,
                    new_value=p2.default_value,
                    details={"attribute": "default_value"}
                ))

        return changes

    def _compare_visuals(self, visuals1: List[Visual], visuals2: List[Visual]) -> List[Change]:
        """Compare visuals."""
        changes = []

        visuals1_map = {v.name: v for v in visuals1}
        visuals2_map = {v.name: v for v in visuals2}

        added = visuals2_map.keys() - visuals1_map.keys()
        removed = visuals1_map.keys() - visuals2_map.keys()

        # Report added visuals
        for name in added:
            changes.append(Change(
                change_type="added",
                element_type="visual",
                element_name=name
            ))

        # Report removed visuals
        for name in removed:
            changes.append(Change(
                change_type="removed",
                element_type="visual",
                element_name=name
            ))

        # Compare common visuals (simplified - just name matching)
        # Could be extended to compare visual_type, data_fields, filters

        return changes

    def _detect_renames(self, added_set, removed_set, old_map, new_map, element_type, parent_name=None):
        """
        Detect renamed elements by similarity matching.

        Returns:
            Tuple of (remaining_added, remaining_removed, rename_changes)
        """
        added = list(added_set)
        removed = list(removed_set)
        rename_changes = []

        # Try to match added and removed elements by name similarity
        for removed_name in removed[:]:  # Copy for safe removal
            removed_obj = old_map[removed_name]
            best_match = None
            best_score = 0

            for added_name in added[:]:
                added_obj = new_map[added_name]

                # Simple string similarity
                score = difflib.SequenceMatcher(
                    None, removed_name, added_name
                ).ratio()

                # Could add more sophisticated similarity checks
                # (e.g., compare descriptions, data types, etc.)

                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = added_name

            if best_match:
                # Found a rename
                added.remove(best_match)
                removed.remove(removed_name)

                element_name = f"{parent_name}.{removed_name}" if parent_name else removed_name
                new_element_name = f"{parent_name}.{best_match}" if parent_name else best_match

                rename_changes.append(Change(
                    change_type="modified",
                    element_type=element_type,
                    element_name=element_name,
                    old_value=removed_name,
                    new_value=best_match,
                    details={
                        "attribute": "name",
                        "similarity_score": best_score,
                        "old_name": removed_name,
                        "new_name": best_match
                    }
                ))

        return set(added), set(removed), rename_changes

    def _build_summary(self, changes: List[Change]) -> Dict[str, int]:
        """Build summary counts from changes."""
        summary = {
            "total": len(changes),
            "added": 0,
            "removed": 0,
            "modified": 0,
        }

        # Count by change type
        for change in changes:
            if change.change_type in summary:
                summary[change.change_type] += 1

        # Count by element type
        for change in changes:
            key = f"{change.element_type}_{change.change_type}"
            summary[key] = summary.get(key, 0) + 1

        return summary


def compare_metadata(metadata1: ReportMetadata, metadata2: ReportMetadata, **kwargs) -> DiffReport:
    """
    Convenience function to compare two ReportMetadata objects.

    Args:
        metadata1: Baseline metadata
        metadata2: New metadata
        **kwargs: Passed to MetadataComparator constructor

    Returns:
        DiffReport with all changes
    """
    comparator = MetadataComparator(**kwargs)
    return comparator.compare(metadata1, metadata2)