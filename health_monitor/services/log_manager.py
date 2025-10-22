"""
Log Manager for Health Monitor application.
Handles logging of status changes with file-based persistence and daily rotation.
"""
import os
import json
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path

from ..models.data_models import LogEntry


class LogManager:
    """Manages logging of health status changes with file-based persistence."""
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize the LogManager.
        
        Args:
            log_directory: Directory to store log files
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        
    def _get_log_file_path(self, log_date: date = None) -> Path:
        """
        Get the log file path for a specific date.
        
        Args:
            log_date: Date for the log file. Defaults to today.
            
        Returns:
            Path to the log file
        """
        if log_date is None:
            log_date = date.today()
        
        filename = f"health_monitor_{log_date.strftime('%Y%m%d')}.log"
        return self.log_directory / filename
    
    def log_status_change(self, target: str, target_type: str, old_status: str, new_status: str, details: str = "") -> None:
        """
        Log a status change for a monitoring target.
        
        Args:
            target: Name of the monitoring target
            target_type: Type of target ('website' or 'database')
            old_status: Previous status
            new_status: New status
            details: Additional details about the status change
        """
        timestamp = datetime.now()
        status_change = f"{old_status}->{new_status}"
        
        log_entry = LogEntry(
            timestamp=timestamp,
            target_name=target,
            target_type=target_type,
            status_change=status_change,
            details=details
        )
        
        self._write_log_entry(log_entry)
    
    def log_health_check(self, target: str, target_type: str, status: str, response_time: float = None, error_message: str = "") -> None:
        """
        Log a health check result (regardless of status change).
        
        Args:
            target: Name of the monitoring target
            target_type: Type of target ('website' or 'database')
            status: Current status ('up' or 'down')
            response_time: Response time in seconds (if available)
            error_message: Error message (if status is 'down')
        """
        timestamp = datetime.now()
        
        # Build details string
        details = ""
        if status == "up" and response_time is not None:
            details = f"Response time: {response_time:.2f}s"
        elif status == "down" and error_message:
            details = f"Error: {error_message}"
        
        log_entry = LogEntry(
            timestamp=timestamp,
            target_name=target,
            target_type=target_type,
            status_change=status,  # For health checks, we just log the current status
            details=details
        )
        
        self._write_log_entry(log_entry)
    
    def _write_log_entry(self, log_entry: LogEntry) -> None:
        """
        Write a log entry to the appropriate daily log file.
        
        Args:
            log_entry: LogEntry to write
        """
        log_file_path = self._get_log_file_path(log_entry.timestamp.date())
        
        # Convert log entry to JSON format
        log_data = {
            "timestamp": log_entry.timestamp.isoformat(),
            "target_name": log_entry.target_name,
            "target_type": log_entry.target_type,
            "status_change": log_entry.status_change,
            "details": log_entry.details
        }
        
        # Append to log file
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except IOError as e:
            print(f"Error writing to log file {log_file_path}: {e}")
    
    def get_daily_log(self, log_date: date) -> List[LogEntry]:
        """
        Retrieve all log entries for a specific date.
        
        Args:
            log_date: Date to retrieve logs for
            
        Returns:
            List of LogEntry objects for the specified date
        """
        log_file_path = self._get_log_file_path(log_date)
        
        if not log_file_path.exists():
            return []
        
        log_entries = []
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_data = json.loads(line)
                            log_entry = LogEntry(
                                timestamp=datetime.fromisoformat(log_data["timestamp"]),
                                target_name=log_data["target_name"],
                                target_type=log_data["target_type"],
                                status_change=log_data["status_change"],
                                details=log_data["details"]
                            )
                            log_entries.append(log_entry)
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Error parsing log entry: {line}, Error: {e}")
        except IOError as e:
            print(f"Error reading log file {log_file_path}: {e}")
        
        return log_entries
    
    def get_recent_logs(self, days: int = 7) -> List[LogEntry]:
        """
        Get log entries from the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of LogEntry objects from the specified period
        """
        all_logs = []
        current_date = date.today()
        
        for i in range(days):
            log_date = date.fromordinal(current_date.toordinal() - i)
            daily_logs = self.get_daily_log(log_date)
            all_logs.extend(daily_logs)
        
        # Sort by timestamp (newest first)
        all_logs.sort(key=lambda x: x.timestamp, reverse=True)
        return all_logs
    
    def cleanup_old_logs(self, retention_days: int = 30) -> None:
        """
        Remove log files older than the specified retention period.
        
        Args:
            retention_days: Number of days to retain log files
        """
        cutoff_date = date.fromordinal(date.today().toordinal() - retention_days)
        
        for log_file in self.log_directory.glob("health_monitor_*.log"):
            try:
                # Extract date from filename
                date_str = log_file.stem.split('_')[-1]  # health_monitor_YYYYMMDD
                file_date = datetime.strptime(date_str, '%Y%m%d').date()
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    print(f"Removed old log file: {log_file}")
            except (ValueError, IndexError) as e:
                print(f"Error processing log file {log_file}: {e}")
    
    def display_log_entries(self, log_entries: List[LogEntry], limit: Optional[int] = None) -> None:
        """
        Display log entries in a formatted way.
        
        Args:
            log_entries: List of LogEntry objects to display
            limit: Maximum number of entries to display
        """
        if not log_entries:
            print("No log entries found.")
            return
        
        entries_to_show = log_entries[:limit] if limit else log_entries
        
        print(f"\n=== Health Monitor Log Entries ({len(entries_to_show)} entries) ===")
        for entry in entries_to_show:
            timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp_str}] {entry.target_name} ({entry.target_type}): {entry.status_change}")
            if entry.details:
                print(f"  Details: {entry.details}")
        print("=" * 50)