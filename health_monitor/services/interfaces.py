"""
Base interfaces for the Health Monitor services.
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime

from health_monitor.models.data_models import (
    WebsiteTarget, DatabaseTarget, HealthStatus, LogEntry
)


class ConfigurationManagerInterface(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def load_website_config(self) -> List[WebsiteTarget]:
        """Load website targets from configuration file."""
        pass
    
    @abstractmethod
    def load_database_config(self) -> List[DatabaseTarget]:
        """Load database targets from configuration file."""
        pass
    
    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        """Validate configuration data."""
        pass
    
    @abstractmethod
    def reload_config(self) -> None:
        """Reload configuration from files."""
        pass


class HealthCheckEngineInterface(ABC):
    """Interface for health check operations."""
    
    @abstractmethod
    def check_website(self, target: WebsiteTarget) -> HealthStatus:
        """Perform health check on a website target."""
        pass
    
    @abstractmethod
    def check_database(self, target: DatabaseTarget) -> HealthStatus:
        """Perform health check on a database target."""
        pass
    
    @abstractmethod
    def run_all_checks(self) -> Dict[str, HealthStatus]:
        """Run health checks on all configured targets."""
        pass


class StatusDisplayInterface(ABC):
    """Interface for status display operations."""
    
    @abstractmethod
    def update_display(self, statuses: Dict[str, HealthStatus]) -> None:
        """Update the status display with current health statuses."""
        pass
    
    @abstractmethod
    def show_error(self, target: str, error: str) -> None:
        """Display error message for a specific target."""
        pass
    
    @abstractmethod
    def refresh_ui(self) -> None:
        """Refresh the user interface display."""
        pass


class LogManagerInterface(ABC):
    """Interface for log management operations."""
    
    @abstractmethod
    def log_status_change(self, target: str, old_status: str, new_status: str) -> None:
        """Log a status change event."""
        pass
    
    @abstractmethod
    def get_daily_log(self, date: str) -> List[LogEntry]:
        """Retrieve log entries for a specific date."""
        pass
    
    @abstractmethod
    def cleanup_old_logs(self, retention_days: int) -> None:
        """Clean up old log files based on retention policy."""
        pass