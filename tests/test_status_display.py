"""
Unit tests for status display system.
"""
import unittest
from unittest.mock import Mock, patch, call
from datetime import datetime
from io import StringIO
import sys

from health_monitor.models.data_models import HealthStatus
from health_monitor.services.status_display import StatusDisplay, StatusChangeTracker


class TestStatusDisplay(unittest.TestCase):
    """Test cases for StatusDisplay."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.display = StatusDisplay()
        
        # Create test health statuses
        self.healthy_status = HealthStatus(
            target_name="test-website",
            is_healthy=True,
            response_time=0.5,
            error_message=None,
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        self.unhealthy_status = HealthStatus(
            target_name="test-database",
            is_healthy=False,
            response_time=0.0,
            error_message="Connection timeout",
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
    
    @patch('health_monitor.services.status_display.os.system')
    @patch('builtins.print')
    def test_update_display_basic(self, mock_print, mock_os_system):
        """Test basic display update functionality."""
        statuses = {
            "test-website": self.healthy_status,
            "test-database": self.unhealthy_status
        }
        
        self.display.update_display(statuses)
        
        # Verify screen was cleared
        mock_os_system.assert_called_once_with('cls')
        
        # Verify print was called multiple times for header, targets, and footer
        self.assertTrue(mock_print.called)
        self.assertGreater(mock_print.call_count, 5)
    
    @patch('builtins.print')
    def test_show_error(self, mock_print):
        """Test error message display."""
        target = "test-target"
        error = "Connection failed"
        
        self.display.show_error(target, error)
        
        # Verify error message was printed with correct format
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn("エラー", call_args)
        self.assertIn(target, call_args)
        self.assertIn(error, call_args)
    
    @patch('builtins.print')
    def test_refresh_ui(self, mock_print):
        """Test UI refresh functionality."""
        self.display.refresh_ui()
        
        # Verify print was called with empty string and flush=True
        mock_print.assert_called_once_with("", end="", flush=True)
    
    def test_detect_status_changes_no_previous(self):
        """Test status change detection with no previous statuses."""
        statuses = {"test-website": self.healthy_status}
        
        self.display._detect_status_changes(statuses)
        
        # Should have no changes since no previous status
        self.assertEqual(len(self.display._status_changes), 0)
    
    def test_detect_status_changes_with_change(self):
        """Test status change detection when status changes."""
        # Set up previous status as unhealthy
        previous_status = HealthStatus(
            target_name="test-website",
            is_healthy=False,
            response_time=0.0,
            error_message="Previous error",
            timestamp=datetime(2023, 1, 1, 11, 0, 0)
        )
        
        # Manually set previous status in change tracker
        self.display._change_tracker._previous_statuses["test-website"] = previous_status
        
        # Now detect changes with healthy status
        statuses = {"test-website": self.healthy_status}
        self.display._detect_status_changes(statuses)
        
        # Should detect 異常→正常 change
        self.assertEqual(len(self.display._status_changes), 1)
        self.assertEqual(self.display._status_changes["test-website"], "異常→正常")
    
    def test_get_status_changes(self):
        """Test getting status changes."""
        # Set up some status changes
        self.display._status_changes = {"test": "正常→異常"}
        
        changes = self.display.get_status_changes()
        
        self.assertEqual(changes, {"test": "正常→異常"})
        # Verify it returns a copy, not the original
        changes["new"] = "test"
        self.assertNotIn("new", self.display._status_changes)
    
    def test_get_change_tracker(self):
        """Test getting the change tracker instance."""
        tracker = self.display.get_change_tracker()
        
        self.assertIsInstance(tracker, StatusChangeTracker)
        self.assertEqual(tracker, self.display._change_tracker)
    
    @patch('health_monitor.services.status_display.os.system')
    def test_clear_screen_windows(self, mock_os_system):
        """Test screen clearing on Windows."""
        with patch('health_monitor.services.status_display.os.name', 'nt'):
            self.display._clear_screen()
            mock_os_system.assert_called_once_with('cls')
    
    @patch('health_monitor.services.status_display.os.system')
    def test_clear_screen_unix(self, mock_os_system):
        """Test screen clearing on Unix systems."""
        with patch('health_monitor.services.status_display.os.name', 'posix'):
            self.display._clear_screen()
            mock_os_system.assert_called_once_with('clear')


class TestStatusChangeTracker(unittest.TestCase):
    """Test cases for StatusChangeTracker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = StatusChangeTracker()
        
        self.healthy_status = HealthStatus(
            target_name="test-target",
            is_healthy=True,
            response_time=0.5,
            error_message=None,
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        self.unhealthy_status = HealthStatus(
            target_name="test-target",
            is_healthy=False,
            response_time=0.0,
            error_message="Connection failed",
            timestamp=datetime(2023, 1, 1, 12, 1, 0)
        )
    
    def test_track_status_change_first_time(self):
        """Test tracking status change for the first time."""
        result = self.tracker.track_status_change("test-target", self.healthy_status)
        
        # Should return None for first time
        self.assertIsNone(result)
        
        # Should store the status
        previous = self.tracker.get_previous_status("test-target")
        self.assertEqual(previous, self.healthy_status)
    
    def test_track_status_change_no_change(self):
        """Test tracking when status doesn't change."""
        # Track first status
        self.tracker.track_status_change("test-target", self.healthy_status)
        
        # Track same status again
        result = self.tracker.track_status_change("test-target", self.healthy_status)
        
        # Should return None since no change
        self.assertIsNone(result)
    
    def test_track_status_change_up_to_down(self):
        """Test tracking status change from healthy to unhealthy."""
        # Track healthy status first
        self.tracker.track_status_change("test-target", self.healthy_status)
        
        # Track unhealthy status
        result = self.tracker.track_status_change("test-target", self.unhealthy_status)
        
        # Should detect 正常→異常 change
        self.assertEqual(result, "正常→異常")
        
        # Should store change indicator
        indicator = self.tracker.get_change_indicator("test-target")
        self.assertEqual(indicator, "正常→異常")
    
    def test_track_status_change_down_to_up(self):
        """Test tracking status change from unhealthy to healthy."""
        # Track unhealthy status first
        self.tracker.track_status_change("test-target", self.unhealthy_status)
        
        # Track healthy status
        result = self.tracker.track_status_change("test-target", self.healthy_status)
        
        # Should detect 異常→正常 change
        self.assertEqual(result, "異常→正常")
        
        # Should store change indicator
        indicator = self.tracker.get_change_indicator("test-target")
        self.assertEqual(indicator, "異常→正常")
    
    def test_get_change_timestamp(self):
        """Test getting change timestamp."""
        # Track status change
        self.tracker.track_status_change("test-target", self.healthy_status)
        self.tracker.track_status_change("test-target", self.unhealthy_status)
        
        # Get change timestamp
        timestamp = self.tracker.get_change_timestamp("test-target")
        self.assertEqual(timestamp, self.unhealthy_status.timestamp)
    
    def test_clear_change_indicator(self):
        """Test clearing change indicator."""
        # Set up change
        self.tracker.track_status_change("test-target", self.healthy_status)
        self.tracker.track_status_change("test-target", self.unhealthy_status)
        
        # Verify indicator exists
        self.assertIsNotNone(self.tracker.get_change_indicator("test-target"))
        
        # Clear indicator
        self.tracker.clear_change_indicator("test-target")
        
        # Verify indicator is cleared
        self.assertIsNone(self.tracker.get_change_indicator("test-target"))
        self.assertIsNone(self.tracker.get_change_timestamp("test-target"))
    
    def test_has_recent_change_true(self):
        """Test detecting recent changes."""
        # Track status change with current timestamp
        current_status = HealthStatus(
            target_name="test-target",
            is_healthy=False,
            response_time=0.0,
            error_message="Error",
            timestamp=datetime.now()
        )
        
        self.tracker.track_status_change("test-target", self.healthy_status)
        self.tracker.track_status_change("test-target", current_status)
        
        # Should detect recent change
        self.assertTrue(self.tracker.has_recent_change("test-target", 60))
    
    def test_has_recent_change_false(self):
        """Test detecting old changes."""
        # Track status change with old timestamp
        old_status = HealthStatus(
            target_name="test-target",
            is_healthy=False,
            response_time=0.0,
            error_message="Error",
            timestamp=datetime(2020, 1, 1, 12, 0, 0)
        )
        
        self.tracker.track_status_change("test-target", self.healthy_status)
        self.tracker.track_status_change("test-target", old_status)
        
        # Should not detect recent change
        self.assertFalse(self.tracker.has_recent_change("test-target", 60))
    
    def test_has_recent_change_no_change(self):
        """Test detecting recent changes when no change occurred."""
        # Should return False for target with no changes
        self.assertFalse(self.tracker.has_recent_change("non-existent", 60))
    
    def test_clear_history(self):
        """Test clearing all history."""
        # Set up some history
        self.tracker.track_status_change("test-target", self.healthy_status)
        self.tracker.track_status_change("test-target", self.unhealthy_status)
        
        # Verify history exists
        self.assertIsNotNone(self.tracker.get_previous_status("test-target"))
        self.assertIsNotNone(self.tracker.get_change_indicator("test-target"))
        
        # Clear history
        self.tracker.clear_history()
        
        # Verify history is cleared
        self.assertIsNone(self.tracker.get_previous_status("test-target"))
        self.assertIsNone(self.tracker.get_change_indicator("test-target"))
        self.assertFalse(self.tracker.has_recent_change("test-target", 60))


class TestStatusDisplayColorOutput(unittest.TestCase):
    """Test cases for color output formatting."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.display = StatusDisplay()
    
    @patch('builtins.print')
    def test_display_target_status_healthy(self, mock_print):
        """Test displaying healthy target status with correct colors."""
        healthy_status = HealthStatus(
            target_name="test-website",
            is_healthy=True,
            response_time=0.5,
            error_message=None,
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        self.display._display_target_status("test-website", healthy_status)
        
        # Verify print was called
        self.assertTrue(mock_print.called)
        
        # Check that the output contains expected elements
        printed_calls = [str(call.args[0]) if call.args else str(call) for call in mock_print.call_args_list]
        printed_output = ''.join(printed_calls)
        self.assertIn("test-website", printed_output)
        self.assertIn("正常", printed_output)
        self.assertIn("0.50s", printed_output)
        self.assertIn("12:00:00", printed_output)
    
    @patch('builtins.print')
    def test_display_target_status_unhealthy(self, mock_print):
        """Test displaying unhealthy target status with error message."""
        unhealthy_status = HealthStatus(
            target_name="test-database",
            is_healthy=False,
            response_time=0.0,
            error_message="Connection timeout",
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        self.display._display_target_status("test-database", unhealthy_status)
        
        # Verify print was called multiple times (status line + error line + spacing)
        self.assertGreaterEqual(mock_print.call_count, 3)
        
        # Check that the output contains expected elements
        printed_calls = [str(call.args[0]) if call.args else str(call) for call in mock_print.call_args_list]
        printed_output = ''.join(printed_calls)
        self.assertIn("test-database", printed_output)
        self.assertIn("異常", printed_output)
        self.assertIn("Connection timeout", printed_output)


if __name__ == '__main__':
    unittest.main()