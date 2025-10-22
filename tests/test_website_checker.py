"""
Unit tests for website health checker.
"""
import unittest
from unittest.mock import Mock, patch
import requests
from datetime import datetime

from health_monitor.models.data_models import WebsiteTarget, HealthStatus
from health_monitor.services.website_checker import WebsiteHealthChecker
from health_monitor.services.retry_handler import CircuitBreakerOpenException


class TestWebsiteHealthChecker(unittest.TestCase):
    """Test cases for WebsiteHealthChecker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = WebsiteHealthChecker(enable_retry=False, enable_circuit_breaker=False)
        self.checker_with_retry = WebsiteHealthChecker(enable_retry=True, enable_circuit_breaker=False)
        self.checker_with_circuit_breaker = WebsiteHealthChecker(enable_retry=False, enable_circuit_breaker=True)
        self.checker_with_both = WebsiteHealthChecker(enable_retry=True, enable_circuit_breaker=True)
        
        self.test_target = WebsiteTarget(
            name="test-site",
            url="https://example.com",
            timeout=10,
            expected_status=200
        )
    
    def tearDown(self):
        """Clean up after tests."""
        self.checker.close()
        self.checker_with_retry.close()
        self.checker_with_circuit_breaker.close()
        self.checker_with_both.close()
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_successful_website_check(self, mock_get):
        """Test successful website health check."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.checker.check_website(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-site")
        self.assertTrue(result.is_healthy)
        self.assertIsNone(result.error_message)
        self.assertGreater(result.response_time, 0)
        self.assertIsInstance(result.timestamp, datetime)
        
        # Verify the request was made correctly
        mock_get.assert_called_once_with(
            "https://example.com",
            timeout=10,
            allow_redirects=True
        )
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_wrong_status_code(self, mock_get):
        """Test website check with unexpected status code."""
        # Mock response with wrong status code
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.checker.check_website(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-site")
        self.assertFalse(result.is_healthy)
        self.assertIn("Unexpected status code: 404", result.error_message)
        self.assertGreater(result.response_time, 0)
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_timeout_error(self, mock_get):
        """Test website check with timeout error."""
        # Mock timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        result = self.checker.check_website(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-site")
        self.assertFalse(result.is_healthy)
        self.assertIn("Request timeout after 10 seconds", result.error_message)
        self.assertGreaterEqual(result.response_time, 0)
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_connection_error(self, mock_get):
        """Test website check with connection error."""
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = self.checker.check_website(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-site")
        self.assertFalse(result.is_healthy)
        self.assertIn("Connection error", result.error_message)
        self.assertGreaterEqual(result.response_time, 0)
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_request_exception(self, mock_get):
        """Test website check with general request exception."""
        # Mock general request exception
        mock_get.side_effect = requests.exceptions.RequestException("Request failed")
        
        result = self.checker.check_website(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-site")
        self.assertFalse(result.is_healthy)
        self.assertTrue("Request" in result.error_message or "Health check failed" in result.error_message)
        self.assertGreaterEqual(result.response_time, 0)
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_unexpected_exception(self, mock_get):
        """Test website check with unexpected exception."""
        # Mock unexpected exception
        mock_get.side_effect = ValueError("Unexpected error")
        
        result = self.checker.check_website(self.test_target)
        
        self.assertIsInstance(result, HealthStatus)
        self.assertEqual(result.target_name, "test-site")
        self.assertFalse(result.is_healthy)
        self.assertIn("Unexpected error", result.error_message)
        self.assertGreaterEqual(result.response_time, 0)
    
    def test_custom_expected_status(self):
        """Test website check with custom expected status code."""
        custom_target = WebsiteTarget(
            name="custom-site",
            url="https://example.com/redirect",
            timeout=5,
            expected_status=301
        )
        
        with patch('health_monitor.services.website_checker.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 301
            mock_get.return_value = mock_response
            
            result = self.checker.check_website(custom_target)
            
            self.assertTrue(result.is_healthy)
            self.assertIsNone(result.error_message)
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_retry_on_server_error(self, mock_get):
        """Test retry behavior on server errors (5xx status codes)."""
        # Mock server error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = self.checker_with_retry.check_website(self.test_target)
        
        # Should fail with server error
        self.assertFalse(result.is_healthy)
        self.assertIn("500", result.error_message)
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_no_retry_on_client_error(self, mock_get):
        """Test no retry on client errors (4xx status codes)."""
        # Mock client error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get = Mock(return_value=mock_response)
        
        with patch.object(self.checker_with_retry, '_perform_http_request') as mock_perform:
            mock_perform.return_value = HealthStatus(
                target_name=self.test_target.name,
                is_healthy=False,
                response_time=0.1,
                error_message="Unexpected status code: 404 (expected: 200)",
                timestamp=datetime.now()
            )
            
            result = self.checker_with_retry.check_website(self.test_target)
            
            # Should not retry on client errors
            mock_perform.assert_called_once()
            self.assertFalse(result.is_healthy)
            self.assertIn("404", result.error_message)
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_circuit_breaker_opens_after_failures(self, mock_get):
        """Test circuit breaker opens after consecutive failures."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Make a few failed requests
        for i in range(3):
            result = self.checker_with_circuit_breaker.check_website(self.test_target)
            self.assertFalse(result.is_healthy)
            self.assertIn("Connection error", result.error_message)
    
    @patch('health_monitor.services.website_checker.requests.Session.get')
    def test_retry_and_circuit_breaker_integration(self, mock_get):
        """Test retry handler working with circuit breaker."""
        # Mock timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        result = self.checker_with_both.check_website(self.test_target)
        
        # Should fail with timeout error
        self.assertFalse(result.is_healthy)
        self.assertIn("timeout", result.error_message.lower())
    
    def test_checker_initialization_options(self):
        """Test different initialization options for error handling."""
        # Test with retry disabled
        checker_no_retry = WebsiteHealthChecker(enable_retry=False, enable_circuit_breaker=True)
        self.assertFalse(checker_no_retry.enable_retry)
        self.assertTrue(checker_no_retry.enable_circuit_breaker)
        self.assertIsNotNone(checker_no_retry.circuit_breakers)
        
        # Test with circuit breaker disabled
        checker_no_cb = WebsiteHealthChecker(enable_retry=True, enable_circuit_breaker=False)
        self.assertTrue(checker_no_cb.enable_retry)
        self.assertFalse(checker_no_cb.enable_circuit_breaker)
        self.assertIsNone(checker_no_cb.circuit_breakers)
        
        # Test with both disabled
        checker_basic = WebsiteHealthChecker(enable_retry=False, enable_circuit_breaker=False)
        self.assertFalse(checker_basic.enable_retry)
        self.assertFalse(checker_basic.enable_circuit_breaker)
        
        # Clean up
        checker_no_retry.close()
        checker_no_cb.close()
        checker_basic.close()


if __name__ == '__main__':
    unittest.main()