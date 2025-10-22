"""
Unit tests for health check engine.
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from health_monitor.models.data_models import WebsiteTarget, DatabaseTarget, HealthStatus
from health_monitor.services.health_check_engine import HealthCheckEngine


class TestHealthCheckEngine(unittest.TestCase):
    """Test cases for HealthCheckEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = HealthCheckEngine(max_workers=2)
        
        self.website_target = WebsiteTarget(
            name="test-website",
            url="https://example.com",
            timeout=10,
            expected_status=200
        )
        
        self.database_target = DatabaseTarget(
            name="test-database",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpass"
        )
    
    def tearDown(self):
        """Clean up after tests."""
        self.engine.close()
    
    @patch('health_monitor.services.health_check_engine.WebsiteHealthChecker.check_website')
    def test_check_website(self, mock_check):
        """Test individual website check."""
        # Mock successful website check
        expected_status = HealthStatus(
            target_name="test-website",
            is_healthy=True,
            response_time=0.5,
            error_message=None,
            timestamp=datetime.now()
        )
        mock_check.return_value = expected_status
        
        result = self.engine.check_website(self.website_target)
        
        self.assertEqual(result, expected_status)
        mock_check.assert_called_once_with(self.website_target)
    
    @patch('health_monitor.services.health_check_engine.DatabaseHealthChecker.check_database')
    def test_check_database(self, mock_check):
        """Test individual database check."""
        # Mock successful database check
        expected_status = HealthStatus(
            target_name="test-database",
            is_healthy=True,
            response_time=0.3,
            error_message=None,
            timestamp=datetime.now()
        )
        mock_check.return_value = expected_status
        
        result = self.engine.check_database(self.database_target)
        
        self.assertEqual(result, expected_status)
        mock_check.assert_called_once_with(self.database_target)
    
    @patch('health_monitor.services.health_check_engine.DatabaseHealthChecker.check_database')
    @patch('health_monitor.services.health_check_engine.WebsiteHealthChecker.check_website')
    def test_run_all_checks_success(self, mock_website_check, mock_database_check):
        """Test running all checks successfully."""
        # Mock successful checks
        website_status = HealthStatus(
            target_name="test-website",
            is_healthy=True,
            response_time=0.5,
            error_message=None,
            timestamp=datetime.now()
        )
        
        database_status = HealthStatus(
            target_name="test-database",
            is_healthy=True,
            response_time=0.3,
            error_message=None,
            timestamp=datetime.now()
        )
        
        mock_website_check.return_value = website_status
        mock_database_check.return_value = database_status
        
        results = self.engine.run_all_checks(
            website_targets=[self.website_target],
            database_targets=[self.database_target]
        )
        
        self.assertEqual(len(results), 2)
        self.assertIn("test-website", results)
        self.assertIn("test-database", results)
        self.assertEqual(results["test-website"], website_status)
        self.assertEqual(results["test-database"], database_status)
        
        # Verify both checks were called
        mock_website_check.assert_called_once_with(self.website_target)
        mock_database_check.assert_called_once_with(self.database_target)
    
    def test_run_all_checks_empty_targets(self):
        """Test running checks with no targets."""
        results = self.engine.run_all_checks(
            website_targets=[],
            database_targets=[]
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(results, {})
    
    def test_run_all_checks_none_targets(self):
        """Test running checks with None targets."""
        results = self.engine.run_all_checks(
            website_targets=None,
            database_targets=None
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(results, {})
    
    @patch('health_monitor.services.health_check_engine.WebsiteHealthChecker.check_website')
    def test_run_all_checks_with_exception(self, mock_website_check):
        """Test running checks when one check raises an exception."""
        # Mock check that raises exception
        mock_website_check.side_effect = Exception("Unexpected error")
        
        results = self.engine.run_all_checks(
            website_targets=[self.website_target],
            database_targets=[]
        )
        
        self.assertEqual(len(results), 1)
        self.assertIn("test-website", results)
        
        error_status = results["test-website"]
        self.assertFalse(error_status.is_healthy)
        self.assertIn("Health check execution failed", error_status.error_message)
        self.assertEqual(error_status.target_name, "test-website")
    
    @patch('health_monitor.services.health_check_engine.WebsiteHealthChecker.check_website')
    def test_get_current_statuses(self, mock_website_check):
        """Test getting current statuses after running checks."""
        # Mock successful check
        website_status = HealthStatus(
            target_name="test-website",
            is_healthy=True,
            response_time=0.5,
            error_message=None,
            timestamp=datetime.now()
        )
        mock_website_check.return_value = website_status
        
        # Run checks to populate statuses
        self.engine.run_all_checks(website_targets=[self.website_target])
        
        # Get current statuses
        current_statuses = self.engine.get_current_statuses()
        
        self.assertEqual(len(current_statuses), 1)
        self.assertIn("test-website", current_statuses)
        self.assertEqual(current_statuses["test-website"], website_status)
    
    @patch('health_monitor.services.health_check_engine.WebsiteHealthChecker.check_website')
    def test_get_target_status(self, mock_website_check):
        """Test getting status for a specific target."""
        # Mock successful check
        website_status = HealthStatus(
            target_name="test-website",
            is_healthy=True,
            response_time=0.5,
            error_message=None,
            timestamp=datetime.now()
        )
        mock_website_check.return_value = website_status
        
        # Run checks to populate statuses
        self.engine.run_all_checks(website_targets=[self.website_target])
        
        # Get specific target status
        target_status = self.engine.get_target_status("test-website")
        self.assertEqual(target_status, website_status)
        
        # Test non-existent target
        non_existent_status = self.engine.get_target_status("non-existent")
        self.assertIsNone(non_existent_status)
    
    def test_clear_statuses(self):
        """Test clearing all stored statuses."""
        # Manually add a status
        test_status = HealthStatus(
            target_name="test",
            is_healthy=True,
            response_time=0.1,
            error_message=None,
            timestamp=datetime.now()
        )
        
        with self.engine._lock:
            self.engine._current_statuses["test"] = test_status
        
        # Verify status exists
        self.assertEqual(len(self.engine.get_current_statuses()), 1)
        
        # Clear statuses
        self.engine.clear_statuses()
        
        # Verify statuses are cleared
        self.assertEqual(len(self.engine.get_current_statuses()), 0)
    
    def test_context_manager(self):
        """Test using engine as context manager."""
        with HealthCheckEngine() as engine:
            self.assertIsInstance(engine, HealthCheckEngine)
        # Engine should be closed after exiting context


if __name__ == '__main__':
    unittest.main()