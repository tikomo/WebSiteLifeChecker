"""
Database health checker implementation.
"""
import psycopg2
from datetime import datetime
import time
import logging

from health_monitor.models.data_models import DatabaseTarget, HealthStatus
from health_monitor.services.retry_handler import RetryHandler, RetryConfig, CircuitBreaker, CircuitBreakerOpenException


class DatabaseHealthChecker:
    """Handles health checks for PostgreSQL database targets."""
    
    def __init__(self, enable_retry: bool = True, enable_circuit_breaker: bool = True):
        """Initialize the database health checker."""
        self.logger = logging.getLogger(__name__)
        self.enable_retry = enable_retry
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Configure retry handler for transient database failures
        if self.enable_retry:
            retry_config = RetryConfig(
                max_attempts=3,
                base_delay=2.0,  # Slightly longer delay for DB connections
                max_delay=15.0,
                backoff_multiplier=2.0,
                jitter=True,
                retryable_exceptions=[
                    psycopg2.OperationalError,  # Connection issues, timeouts
                    psycopg2.InterfaceError,    # Connection interface issues
                ]
            )
            self.retry_handler = RetryHandler(retry_config)
        
        # Circuit breakers per target to prevent cascading failures
        self.circuit_breakers = {} if self.enable_circuit_breaker else None
    
    def check_database(self, target: DatabaseTarget) -> HealthStatus:
        """
        Perform health check on a PostgreSQL database target with retry and circuit breaker support.
        
        Args:
            target: DatabaseTarget instance containing connection information
            
        Returns:
            HealthStatus instance with check results
        """
        timestamp = datetime.now()
        
        # Get or create circuit breaker for this target
        circuit_breaker = None
        if self.enable_circuit_breaker:
            if target.name not in self.circuit_breakers:
                self.circuit_breakers[target.name] = CircuitBreaker(
                    failure_threshold=3,  # Lower threshold for DB connections
                    recovery_timeout=120.0,  # Longer recovery time for DB issues
                    expected_exception=psycopg2.Error
                )
            circuit_breaker = self.circuit_breakers[target.name]
        
        try:
            # Execute with circuit breaker and retry logic
            if circuit_breaker and self.enable_retry:
                # Use both circuit breaker and retry
                result = circuit_breaker.call(
                    self.retry_handler.execute_with_retry,
                    self._perform_database_connection,
                    target
                )
            elif circuit_breaker:
                # Use only circuit breaker
                result = circuit_breaker.call(self._perform_database_connection, target)
            elif self.enable_retry:
                # Use only retry
                result = self.retry_handler.execute_with_retry(self._perform_database_connection, target)
            else:
                # No error handling enhancements
                result = self._perform_database_connection(target)
            
            return result
            
        except Exception as e:
            # Create error status for any unhandled exceptions
            return HealthStatus(
                target_name=target.name,
                is_healthy=False,
                response_time=0.0,
                error_message=f"Database health check failed: {str(e)}",
                timestamp=timestamp
            )
    
    def _perform_database_connection(self, target: DatabaseTarget) -> HealthStatus:
        """
        Perform the actual database connection test.
        
        Args:
            target: DatabaseTarget instance
            
        Returns:
            HealthStatus instance with check results
        """
        start_time = time.time()
        timestamp = datetime.now()
        connection = None
        
        try:
            # Build connection string
            connection_params = {
                'host': target.host,
                'port': target.port,
                'database': target.database,
                'user': target.username,
                'password': target.password,
                'sslmode': target.sslmode,
                'connect_timeout': 5  # 5 second timeout for connection
            }
            
            # Establish connection
            connection = psycopg2.connect(**connection_params)
            
            # Test the connection with a simple query
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            response_time = time.time() - start_time
            
            # Verify we got expected result
            if result and result[0] == 1:
                return HealthStatus(
                    target_name=target.name,
                    is_healthy=True,
                    response_time=response_time,
                    error_message=None,
                    timestamp=timestamp
                )
            else:
                return HealthStatus(
                    target_name=target.name,
                    is_healthy=False,
                    response_time=response_time,
                    error_message="Database query returned unexpected result",
                    timestamp=timestamp
                )
                
        except psycopg2.OperationalError as e:
            response_time = time.time() - start_time
            error_msg = str(e).strip()
            
            # Provide more specific error messages for common issues
            if "timeout expired" in error_msg.lower():
                error_message = f"Connection timeout: {error_msg}"
                self.logger.warning(f"DB timeout for {target.name}: {error_message}")
            elif "could not connect" in error_msg.lower():
                error_message = f"Connection failed: {error_msg}"
                self.logger.warning(f"DB connection failed for {target.name}: {error_message}")
            elif "authentication failed" in error_msg.lower():
                error_message = f"Authentication failed: {error_msg}"
                self.logger.error(f"DB auth failed for {target.name}: {error_message}")
                # Don't retry authentication failures
                raise psycopg2.DatabaseError(error_message)
            elif "ssl" in error_msg.lower():
                error_message = f"SSL connection error: {error_msg}"
                self.logger.warning(f"DB SSL error for {target.name}: {error_message}")
            else:
                error_message = f"Database operational error: {error_msg}"
                self.logger.warning(f"DB operational error for {target.name}: {error_message}")
            
            # Raise the exception to trigger retry logic
            raise psycopg2.OperationalError(error_message)
            
        except psycopg2.DatabaseError as e:
            response_time = time.time() - start_time
            error_msg = f"Database error: {str(e)}"
            self.logger.error(f"DB error for {target.name}: {error_msg}")
            # Database errors usually shouldn't be retried
            raise psycopg2.DatabaseError(error_msg)
            
        except psycopg2.Error as e:
            response_time = time.time() - start_time
            error_msg = f"PostgreSQL error: {str(e)}"
            self.logger.error(f"PostgreSQL error for {target.name}: {error_msg}")
            raise e
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected DB error for {target.name}: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            # Always close the connection if it was established
            if connection:
                try:
                    connection.close()
                except Exception:
                    # Ignore errors when closing connection
                    pass