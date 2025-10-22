"""
Unit tests for log manager.
"""
import unittest
import tempfile
import shutil
import json
from datetime import datetime, date
from pathlib import Path
from unittest.mock import patch, mock_open

from health_monitor.models.data_models import LogEntry
from health_monitor.services.log_manager import LogManager


class TestLogManager(unittest.TestCase):
    """Test cases for LogManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_manager = LogManager(log_directory=self.temp_dir)
        
        # Test data
        self.test_timestamp = datetime(2024, 1, 15, 10, 30, 45)
        self.test_log_entry = LogEntry(
            timestamp=self.test_timestamp,
            target_name="test-website",
            target_type="website",
            status_change="up->down",
            details="Connection timeout"
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_directory_creation(self):
        """Test that log directory is created if it doesn't exist."""
        new_temp_dir = Path(self.temp_dir) / "new_logs"
        self.assertFalse(new_temp_dir.exists())
        
        LogManager(log_directory=str(new_temp_dir))
        self.assertTrue(new_temp_dir.exists())
    
    def test_get_log_file_path_default_date(self):
        """Test getting log file path with default date (today)."""
        today = date.today()
        expected_filename = f"health_monitor_{today.strftime('%Y%m%d')}.log"
        
        log_path = self.log_manager._get_log_file_path()
        
        self.assertEqual(log_path.name, expected_filename)
        self.assertEqual(log_path.parent, Path(self.temp_dir))
    
    def test_get_log_file_path_specific_date(self):
        """Test getting log file path with specific date."""
        test_date = date(2024, 1, 15)
        expected_filename = "health_monitor_20240115.log"
        
        log_path = self.log_manager._get_log_file_path(test_date)
        
        self.assertEqual(log_path.name, expected_filename)
        self.assertEqual(log_path.parent, Path(self.temp_dir))
    
    def test_log_status_change(self):
        """Test logging a status change."""
        with patch('health_monitor.services.log_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = self.test_timestamp
            
            self.log_manager.log_status_change(
                target="test-website",
                target_type="website",
                old_status="up",
                new_status="down",
                details="Connection timeout"
            )
        
        # Verify log file was created and contains correct data
        log_file_path = self.log_manager._get_log_file_path(self.test_timestamp.date())
        self.assertTrue(log_file_path.exists())
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_line = f.read().strip()
            log_data = json.loads(log_line)
        
        self.assertEqual(log_data["timestamp"], self.test_timestamp.isoformat())
        self.assertEqual(log_data["target_name"], "test-website")
        self.assertEqual(log_data["target_type"], "website")
        self.assertEqual(log_data["status_change"], "up->down")
        self.assertEqual(log_data["details"], "Connection timeout")
    
    def test_write_log_entry(self):
        """Test writing a log entry to file."""
        self.log_manager._write_log_entry(self.test_log_entry)
        
        # Verify log file was created and contains correct data
        log_file_path = self.log_manager._get_log_file_path(self.test_timestamp.date())
        self.assertTrue(log_file_path.exists())
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_line = f.read().strip()
            log_data = json.loads(log_line)
        
        self.assertEqual(log_data["timestamp"], self.test_timestamp.isoformat())
        self.assertEqual(log_data["target_name"], "test-website")
        self.assertEqual(log_data["target_type"], "website")
        self.assertEqual(log_data["status_change"], "up->down")
        self.assertEqual(log_data["details"], "Connection timeout")
    
    def test_write_multiple_log_entries(self):
        """Test writing multiple log entries to the same file."""
        # Create second log entry
        second_entry = LogEntry(
            timestamp=datetime(2024, 1, 15, 11, 0, 0),
            target_name="test-database",
            target_type="database",
            status_change="down->up",
            details="Connection restored"
        )
        
        # Write both entries
        self.log_manager._write_log_entry(self.test_log_entry)
        self.log_manager._write_log_entry(second_entry)
        
        # Verify both entries are in the file
        log_file_path = self.log_manager._get_log_file_path(self.test_timestamp.date())
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        
        # Verify first entry
        first_data = json.loads(lines[0].strip())
        self.assertEqual(first_data["target_name"], "test-website")
        
        # Verify second entry
        second_data = json.loads(lines[1].strip())
        self.assertEqual(second_data["target_name"], "test-database")
    
    def test_get_daily_log_existing_file(self):
        """Test retrieving daily log entries from existing file."""
        # Write test entry
        self.log_manager._write_log_entry(self.test_log_entry)
        
        # Retrieve entries
        entries = self.log_manager.get_daily_log(self.test_timestamp.date())
        
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.timestamp, self.test_timestamp)
        self.assertEqual(entry.target_name, "test-website")
        self.assertEqual(entry.target_type, "website")
        self.assertEqual(entry.status_change, "up->down")
        self.assertEqual(entry.details, "Connection timeout")
    
    def test_get_daily_log_nonexistent_file(self):
        """Test retrieving daily log entries from non-existent file."""
        future_date = date(2025, 12, 31)
        entries = self.log_manager.get_daily_log(future_date)
        
        self.assertEqual(len(entries), 0)
    
    def test_get_daily_log_with_invalid_json(self):
        """Test retrieving daily log entries with invalid JSON lines."""
        log_file_path = self.log_manager._get_log_file_path(self.test_timestamp.date())
        
        # Write valid and invalid entries
        with open(log_file_path, 'w', encoding='utf-8') as f:
            # Valid entry
            valid_data = {
                "timestamp": self.test_timestamp.isoformat(),
                "target_name": "test-website",
                "target_type": "website",
                "status_change": "up->down",
                "details": "Connection timeout"
            }
            f.write(json.dumps(valid_data) + '\n')
            
            # Invalid JSON
            f.write('invalid json line\n')
            
            # Another valid entry
            valid_data2 = {
                "timestamp": self.test_timestamp.isoformat(),
                "target_name": "test-database",
                "target_type": "database",
                "status_change": "down->up",
                "details": "Connection restored"
            }
            f.write(json.dumps(valid_data2) + '\n')
        
        # Should return only valid entries
        entries = self.log_manager.get_daily_log(self.test_timestamp.date())
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].target_name, "test-website")
        self.assertEqual(entries[1].target_name, "test-database")
    
    def test_get_recent_logs(self):
        """Test retrieving recent log entries from multiple days."""
        # Create entries for different days
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)
        
        # Entry for today
        today_entry = LogEntry(
            timestamp=datetime.combine(today, datetime.min.time()),
            target_name="today-target",
            target_type="website",
            status_change="up->down",
            details="Today's issue"
        )
        
        # Entry for yesterday
        yesterday_entry = LogEntry(
            timestamp=datetime.combine(yesterday, datetime.min.time()),
            target_name="yesterday-target",
            target_type="database",
            status_change="down->up",
            details="Yesterday's recovery"
        )
        
        # Write entries
        self.log_manager._write_log_entry(today_entry)
        self.log_manager._write_log_entry(yesterday_entry)
        
        # Get recent logs (2 days)
        recent_logs = self.log_manager.get_recent_logs(days=2)
        
        # Should be sorted by timestamp (newest first)
        self.assertEqual(len(recent_logs), 2)
        self.assertEqual(recent_logs[0].target_name, "today-target")
        self.assertEqual(recent_logs[1].target_name, "yesterday-target")
    
    def test_cleanup_old_logs(self):
        """Test cleanup of old log files."""
        # Create log files for different dates
        old_date = date.fromordinal(date.today().toordinal() - 35)  # 35 days ago
        recent_date = date.fromordinal(date.today().toordinal() - 5)  # 5 days ago
        
        old_log_path = self.log_manager._get_log_file_path(old_date)
        recent_log_path = self.log_manager._get_log_file_path(recent_date)
        
        # Create the log files
        old_log_path.touch()
        recent_log_path.touch()
        
        # Verify both files exist
        self.assertTrue(old_log_path.exists())
        self.assertTrue(recent_log_path.exists())
        
        # Cleanup with 30 days retention
        self.log_manager.cleanup_old_logs(retention_days=30)
        
        # Old file should be removed, recent file should remain
        self.assertFalse(old_log_path.exists())
        self.assertTrue(recent_log_path.exists())
    
    def test_cleanup_old_logs_invalid_filename(self):
        """Test cleanup with invalid log filenames."""
        # Create file with invalid name format
        invalid_file = Path(self.temp_dir) / "invalid_log_file.log"
        invalid_file.touch()
        
        # Should not raise exception
        self.log_manager.cleanup_old_logs(retention_days=30)
        
        # Invalid file should still exist (not processed)
        self.assertTrue(invalid_file.exists())
    
    @patch('builtins.print')
    def test_display_log_entries_empty(self, mock_print):
        """Test displaying empty log entries."""
        self.log_manager.display_log_entries([])
        
        mock_print.assert_called_once_with("No log entries found.")
    
    @patch('builtins.print')
    def test_display_log_entries_with_data(self, mock_print):
        """Test displaying log entries with data."""
        entries = [self.test_log_entry]
        
        self.log_manager.display_log_entries(entries)
        
        # Verify print was called with expected format
        calls = mock_print.call_args_list
        self.assertGreater(len(calls), 0)
        
        # Check that timestamp and target info are in the output
        output_text = ' '.join([str(call[0][0]) for call in calls])
        self.assertIn("test-website", output_text)
        self.assertIn("website", output_text)
        self.assertIn("up->down", output_text)
    
    @patch('builtins.print')
    def test_display_log_entries_with_limit(self, mock_print):
        """Test displaying log entries with limit."""
        # Create multiple entries
        entries = []
        for i in range(5):
            entry = LogEntry(
                timestamp=datetime(2024, 1, 15, 10, i, 0),
                target_name=f"target-{i}",
                target_type="website",
                status_change="up->down",
                details=f"Issue {i}"
            )
            entries.append(entry)
        
        # Display with limit of 3
        self.log_manager.display_log_entries(entries, limit=3)
        
        # Should only display 3 entries
        calls = mock_print.call_args_list
        output_text = ' '.join([str(call[0][0]) for call in calls])
        
        # Should contain first 3 targets
        self.assertIn("target-0", output_text)
        self.assertIn("target-1", output_text)
        self.assertIn("target-2", output_text)
        
        # Should not contain last 2 targets
        self.assertNotIn("target-3", output_text)
        self.assertNotIn("target-4", output_text)


if __name__ == '__main__':
    unittest.main()