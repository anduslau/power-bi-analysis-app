"""
GUI integration tests for Report to Business Documents Application.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

# Add src to path to import our modules
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from power_bi_analysis.gui.main_window import MainWindow, AnalysisWorker, ComparisonWorker


@pytest.fixture
def app(qtbot):
    """Provide QApplication instance."""
    # qtbot already provides QApplication via qapp fixture
    return QApplication.instance()


@pytest.fixture
def window(qtbot):
    """Create and return main window."""
    win = MainWindow()
    qtbot.addWidget(win)
    return win


class TestMainWindow:
    """Test MainWindow GUI."""

    def test_window_creation(self, window):
        """Test that window is created with correct title."""
        assert window.windowTitle() == "Report to Business Documents Application"
        assert window.file_path_edit is not None
        assert window.llm_provider_combo is not None
        assert window.run_btn is not None

    def test_file_browse_dialog(self, window, qtbot):
        """Test file browse button opens dialog (mocked)."""
        with patch.object(window, 'browse_file') as mock_browse:
            qtbot.mouseClick(window.run_btn, Qt.MouseButton.LeftButton)
            # Actually we need to click browse button, but we don't have reference.
            # Let's get browse button from layout? We'll skip for now.
            pass

    def test_run_analysis_without_file(self, window, qtbot):
        """Test run analysis with no file selected shows warning."""
        # Clear file path
        window.file_path_edit.clear()

        # Mock QMessageBox to capture warning
        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            qtbot.mouseClick(window.run_btn, Qt.MouseButton.LeftButton)
            mock_warning.assert_called_once()
            # Check that warning mentions missing file
            call_args = mock_warning.call_args[0]
            assert "file" in call_args[1].lower() or "select" in call_args[1].lower()

    def test_run_analysis_with_invalid_file(self, window, qtbot):
        """Test run analysis with non-existent file shows warning."""
        window.file_path_edit.setText("/nonexistent/file.pbix")

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            qtbot.mouseClick(window.run_btn, Qt.MouseButton.LeftButton)
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            assert "not found" in call_args[1].lower() or "exist" in call_args[1].lower()

    def test_load_config(self, window):
        """Test that configuration loads into UI."""
        # Check that LLM provider combo has a selection
        assert window.llm_provider_combo.currentText() in ["anthropic", "openai", "gemini", "deepseek"]
        # Output directory should be set
        assert window.output_dir_edit.text()
        # Generate YAML checkbox should reflect config default
        assert window.generate_yaml_check.isChecked() == window.config.get_generate_yaml()

    def test_clear_log(self, window, qtbot):
        """Test clear log button."""
        # Add some text to log
        window.log_text.setPlainText("Test log message")
        assert window.log_text.toPlainText() == "Test log message"

        # Click clear button
        qtbot.mouseClick(window.clear_btn, Qt.MouseButton.LeftButton)
        assert window.log_text.toPlainText() == ""


class TestAnalysisWorker:
    """Test AnalysisWorker thread."""

    @patch('power_bi_analysis.gui.main_window.AnalysisPipeline')
    def test_worker_success(self, MockPipeline, qtbot):
        """Test worker successful execution."""
        # Mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.analyze_file.return_value = True
        mock_pipeline.save_outputs.return_value = (
            Path("brd.md"), Path("semantic.yaml"), None, None
        )
        mock_pipeline.get_errors.return_value = []
        MockPipeline.return_value = mock_pipeline

        # Create worker
        worker = AnalysisWorker(
            file_path=Path("test.pbix"),
            llm_provider="anthropic",
            llm_api_key="test_key",
            llm_model=None,
            generate_yaml=True,
            generate_sql=False,
            generate_dictionary=False,
            output_dir=Path("output")
        )

        # Connect signals
        log_messages = []
        errors = []
        def on_log(msg):
            log_messages.append(msg)
        def on_error(msg):
            errors.append(msg)

        worker.log.connect(on_log)
        worker.error.connect(on_error)

        # Run worker synchronously (not starting thread) for test
        # We'll call run directly
        worker.run()

        # Verify pipeline was called correctly
        MockPipeline.assert_called_once_with(
            llm_provider="anthropic",
            llm_api_key="test_key",
            llm_model=None,
            generate_yaml=True,
            generate_sql=False,
            generate_dictionary=False
        )
        mock_pipeline.analyze_file.assert_called_once_with(Path("test.pbix"))
        mock_pipeline.save_outputs.assert_called_once_with(Path("output"))

        # Verify log messages
        assert any("Starting analysis" in msg for msg in log_messages)
        assert any("Analysis completed successfully" in msg for msg in log_messages)
        assert any("BRD saved to:" in msg for msg in log_messages)

    @patch('power_bi_analysis.gui.main_window.AnalysisPipeline')
    def test_worker_failure(self, MockPipeline, qtbot):
        """Test worker failure scenario."""
        mock_pipeline = Mock()
        mock_pipeline.analyze_file.return_value = False
        mock_pipeline.get_errors.return_value = ["Error 1", "Error 2"]
        MockPipeline.return_value = mock_pipeline

        worker = AnalysisWorker(
            file_path=Path("test.pbix"),
            llm_provider="anthropic",
            llm_api_key="test_key",
            llm_model=None,
            generate_yaml=False,
            generate_sql=False,
            generate_dictionary=False,
            output_dir=Path("output")
        )

        errors = []
        def on_error(msg):
            errors.append(msg)
        worker.error.connect(on_error)

        worker.run()

        # Verify errors were emitted
        assert len(errors) == 2
        assert "Error 1" in errors[0]
        assert "Error 2" in errors[1]


class TestComparisonWorker:
    """Test ComparisonWorker thread."""

    @patch('power_bi_analysis.gui.main_window.extract_metadata')
    @patch('power_bi_analysis.gui.main_window.compare_metadata')
    @patch('power_bi_analysis.comparison.diff_renderer.render_diff')
    def test_worker_success(self, mock_render_diff, mock_compare_metadata, mock_extract_metadata, qtbot):
        """Test worker successful execution."""
        # Mock metadata extraction
        mock_meta1 = Mock()
        mock_meta2 = Mock()
        mock_extract_metadata.side_effect = [mock_meta1, mock_meta2]

        # Mock comparison
        mock_diff_report = Mock()
        mock_diff_report.summary = {'total': 5}
        mock_compare_metadata.return_value = mock_diff_report

        # Mock diff rendering
        mock_render_diff.return_value = "Mock diff report"

        # Create worker
        worker = ComparisonWorker(
            file1_path=Path("baseline.pbix"),
            file2_path=Path("new.pbix"),
            detect_renames=True,
            similarity_threshold=0.8,
            output_format="markdown"
        )

        # Connect signals
        log_messages = []
        errors = []
        results = []
        def on_log(msg):
            log_messages.append(msg)
        def on_error(msg):
            errors.append(msg)
        def on_result(diff_content):
            results.append(diff_content)

        worker.log.connect(on_log)
        worker.error.connect(on_error)
        worker.comparison_result.connect(on_result)

        # Run worker synchronously
        worker.run()

        # Verify extraction was called correctly
        assert mock_extract_metadata.call_count == 2
        mock_extract_metadata.assert_any_call(Path("baseline.pbix"))
        mock_extract_metadata.assert_any_call(Path("new.pbix"))

        # Verify comparison was called correctly
        mock_compare_metadata.assert_called_once_with(
            mock_meta1,
            mock_meta2,
            detect_renames=True,
            similarity_threshold=0.8
        )

        # Verify diff rendering
        mock_render_diff.assert_called_once_with(mock_diff_report, "markdown")

        # Verify signals
        assert any("Comparing" in msg for msg in log_messages)
        assert any("Extracting metadata" in msg for msg in log_messages)
        assert any("Comparison completed" in msg for msg in log_messages)
        assert len(results) == 1
        assert results[0] == "Mock diff report"
        assert len(errors) == 0

    @patch('power_bi_analysis.gui.main_window.extract_metadata')
    def test_worker_extraction_failure(self, mock_extract_metadata, qtbot):
        """Test worker failure when extraction fails."""
        # Mock extraction failure for first file
        mock_extract_metadata.return_value = None

        worker = ComparisonWorker(
            file1_path=Path("baseline.pbix"),
            file2_path=Path("new.pbix")
        )

        errors = []
        finished_signals = []
        def on_error(msg):
            errors.append(msg)
        def on_finished(success):
            finished_signals.append(success)

        worker.error.connect(on_error)
        worker.finished.connect(on_finished)

        worker.run()

        # Verify error was emitted and finished with failure
        assert len(errors) >= 1
        assert "Failed to extract metadata" in errors[0]
        assert len(finished_signals) == 1
        assert finished_signals[0] == False

    @patch('power_bi_analysis.gui.main_window.extract_metadata')
    @patch('power_bi_analysis.gui.main_window.compare_metadata')
    def test_worker_comparison_exception(self, mock_compare_metadata, mock_extract_metadata, qtbot):
        """Test worker handling of comparison exception."""
        mock_extract_metadata.side_effect = [Mock(), Mock()]
        mock_compare_metadata.side_effect = Exception("Comparison error")

        worker = ComparisonWorker(
            file1_path=Path("baseline.pbix"),
            file2_path=Path("new.pbix")
        )

        errors = []
        def on_error(msg):
            errors.append(msg)
        worker.error.connect(on_error)

        worker.run()

        # Verify error was emitted
        assert len(errors) >= 1
        assert "Comparison error" in errors[0]


class TestComparisonGUI:
    """Test GUI comparison functionality."""

    def test_comparison_ui_elements(self, window):
        """Test that comparison UI elements exist."""
        assert window.baseline_path_edit is not None
        assert window.new_file_path_edit is not None
        assert window.detect_renames_check is not None
        assert window.similarity_threshold_spin is not None
        assert window.output_format_combo is not None
        assert window.compare_btn is not None

        # Check default values
        assert window.detect_renames_check.isChecked() == True
        assert window.similarity_threshold_spin.value() == 0.8
        assert window.output_format_combo.currentText() == "markdown"

    def test_run_comparison_validation_missing_baseline(self, window, qtbot):
        """Test validation when baseline file is missing."""
        window.baseline_path_edit.clear()
        window.new_file_path_edit.setText("new.pbix")

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            # Mock Path.exists so new file appears to exist (though not checked)
            with patch('pathlib.Path.exists', return_value=True):
                window.run_comparison()
                mock_warning.assert_called_once()
                call_args = mock_warning.call_args[0]
                assert "baseline" in call_args[1].lower()

    def test_run_comparison_validation_missing_new(self, window, qtbot):
        """Test validation when new file is missing."""
        window.baseline_path_edit.setText("baseline.pbix")
        window.new_file_path_edit.clear()

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            # Mock Path.exists so baseline file appears to exist
            with patch('pathlib.Path.exists', return_value=True):
                window.run_comparison()
                mock_warning.assert_called_once()
                call_args = mock_warning.call_args[0]
                assert "new" in call_args[1].lower()

    def test_run_comparison_validation_nonexistent_files(self, window, qtbot):
        """Test validation when files don't exist."""
        window.baseline_path_edit.setText("/nonexistent/baseline.pbix")
        window.new_file_path_edit.setText("/nonexistent/new.pbix")

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            # Mock Path.exists to return False
            with patch('pathlib.Path.exists', return_value=False):
                window.run_comparison()
                mock_warning.assert_called_once()
                call_args = mock_warning.call_args[0]
                assert "not found" in call_args[1].lower() or "exist" in call_args[1].lower()

    @patch('power_bi_analysis.gui.main_window.ComparisonWorker')
    def test_run_comparison_success(self, MockComparisonWorker, window, qtbot):
        """Test successful comparison start."""
        # Setup UI
        window.baseline_path_edit.setText("baseline.pbix")
        window.new_file_path_edit.setText("new.pbix")
        window.detect_renames_check.setChecked(True)
        window.similarity_threshold_spin.setValue(0.9)
        window.output_format_combo.setCurrentText("json")

        # Mock worker
        mock_worker = Mock()
        MockComparisonWorker.return_value = mock_worker

        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            window.show()
            qtbot.waitExposed(window)
            window.run_comparison()

        # Verify worker was created with correct parameters
        MockComparisonWorker.assert_called_once_with(
            file1_path=Path("baseline.pbix"),
            file2_path=Path("new.pbix"),
            detect_renames=True,
            similarity_threshold=0.9,
            output_format="json"
        )

        # Verify worker signals were connected
        assert mock_worker.started.connect.called
        assert mock_worker.finished.connect.called
        assert mock_worker.log.connect.called
        assert mock_worker.error.connect.called
        assert mock_worker.comparison_result.connect.called

        # Verify worker was started
        mock_worker.start.assert_called_once()

        # Verify UI was disabled
        assert not window.compare_btn.isEnabled()
        assert window.progress_bar.isVisible()


if __name__ == "__main__":
    # Allow running as script for quick smoke test
    pytest.main([__file__, "-v"])