"""
Self-monitoring and diagnostics for the health monitor application.
"""
import psutil
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import os


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    process_count: int
    thread_count: int


@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""
    timestamp: datetime
    uptime_seconds: float
    total_checks_performed: int
    successful_checks: int
    failed_checks: int
    average_response_time: float
    active_targets: int
    circuit_breakers_open: int
    retry_attempts: int


@dataclass
class DiagnosticInfo:
    """Diagnostic information for troubleshooting."""
    timestamp: datetime
    log_level: str
    component: str
    message: str
    details: Optional[Dict[str, Any]] = None


class SelfMonitor:
    """Monitors the health monitor application itself."""
    
    def __init__(self, metrics_retention_hours: int = 24):
        """
        Initialize self-monitoring system.
        
        Args:
            metrics_retention_hours: How long to keep metrics history
        """
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.now()
        self.metrics_retention_hours = metrics_retention_hours
        
        # Metrics storage
        self._system_metrics: List[SystemMetrics] = []
        self._app_metrics: List[ApplicationMetrics] = []
        self._diagnostics: List[DiagnosticInfo] = []
        self._lock = threading.Lock()
        
        # Application counters
        self._total_checks = 0
        self._successful_checks = 0
        self._failed_checks = 0
        self._response_times: List[float] = []
        self._active_targets = 0
        self._circuit_breakers_open = 0
        self._retry_attempts = 0
        
        # Monitoring thread
        self._monitoring_active = False
        self._monitoring_thread = None
        self._monitoring_interval = 30  # seconds
        
        # Health thresholds
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.disk_threshold = 90.0  # %
        self.response_time_threshold = 10.0  # seconds
        
    def start_monitoring(self):
        """Start the self-monitoring thread."""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="SelfMonitor"
        )
        self._monitoring_thread.start()
        self.logger.info("Self-monitoring started")
    
    def stop_monitoring(self):
        """Stop the self-monitoring thread."""
        self._monitoring_active = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
        self.logger.info("Self-monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                
                # Collect application metrics
                app_metrics = self._collect_application_metrics()
                
                # Store metrics
                with self._lock:
                    self._system_metrics.append(system_metrics)
                    self._app_metrics.append(app_metrics)
                    
                    # Clean up old metrics
                    self._cleanup_old_metrics()
                
                # Check for health issues
                self._check_system_health(system_metrics, app_metrics)
                
            except Exception as e:
                self.logger.error(f"Error in self-monitoring loop: {e}")
                self.add_diagnostic("SelfMonitor", "ERROR", f"Monitoring loop error: {e}")
            
            # Wait for next interval
            time.sleep(self._monitoring_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Process info
            current_process = psutil.Process()
            process_count = len(psutil.pids())
            thread_count = current_process.num_threads()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                process_count=process_count,
                thread_count=thread_count
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            # Return default metrics on error
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_free_gb=0.0,
                process_count=0,
                thread_count=0
            )
    
    def _collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate average response time
        avg_response_time = 0.0
        if self._response_times:
            avg_response_time = sum(self._response_times) / len(self._response_times)
        
        return ApplicationMetrics(
            timestamp=datetime.now(),
            uptime_seconds=uptime,
            total_checks_performed=self._total_checks,
            successful_checks=self._successful_checks,
            failed_checks=self._failed_checks,
            average_response_time=avg_response_time,
            active_targets=self._active_targets,
            circuit_breakers_open=self._circuit_breakers_open,
            retry_attempts=self._retry_attempts
        )
    
    def _check_system_health(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Check for system health issues and log warnings."""
        issues = []
        
        # Check CPU usage
        if system_metrics.cpu_percent > self.cpu_threshold:
            issues.append(f"High CPU usage: {system_metrics.cpu_percent:.1f}%")
        
        # Check memory usage
        if system_metrics.memory_percent > self.memory_threshold:
            issues.append(f"High memory usage: {system_metrics.memory_percent:.1f}%")
        
        # Check disk usage
        if system_metrics.disk_usage_percent > self.disk_threshold:
            issues.append(f"High disk usage: {system_metrics.disk_usage_percent:.1f}%")
        
        # Check response times
        if app_metrics.average_response_time > self.response_time_threshold:
            issues.append(f"High response times: {app_metrics.average_response_time:.2f}s")
        
        # Check circuit breakers
        if app_metrics.circuit_breakers_open > 0:
            issues.append(f"Circuit breakers open: {app_metrics.circuit_breakers_open}")
        
        # Log issues
        for issue in issues:
            self.logger.warning(f"Health issue detected: {issue}")
            self.add_diagnostic("HealthCheck", "WARNING", issue)
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.metrics_retention_hours)
        
        # Clean system metrics
        self._system_metrics = [
            m for m in self._system_metrics if m.timestamp > cutoff_time
        ]
        
        # Clean application metrics
        self._app_metrics = [
            m for m in self._app_metrics if m.timestamp > cutoff_time
        ]
        
        # Clean diagnostics
        self._diagnostics = [
            d for d in self._diagnostics if d.timestamp > cutoff_time
        ]
    
    def record_health_check(self, success: bool, response_time: float):
        """Record a health check result."""
        self._total_checks += 1
        if success:
            self._successful_checks += 1
        else:
            self._failed_checks += 1
        
        # Keep only recent response times for average calculation
        self._response_times.append(response_time)
        if len(self._response_times) > 100:  # Keep last 100 measurements
            self._response_times.pop(0)
    
    def update_target_count(self, count: int):
        """Update the count of active monitoring targets."""
        self._active_targets = count
    
    def update_circuit_breaker_count(self, count: int):
        """Update the count of open circuit breakers."""
        self._circuit_breakers_open = count
    
    def record_retry_attempt(self):
        """Record a retry attempt."""
        self._retry_attempts += 1
    
    def add_diagnostic(self, component: str, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add diagnostic information."""
        diagnostic = DiagnosticInfo(
            timestamp=datetime.now(),
            log_level=level,
            component=component,
            message=message,
            details=details
        )
        
        with self._lock:
            self._diagnostics.append(diagnostic)
            
        # Also log to standard logger
        if level == "ERROR":
            self.logger.error(f"[{component}] {message}")
        elif level == "WARNING":
            self.logger.warning(f"[{component}] {message}")
        else:
            self.logger.info(f"[{component}] {message}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system and application metrics."""
        with self._lock:
            latest_system = self._system_metrics[-1] if self._system_metrics else None
            latest_app = self._app_metrics[-1] if self._app_metrics else None
        
        return {
            "system": latest_system.__dict__ if latest_system else None,
            "application": latest_app.__dict__ if latest_app else None,
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
        }
    
    def get_metrics_history(self, hours: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Get metrics history for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            system_history = [
                m.__dict__ for m in self._system_metrics 
                if m.timestamp > cutoff_time
            ]
            app_history = [
                m.__dict__ for m in self._app_metrics 
                if m.timestamp > cutoff_time
            ]
        
        return {
            "system_metrics": system_history,
            "application_metrics": app_history
        }
    
    def get_diagnostics(self, hours: int = 1, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get diagnostic information for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            diagnostics = [
                d.__dict__ for d in self._diagnostics 
                if d.timestamp > cutoff_time and (level is None or d.log_level == level)
            ]
        
        return diagnostics
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of application health."""
        current_metrics = self.get_current_metrics()
        recent_diagnostics = self.get_diagnostics(hours=1)
        
        # Count diagnostic levels
        error_count = len([d for d in recent_diagnostics if d["log_level"] == "ERROR"])
        warning_count = len([d for d in recent_diagnostics if d["log_level"] == "WARNING"])
        
        # Calculate success rate
        success_rate = 0.0
        if self._total_checks > 0:
            success_rate = (self._successful_checks / self._total_checks) * 100
        
        # Determine overall health status
        health_status = "HEALTHY"
        if error_count > 0 or self._circuit_breakers_open > 0:
            health_status = "UNHEALTHY"
        elif warning_count > 5 or success_rate < 95:
            health_status = "DEGRADED"
        
        return {
            "status": health_status,
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
            "success_rate_percent": success_rate,
            "total_checks": self._total_checks,
            "active_targets": self._active_targets,
            "circuit_breakers_open": self._circuit_breakers_open,
            "recent_errors": error_count,
            "recent_warnings": warning_count,
            "current_metrics": current_metrics
        }
    
    def export_diagnostics(self, filepath: str):
        """Export diagnostic information to a file."""
        try:
            diagnostics_data = {
                "export_timestamp": datetime.now().isoformat(),
                "health_summary": self.get_health_summary(),
                "metrics_history": self.get_metrics_history(hours=24),
                "diagnostics": self.get_diagnostics(hours=24)
            }
            
            with open(filepath, 'w') as f:
                json.dump(diagnostics_data, f, indent=2, default=str)
            
            self.logger.info(f"Diagnostics exported to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export diagnostics: {e}")
            raise