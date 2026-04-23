"""
Main GUI window for Insight Fabric.
"""

import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QComboBox, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox, QGroupBox, QFormLayout,
    QSplitter, QFrame, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor, QPalette, QColor

from ..config import Config
from ..orchestration.pipeline import AnalysisPipeline
from ..comparison import compare_metadata
from ..extractors import extract_metadata


class AnalysisWorker(QThread):
    """Worker thread to run analysis pipeline."""

    # Signals
    started = pyqtSignal()
    finished = pyqtSignal(bool)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, file_path: Path, llm_provider: str, llm_api_key: Optional[str],
                 llm_model: Optional[str], generate_yaml: bool, generate_sql: bool,
                 generate_dictionary: bool, output_dir: Path,
                 llm_options: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.file_path = file_path
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.generate_yaml = generate_yaml
        self.generate_sql = generate_sql
        self.generate_dictionary = generate_dictionary
        self.output_dir = output_dir
        self.llm_options = llm_options or {}
        self.pipeline: Optional[AnalysisPipeline] = None

    def run(self):
        """Run the analysis pipeline."""
        self.started.emit()
        self.log.emit(f"Starting analysis of {self.file_path.name}")

        try:
            # Create pipeline
            self.pipeline = AnalysisPipeline(
                llm_provider=self.llm_provider,
                llm_api_key=self.llm_api_key,
                llm_model=self.llm_model,
                llm_options=self.llm_options,
                generate_yaml=self.generate_yaml,
                generate_sql=self.generate_sql,
                generate_dictionary=self.generate_dictionary
            )

            # Run analysis
            success = self.pipeline.analyze_file(self.file_path)

            if success:
                self.log.emit("Analysis completed successfully")
                # Save outputs
                try:
                    brd_path, yaml_path, sql_path, dict_path = self.pipeline.save_outputs(self.output_dir)
                    self.log.emit(f"BRD saved to: {brd_path}")
                    if yaml_path:
                        self.log.emit(f"Semantic YAML saved to: {yaml_path}")
                    if sql_path:
                        self.log.emit(f"SQL schema saved to: {sql_path}")
                    if dict_path:
                        self.log.emit(f"Data dictionary saved to: {dict_path}")
                except Exception as e:
                    self.error.emit(f"Failed to save outputs: {e}")
                    success = False
            else:
                errors = self.pipeline.get_errors()
                for err in errors:
                    self.error.emit(err)
                self.log.emit("Analysis failed with errors")

            self.finished.emit(success)

        except Exception as e:
            self.error.emit(f"Unexpected error: {e}")
            self.log.emit(traceback.format_exc())
            self.finished.emit(False)


class ComparisonWorker(QThread):
    """Worker thread to compare two BI files."""

    # Signals
    started = pyqtSignal()
    finished = pyqtSignal(bool)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    log = pyqtSignal(str)
    comparison_result = pyqtSignal(str)  # emits diff report content

    def __init__(self, file1_path: Path, file2_path: Path, detect_renames: bool = True,
                 similarity_threshold: float = 0.8, output_format: str = "markdown"):
        super().__init__()
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.detect_renames = detect_renames
        self.similarity_threshold = similarity_threshold
        self.output_format = output_format

    def run(self):
        """Run the comparison."""
        self.started.emit()
        self.log.emit(f"Comparing {self.file1_path.name} (baseline) with {self.file2_path.name} (new)")

        try:
            # Extract metadata from both files
            self.log.emit("Extracting metadata from baseline file...")
            meta1 = extract_metadata(self.file1_path)
            if not meta1:
                self.error.emit(f"Failed to extract metadata from {self.file1_path}")
                self.finished.emit(False)
                return

            self.log.emit("Extracting metadata from new file...")
            meta2 = extract_metadata(self.file2_path)
            if not meta2:
                self.error.emit(f"Failed to extract metadata from {self.file2_path}")
                self.finished.emit(False)
                return

            # Compare metadata
            self.log.emit("Comparing metadata...")
            diff_report = compare_metadata(
                meta1,
                meta2,
                detect_renames=self.detect_renames,
                similarity_threshold=self.similarity_threshold
            )

            # Generate output
            from ..comparison.diff_renderer import render_diff
            output_content = render_diff(diff_report, self.output_format)

            self.comparison_result.emit(output_content)
            self.log.emit(f"Comparison completed. Total changes: {diff_report.summary.get('total', 0)}")
            self.finished.emit(True)

        except Exception as e:
            self.error.emit(f"Comparison error: {e}")
            self.log.emit(traceback.format_exc())
            self.finished.emit(False)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.worker: Optional[AnalysisWorker] = None
        self.comparison_worker: Optional[ComparisonWorker] = None
        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Insight Fabric")
        self.setMinimumSize(800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select a Power BI (.pbix), Excel (.xlsx), RDL (.rdl), or data file...")
        file_browse_btn = QPushButton("Browse...")
        file_browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path_edit, 1)
        file_layout.addWidget(file_browse_btn)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # Options group
        options_group = QGroupBox("Analysis Options")
        options_layout = QFormLayout()

        # LLM provider
        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItems(["anthropic", "openai", "gemini", "deepseek"])
        options_layout.addRow("LLM Provider:", self.llm_provider_combo)

        # API key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Leave empty to use environment variable or config")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        options_layout.addRow("API Key:", self.api_key_edit)

        # Model (optional)
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("Leave empty for provider default")
        options_layout.addRow("Model:", self.model_edit)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Output directory for generated files")
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.output_dir_edit, 1)
        output_layout.addWidget(output_browse_btn)
        options_layout.addRow("Output Directory:", output_layout)

        # Checkboxes
        self.generate_yaml_check = QCheckBox("Generate Semantic YAML")
        self.generate_yaml_check.setChecked(True)
        options_layout.addRow(self.generate_yaml_check)

        self.generate_sql_check = QCheckBox("Generate SQL Schema")
        options_layout.addRow(self.generate_sql_check)

        self.generate_dict_check = QCheckBox("Generate Data Dictionary")
        options_layout.addRow(self.generate_dict_check)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # Comparison group
        comparison_group = QGroupBox("File Comparison")
        comparison_layout = QFormLayout()

        # Baseline file selection
        baseline_layout = QHBoxLayout()
        self.baseline_path_edit = QLineEdit()
        self.baseline_path_edit.setPlaceholderText("Select baseline file (older version)...")
        baseline_browse_btn = QPushButton("Browse...")
        baseline_browse_btn.clicked.connect(lambda: self.browse_baseline_file())
        baseline_layout.addWidget(self.baseline_path_edit, 1)
        baseline_layout.addWidget(baseline_browse_btn)
        comparison_layout.addRow("Baseline File:", baseline_layout)

        # New file selection (can reuse main file path or separate)
        new_file_layout = QHBoxLayout()
        self.new_file_path_edit = QLineEdit()
        self.new_file_path_edit.setPlaceholderText("Select new file (updated version)...")
        new_file_browse_btn = QPushButton("Browse...")
        new_file_browse_btn.clicked.connect(lambda: self.browse_new_file())
        new_file_layout.addWidget(self.new_file_path_edit, 1)
        new_file_layout.addWidget(new_file_browse_btn)
        comparison_layout.addRow("New File:", new_file_layout)

        # Comparison options
        self.detect_renames_check = QCheckBox("Detect renames")
        self.detect_renames_check.setChecked(True)
        comparison_layout.addRow(self.detect_renames_check)

        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Similarity threshold:"))
        self.similarity_threshold_spin = QDoubleSpinBox()
        self.similarity_threshold_spin.setRange(0.0, 1.0)
        self.similarity_threshold_spin.setSingleStep(0.05)
        self.similarity_threshold_spin.setValue(0.8)
        self.similarity_threshold_spin.setDecimals(2)
        threshold_layout.addWidget(self.similarity_threshold_spin)
        threshold_layout.addStretch()
        comparison_layout.addRow(threshold_layout)

        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["markdown", "json", "html"])
        comparison_layout.addRow("Output Format:", self.output_format_combo)

        # Compare button
        self.compare_btn = QPushButton("Compare Files")
        self.compare_btn.clicked.connect(self.run_comparison)
        self.compare_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.compare_btn.setMinimumHeight(35)
        comparison_layout.addRow(self.compare_btn)

        comparison_group.setLayout(comparison_layout)
        main_layout.addWidget(comparison_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Log/output text area
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)  # stretch factor

        # Button row
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Analysis")
        self.run_btn.clicked.connect(self.run_analysis)
        self.run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.run_btn.setMinimumHeight(40)

        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.clear_log)

        self.quit_btn = QPushButton("Quit")
        self.quit_btn.clicked.connect(self.close)

        button_layout.addWidget(self.run_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.quit_btn)
        main_layout.addLayout(button_layout)

    def load_config(self):
        """Load configuration values into UI."""
        # LLM provider
        provider = self.config.get_llm_provider()
        index = self.llm_provider_combo.findText(provider)
        if index >= 0:
            self.llm_provider_combo.setCurrentIndex(index)

        # API key (not loaded for security)
        # Model
        model = self.config.get_llm_model()
        if model:
            self.model_edit.setText(model)

        # Output directory
        output_dir = self.config.get_output_dir()
        self.output_dir_edit.setText(str(output_dir))

        # Generate YAML default
        generate_yaml = self.config.get_generate_yaml()
        self.generate_yaml_check.setChecked(generate_yaml)

    def browse_file(self):
        """Open file dialog to select a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "Supported Files (*.pbix *.pbit *.pbip *.xlsx *.xlsm *.rdl *.csv *.json *.parquet);;All Files (*.*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def browse_output_dir(self):
        """Open directory dialog to select output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_edit.text() or str(Path.home())
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def browse_baseline_file(self):
        """Open file dialog to select baseline file for comparison."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Baseline File",
            "",
            "Supported Files (*.pbix *.pbit *.pbip *.xlsx *.xlsm *.rdl *.csv *.json *.parquet);;All Files (*.*)"
        )
        if file_path:
            self.baseline_path_edit.setText(file_path)

    def browse_new_file(self):
        """Open file dialog to select new file for comparison."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select New File",
            "",
            "Supported Files (*.pbix *.pbit *.pbip *.xlsx *.xlsm *.rdl *.csv *.json *.parquet);;All Files (*.*)"
        )
        if file_path:
            self.new_file_path_edit.setText(file_path)

    def log_message(self, message: str):
        """Append message to log text area."""
        self.log_text.append(message)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def clear_log(self):
        """Clear the log text area."""
        self.log_text.clear()

    def run_analysis(self):
        """Start analysis with current parameters."""
        # Validate file
        file_path_str = self.file_path_edit.text().strip()
        if not file_path_str:
            QMessageBox.warning(self, "Missing File", "Please select a file to analyze.")
            return

        file_path = Path(file_path_str)
        if not file_path.exists():
            QMessageBox.warning(self, "File Not Found", f"The file does not exist:\n{file_path}")
            return

        # Output directory
        output_dir_str = self.output_dir_edit.text().strip()
        if not output_dir_str:
            QMessageBox.warning(self, "Missing Output Directory", "Please select an output directory.")
            return

        output_dir = Path(output_dir_str)

        # Get LLM parameters
        llm_provider = self.llm_provider_combo.currentText()
        llm_api_key = self.api_key_edit.text().strip() or None
        llm_model = self.model_edit.text().strip() or None
        llm_options = self.config.get_llm_options(llm_provider)

        # Get generation options
        generate_yaml = self.generate_yaml_check.isChecked()
        generate_sql = self.generate_sql_check.isChecked()
        generate_dict = self.generate_dict_check.isChecked()

        # Disable UI during analysis
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # indeterminate

        # Clear previous errors
        self.clear_log()
        self.log_message(f"Starting analysis of {file_path.name}...")
        self.log_message(f"LLM Provider: {llm_provider}")
        self.log_message(f"Output directory: {output_dir}")

        # Create and start worker thread
        self.worker = AnalysisWorker(
            file_path=file_path,
            llm_provider=llm_provider,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
            generate_yaml=generate_yaml,
            generate_sql=generate_sql,
            generate_dictionary=generate_dict,
            output_dir=output_dir,
            llm_options=llm_options
        )

        # Connect signals
        self.worker.started.connect(self.on_analysis_started)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.log.connect(self.log_message)
        self.worker.error.connect(self.log_message)

        self.worker.start()

    def set_ui_enabled(self, enabled: bool):
        """Enable or disable UI controls."""
        self.file_path_edit.setEnabled(enabled)
        self.llm_provider_combo.setEnabled(enabled)
        self.api_key_edit.setEnabled(enabled)
        self.model_edit.setEnabled(enabled)
        self.output_dir_edit.setEnabled(enabled)
        self.generate_yaml_check.setEnabled(enabled)
        self.generate_sql_check.setEnabled(enabled)
        self.generate_dict_check.setEnabled(enabled)
        self.run_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        # Also enable/disable comparison UI when analysis UI is toggled
        self.baseline_path_edit.setEnabled(enabled)
        self.new_file_path_edit.setEnabled(enabled)
        self.detect_renames_check.setEnabled(enabled)
        self.similarity_threshold_spin.setEnabled(enabled)
        self.output_format_combo.setEnabled(enabled)
        self.compare_btn.setEnabled(enabled)

    def on_analysis_started(self):
        """Handle analysis started signal."""
        self.log_message("Analysis in progress...")

    def on_analysis_finished(self, success: bool):
        """Handle analysis finished signal."""
        self.progress_bar.setVisible(False)
        self.set_ui_enabled(True)

        if success:
            self.log_message("Analysis completed successfully!")
            QMessageBox.information(self, "Success", "Analysis completed successfully!")
        else:
            self.log_message("Analysis failed.")
            QMessageBox.warning(self, "Analysis Failed", "Analysis failed. Check log for details.")

    def run_comparison(self):
        """Start comparison of two files."""
        # Validate baseline file
        baseline_path_str = self.baseline_path_edit.text().strip()
        if not baseline_path_str:
            QMessageBox.warning(self, "Missing Baseline File", "Please select a baseline file.")
            return

        baseline_path = Path(baseline_path_str)
        if not baseline_path.exists():
            QMessageBox.warning(self, "File Not Found", f"Baseline file does not exist:\n{baseline_path}")
            return

        # Validate new file
        new_file_path_str = self.new_file_path_edit.text().strip()
        if not new_file_path_str:
            QMessageBox.warning(self, "Missing New File", "Please select a new file.")
            return

        new_file_path = Path(new_file_path_str)
        if not new_file_path.exists():
            QMessageBox.warning(self, "File Not Found", f"New file does not exist:\n{new_file_path}")
            return

        # Get comparison options
        detect_renames = self.detect_renames_check.isChecked()
        similarity_threshold = self.similarity_threshold_spin.value()
        output_format = self.output_format_combo.currentText()

        # Disable UI during comparison
        self.set_comparison_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # indeterminate

        # Clear previous logs
        self.clear_log()
        self.log_message(f"Starting comparison: {baseline_path.name} (baseline) vs {new_file_path.name} (new)")
        self.log_message(f"Detect renames: {detect_renames}")
        self.log_message(f"Similarity threshold: {similarity_threshold}")
        self.log_message(f"Output format: {output_format}")

        # Create and start worker thread
        self.comparison_worker = ComparisonWorker(
            file1_path=baseline_path,
            file2_path=new_file_path,
            detect_renames=detect_renames,
            similarity_threshold=similarity_threshold,
            output_format=output_format
        )

        # Connect signals
        self.comparison_worker.started.connect(self.on_comparison_started)
        self.comparison_worker.finished.connect(self.on_comparison_finished)
        self.comparison_worker.log.connect(self.log_message)
        self.comparison_worker.error.connect(self.log_message)
        self.comparison_worker.comparison_result.connect(self.on_comparison_result)

        self.comparison_worker.start()

    def set_comparison_ui_enabled(self, enabled: bool):
        """Enable or disable comparison UI controls."""
        # Use set_ui_enabled which now handles both analysis and comparison UI
        self.set_ui_enabled(enabled)

    def on_comparison_started(self):
        """Handle comparison started signal."""
        self.log_message("Comparison in progress...")

    def on_comparison_finished(self, success: bool):
        """Handle comparison finished signal."""
        self.progress_bar.setVisible(False)
        self.set_comparison_ui_enabled(True)

        if success:
            self.log_message("Comparison completed successfully!")
            QMessageBox.information(self, "Success", "Comparison completed successfully!")
        else:
            self.log_message("Comparison failed.")
            QMessageBox.warning(self, "Comparison Failed", "Comparison failed. Check log for details.")

    def on_comparison_result(self, diff_content: str):
        """Handle comparison result signal with diff content."""
        # Display diff in log area
        self.log_message("\n=== DIFF REPORT ===\n")
        self.log_message(diff_content)
        self.log_message("\n=== END DIFF REPORT ===\n")

        # Offer to save to file
        reply = QMessageBox.question(
            self,
            "Save Diff Report",
            "Would you like to save the diff report to a file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.save_diff_report(diff_content)

    def save_diff_report(self, diff_content: str):
        """Save diff report to a file."""
        # Suggest a filename based on the compared files
        baseline_path = Path(self.baseline_path_edit.text().strip())
        new_file_path = Path(self.new_file_path_edit.text().strip())
        output_format = self.output_format_combo.currentText()

        default_name = f"{baseline_path.stem}_vs_{new_file_path.stem}_diff.{output_format}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Diff Report",
            default_name,
            f"{output_format.upper()} files (*.{output_format});;All files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(diff_content)
                self.log_message(f"Diff report saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save diff report:\n{e}")


def main():
    """Entry point for GUI application."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("Insight Fabric")
    app.setOrganizationName("InsightFabric")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()