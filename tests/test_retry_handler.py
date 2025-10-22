"""
Unit tests for retry handler and circuit breaker functionality.
"""
import unittest
from unittest.mock import Mock, patch
import time
import requests
import psycopg2

from health_monitor.services.retry_handler import (
    RetryHandler, RetryConfig, CircuitBreaker, CircuitBreakerOpenException
)


class TestRetryConfig(unittest.TestCase):
    """Test cases for RetryConfig."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        self.assertEqual(config.max_attempts, 3)
        self.assertEqual(config.base_delay, 1.0)
        self.assertEqual(config.max_delay, 30.0)
        self.assertEqual(config.backoff_multiplier, 2.0)
        self.assertTrue(config.jitter)
        self.assertEqual(config.retryable_exceptions, [])
    
    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=10.0,
            backoff_multiplier=1.5,
            jitter=False,
            retryable_exceptions=[ValueError, TypeError]
        )
        
        self.assertEqual(config.max_attempts, 5)
        self.assertEqual(config.base_delay, 0.5)
        self.assertEqual(config.max_delay, 10.0)
        self.assertEqual(config.backoff_multiplier, 1.5)
        self.assertFalse(config.jitter)
        self.assertEqual(config.retryable_exceptions, [ValueError, TypeError])


class TestRetryHandler(unittest.TestCase):
    """Test cases for RetryHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,  # Short delay for tests
            max_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False,  # Disable jitter for predictable tests
            retryable_exceptions=[ValueError, requests.exceptions.ConnectionError]
        )
        self.handler = RetryHandler(self.config)
    
    def test_successful_execution_no_retry(self):
        """Test successful function execution without retries."""
        mock_func = Mock(return_value="success")
        
        result = self.handler.execute_with_retry(mock_func, "arg1", kwarg1="value1")
        
        self.assertEqual(result, "success")
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_retry_on_retryable_exception(self):
        """Test retry behavior on retryable exceptions."""
        mock_func = Mock()
        mock_func.side_effect = [ValueError("error1"), ValueError("error2"), "success"]
        
        start_time = time.time()
        result = self.handler.execute_with_retry(mock_func)
        end_time = time.time()
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        # Should have delays between attempts
        self.assertGreater(end_time - start_time, 0.2)  # At least 0.1 + 0.2 seconds delay
    
    def test_no_retry_on_non_retryable_exception(self):
        """Test no retry on non-retryable exceptions."""
        mock_func = Mock(side_effect=TypeError("not retryable"))
        
        with self.assertRaises(TypeError):
            self.handler.execute_with_retry(mock_func)
        
        mock_func.assert_called_once()
    
    def test_max_attempts_reached(self):
        """Test behavior when max attempts are reached."""
        mock_func = Mock(side_effect=ValueError("persistent error"))
        
        with self.assertRaises(ValueError) as context:
            self.handler.execute_with_retry(mock_func)
        
        self.assertEqual(str(context.exception), "persistent error")
        self.assertEqual(mock_func.call_count, 3)
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        # Test delay calculation without jitter
        delay0 = self.handler._calculate_delay(0)
        delay1 = self.handler._calculate_delay(1)
        delay2 = self.handler._calculate_delay(2)
        
        self.assertEqual(delay0, 0.1)  # base_delay
        self.assertEqual(delay1, 0.2)  # base_delay * 2^1
        self.assertEqual(delay2, 0.4)  # base_delay * 2^2
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        # Test with high attempt number
        delay = self.handler._calculate_delay(10)
        self.assertEqual(delay, 1.0)  # Should be capped at max_delay
    
    def test_jitter_enabled(self):
        """Test jitter adds randomness to delays."""
        config_with_jitter = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            jitter=True
        )
        handler_with_jitter = RetryHandler(config_with_jitter)
        
        # Calculate multiple delays and check they're different
        delays = [handler_with_jitter._calculate_delay(0) for _ in range(10)]
        
        # Should have some variation due to jitter
        self.assertGreater(len(set(delays)), 1)
        # All delays should be positive
        self.assertTrue(all(d > 0 for d in delays))


class TestCircuitBreaker(unittest.TestCase):
    """Test cases for CircuitBreaker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=0.1,  # Short timeout for tests
            expected_exception=ValueError
        )
    
    def test_initial_state_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        self.assertEqual(self.circuit_breaker.state, 'CLOSED')
        self.assertEqual(self.circuit_breaker.failure_count, 0)
    
    def test_successful_calls_keep_circuit_closed(self):
        """Test successful calls keep circuit in CLOSED state."""
        mock_func = Mock(return_value="success")
        
        for _ in range(5):
            result = self.circuit_breaker.call(mock_func)
            self.assertEqual(result, "success")
        
        self.assertEqual(self.circuit_breaker.state, 'CLOSED')
        self.assertEqual(self.circuit_breaker.failure_count, 0)
    
    def test_failures_increment_count(self):
        """Test failures increment failure count."""
        mock_func = Mock(side_effect=ValueError("error"))
        
        # First two failures should not open circuit
        for i in range(2):
            with self.assertRaises(ValueError):
                self.circuit_breaker.call(mock_func)
            self.assertEqual(self.circuit_breaker.failure_count, i + 1)
            self.assertEqual(self.circuit_breaker.state, 'CLOSED')
    
    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold is reached."""
        mock_func = Mock(side_effect=ValueError("error"))
        
        # Reach failure threshold
        for _ in range(3):
            with self.assertRaises(ValueError):
                self.circuit_breaker.call(mock_func)
        
        self.assertEqual(self.circuit_breaker.state, 'OPEN')
        self.assertEqual(self.circuit_breaker.failure_count, 3)
    
    def test_open_circuit_rejects_calls(self):
        """Test open circuit rejects calls immediately."""
        mock_func = Mock(side_effect=ValueError("error"))
        
        # Open the circuit
        for _ in range(3):
            with self.assertRaises(ValueError):
                self.circuit_breaker.call(mock_func)
        
        # Next call should be rejected immediately
        with self.assertRaises(CircuitBreakerOpenException):
            self.circuit_breaker.call(mock_func)
        
        # Function should not have been called
        self.assertEqual(mock_func.call_count, 3)
    
    def test_circuit_recovery_after_timeout(self):
        """Test circuit recovery after timeout period."""
        mock_func = Mock(side_effect=ValueError("error"))
        
        # Open the circuit
        for _ in range(3):
            with self.assertRaises(ValueError):
                self.circuit_breaker.call(mock_func)
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Next call should move to HALF_OPEN
        mock_func.side_effect = None
        mock_func.return_value = "success"
        
        result = self.circuit_breaker.call(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(self.circuit_breaker.state, 'CLOSED')
        self.assertEqual(self.circuit_breaker.failure_count, 0)
    
    def test_half_open_success_closes_circuit(self):
        """Test successful call in HALF_OPEN state closes circuit."""
        # Manually set to HALF_OPEN state
        self.circuit_breaker.state = 'HALF_OPEN'
        self.circuit_breaker.failure_count = 3
        
        mock_func = Mock(return_value="success")
        result = self.circuit_breaker.call(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(self.circuit_breaker.state, 'CLOSED')
        self.assertEqual(self.circuit_breaker.failure_count, 0)
    
    def test_half_open_failure_reopens_circuit(self):
        """Test failure in HALF_OPEN state reopens circuit."""
        # Manually set to HALF_OPEN state
        self.circuit_breaker.state = 'HALF_OPEN'
        self.circuit_breaker.failure_count = 2
        
        mock_func = Mock(side_effect=ValueError("error"))
        
        with self.assertRaises(ValueError):
            self.circuit_breaker.call(mock_func)
        
        self.assertEqual(self.circuit_breaker.state, 'OPEN')
        self.assertEqual(self.circuit_breaker.failure_count, 3)
    
    def test_non_expected_exceptions_dont_count(self):
        """Test non-expected exceptions don't count as failures."""
        mock_func = Mock(side_effect=TypeError("not expected"))
        
        with self.assertRaises(TypeError):
            self.circuit_breaker.call(mock_func)
        
        # Should not increment failure count
        self.assertEqual(self.circuit_breaker.failure_count, 0)
        self.assertEqual(self.circuit_breaker.state, 'CLOSED')


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling components."""
    
    def test_retry_with_circuit_breaker_success(self):
        """Test retry handler working with circuit breaker on eventual success."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.05,
            retryable_exceptions=[ValueError]
        )
        retry_handler = RetryHandler(config)
        circuit_breaker = CircuitBreaker(failure_threshold=5, expected_exception=ValueError)
        
        mock_func = Mock()
        mock_func.side_effect = [ValueError("error1"), ValueError("error2"), "success"]
        
        # Execute with both retry and circuit breaker
        result = circuit_breaker.call(retry_handler.execute_with_retry, mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(circuit_breaker.state, 'CLOSED')
    
    def test_circuit_breaker_prevents_excessive_retries(self):
        """Test circuit breaker prevents excessive retries when open."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.05,
            retryable_exceptions=[ValueError]
        )
        retry_handler = RetryHandler(config)
        circuit_breaker = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)
        
        mock_func = Mock(side_effect=ValueError("persistent error"))
        
        # Make multiple calls to open the circuit breaker
        # Each call to circuit_breaker.call counts as one failure
        with self.assertRaises(ValueError):
            circuit_breaker.call(retry_handler.execute_with_retry, mock_func)
        
        with self.assertRaises(ValueError):
            circuit_breaker.call(retry_handler.execute_with_retry, mock_func)
        
        self.assertEqual(circuit_breaker.state, 'OPEN')
        
        # Next call should be rejected immediately
        with self.assertRaises(CircuitBreakerOpenException):
            circuit_breaker.call(retry_handler.execute_with_retry, mock_func)
        
        # Should have made 2 full retry sequences (5 attempts each) = 10 total calls
        self.assertEqual(mock_func.call_count, 10)


if __name__ == '__main__':
    unittest.main()