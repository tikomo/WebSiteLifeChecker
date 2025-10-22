"""
Health check engine implementation with parallel execution support.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any
import threading
import time

from health_monitor.models.data_models import WebsiteTarget, DatabaseTarget, HealthStatus
from health_monitor.services.interfaces import HealthCheckEngineInterface
from health_monitor.services.website_checker import WebsiteHealthChecker
from health_monitor.services.database_checker import DatabaseHealthChecker
from health_monitor.services.log_manager import LogManager
from health_monitor.services.self_monitor import SelfMonitor


class HealthCheckEngine(HealthCheckEngineInterface):
    """
    Orchestrates health checks for multiple targets with parallel execution.
    """
    
    def __init__(self, max_workers: int = 10, log_manager: Optional[LogManager] = None,
                 enable_retry: bool = True, enable_circuit_breaker: bool = True,
                 enable_self_monitoring: bool = True, log_all_checks: bool = False):
        """
        Initialize the health check engine.
        
        Args:
            max_workers: Maximum number of concurrent health check threads
            log_manager: LogManager instance for status change logging
            enable_retry: Whether to enable retry logic with exponential backoff
            enable_circuit_breaker: Whether to enable circuit breaker pattern
            enable_self_monitoring: Whether to enable self-monitoring and diagnostics
            log_all_checks: Whether to log all health check results (not just status changes)
        """
        self.max_workers = max_workers
        self.website_checker = WebsiteHealthChecker(
            enable_retry=enable_retry,
            enable_circuit_breaker=enable_circuit_breaker
        )
        self.database_checker = DatabaseHealthChecker(
            enable_retry=enable_retry,
            enable_circuit_breaker=enable_circuit_breaker
        )
        self.log_manager = log_manager or LogManager()
        self.log_all_checks = log_all_checks
        self._lock = threading.Lock()
        self._current_statuses: Dict[str, HealthStatus] = {}
        self._previous_statuses: Dict[str, bool] = {}  # Track previous healthy status
        
        # Self-monitoring
        self.self_monitor = SelfMonitor() if enable_self_monitoring else None
        if self.self_monitor:
            self.self_monitor.start_monitoring()
        
    def check_website(self, target: WebsiteTarget) -> HealthStatus:
        """
        Perform health check on a website target.
        
        Args:
            target: WebsiteTarget instance
            
        Returns:
            HealthStatus instance with check results
        """
        return self.website_checker.check_website(target)
    
    def check_database(self, target: DatabaseTarget) -> HealthStatus:
        """
        Perform health check on a database target.
        
        Args:
            target: DatabaseTarget instance
            
        Returns:
            HealthStatus instance with check results
        """
        return self.database_checker.check_database(target)
    
    def run_all_checks(self, website_targets: List[WebsiteTarget] = None, 
                      database_targets: List[DatabaseTarget] = None) -> Dict[str, HealthStatus]:
        """
        Run health checks on all configured targets in parallel.
        
        Args:
            website_targets: List of website targets to check
            database_targets: List of database targets to check
            
        Returns:
            Dictionary mapping target names to their health status
        """
        if website_targets is None:
            website_targets = []
        if database_targets is None:
            database_targets = []
            
        results = {}
        
        # Create a list of all check tasks
        check_tasks = []
        
        # Add website check tasks
        for target in website_targets:
            check_tasks.append(('website', target))
            
        # Add database check tasks  
        for target in database_targets:
            check_tasks.append(('database', target))
        
        if not check_tasks:
            return results
        
        # Update self-monitoring with target count
        if self.self_monitor:
            self.self_monitor.update_target_count(len(check_tasks))
        
        # Execute all checks in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_target = {}
            
            for check_type, target in check_tasks:
                if check_type == 'website':
                    future = executor.submit(self.check_website, target)
                else:  # database
                    future = executor.submit(self.check_database, target)
                    
                future_to_target[future] = (check_type, target)
            
            # Collect results as they complete
            for future in as_completed(future_to_target):
                check_type, target = future_to_target[future]
                
                try:
                    health_status = future.result()
                    results[target.name] = health_status
                    
                    # Record metrics for self-monitoring
                    if self.self_monitor:
                        self.self_monitor.record_health_check(
                            success=health_status.is_healthy,
                            response_time=health_status.response_time
                        )
                    
                except Exception as e:
                    # Create error status if check failed unexpectedly
                    from datetime import datetime
                    error_status = HealthStatus(
                        target_name=target.name,
                        is_healthy=False,
                        response_time=0.0,
                        error_message=f"Health check execution failed: {str(e)}",
                        timestamp=datetime.now()
                    )
                    results[target.name] = error_status
                    
                    # Record failed check for self-monitoring
                    if self.self_monitor:
                        self.self_monitor.record_health_check(success=False, response_time=0.0)
                        self.self_monitor.add_diagnostic(
                            "HealthCheckEngine", "ERROR", 
                            f"Health check execution failed for {target.name}: {str(e)}"
                        )
        
        # Update internal status tracking and log status changes
        with self._lock:
            self._update_statuses_and_log_changes(results, website_targets, database_targets)
            
            # Update circuit breaker count for self-monitoring
            if self.self_monitor:
                open_breakers = 0
                if hasattr(self.website_checker, 'circuit_breakers') and self.website_checker.circuit_breakers:
                    open_breakers += sum(1 for cb in self.website_checker.circuit_breakers.values() if cb.state == 'OPEN')
                if hasattr(self.database_checker, 'circuit_breakers') and self.database_checker.circuit_breakers:
                    open_breakers += sum(1 for cb in self.database_checker.circuit_breakers.values() if cb.state == 'OPEN')
                self.self_monitor.update_circuit_breaker_count(open_breakers)
            
        return results
    
    def get_current_statuses(self) -> Dict[str, HealthStatus]:
        """
        Get the current health statuses of all targets.
        
        Returns:
            Dictionary mapping target names to their latest health status
        """
        with self._lock:
            return self._current_statuses.copy()
    
    def get_target_status(self, target_name: str) -> HealthStatus:
        """
        Get the current health status of a specific target.
        
        Args:
            target_name: Name of the target to get status for
            
        Returns:
            HealthStatus instance or None if target not found
        """
        with self._lock:
            return self._current_statuses.get(target_name)
    
    def _update_statuses_and_log_changes(self, new_results: Dict[str, HealthStatus], 
                                        website_targets: List[WebsiteTarget], 
                                        database_targets: List[DatabaseTarget]):
        """
        Update internal status tracking and log any status changes.
        
        Args:
            new_results: New health check results
            website_targets: List of website targets checked
            database_targets: List of database targets checked
        """
        # Create target type mapping
        target_types = {}
        for target in website_targets:
            target_types[target.name] = 'website'
        for target in database_targets:
            target_types[target.name] = 'database'
        
        # Check for status changes and log them
        for target_name, new_status in new_results.items():
            previous_healthy = self._previous_statuses.get(target_name)
            current_healthy = new_status.is_healthy
            
            # Log status change if there was a previous status and it changed, or if this is the first check
            if (previous_healthy is not None and previous_healthy != current_healthy) or previous_healthy is None:
                old_status = "up" if previous_healthy else ("unknown" if previous_healthy is None else "down")
                new_status_str = "up" if current_healthy else "down"
                target_type = target_types.get(target_name, 'unknown')
                
                details = ""
                if new_status.error_message:
                    details = f"Error: {new_status.error_message}"
                elif current_healthy:
                    details = f"Response time: {new_status.response_time:.2f}s"
                
                self.log_manager.log_status_change(
                    target=target_name,
                    target_type=target_type,
                    old_status=old_status,
                    new_status=new_status_str,
                    details=details
                )
            
            # Update tracking
            self._previous_statuses[target_name] = current_healthy
            
            # Log all health checks if enabled (regardless of status change)
            if self.log_all_checks:
                status_str = "up" if current_healthy else "down"
                target_type = target_types.get(target_name, 'unknown')
                
                self.log_manager.log_health_check(
                    target=target_name,
                    target_type=target_type,
                    status=status_str,
                    response_time=new_status.response_time if current_healthy else None,
                    error_message=new_status.error_message if not current_healthy else ""
                )
        
        # Update current statuses
        self._current_statuses.update(new_results)
    
    def get_status_history(self, days: int = 7) -> List:
        """
        Get status change history from the log manager.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of LogEntry objects
        """
        return self.log_manager.get_recent_logs(days)
    
    def display_recent_changes(self, days: int = 1, limit: int = 20):
        """
        Display recent status changes.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of entries to display
        """
        recent_logs = self.log_manager.get_recent_logs(days)
        self.log_manager.display_log_entries(recent_logs, limit)
    
    def clear_statuses(self):
        """Clear all stored status information."""
        with self._lock:
            self._current_statuses.clear()
            self._previous_statuses.clear()
    
    def get_self_monitoring_data(self) -> Optional[Dict[str, Any]]:
        """Get self-monitoring data if available."""
        if self.self_monitor:
            return self.self_monitor.get_health_summary()
        return None
    
    def export_diagnostics(self, filepath: str):
        """Export diagnostic information to a file."""
        if self.self_monitor:
            self.self_monitor.export_diagnostics(filepath)
        else:
            raise RuntimeError("Self-monitoring is not enabled")
    
    def close(self):
        """Clean up resources used by the health check engine."""
        if self.self_monitor:
            self.self_monitor.stop_monitoring()
        self.website_checker.close()
        # Database checker doesn't need explicit cleanup
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()