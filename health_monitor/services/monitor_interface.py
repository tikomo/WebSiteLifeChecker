"""
Main monitor application interface.
"""
from abc import ABC, abstractmethod


class HealthMonitorInterface(ABC):
    """Interface for the main health monitoring application."""
    
    @abstractmethod
    def start_monitoring(self) -> None:
        """Start the continuous monitoring process."""
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop the monitoring process gracefully."""
        pass
    
    @abstractmethod
    def reload_configuration(self) -> None:
        """Reload configuration without restarting the application."""
        pass
    
    @abstractmethod
    def get_current_status(self) -> dict:
        """Get the current status of all monitored targets."""
        pass