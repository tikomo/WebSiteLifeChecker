"""
Integration tests for the main Health Monitor application.
Tests the complete monitoring workflow and configuration reload functionality.
"""
import unittest
import tempfile
import json
import os
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

from health_monitor.main import HealthMonitorApp
from health_monitor.models.data_models import WebsiteTarget, DatabaseTarget


class TestHealthMonitorIntegration(unittest.TestCase):
    """Integration tests for the Health Monitor application."""
    
    def setUp(self):
        """Set up test environment with temporary directories and config files."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, "config")
        self.log_dir = os.path.join(self.temp_dir, "logs")
        
        os.makedirs(self.config_dir)
        os.makedirs(self.log_dir)
        
        # Create test configuration files
        self._create_test_config_files()
        
        # Initialize the application
        self.app = HealthMonitorApp(
            config_dir=self.config_dir,
            log_dir=self.log_dir,
            check_interval=1  # Short interval for testing
        )
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_config_files(self):
        """Create test configuration files."""
        # Website configuration
        websites_config = {
            "websites": [
                {
                    "name": "Test Website 1",
                    "url": "https://example.com/test1",
                    "timeout": 10,
                    "expected_status": 200
                },
                {
                    "name": "Test Website 2",
                    "url": "https://example.com/test2",
                    "timeout": 5,
                    "expected_status": 200
                }
            ]
        }
        
        with open(os.path.join(self.config_dir, "websites.json"), 'w', encoding='utf-8') as f:
            json.dump(websites_config, f, ensure_ascii=False, indent=2)
        
        # Database configuration (using mock data)
        databases_config = {
            "databases": [
                {
                    "name": "Test Database 1",
                    "host": "localhost",
                    "port": 5432,
                    "database": "test_db",
                    "username": "test_user",
                    "password": "test_pass",
                    "sslmode": "prefer"
                }
            ]
        }
        
        with open(os.path.join(self.config_dir, "databases.json"), 'w', encoding='utf-8') as f:
            json.dump(databases_config, f, ensure_ascii=False, indent=2)
    
    def test_application_initialization(self):
        """Test that the application initializes correctly."""
        # Test initialization
        result = self.app.initialize()
        self.assertTrue(result)
        
        # Check that configuration was loaded
        self.assertEqual(len(self.app.website_targets), 2)
        self.assertEqual(len(self.app.database_targets), 1)
        
        # Check website targets
        self.assertEqual(self.app.website_targets[0].name, "Test Website 1")
        self.assertEqual(self.app.website_targets[0].url, "https://httpbin.org/status/200")
        
        # Check database targets
        self.assertEqual(self.app.database_targets[0].name, "Test Database 1")
        self.assertEqual(self.app.database_targets[0].host, "localhost")
    
    def test_configuration_reload(self):
        """Test configuration reload functionality."""
        # Initialize the application
        self.app.initialize()
        initial_website_count = len(self.app.website_targets)
        
        # Modify configuration file
        updated_config = {
            "websites": [
                {
                    "name": "Updated Website",
                    "url": "https://example.com/updated",
                    "timeout": 15,
                    "expected_status": 200
                },
                {
                    "name": "New Website",
                    "url": "https://example.com/new",
                    "timeout": 10,
                    "expected_status": 200
                },
                {
                    "name": "Another Website",
                    "url": "https://example.com/another",
                    "timeout": 8,
                    "expected_status": 200
                }
            ]
        }
        
        # Wait a moment to ensure file timestamp changes
        time.sleep(0.1)
        
        with open(os.path.join(self.config_dir, "websites.json"), 'w', encoding='utf-8') as f:
            json.dump(updated_config, f, ensure_ascii=False, indent=2)
        
        # Force file modification time to be different
        time.sleep(1.1)  # Ensure file modification time is different
        
        # Trigger configuration reload check
        self.app._check_and_reload_config()
        
        # Verify configuration was reloaded
        self.assertEqual(len(self.app.website_targets), 3)
        self.assertEqual(self.app.website_targets[0].name, "Updated Website")
        self.assertEqual(self.app.website_targets[1].name, "New Website")
        self.assertEqual(self.app.website_targets[2].name, "Another Website")
    
    @patch('health_monitor.services.website_checker.WebsiteHealthChecker.check_website')
    @patch('health_monitor.services.database_checker.DatabaseHealthChecker.check_database')
    def test_complete_monitoring_workflow(self, mock_db_check, mock_web_check):
        """Test the complete monitoring workflow with mocked health checks."""
        from health_monitor.models.data_models import HealthStatus
        from datetime import datetime
        
        # Mock health check responses
        mock_web_check.side_effect = [
            HealthStatus(
                target_name="Test Website 1",
                is_healthy=True,
                response_time=0.5,
                error_message=None,
                timestamp=datetime.now()
            ),
            HealthStatus(
                target_name="Test Website 2",
                is_healthy=False,
                response_time=0.0,
                error_message="HTTP 404 Not Found",
                timestamp=datetime.now()
            )
        ]
        
        mock_db_check.return_value = HealthStatus(
            target_name="Test Database 1",
            is_healthy=False,
            response_time=0.0,
            error_message="Connection refused",
            timestamp=datetime.now()
        )
        
        # Initialize and perform health checks
        self.app.initialize()
        self.app._perform_health_checks()
        
        # Verify health checks were called
        self.assertEqual(mock_web_check.call_count, 2)
        self.assertEqual(mock_db_check.call_count, 1)
        
        # Check status summary
        summary = self.app.get_status_summary()
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['healthy'], 1)
        self.assertEqual(summary['unhealthy'], 2)
    
    def test_graceful_shutdown(self):
        """Test graceful shutdown functionality."""
        # Initialize the application
        self.app.initialize()
        
        # Simulate some health check results
        with patch('health_monitor.services.website_checker.WebsiteHealthChecker.check_website') as mock_web_check:
            from health_monitor.models.data_models import HealthStatus
            from datetime import datetime
            
            mock_web_check.return_value = HealthStatus(
                target_name="Test Website 1",
                is_healthy=True,
                response_time=0.3,
                error_message=None,
                timestamp=datetime.now()
            )
            
            # Perform one health check to populate statuses
            self.app._perform_health_checks()
        
        # Test shutdown
        self.app._shutdown()
        
        # Verify application state
        self.assertFalse(self.app.running)
        self.assertTrue(self.app.shutdown_event.is_set())
    
    def test_configuration_error_handling(self):
        """Test handling of configuration errors."""
        # Create invalid configuration file
        invalid_config = {"invalid": "structure"}
        
        with open(os.path.join(self.config_dir, "websites.json"), 'w', encoding='utf-8') as f:
            json.dump(invalid_config, f)
        
        # Initialize application with invalid config
        result = self.app.initialize()
        
        # Should still initialize but with empty targets
        self.assertTrue(result)  # Initialize should succeed even with config errors
        self.assertEqual(len(self.app.website_targets), 0)
    
    def test_missing_configuration_files(self):
        """Test behavior when configuration files are missing."""
        # Remove configuration files
        os.remove(os.path.join(self.config_dir, "websites.json"))
        os.remove(os.path.join(self.config_dir, "databases.json"))
        
        # Try to initialize
        result = self.app.initialize()
        
        # Should fail to initialize without any targets
        self.assertFalse(result)
        self.assertEqual(len(self.app.website_targets), 0)
        self.assertEqual(len(self.app.database_targets), 0)
    
    def test_status_summary_calculation(self):
        """Test status summary calculation."""
        # Initialize the application
        self.app.initialize()
        
        # Mock some health statuses
        with patch.object(self.app.health_engine, 'get_current_statuses') as mock_get_statuses:
            from health_monitor.models.data_models import HealthStatus
            from datetime import datetime
            
            mock_statuses = {
                "Test Website 1": HealthStatus(
                    target_name="Test Website 1",
                    is_healthy=True,
                    response_time=0.5,
                    error_message=None,
                    timestamp=datetime.now()
                ),
                "Test Website 2": HealthStatus(
                    target_name="Test Website 2",
                    is_healthy=False,
                    response_time=0.0,
                    error_message="Error",
                    timestamp=datetime.now()
                ),
                "Test Database 1": HealthStatus(
                    target_name="Test Database 1",
                    is_healthy=True,
                    response_time=0.1,
                    error_message=None,
                    timestamp=datetime.now()
                )
            }
            
            mock_get_statuses.return_value = mock_statuses
            
            # Get status summary
            summary = self.app.get_status_summary()
            
            # Verify summary
            self.assertEqual(summary['total'], 3)
            self.assertEqual(summary['healthy'], 2)
            self.assertEqual(summary['unhealthy'], 1)
            self.assertEqual(summary['websites'], 2)
            self.assertEqual(summary['databases'], 1)


if __name__ == '__main__':
    unittest.main()