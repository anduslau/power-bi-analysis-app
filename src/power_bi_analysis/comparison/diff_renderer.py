"""
Render DiffReport objects to various output formats.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models import DiffReport, Change


class DiffRenderer:
    """Render DiffReport objects to different output formats."""

    def __init__(self, diff_report: DiffReport):
        """
        Initialize renderer with a DiffReport.

        Args:
            diff_report: DiffReport to render
        """
        self.diff_report = diff_report

    def to_markdown(self, include_summary: bool = True, include_details: bool = True) -> str:
        """
        Render diff report as markdown.

        Args:
            include_summary: Include summary section
            include_details: Include detailed changes section

        Returns:
            Markdown string
        """
        lines = []

        # Header
        lines.append(f"# Comparison Report")
        lines.append("")
        lines.append(f"**Compared:** `{self.diff_report.file1}` → `{self.diff_report.file2}`")
        lines.append(f"**Date:** {self.diff_report.comparison_date}")
        lines.append("")

        if include_summary:
            lines.extend(self._markdown_summary())

        if include_details and self.diff_report.changes:
            lines.extend(self._markdown_details())

        return "\n".join(lines)

    def _markdown_summary(self) -> List[str]:
        """Generate markdown summary section."""
        lines = []
        summary = self.diff_report.summary

        lines.append("## Summary")
        lines.append("")

        # Overall counts
        lines.append("| Change Type | Count |")
        lines.append("|-------------|-------|")
        lines.append(f"| **Total Changes** | **{summary.get('total', 0)}** |")
        lines.append(f"| Added | {summary.get('added', 0)} |")
        lines.append(f"| Removed | {summary.get('removed', 0)} |")
        lines.append(f"| Modified | {summary.get('modified', 0)} |")
        lines.append("")

        # Breakdown by element type
        element_counts = {}
        for key, count in summary.items():
            if '_' in key:
                element_type, change_type = key.split('_', 1)
                if element_type not in element_counts:
                    element_counts[element_type] = {}
                element_counts[element_type][change_type] = count

        if element_counts:
            lines.append("### Breakdown by Element Type")
            lines.append("")
            lines.append("| Element Type | Added | Removed | Modified | Total |")
            lines.append("|--------------|-------|---------|----------|-------|")

            for element_type in sorted(element_counts.keys()):
                counts = element_counts[element_type]
                added = counts.get('added', 0)
                removed = counts.get('removed', 0)
                modified = counts.get('modified', 0)
                total = added + removed + modified
                lines.append(f"| {element_type.capitalize()} | {added} | {removed} | {modified} | {total} |")

            lines.append("")

        return lines

    def _markdown_details(self) -> List[str]:
        """Generate markdown details section."""
        lines = []

        lines.append("## Detailed Changes")
        lines.append("")

        # Group changes by element type
        changes_by_type: Dict[str, List[Change]] = {}
        for change in self.diff_report.changes:
            element_type = change.element_type
            if element_type not in changes_by_type:
                changes_by_type[element_type] = []
            changes_by_type[element_type].append(change)

        # Sort element types for consistent output
        for element_type in sorted(changes_by_type.keys()):
            changes = changes_by_type[element_type]

            lines.append(f"### {element_type.capitalize()}s")
            lines.append("")

            # Group by change type within element type
            added = [c for c in changes if c.change_type == 'added']
            removed = [c for c in changes if c.change_type == 'removed']
            modified = [c for c in changes if c.change_type == 'modified']

            if added:
                lines.append("#### Added")
                lines.append("")
                for change in added:
                    lines.append(f"- **{change.element_name}**")
                    if change.new_value:
                        lines.append(f"  - New value: {change.new_value}")
                lines.append("")

            if removed:
                lines.append("#### Removed")
                lines.append("")
                for change in removed:
                    lines.append(f"- **{change.element_name}**")
                    if change.old_value:
                        lines.append(f"  - Old value: {change.old_value}")
                lines.append("")

            if modified:
                lines.append("#### Modified")
                lines.append("")
                for change in modified:
                    lines.append(f"- **{change.element_name}**")

                    # Handle rename specially
                    if change.details.get('attribute') == 'name':
                        old_name = change.details.get('old_name', change.old_value)
                        new_name = change.details.get('new_name', change.new_value)
                        similarity = change.details.get('similarity_score')
                        lines.append(f"  - Renamed: `{old_name}` → `{new_name}`")
                        if similarity:
                            lines.append(f"  - Similarity score: {similarity:.2f}")
                    else:
                        if change.old_value:
                            lines.append(f"  - Old value: {change.old_value}")
                        if change.new_value:
                            lines.append(f"  - New value: {change.new_value}")

                    # Show attribute if available
                    attribute = change.details.get('attribute')
                    if attribute and attribute != 'name':
                        lines.append(f"  - Attribute: {attribute}")

                lines.append("")

        return lines

    def to_json(self, indent: int = 2) -> str:
        """
        Render diff report as JSON.

        Args:
            indent: JSON indentation

        Returns:
            JSON string
        """
        # Convert dataclasses to dictionaries
        report_dict = {
            "file1": self.diff_report.file1,
            "file2": self.diff_report.file2,
            "comparison_date": self.diff_report.comparison_date,
            "summary": self.diff_report.summary,
            "changes": [
                {
                    "change_type": change.change_type,
                    "element_type": change.element_type,
                    "element_name": change.element_name,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "details": change.details
                }
                for change in self.diff_report.changes
            ]
        }

        return json.dumps(report_dict, indent=indent, default=str)

    def to_html(self, include_css: bool = True) -> str:
        """
        Render diff report as HTML.

        Args:
            include_css: Include inline CSS styles

        Returns:
            HTML string
        """
        lines = []

        lines.append('<!DOCTYPE html>')
        lines.append('<html lang="en">')
        lines.append('<head>')
        lines.append('    <meta charset="UTF-8">')
        lines.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        lines.append('    <title>Comparison Report</title>')

        if include_css:
            lines.append('    <style>')
            lines.append('        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }')
            lines.append('        .header { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }')
            lines.append('        .summary-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }')
            lines.append('        .summary-table th, .summary-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }')
            lines.append('        .summary-table th { background: #f9f9f9; }')
            lines.append('        .change-section { margin-bottom: 30px; }')
            lines.append('        .change-type { font-weight: bold; margin-top: 15px; margin-bottom: 10px; padding-left: 10px; border-left: 4px solid; }')
            lines.append('        .added { border-color: #28a745; color: #28a745; }')
            lines.append('        .removed { border-color: #dc3545; color: #dc3545; }')
            lines.append('        .modified { border-color: #ffc107; color: #ffc107; }')
            lines.append('        .change-item { margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px; }')
            lines.append('        .element-name { font-weight: bold; }')
            lines.append('        .change-details { margin-left: 20px; font-size: 0.9em; color: #666; }')
            lines.append('        .toggle-button { background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; margin: 5px 0; }')
            lines.append('        .toggle-button:hover { background: #0056b3; }')
            lines.append('        .hidden { display: none; }')
            lines.append('    </style>')

        lines.append('</head>')
        lines.append('<body>')

        # Header
        lines.append('    <div class="header">')
        lines.append(f'        <h1>Comparison Report</h1>')
        lines.append(f'        <p><strong>Compared:</strong> <code>{self.diff_report.file1}</code> → <code>{self.diff_report.file2}</code></p>')
        lines.append(f'        <p><strong>Date:</strong> {self.diff_report.comparison_date}</p>')
        lines.append('    </div>')

        # Summary
        lines.append('    <h2>Summary</h2>')
        lines.append('    <table class="summary-table">')
        lines.append('        <thead>')
        lines.append('            <tr>')
        lines.append('                <th>Change Type</th>')
        lines.append('                <th>Count</th>')
        lines.append('            </tr>')
        lines.append('        </thead>')
        lines.append('        <tbody>')
        lines.append(f'            <tr><td><strong>Total Changes</strong></td><td><strong>{self.diff_report.summary.get("total", 0)}</strong></td></tr>')
        lines.append(f'            <tr><td>Added</td><td>{self.diff_report.summary.get("added", 0)}</td></tr>')
        lines.append(f'            <tr><td>Removed</td><td>{self.diff_report.summary.get("removed", 0)}</td></tr>')
        lines.append(f'            <tr><td>Modified</td><td>{self.diff_report.summary.get("modified", 0)}</td></tr>')
        lines.append('        </tbody>')
        lines.append('    </table>')

        # Detailed changes
        if self.diff_report.changes:
            lines.append('    <h2>Detailed Changes</h2>')

            # Group changes by element type
            changes_by_type: Dict[str, List[Change]] = {}
            for change in self.diff_report.changes:
                element_type = change.element_type
                if element_type not in changes_by_type:
                    changes_by_type[element_type] = []
                changes_by_type[element_type].append(change)

            for element_type in sorted(changes_by_type.keys()):
                lines.append(f'    <div class="change-section">')
                lines.append(f'        <h3>{element_type.capitalize()}s</h3>')

                changes = changes_by_type[element_type]

                # Added
                added = [c for c in changes if c.change_type == 'added']
                if added:
                    lines.append('        <div class="change-type added">Added</div>')
                    for change in added:
                        lines.append('        <div class="change-item">')
                        lines.append(f'            <div class="element-name">{change.element_name}</div>')
                        if change.new_value:
                            lines.append(f'            <div class="change-details">New value: {change.new_value}</div>')
                        lines.append('        </div>')

                # Removed
                removed = [c for c in changes if c.change_type == 'removed']
                if removed:
                    lines.append('        <div class="change-type removed">Removed</div>')
                    for change in removed:
                        lines.append('        <div class="change-item">')
                        lines.append(f'            <div class="element-name">{change.element_name}</div>')
                        if change.old_value:
                            lines.append(f'            <div class="change-details">Old value: {change.old_value}</div>')
                        lines.append('        </div>')

                # Modified
                modified = [c for c in changes if c.change_type == 'modified']
                if modified:
                    lines.append('        <div class="change-type modified">Modified</div>')
                    for change in modified:
                        lines.append('        <div class="change-item">')
                        lines.append(f'            <div class="element-name">{change.element_name}</div>')

                        # Handle rename specially
                        if change.details.get('attribute') == 'name':
                            old_name = change.details.get('old_name', change.old_value)
                            new_name = change.details.get('new_name', change.new_value)
                            similarity = change.details.get('similarity_score')
                            lines.append(f'            <div class="change-details">Renamed: <code>{old_name}</code> → <code>{new_name}</code></div>')
                            if similarity:
                                lines.append(f'            <div class="change-details">Similarity score: {similarity:.2f}</div>')
                        else:
                            if change.old_value:
                                lines.append(f'            <div class="change-details">Old value: {change.old_value}</div>')
                            if change.new_value:
                                lines.append(f'            <div class="change-details">New value: {change.new_value}</div>')

                        attribute = change.details.get('attribute')
                        if attribute and attribute != 'name':
                            lines.append(f'            <div class="change-details">Attribute: {attribute}</div>')

                        lines.append('        </div>')

                lines.append('    </div>')

        # Simple JavaScript for toggling
        lines.append('''
    <script>
        function toggleElementType(elementType) {
            const sections = document.querySelectorAll('.change-section');
            sections.forEach(section => {
                if (section.querySelector('h3').textContent.toLowerCase().includes(elementType.toLowerCase())) {
                    section.style.display = section.style.display === 'none' ? 'block' : 'none';
                }
            });
        }

        // Add toggle buttons for each element type
        document.addEventListener('DOMContentLoaded', function() {
            const changeSections = document.querySelectorAll('.change-section h3');
            const buttonContainer = document.createElement('div');
            buttonContainer.style.margin = '20px 0';

            changeSections.forEach(section => {
                const elementType = section.textContent.replace('s', '').toLowerCase();
                const button = document.createElement('button');
                button.className = 'toggle-button';
                button.textContent = 'Toggle ' + section.textContent;
                button.onclick = () => toggleElementType(elementType);
                buttonContainer.appendChild(button);
                buttonContainer.appendChild(document.createTextNode(' '));
            });

            const detailedChanges = document.querySelector('h2');
            if (detailedChanges && changeSections.length > 0) {
                detailedChanges.parentNode.insertBefore(buttonContainer, detailedChanges.nextSibling);
            }
        });
    </script>
''')

        lines.append('</body>')
        lines.append('</html>')

        return "\n".join(lines)


def render_diff(diff_report: DiffReport, format: str = "markdown", **kwargs) -> str:
    """
    Convenience function to render a DiffReport.

    Args:
        diff_report: DiffReport to render
        format: Output format ("markdown", "json", "html")
        **kwargs: Passed to renderer method

    Returns:
        Rendered string in specified format

    Raises:
        ValueError: If format is not supported
    """
    renderer = DiffRenderer(diff_report)

    if format == "markdown":
        return renderer.to_markdown(**kwargs)
    elif format == "json":
        return renderer.to_json(**kwargs)
    elif format == "html":
        return renderer.to_html(**kwargs)
    else:
        raise ValueError(f"Unsupported format: {format}. Supported: markdown, json, html")