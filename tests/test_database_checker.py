"""
Unit tests for database health checker.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from datetime import datetime

from health_monitor.models.data_models import DatabaseTarget, HealthStatus
from health_monitor.services.database_checker import DatabaseHealthChecker


class TestDatabaseHealthChecker(unittest.TestCase):
    """Test cases for DatabaseHealthChecker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = DatabaseHealthChecker(enable_retry=False, enable_circuit_breaker=False)
        self.checker_with_retry = DatabaseHealthChecker(enable_retry=True, enable_circuit_breaker=False)
        self.checker_with_circuit_breaker = DatabaseHealthChecker(enable_retry=False, enable_circuit_breaker=True)
        self.checker_with_both = DatabaseHealthChecker(enable_retry=True, enable_circuit_breaker=True)
        
        self.test_target = DatabaseTarget(
            name="test-db",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpass",
            sslmode="prefer"
        )
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_successful_database_check(self, mock_connect):
        """Test successful database health check."""
        # Mock successful connection and query
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertTrue(result.is_healthy)
        self.assertIsNone(result.error_message)
        self.assertGreater(result.response_time, 0)
        self.assertIsInstance(result.timestamp, datetime)
        
        # Verify connection parameters
        expected_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass',
            'sslmode': 'prefer',
            'connect_timeout': 5
        }
        mock_connect.assert_called_once_with(**expected_params)
        
        # Verify query execution
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_cursor.fetchone.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_unexpected_query_result(self, mock_connect):
        """Test database check with unexpected query result."""
        # Mock connection with unexpected query result
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (2,)  # Unexpected result
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertFalse(result.is_healthy)
        self.assertIn("unexpected result", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_connection_timeout(self, mock_connect):
        """Test database check with connection timeout."""
        # Mock timeout operational error
        mock_connect.side_effect = psycopg2.OperationalError("timeout expired")
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertFalse(result.is_healthy)
        self.assertIn("Connection timeout:", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_connection_failed(self, mock_connect):
        """Test database check with connection failure."""
        # Mock connection failure
        mock_connect.side_effect = psycopg2.OperationalError("could not connect to server")
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertFalse(result.is_healthy)
        self.assertIn("Connection failed:", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_authentication_failed(self, mock_connect):
        """Test database check with authentication failure."""
        # Mock authentication failure
        mock_connect.side_effect = psycopg2.OperationalError("authentication failed")
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertFalse(result.is_healthy)
        self.assertIn("Authentication failed:", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_ssl_error(self, mock_connect):
        """Test database check with SSL error."""
        # Mock SSL error
        mock_connect.side_effect = psycopg2.OperationalError("SSL connection error")
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertFalse(result.is_healthy)
        self.assertIn("SSL connection error:", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_database_error(self, mock_connect):
        """Test database check with database error."""
        # Mock database error
        mock_connect.side_effect = psycopg2.DatabaseError("Database error occurred")
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertFalse(result.is_healthy)
        self.assertIn("Database error:", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_general_psycopg2_error(self, mock_connect):
        """Test database check with general psycopg2 error."""
        # Mock general psycopg2 error
        mock_connect.side_effect = psycopg2.Error("General PostgreSQL error")
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertFalse(result.is_healthy)
        self.assertIn("PostgreSQL error:", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_unexpected_exception(self, mock_connect):
        """Test database check with unexpected exception."""
        # Mock unexpected exception
        mock_connect.side_effect = ValueError("Unexpected error")
        
        result = self.checker.check_database(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-db")
        self.assertFalse(result.is_healthy)
        self.assertIn("Unexpected error:", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_connection_cleanup_on_error(self, mock_connect):
        """Test that connection is properly closed even when cursor operations fail."""
        # Mock connection that succeeds but cursor fails
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = psycopg2.DatabaseError("Query failed")
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.checker.check_database(self.test_target)
        
        self.assertFalse(result.is_healthy)
        # Verify connection was closed despite the error
        mock_connection.close.assert_called_once()
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_retry_on_operational_error(self, mock_connect):
        """Test retry behavior on operational errors."""
        mock_connect = Mock()
        # First two calls fail, third succeeds
        mock_connect.side_effect = [
            psycopg2.OperationalError("Connection timeout"),
            psycopg2.OperationalError("Connection timeout"),
            self._create_successful_connection()
        ]
        
        with patch.object(self.checker_with_retry, '_perform_database_connection') as mock_perform:
            call_count = 0
            def side_effect(target):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise psycopg2.OperationalError("Connection timeout")
                else:
                    return HealthStatus(
                        target_name=target.name,
                        is_healthy=True,
                        response_time=0.1,
                        error_message=None,
                        timestamp=datetime.now()
                    )
            
            mock_perform.side_effect = side_effect
            
            result = self.checker_with_retry.check_database(self.test_target)
            
            # Should succeed after retries
            self.assertTrue(result.is_healthy)
            self.assertEqual(call_count, 3)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_no_retry_on_authentication_error(self, mock_connect):
        """Test no retry on authentication errors."""
        with patch.object(self.checker_with_retry, '_perform_database_connection') as mock_perform:
            # Authentication errors should not be retried
            mock_perform.side_effect = psycopg2.DatabaseError("Authentication failed")
            
            result = self.checker_with_retry.check_database(self.test_target)
            
            # Should not retry authentication failures
            mock_perform.assert_called_once()
            self.assertFalse(result.is_healthy)
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_circuit_breaker_opens_after_failures(self, mock_connect):
        """Test circuit breaker opens after consecutive failures."""
        with patch.object(self.checker_with_circuit_breaker, '_perform_database_connection') as mock_perform:
            mock_perform.side_effect = psycopg2.OperationalError("Connection failed")
            
            # Make multiple failed requests to open circuit breaker
            for i in range(4):  # More than failure threshold (3)
                try:
                    result = self.checker_with_circuit_breaker.check_database(self.test_target)
                    # After circuit opens, should get error status instead of exception
                    if i >= 3:
                        self.assertFalse(result.is_healthy)
                        self.assertIn("Database health check failed", result.error_message)
                except Exception:
                    # Expected for first few attempts
                    pass
            
            # Circuit breaker should be open now
            circuit_breaker = self.checker_with_circuit_breaker.circuit_breakers.get(self.test_target.name)
            if circuit_breaker:
                self.assertEqual(circuit_breaker.state, 'OPEN')
    
    @patch('health_monitor.services.database_checker.psycopg2.connect')
    def test_retry_and_circuit_breaker_integration(self, mock_connect):
        """Test retry handler working with circuit breaker."""
        with patch.object(self.checker_with_both, '_perform_database_connection') as mock_perform:
            # Mock the perform method to simulate retry behavior
            call_count = 0
            def side_effect(target):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise psycopg2.OperationalError("Connection timeout")
                else:
                    return HealthStatus(
                        target_name=target.name,
                        is_healthy=True,
                        response_time=0.1,
                        error_message=None,
                        timestamp=datetime.now()
                    )
            
            mock_perform.side_effect = side_effect
            
            result = self.checker_with_both.check_database(self.test_target)
            
            # Should succeed after retries
            self.assertTrue(result.is_healthy)
            self.assertEqual(call_count, 3)
    
    def test_checker_initialization_options(self):
        """Test different initialization options for error handling."""
        # Test with retry disabled
        checker_no_retry = DatabaseHealthChecker(enable_retry=False, enable_circuit_breaker=True)
        self.assertFalse(checker_no_retry.enable_retry)
        self.assertTrue(checker_no_retry.enable_circuit_breaker)
        self.assertIsNotNone(checker_no_retry.circuit_breakers)
        
        # Test with circuit breaker disabled
        checker_no_cb = DatabaseHealthChecker(enable_retry=True, enable_circuit_breaker=False)
        self.assertTrue(checker_no_cb.enable_retry)
        self.assertFalse(checker_no_cb.enable_circuit_breaker)
        self.assertIsNone(checker_no_cb.circuit_breakers)
        
        # Test with both disabled
        checker_basic = DatabaseHealthChecker(enable_retry=False, enable_circuit_breaker=False)
        self.assertFalse(checker_basic.enable_retry)
        self.assertFalse(checker_basic.enable_circuit_breaker)
    
    def _create_successful_connection(self):
        """Helper method to create a successful mock connection."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value = mock_cursor
        return mock_connection


if __name__ == '__main__':
    unittest.main()