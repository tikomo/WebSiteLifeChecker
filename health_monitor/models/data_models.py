"""
Core data models for the Health Monitor application.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WebsiteTarget:
    """Represents a website target for health monitoring."""
    name: str
    url: str
    timeout: int = 10
    expected_status: int = 200


@dataclass
class DatabaseTarget:
    """Represents a PostgreSQL database target for health monitoring."""
    name: str
    host: str
    port: int
    database: str
    username: str
    password: str
    sslmode: str = "prefer"


@dataclass
class HealthStatus:
    """Represents the health status of a monitoring target."""
    target_name: str
    is_healthy: bool
    response_time: float
    error_message: Optional[str]
    timestamp: datetime


@dataclass
class LogEntry:
    """Represents a log entry for status changes."""
    timestamp: datetime
    target_name: str
    target_type: str  # 'website' or 'database'
    status_change: str  # 'up->down' or 'down->up'
    details: str