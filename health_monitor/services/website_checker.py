"""
Website health checker implementation.
"""
import requests
from datetime import datetime
from typing import Optional
import time
import logging

from health_monitor.models.data_models import WebsiteTarget, HealthStatus
from health_monitor.services.retry_handler import RetryHandler, RetryConfig, CircuitBreaker, CircuitBreakerOpenException


class WebsiteHealthChecker:
    """Handles health checks for website targets."""
    
    def __init__(self, enable_retry: bool = True, enable_circuit_breaker: bool = True):
        """Initialize the website health checker."""
        self.session = requests.Session()
        # Set default headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Health-Monitor/1.0'
        })
        
        self.logger = logging.getLogger(__name__)
        self.enable_retry = enable_retry
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Configure retry handler for transient failures
        if self.enable_retry:
            retry_config = RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                backoff_multiplier=2.0,
                jitter=True,
                retryable_exceptions=[
                    requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError
                ]
            )
            self.retry_handler = RetryHandler(retry_config)
        
        # Circuit breakers per target to prevent cascading failures
        self.circuit_breakers = {} if self.enable_circuit_breaker else None
    
    def check_website(self, target: WebsiteTarget) -> HealthStatus:
        """
        Perform health check on a website target with retry and circuit breaker support.
        
        Args:
            target: WebsiteTarget instance containing URL and configuration
            
        Returns:
            HealthStatus instance with check results
        """
        timestamp = datetime.now()
        
        # Get or create circuit breaker for this target
        circuit_breaker = None
        if self.enable_circuit_breaker:
            if target.name not in self.circuit_breakers:
                self.circuit_breakers[target.name] = CircuitBreaker(
                    failure_threshold=5,
                    recovery_timeout=60.0,
                    expected_exception=requests.exceptions.RequestException
                )
            circuit_breaker = self.circuit_breakers[target.name]
        
        try:
            # Execute with circuit breaker and retry logic
            if circuit_breaker and self.enable_retry:
                # Use both circuit breaker and retry
                result = circuit_breaker.call(
                    self.retry_handler.execute_with_retry,
                    self._perform_http_request,
                    target
                )
            elif circuit_breaker:
                # Use only circuit breaker
                result = circuit_breaker.call(self._perform_http_request, target)
            elif self.enable_retry:
                # Use only retry
                result = self.retry_handler.execute_with_retry(self._perform_http_request, target)
            else:
                # No error handling enhancements
                result = self._perform_http_request(target)
            
            return result
            
        except Exception as e:
            # Create error status for any unhandled exceptions
            return HealthStatus(
                target_name=target.name,
                is_healthy=False,
                response_time=0.0,
                error_message=f"Health check failed: {str(e)}",
                timestamp=timestamp
            )
    
    def _perform_http_request(self, target: WebsiteTarget) -> HealthStatus:
        """
        Perform the actual HTTP request for health checking.
        
        Args:
            target: WebsiteTarget instance
            
        Returns:
            HealthStatus instance with check results
        """
        start_time = time.time()
        timestamp = datetime.now()
        
        try:
            # Perform HTTP GET request with timeout
            response = self.session.get(
                target.url,
                timeout=target.timeout,
                allow_redirects=True
            )
            
            response_time = time.time() - start_time
            
            # Check if status code matches expected
            is_healthy = response.status_code == target.expected_status
            
            if is_healthy:
                return HealthStatus(
                    target_name=target.name,
                    is_healthy=True,
                    response_time=response_time,
                    error_message=None,
                    timestamp=timestamp
                )
            else:
                # Non-2xx status codes should trigger retries for some cases
                if response.status_code >= 500:
                    # Server errors should be retried
                    raise requests.exceptions.HTTPError(
                        f"Server error: {response.status_code} (expected: {target.expected_status})"
                    )
                else:
                    # Client errors (4xx) should not be retried
                    return HealthStatus(
                        target_name=target.name,
                        is_healthy=False,
                        response_time=response_time,
                        error_message=f"Unexpected status code: {response.status_code} (expected: {target.expected_status})",
                        timestamp=timestamp
                    )
                
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            error_msg = f"Request timeout after {target.timeout} seconds"
            self.logger.warning(f"Timeout for {target.name}: {error_msg}")
            raise requests.exceptions.Timeout(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            response_time = time.time() - start_time
            error_msg = f"Connection error: {str(e)}"
            self.logger.warning(f"Connection error for {target.name}: {error_msg}")
            raise requests.exceptions.ConnectionError(error_msg)
            
        except requests.exceptions.HTTPError as e:
            response_time = time.time() - start_time
            error_msg = f"HTTP error: {str(e)}"
            self.logger.warning(f"HTTP error for {target.name}: {error_msg}")
            raise e
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            error_msg = f"Request error: {str(e)}"
            self.logger.warning(f"Request error for {target.name}: {error_msg}")
            raise e
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error for {target.name}: {error_msg}")
            raise Exception(error_msg)
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()