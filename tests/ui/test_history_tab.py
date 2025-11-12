"""HistoryTab and HistoryDetailDialog UI Test Suite

Tests for the history tab functionality including:
- History record data loading and display
- Search and filtering functionality
- Statistics calculations
- Detail dialog display and interactions
- Delete and copy operations
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt

from sonicinput.core.interfaces.history import HistoryRecord
from sonicinput.ui.settings_tabs.history_tab import HistoryTab, HistoryDetailDialog


# ============= Fixtures =============

@pytest.fixture
def mock_history_service():
    """Mock HistoryStorageService"""
    service = Mock()
    service.get_records = Mock(return_value=[])
    service.delete_record = Mock(return_value=True)
    service.update_record = Mock(return_value=True)
    return service


@pytest.fixture
def sample_history_records():
    """Create sample HistoryRecord objects for testing"""
    return [
        HistoryRecord(
            id="test-id-1",
            timestamp=datetime(2025, 11, 12, 10, 30, 0),
            audio_file_path="C:/test/audio1.wav",
            duration=5.5,
            transcription_text="Test transcription 1",
            transcription_provider="local",
            transcription_status="success",
            transcription_error=None,
            ai_optimized_text="Test AI text 1",
            ai_provider="openrouter",
            ai_status="success",
            ai_error=None,
            final_text="Test AI text 1",
        ),
        HistoryRecord(
            id="test-id-2",
            timestamp=datetime(2025, 11, 12, 11, 15, 0),
            audio_file_path="C:/test/audio2.wav",
            duration=3.2,
            transcription_text="Test transcription 2",
            transcription_provider="groq",
            transcription_status="success",
            transcription_error=None,
            ai_optimized_text="Test AI text 2",
            ai_provider="groq",
            ai_status="success",
            ai_error=None,
            final_text="Test AI text 2",
        ),
        HistoryRecord(
            id="test-id-3",
            timestamp=datetime(2025, 11, 12, 12, 0, 0),
            audio_file_path="C:/test/audio3.wav",
            duration=7.8,
            transcription_text="Test transcription 3",
            transcription_provider="local",
            transcription_status="success",
            transcription_error=None,
            ai_optimized_text=None,
            ai_provider=None,
            ai_status="skipped",
            ai_error=None,
            final_text="Test transcription 3",
        ),
    ]


@pytest.fixture
def history_tab(qtbot, mock_history_service, isolated_config):
    """Create HistoryTab instance with mocked services"""
    from sonicinput.ui.settings_tabs.history_tab import HistoryTab

    mock_config_manager = Mock()
    mock_config_manager.get_history_service = Mock(return_value=mock_history_service)
    mock_config_manager.get_setting = Mock(return_value=None)

    mock_parent_window = Mock()

    tab = HistoryTab(
        config_manager=mock_config_manager,
        parent_window=mock_parent_window,
        transcription_service=None,
        ai_processing_controller=None,
    )

    # Create the widget (lazy initialization)
    widget = tab.create()
    qtbot.addWidget(widget)

    yield tab

    # Cleanup
    widget.deleteLater()


@pytest.fixture
def history_detail_dialog(qtbot, sample_history_records, mock_history_service):
    """Create HistoryDetailDialog instance with sample record"""
    record = sample_history_records[0]  # Use first record
    mock_parent_window = Mock()

    dialog = HistoryDetailDialog(
        record=record,
        parent_window=mock_parent_window,
        history_service=mock_history_service,
        transcription_service=None,
        ai_processing_controller=None,
        config_service=None,
        parent=None,
    )

    qtbot.addWidget(dialog)

    yield dialog

    # Cleanup
    dialog.deleteLater()


# ============= TestHistoryTabDataLoading =============

@pytest.mark.gui
class TestHistoryTabDataLoading:
    """Tests for history data loading and display"""

    def test_load_history_displays_records(self, qtbot, history_tab, mock_history_service, sample_history_records):
        """Test that history records are loaded and displayed correctly"""
        # Setup: Mock service to return 3 records
        mock_history_service.get_records.return_value = sample_history_records

        # Action: Load history
        history_tab._load_history()
        qtbot.wait(100)

        # Assert: Table should have 3 rows
        assert history_tab.history_table.rowCount() == 3

        # Verify first row data
        time_item = history_tab.history_table.item(0, 0)
        duration_item = history_tab.history_table.item(0, 1)
        trans_item = history_tab.history_table.item(0, 2)
        status_item = history_tab.history_table.item(0, 3)

        assert time_item is not None
        assert "11-12 10:30" in time_item.text()
        assert duration_item.text() == "5.5s"
        assert trans_item.text() == "Test transcription 1"
        assert status_item.text() == "Success"

        # Verify service was called
        mock_history_service.get_records.assert_called_once()

    def test_search_filter_matches_transcription(self, qtbot, history_tab, mock_history_service, sample_history_records):
        """Test that search filter correctly filters records by transcription text"""
        # Setup: Load records
        mock_history_service.get_records.return_value = sample_history_records
        history_tab._load_history()
        qtbot.wait(100)

        # Initially should show all 3 records
        assert history_tab.history_table.rowCount() == 3

        # Action: Set search text to filter
        history_tab.search_input.setText("transcription 2")
        qtbot.wait(100)

        # Assert: Should only show 1 matching record
        assert history_tab.history_table.rowCount() == 1
        trans_text = history_tab.history_table.item(0, 2).text()
        assert "transcription 2" in trans_text.lower()

        # Clear search
        history_tab.search_input.setText("")
        qtbot.wait(100)

        # Should show all records again
        assert history_tab.history_table.rowCount() == 3

    def test_statistics_calculate_correctly(self, qtbot, history_tab, mock_history_service):
        """Test that statistics are calculated correctly from loaded records"""
        # Create 5 records with known durations and statuses
        test_records = [
            HistoryRecord(
                id=f"test-{i}",
                timestamp=datetime(2025, 11, 12, 10 + i, 0, 0),
                audio_file_path=f"C:/test/audio{i}.wav",
                duration=float(i + 1),  # 1.0, 2.0, 3.0, 4.0, 5.0
                transcription_text=f"Test {i}",
                transcription_provider="local",
                transcription_status="success",
                transcription_error=None,
                ai_optimized_text=f"AI {i}" if i < 4 else None,  # 4 success, 1 skipped
                ai_provider="groq" if i < 4 else None,
                ai_status="success" if i < 4 else "skipped",
                ai_error=None,
                final_text=f"Final {i}",
            )
            for i in range(5)
        ]

        # Setup: Load records
        mock_history_service.get_records.return_value = test_records
        history_tab._load_history()
        qtbot.wait(100)

        # Assert: Statistics should be calculated correctly
        # Total: 5 records
        assert "5" in history_tab.total_records_label.text()

        # Total duration: 1 + 2 + 3 + 4 + 5 = 15.0s
        assert "15.0s" in history_tab.total_duration_label.text()

        # Success rate: All 5 have success transcription and success/skipped AI = 100%
        assert "100.0%" in history_tab.success_rate_label.text()


# ============= TestHistoryDetailDialog =============

@pytest.mark.gui
class TestHistoryDetailDialog:
    """Tests for HistoryDetailDialog functionality"""

    def test_detail_dialog_displays_record_info(self, qtbot, history_detail_dialog, sample_history_records):
        """Test that detail dialog correctly displays all record information"""
        record = sample_history_records[0]
        dialog = history_detail_dialog

        # Show dialog
        dialog.show()
        qtbot.waitExposed(dialog)
        qtbot.wait(100)

        # Assert: Window title
        assert "Recording Details" in dialog.windowTitle()

        # Assert: Transcription text is displayed
        trans_text = dialog.trans_text_edit.toPlainText()
        assert trans_text == "Test transcription 1"

        # Assert: AI optimized text is displayed
        optimized_text = dialog.optimized_text_edit.toPlainText()
        assert "Test AI text 1" in optimized_text

        # Assert: Dialog has expected size
        assert dialog.minimumSize().width() >= 700
        assert dialog.minimumSize().height() >= 600

    def test_copy_button_copies_optimized_text(self, qtbot, history_detail_dialog):
        """Test that copy button copies AI-optimized text to clipboard"""
        dialog = history_detail_dialog

        # Mock QMessageBox to avoid blocking
        with patch.object(QMessageBox, 'information') as mock_info:
            # Mock clipboard
            mock_clipboard = Mock()

            with patch.object(QApplication, 'clipboard', return_value=mock_clipboard):
                # Action: Click copy button
                dialog._copy_to_clipboard()
                qtbot.wait(50)

                # Assert: Clipboard setText was called with optimized text
                mock_clipboard.setText.assert_called_once()
                copied_text = mock_clipboard.setText.call_args[0][0]
                assert "Test AI text 1" in copied_text

                # Assert: Success message was shown
                mock_info.assert_called_once()
                call_args = mock_info.call_args[0]
                assert "Success" in call_args[1]

    def test_delete_button_removes_record(self, qtbot, history_detail_dialog, mock_history_service):
        """Test that delete button removes the record after confirmation"""
        dialog = history_detail_dialog

        # Mock QMessageBox.question to return Yes
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            # Mock QMessageBox.information to avoid blocking
            with patch.object(QMessageBox, 'information') as mock_info:
                # Action: Click delete button
                dialog._delete_record()
                qtbot.wait(50)

                # Assert: delete_record was called with correct ID
                mock_history_service.delete_record.assert_called_once_with("test-id-1")

                # Assert: Success message was shown
                mock_info.assert_called_once()
                call_args = mock_info.call_args[0]
                assert "Success" in call_args[1]

    def test_double_click_opens_detail_dialog(self, qtbot, history_tab, mock_history_service, sample_history_records):
        """Test that double-clicking a row opens the detail dialog"""
        # Setup: Load records into table
        mock_history_service.get_records.return_value = sample_history_records
        history_tab._load_history()
        qtbot.wait(100)

        # Mock _show_detail_dialog to verify it's called
        with patch.object(history_tab, '_show_detail_dialog') as mock_show_dialog:
            # Action: Double-click first row
            index = history_tab.history_table.model().index(0, 0)
            history_tab._on_row_double_clicked(index)
            qtbot.wait(50)

            # Assert: Dialog was shown with correct record
            mock_show_dialog.assert_called_once()
            called_record = mock_show_dialog.call_args[0][0]
            assert called_record.id == "test-id-1"

    def test_close_button_closes_dialog(self, qtbot, history_detail_dialog):
        """Test that close button closes the dialog"""
        dialog = history_detail_dialog

        # Show dialog
        dialog.show()
        qtbot.waitExposed(dialog)
        qtbot.wait(100)

        # Find close button (it's connected to accept())
        # We'll test by calling the slot directly
        dialog.accept()
        qtbot.wait(50)

        # Assert: Dialog should be closed (not visible)
        assert not dialog.isVisible()


# ============= Additional Edge Case Tests =============

@pytest.mark.gui
class TestHistoryTabEdgeCases:
    """Tests for edge cases and error handling"""

    def test_empty_history_displays_correctly(self, qtbot, history_tab, mock_history_service):
        """Test that empty history is handled gracefully"""
        # Setup: Return empty list
        mock_history_service.get_records.return_value = []

        # Action: Load history
        history_tab._load_history()
        qtbot.wait(100)

        # Assert: Table is empty
        assert history_tab.history_table.rowCount() == 0

        # Assert: Statistics show zeros
        assert "0" in history_tab.total_records_label.text()
        assert "0.0s" in history_tab.total_duration_label.text()
        assert "0%" in history_tab.success_rate_label.text()

    def test_failed_transcription_displays_correctly(self, qtbot, history_tab, mock_history_service):
        """Test that failed transcription records are displayed correctly"""
        failed_record = HistoryRecord(
            id="failed-1",
            timestamp=datetime(2025, 11, 12, 10, 0, 0),
            audio_file_path="C:/test/failed.wav",
            duration=2.5,
            transcription_text="",
            transcription_provider="local",
            transcription_status="failed",
            transcription_error="Model not loaded",
            ai_optimized_text=None,
            ai_provider=None,
            ai_status="skipped",
            ai_error=None,
            final_text="",
        )

        # Setup: Return failed record
        mock_history_service.get_records.return_value = [failed_record]

        # Action: Load history
        history_tab._load_history()
        qtbot.wait(100)

        # Assert: Record is displayed
        assert history_tab.history_table.rowCount() == 1

        # Assert: Statistics reflect failure (success rate should be 0%)
        assert "0.0%" in history_tab.success_rate_label.text()

    def test_service_unavailable_shows_warning(self, qtbot, history_tab, mock_history_service):
        """Test that warning is shown when history service is unavailable"""
        # Setup: Make service return None
        history_tab.config_manager.get_history_service = Mock(return_value=None)
        history_tab.history_service = None

        # Mock QMessageBox.warning to avoid blocking
        with patch.object(QMessageBox, 'warning') as mock_warning:
            # Action: Try to load history
            history_tab._load_history()
            qtbot.wait(50)

            # Assert: Warning was shown
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            assert "Error" in call_args[1]
            assert "History service not available" in call_args[2]


@pytest.mark.gui
class TestHistoryDetailDialogEdgeCases:
    """Tests for detail dialog edge cases"""

    def test_dialog_with_failed_ai_status(self, qtbot, mock_history_service):
        """Test detail dialog displays correctly when AI failed"""
        failed_ai_record = HistoryRecord(
            id="ai-failed",
            timestamp=datetime(2025, 11, 12, 10, 0, 0),
            audio_file_path="C:/test/ai_failed.wav",
            duration=3.0,
            transcription_text="Original text",
            transcription_provider="local",
            transcription_status="success",
            transcription_error=None,
            ai_optimized_text=None,
            ai_provider="groq",
            ai_status="failed",
            ai_error="API timeout",
            final_text="Original text",
        )

        dialog = HistoryDetailDialog(
            record=failed_ai_record,
            parent_window=Mock(),
            history_service=mock_history_service,
        )

        # Show dialog
        dialog.show()
        qtbot.wait(100)

        # Assert: Original text is shown with AI failed note
        optimized_text = dialog.optimized_text_edit.toPlainText()
        assert "Original text" in optimized_text
        assert "AI failed" in optimized_text

        # Cleanup
        dialog.deleteLater()

    def test_delete_confirmation_can_be_cancelled(self, qtbot, history_detail_dialog, mock_history_service):
        """Test that delete can be cancelled"""
        dialog = history_detail_dialog

        # Mock QMessageBox.question to return No
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
            # Action: Try to delete
            dialog._delete_record()
            qtbot.wait(50)

            # Assert: delete_record was NOT called
            mock_history_service.delete_record.assert_not_called()


# ============= TestHistoryRetryFeature =============

@pytest.mark.gui
class TestHistoryRetryFeature:
    """Test suite for History Tab Retry functionality with real threading

    These tests validate the retry feature in HistoryDetailDialog, ensuring proper
    threading behavior, signal handling, and UI updates during reprocessing.

    IMPORTANT: These tests use REAL QThread execution (not mocked), only mocking
    the actual work (file I/O, transcription, AI processing).
    """

    @pytest.fixture
    def history_detail_dialog_with_services(self, qtbot, sample_history_records, mock_history_service, isolated_config, monkeypatch):
        """Create HistoryDetailDialog with all required services for retry

        This fixture provides a fully-configured dialog with mocked services
        that can be used for testing retry functionality.
        """
        from sonicinput.ui.settings_tabs.history_tab import HistoryDetailDialog
        from PySide6.QtWidgets import QMessageBox
        import numpy as np

        # Globally mock all QMessageBox methods at fixture level to prevent dialog blocking
        monkeypatch.setattr(QMessageBox, 'information', lambda *args, **kwargs: None)
        monkeypatch.setattr(QMessageBox, 'warning', lambda *args, **kwargs: None)
        monkeypatch.setattr(QMessageBox, 'critical', lambda *args, **kwargs: None)

        record = sample_history_records[0]
        mock_parent_window = Mock()

        # Setup transcription service mock
        mock_transcription_service = Mock()
        mock_transcription_service.transcribe_sync = Mock(return_value={
            "success": True,
            "text": "Updated transcription",
            "language": "zh",
        })

        # Setup AI controller mock
        mock_ai_controller = Mock()
        mock_ai_controller.process_with_ai = Mock(return_value="Updated AI text")
        mock_ai_controller._current_record_id = None

        # Setup config service mock
        mock_config_service = Mock()
        mock_config_service.get_setting = Mock(side_effect=lambda key, default=None: {
            "transcription.provider": "local",
            "transcription.local.language": "zh",
            "transcription.temperature": 0.0,
            "ai.enabled": True,
            "ai.provider": "openrouter",
        }.get(key, default))

        dialog = HistoryDetailDialog(
            record=record,
            parent_window=mock_parent_window,
            history_service=mock_history_service,
            transcription_service=mock_transcription_service,
            ai_processing_controller=mock_ai_controller,
            config_service=mock_config_service,
        )
        qtbot.addWidget(dialog)

        yield dialog

        # Cleanup: Ensure worker is stopped
        if dialog.reprocessing_worker and dialog.reprocessing_worker.isRunning():
            dialog.reprocessing_worker.should_stop = True
            dialog.reprocessing_worker.wait(1000)

        dialog.deleteLater()

    @pytest.fixture
    def history_detail_dialog_no_services(self, qtbot, sample_history_records, mock_history_service):
        """Create dialog WITHOUT transcription/AI services to test error handling"""
        from sonicinput.ui.settings_tabs.history_tab import HistoryDetailDialog

        record = sample_history_records[0]
        mock_parent_window = Mock()

        dialog = HistoryDetailDialog(
            record=record,
            parent_window=mock_parent_window,
            history_service=mock_history_service,
            transcription_service=None,  # No service
            ai_processing_controller=None,
            config_service=None,
        )
        qtbot.addWidget(dialog)

        yield dialog

        dialog.deleteLater()

    def test_retry_button_requires_services(self, qtbot, history_detail_dialog_no_services):
        """Test that retry button shows warning when services are not available

        Scenario: User clicks Retry when transcription_service is None
        Expected: Warning dialog appears, no worker is created
        """
        dialog = history_detail_dialog_no_services

        # Verify initial state
        assert dialog.transcription_service is None
        assert dialog.config_service is None
        assert dialog.reprocessing_worker is None

        # Mock QMessageBox.warning to capture the warning
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            # Click retry button
            dialog.retry_button.click()
            qtbot.wait(50)

            # Verify warning was shown
            assert mock_warning.called
            call_args = mock_warning.call_args
            assert call_args[0][0] == dialog  # parent
            assert "Service Unavailable" in call_args[0][1]  # title
            assert "transcription service" in call_args[0][2].lower()  # message

            # Verify no worker was created
            assert dialog.reprocessing_worker is None


    def test_retry_completion_updates_record(self, qtbot, history_detail_dialog_with_services, mock_history_service):
        """Test real threading: worker completes and updates record

        CRITICAL TEST: This validates real QThread execution with actual signals.
        We DO NOT mock threading.Thread - we let the QThread run for real.
        We only mock the actual work (file I/O, transcription, AI processing).

        Scenario: User confirms retry, worker processes in background, completes successfully
        Expected:
            1. Worker thread runs and completes
            2. history_service.update_record() is called with updated HistoryRecord
            3. UI text fields are updated with new content
            4. Success message is shown
        """
        import numpy as np
        dialog = history_detail_dialog_with_services

        # Store original text to verify it changes
        original_trans_text = dialog.trans_text_edit.toPlainText()
        original_optimized_text = dialog.optimized_text_edit.toPlainText()

        # Mock transcription service with realistic delay
        def mock_transcribe_with_delay(audio_data, language=None, temperature=0.0):
            import time
            time.sleep(0.1)  # Simulate processing time
            return {
                "success": True,
                "text": "Updated transcription from worker",
                "language": "zh",
            }

        dialog.transcription_service.transcribe_sync = Mock(side_effect=mock_transcribe_with_delay)

        # Mock AI processing with delay
        def mock_ai_with_delay(text):
            import time
            time.sleep(0.1)  # Simulate AI processing
            return "Updated AI optimized text from worker"

        dialog.ai_processing_controller.process_with_ai = Mock(side_effect=mock_ai_with_delay)

        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('sonicinput.audio.recorder.AudioRecorder.load_audio_from_file') as mock_load:
                # Return realistic audio data
                mock_load.return_value = np.random.random(16000 * 3).astype(np.float32)

                with patch('PySide6.QtWidgets.QMessageBox.question',
                          return_value=QMessageBox.StandardButton.Yes):
                    with patch('PySide6.QtWidgets.QMessageBox.critical'):  # Mock error dialogs
                        with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info:
                            # Click retry button
                            dialog.retry_button.click()
                            qtbot.wait(100)  # Let thread start

                            # Verify worker was created and started
                            assert dialog.reprocessing_worker is not None
                            assert dialog.reprocessing_worker.isRunning()

                            # Wait for worker to finish (REAL THREADING TEST!)
                            # Use qtbot.waitUntil to wait for thread completion
                            def worker_finished():
                                return (dialog.reprocessing_worker is None or
                                       not dialog.reprocessing_worker.isRunning())

                            # Wait up to 5 seconds for thread to complete
                            qtbot.waitUntil(worker_finished, timeout=5000)

                            # Give UI time to process signals
                            qtbot.wait(100)

                            # Verify transcription service was called
                            assert dialog.transcription_service.transcribe_sync.called

                            # Verify AI controller was called
                            assert dialog.ai_processing_controller.process_with_ai.called

                            # Verify history service update_record was called
                            assert mock_history_service.update_record.called

                            # Verify the updated record has correct data
                            updated_record = mock_history_service.update_record.call_args[0][0]
                            assert updated_record.id == dialog.record.id
                            assert updated_record.transcription_text == "Updated transcription from worker"
                            assert updated_record.ai_optimized_text == "Updated AI optimized text from worker"
                            assert updated_record.transcription_status == "success"
                            assert updated_record.ai_status == "success"
                            assert updated_record.transcription_provider == "local"

                            # Verify UI was updated
                            new_trans_text = dialog.trans_text_edit.toPlainText()
                            new_optimized_text = dialog.optimized_text_edit.toPlainText()

                            assert new_trans_text != original_trans_text
                            assert "Updated transcription from worker" in new_trans_text
                            assert new_optimized_text != original_optimized_text
                            assert "Updated AI optimized text from worker" in new_optimized_text

                            # Verify success message was shown
                            assert mock_info.called
                            success_msg = mock_info.call_args[0][2]
                            assert "successfully reprocessed" in success_msg.lower()

                            # Verify worker was cleaned up
                            assert dialog.reprocessing_worker is None

    def test_retry_handles_transcription_failure(self, qtbot, history_detail_dialog_with_services, mock_history_service):
        """Test that retry handles transcription errors gracefully

        Scenario: Transcription service fails during retry
        Expected: Error dialog shown, record updated with failure status
        """
        import numpy as np
        dialog = history_detail_dialog_with_services

        # Mock transcription to fail
        def mock_transcribe_failure(audio_data, language=None, temperature=0.0):
            import time
            time.sleep(0.05)
            return {
                "success": False,
                "error": "Transcription model not loaded",
                "text": "",
            }

        dialog.transcription_service.transcribe_sync = Mock(side_effect=mock_transcribe_failure)

        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('sonicinput.audio.recorder.AudioRecorder.load_audio_from_file') as mock_load:
                mock_load.return_value = np.random.random(16000).astype(np.float32)

                with patch('PySide6.QtWidgets.QMessageBox.question',
                          return_value=QMessageBox.StandardButton.Yes):
                    with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_error:
                        # Click retry
                        dialog.retry_button.click()
                        qtbot.wait(100)

                        # Wait for worker to finish
                        def worker_finished():
                            return dialog.reprocessing_worker is None or not dialog.reprocessing_worker.isRunning()

                        qtbot.waitUntil(worker_finished, timeout=3000)
                        qtbot.wait(100)

                        # Verify error dialog was shown
                        assert mock_error.called
                        error_msg = str(mock_error.call_args)
                        assert "failed" in error_msg.lower() or "error" in error_msg.lower()

                        # Verify record was updated with failure status
                        assert mock_history_service.update_record.called
                        updated_record = mock_history_service.update_record.call_args[0][0]
                        assert updated_record.transcription_status == "failed"
                        assert updated_record.transcription_error is not None
                        assert "not loaded" in updated_record.transcription_error

    def test_retry_handles_missing_audio_file(self, qtbot, history_detail_dialog_with_services):
        """Test retry handles missing audio file gracefully

        Scenario: Audio file doesn't exist when retry is attempted
        Expected: Error dialog shown, no processing occurs
        """
        dialog = history_detail_dialog_with_services

        # Mock file not existing
        with patch('os.path.exists', return_value=False):
            with patch('PySide6.QtWidgets.QMessageBox.question',
                      return_value=QMessageBox.StandardButton.Yes):
                with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_error:
                    # Click retry
                    dialog.retry_button.click()
                    qtbot.wait(100)

                    # Wait for worker to finish
                    def worker_finished():
                        return dialog.reprocessing_worker is None or not dialog.reprocessing_worker.isRunning()

                    qtbot.waitUntil(worker_finished, timeout=3000)
                    qtbot.wait(100)

                    # Verify error dialog was shown
                    assert mock_error.called
                    error_msg = str(mock_error.call_args)
                    assert "file not found" in error_msg.lower() or "audio" in error_msg.lower()

    def test_retry_user_cancels_confirmation(self, qtbot, history_detail_dialog_with_services):
        """Test that canceling confirmation dialog aborts retry

        Scenario: User clicks Retry but then clicks No on confirmation
        Expected: No worker created, no processing occurs
        """
        dialog = history_detail_dialog_with_services

        # Mock user clicking No
        with patch('PySide6.QtWidgets.QMessageBox.question',
                  return_value=QMessageBox.StandardButton.No):
            # Click retry button
            dialog.retry_button.click()
            qtbot.wait(50)

            # Verify no worker was created
            assert dialog.reprocessing_worker is None
            assert dialog.progress_dialog is None

    def test_retry_ai_disabled_skips_ai_processing(self, qtbot, history_detail_dialog_with_services, mock_history_service):
        """Test that AI processing is skipped when AI is disabled

        Scenario: AI is disabled in config, user retries
        Expected: Only transcription runs, AI status is 'skipped'
        """
        import numpy as np
        dialog = history_detail_dialog_with_services

        # Configure AI as disabled
        dialog.config_service.get_setting = Mock(side_effect=lambda key, default=None: {
            "transcription.provider": "local",
            "transcription.local.language": "zh",
            "transcription.temperature": 0.0,
            "ai.enabled": False,  # AI disabled
            "ai.provider": "openrouter",
        }.get(key, default))

        # Mock transcription
        def mock_transcribe(audio_data, language=None, temperature=0.0):
            import time
            time.sleep(0.05)
            return {
                "success": True,
                "text": "Transcription without AI",
                "language": "zh",
            }

        dialog.transcription_service.transcribe_sync = Mock(side_effect=mock_transcribe)

        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('sonicinput.audio.recorder.AudioRecorder.load_audio_from_file') as mock_load:
                mock_load.return_value = np.random.random(16000).astype(np.float32)

                with patch('PySide6.QtWidgets.QMessageBox.question',
                          return_value=QMessageBox.StandardButton.Yes):
                    with patch('PySide6.QtWidgets.QMessageBox.information'):
                        # Click retry
                        dialog.retry_button.click()
                        qtbot.wait(100)

                        # Wait for completion
                        def worker_finished():
                            return dialog.reprocessing_worker is None or not dialog.reprocessing_worker.isRunning()

                        qtbot.waitUntil(worker_finished, timeout=3000)
                        qtbot.wait(100)

                        # Verify transcription was called
                        assert dialog.transcription_service.transcribe_sync.called

                        # Verify AI was NOT called
                        assert not dialog.ai_processing_controller.process_with_ai.called

                        # Verify record has AI status as 'skipped'
                        updated_record = mock_history_service.update_record.call_args[0][0]
                        assert updated_record.ai_status == "skipped"
                        assert updated_record.ai_optimized_text is None or updated_record.ai_optimized_text == ""
                        assert updated_record.final_text == "Transcription without AI"
