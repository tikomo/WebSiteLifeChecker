"""
Unit tests for self-monitoring functionality.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import tempfile
import os
import json
from datetime import datetime, timedelta

from health_monitor.services.self_monitor import (
    SelfMonitor, SystemMetrics, ApplicationMetrics, DiagnosticInfo
)


class TestSystemMetrics(unittest.TestCase):
    """Test cases for SystemMetrics dataclass."""
    
    def test_system_metrics_creation(self):
        """Test SystemMetrics creation and attributes."""
        timestamp = datetime.now()
        metrics = SystemMetrics(
            timestamp=timestamp,
            cpu_percent=45.5,
            memory_percent=60.2,
            memory_used_mb=1024.0,
            memory_available_mb=512.0,
            disk_usage_percent=75.0,
            disk_free_gb=50.5,
            process_count=150,
            thread_count=8
        )
        
        self.assertEqual(metrics.timestamp, timestamp)
        self.assertEqual(metrics.cpu_percent, 45.5)
        self.assertEqual(metrics.memory_percent, 60.2)
        self.assertEqual(metrics.memory_used_mb, 1024.0)
        self.assertEqual(metrics.memory_available_mb, 512.0)
        self.assertEqual(metrics.disk_usage_percent, 75.0)
        self.assertEqual(metrics.disk_free_gb, 50.5)
        self.assertEqual(metrics.process_count, 150)
        self.assertEqual(metrics.thread_count, 8)


class TestApplicationMetrics(unittest.TestCase):
    """Test cases for ApplicationMetrics dataclass."""
    
    def test_application_metrics_creation(self):
        """Test ApplicationMetrics creation and attributes."""
        timestamp = datetime.now()
        metrics = ApplicationMetrics(
            timestamp=timestamp,
            uptime_seconds=3600.0,
            total_checks_performed=100,
            successful_checks=95,
            failed_checks=5,
            average_response_time=0.5,
            active_targets=10,
            circuit_breakers_open=1,
            retry_attempts=15
        )
        
        self.assertEqual(metrics.timestamp, timestamp)
        self.assertEqual(metrics.uptime_seconds, 3600.0)
        self.assertEqual(metrics.total_checks_performed, 100)
        self.assertEqual(metrics.successful_checks, 95)
        self.assertEqual(metrics.failed_checks, 5)
        self.assertEqual(metrics.average_response_time, 0.5)
        self.assertEqual(metrics.active_targets, 10)
        self.assertEqual(metrics.circuit_breakers_open, 1)
        self.assertEqual(metrics.retry_attempts, 15)


class TestSelfMonitor(unittest.TestCase):
    """Test cases for SelfMonitor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = SelfMonitor(metrics_retention_hours=1)
    
    def tearDown(self):
        """Clean up after tests."""
        self.monitor.stop_monitoring()
    
    def test_initial_state(self):
        """Test initial state of SelfMonitor."""
        self.assertFalse(self.monitor._monitoring_active)
        self.assertIsNone(self.monitor._monitoring_thread)
        self.assertEqual(self.monitor._total_checks, 0)
        self.assertEqual(self.monitor._successful_checks, 0)
        self.assertEqual(self.monitor._failed_checks, 0)
        self.assertEqual(self.monitor._active_targets, 0)
        self.assertEqual(self.monitor._circuit_breakers_open, 0)
        self.assertEqual(self.monitor._retry_attempts, 0)
    
    def test_record_health_check_success(self):
        """Test recording successful health checks."""
        self.monitor.record_health_check(success=True, response_time=0.5)
        
        self.assertEqual(self.monitor._total_checks, 1)
        self.assertEqual(self.monitor._successful_checks, 1)
        self.assertEqual(self.monitor._failed_checks, 0)
        self.assertIn(0.5, self.monitor._response_times)
    
    def test_record_health_check_failure(self):
        """Test recording failed health checks."""
        self.monitor.record_health_check(success=False, response_time=2.0)
        
        self.assertEqual(self.monitor._total_checks, 1)
        self.assertEqual(self.monitor._successful_checks, 0)
        self.assertEqual(self.monitor._failed_checks, 1)
        self.assertIn(2.0, self.monitor._response_times)
    
    def test_response_times_limit(self):
        """Test response times list is limited to 100 entries."""
        # Add more than 100 response times
        for i in range(150):
            self.monitor.record_health_check(success=True, response_time=float(i))
        
        # Should only keep last 100
        self.assertEqual(len(self.monitor._response_times), 100)
        self.assertEqual(self.monitor._response_times[0], 50.0)  # First kept entry
        self.assertEqual(self.monitor._response_times[-1], 149.0)  # Last entry
    
    def test_update_counters(self):
        """Test updating various counters."""
        self.monitor.update_target_count(5)
        self.monitor.update_circuit_breaker_count(2)
        self.monitor.record_retry_attempt()
        self.monitor.record_retry_attempt()
        
        self.assertEqual(self.monitor._active_targets, 5)
        self.assertEqual(self.monitor._circuit_breakers_open, 2)
        self.assertEqual(self.monitor._retry_attempts, 2)
    
    def test_add_diagnostic(self):
        """Test adding diagnostic information."""
        self.monitor.add_diagnostic("TestComponent", "ERROR", "Test error message")
        
        diagnostics = self.monitor.get_diagnostics(hours=1)
        self.assertEqual(len(diagnostics), 1)
        
        diagnostic = diagnostics[0]
        self.assertEqual(diagnostic["component"], "TestComponent")
        self.assertEqual(diagnostic["log_level"], "ERROR")
        self.assertEqual(diagnostic["message"], "Test error message")
        self.assertIsNone(diagnostic["details"])
    
    def test_add_diagnostic_with_details(self):
        """Test adding diagnostic with details."""
        details = {"error_code": 500, "url": "https://example.com"}
        self.monitor.add_diagnostic("WebChecker", "WARNING", "High response time", details)
        
        diagnostics = self.monitor.get_diagnostics(hours=1)
        diagnostic = diagnostics[0]
        self.assertEqual(diagnostic["details"], details)
    
    @patch('health_monitor.services.self_monitor.psutil.cpu_percent')
    @patch('health_monitor.services.self_monitor.psutil.virtual_memory')
    @patch('health_monitor.services.self_monitor.psutil.disk_usage')
    @patch('health_monitor.services.self_monitor.psutil.pids')
    @patch('health_monitor.services.self_monitor.psutil.Process')
    def test_collect_system_metrics(self, mock_process, mock_pids, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection."""
        # Mock system data
        mock_cpu.return_value = 45.5
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.2
        mock_memory_obj.used = 1024 * 1024 * 1024  # 1GB in bytes
        mock_memory_obj.available = 512 * 1024 * 1024  # 512MB in bytes
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.total = 100 * 1024 * 1024 * 1024  # 100GB
        mock_disk_obj.used = 75 * 1024 * 1024 * 1024   # 75GB
        mock_disk_obj.free = 25 * 1024 * 1024 * 1024   # 25GB
        mock_disk.return_value = mock_disk_obj
        
        mock_pids.return_value = list(range(150))  # 150 processes
        
        mock_process_obj = Mock()
        mock_process_obj.num_threads.return_value = 8
        mock_process.return_value = mock_process_obj
        
        # Collect metrics
        metrics = self.monitor._collect_system_metrics()
        
        # Verify metrics
        self.assertEqual(metrics.cpu_percent, 45.5)
        self.assertEqual(metrics.memory_percent, 60.2)
        self.assertEqual(metrics.memory_used_mb, 1024.0)
        self.assertEqual(metrics.memory_available_mb, 512.0)
        self.assertEqual(metrics.disk_usage_percent, 75.0)
        self.assertAlmostEqual(metrics.disk_free_gb, 25.0, places=1)
        self.assertEqual(metrics.process_count, 150)
        self.assertEqual(metrics.thread_count, 8)
    
    def test_collect_application_metrics(self):
        """Test application metrics collection."""
        # Set up some test data
        self.monitor._total_checks = 100
        self.monitor._successful_checks = 95
        self.monitor._failed_checks = 5
        self.monitor._response_times = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.monitor._active_targets = 10
        self.monitor._circuit_breakers_open = 1
        self.monitor._retry_attempts = 15
        
        metrics = self.monitor._collect_application_metrics()
        
        self.assertGreater(metrics.uptime_seconds, 0)
        self.assertEqual(metrics.total_checks_performed, 100)
        self.assertEqual(metrics.successful_checks, 95)
        self.assertEqual(metrics.failed_checks, 5)
        self.assertEqual(metrics.average_response_time, 0.3)  # Average of [0.1, 0.2, 0.3, 0.4, 0.5]
        self.assertEqual(metrics.active_targets, 10)
        self.assertEqual(metrics.circuit_breakers_open, 1)
        self.assertEqual(metrics.retry_attempts, 15)
    
    def test_get_current_metrics(self):
        """Test getting current metrics."""
        # Add some test data
        self.monitor.record_health_check(success=True, response_time=0.5)
        
        # Mock system metrics collection to avoid psutil dependencies
        with patch.object(self.monitor, '_collect_system_metrics') as mock_system, \
             patch.object(self.monitor, '_collect_application_metrics') as mock_app:
            
            mock_system_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=50.0,
                memory_percent=70.0,
                memory_used_mb=1000.0,
                memory_available_mb=500.0,
                disk_usage_percent=80.0,
                disk_free_gb=20.0,
                process_count=100,
                thread_count=5
            )
            mock_system.return_value = mock_system_metrics
            
            mock_app_metrics = ApplicationMetrics(
                timestamp=datetime.now(),
                uptime_seconds=3600.0,
                total_checks_performed=1,
                successful_checks=1,
                failed_checks=0,
                average_response_time=0.5,
                active_targets=5,
                circuit_breakers_open=0,
                retry_attempts=0
            )
            mock_app.return_value = mock_app_metrics
            
            # Manually add metrics to storage
            self.monitor._system_metrics.append(mock_system_metrics)
            self.monitor._app_metrics.append(mock_app_metrics)
            
            current = self.monitor.get_current_metrics()
            
            self.assertIsNotNone(current["system"])
            self.assertIsNotNone(current["application"])
            self.assertGreater(current["uptime_hours"], 0)
    
    def test_get_health_summary(self):
        """Test getting health summary."""
        # Add some test data
        self.monitor._total_checks = 100
        self.monitor._successful_checks = 95
        self.monitor._failed_checks = 5
        self.monitor._active_targets = 10
        self.monitor._circuit_breakers_open = 0
        
        summary = self.monitor.get_health_summary()
        
        self.assertIn("status", summary)
        self.assertIn("uptime_hours", summary)
        self.assertIn("success_rate_percent", summary)
        self.assertEqual(summary["success_rate_percent"], 95.0)
        self.assertEqual(summary["total_checks"], 100)
        self.assertEqual(summary["active_targets"], 10)
        self.assertEqual(summary["circuit_breakers_open"], 0)
    
    def test_health_status_calculation(self):
        """Test health status calculation logic."""
        # Test HEALTHY status
        self.monitor._total_checks = 100
        self.monitor._successful_checks = 98
        self.monitor._circuit_breakers_open = 0
        
        summary = self.monitor.get_health_summary()
        self.assertEqual(summary["status"], "HEALTHY")
        
        # Test DEGRADED status (low success rate)
        self.monitor._successful_checks = 90  # 90% success rate
        summary = self.monitor.get_health_summary()
        self.assertEqual(summary["status"], "DEGRADED")
        
        # Test UNHEALTHY status (circuit breakers open)
        self.monitor._circuit_breakers_open = 1
        summary = self.monitor.get_health_summary()
        self.assertEqual(summary["status"], "UNHEALTHY")
    
    def test_export_diagnostics(self):
        """Test exporting diagnostics to file."""
        # Add some test data
        self.monitor.record_health_check(success=True, response_time=0.5)
        self.monitor.add_diagnostic("TestComponent", "INFO", "Test message")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Export diagnostics
            self.monitor.export_diagnostics(temp_path)
            
            # Verify file was created and contains expected data
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn("export_timestamp", data)
            self.assertIn("health_summary", data)
            self.assertIn("metrics_history", data)
            self.assertIn("diagnostics", data)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_metrics_cleanup(self):
        """Test old metrics cleanup."""
        # Create old metrics (older than retention period)
        old_time = datetime.now() - timedelta(hours=2)
        recent_time = datetime.now()
        
        old_system_metric = SystemMetrics(
            timestamp=old_time,
            cpu_percent=50.0, memory_percent=60.0, memory_used_mb=1000.0,
            memory_available_mb=500.0, disk_usage_percent=70.0, disk_free_gb=30.0,
            process_count=100, thread_count=5
        )
        
        recent_system_metric = SystemMetrics(
            timestamp=recent_time,
            cpu_percent=45.0, memory_percent=55.0, memory_used_mb=900.0,
            memory_available_mb=600.0, disk_usage_percent=65.0, disk_free_gb=35.0,
            process_count=95, thread_count=4
        )
        
        old_diagnostic = DiagnosticInfo(
            timestamp=old_time,
            log_level="INFO",
            component="Test",
            message="Old message"
        )
        
        recent_diagnostic = DiagnosticInfo(
            timestamp=recent_time,
            log_level="INFO",
            component="Test",
            message="Recent message"
        )
        
        # Add metrics
        self.monitor._system_metrics.extend([old_system_metric, recent_system_metric])
        self.monitor._diagnostics.extend([old_diagnostic, recent_diagnostic])
        
        # Run cleanup
        self.monitor._cleanup_old_metrics()
        
        # Verify old metrics were removed
        self.assertEqual(len(self.monitor._system_metrics), 1)
        self.assertEqual(len(self.monitor._diagnostics), 1)
        self.assertEqual(self.monitor._system_metrics[0].timestamp, recent_time)
        self.assertEqual(self.monitor._diagnostics[0].timestamp, recent_time)


if __name__ == '__main__':
    unittest.main()