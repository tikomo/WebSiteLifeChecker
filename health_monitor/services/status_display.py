"""
Status display implementation for the Health Monitor application.
Provides console-based status display with colorama for colored output.
"""
import os
import sys
from datetime import datetime
from typing import Dict, Optional
from colorama import init, Fore, Back, Style

from health_monitor.models.data_models import HealthStatus
from health_monitor.services.interfaces import StatusDisplayInterface


class StatusDisplay(StatusDisplayInterface):
    """Console-based status display with colored output."""
    
    def __init__(self):
        """Initialize the status display with colorama."""
        # Initialize colorama for Windows compatibility
        init(autoreset=True)
        self._previous_statuses: Dict[str, HealthStatus] = {}
        self._status_changes: Dict[str, str] = {}
        self._change_tracker = StatusChangeTracker()
        
    def update_display(self, statuses: Dict[str, HealthStatus]) -> None:
        """Update the status display with current health statuses."""
        # Detect status changes before updating display
        self._detect_status_changes(statuses)
        
        # Clear screen for real-time updates
        self._clear_screen()
        
        # Display header
        self._display_header()
        
        # Display each target status
        for target_name, status in statuses.items():
            self._display_target_status(target_name, status)
        
        # Display footer with timestamp
        self._display_footer()
        
        # Update previous statuses for next comparison
        self._previous_statuses = statuses.copy()
    
    def show_error(self, target: str, error: str) -> None:
        """Display error message for a specific target."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_msg = f"[{timestamp}] エラー - {target}: {error}"
        print(f"{Fore.RED}{Style.BRIGHT}{error_msg}{Style.RESET_ALL}")
    
    def refresh_ui(self) -> None:
        """Refresh the user interface display."""
        # Force a screen refresh by printing a newline
        print("", end="", flush=True)
    
    def get_status_changes(self) -> Dict[str, str]:
        """Get current status changes for external use."""
        return self._status_changes.copy()
    
    def get_change_tracker(self) -> 'StatusChangeTracker':
        """Get the status change tracker instance."""
        return self._change_tracker
    
    def _detect_status_changes(self, current_statuses: Dict[str, HealthStatus]) -> None:
        """Detect status changes between current and previous statuses."""
        self._status_changes.clear()
        
        for target_name, current_status in current_statuses.items():
            # Use the enhanced change tracker
            change_indicator = self._change_tracker.track_status_change(target_name, current_status)
            
            if change_indicator:
                self._status_changes[target_name] = change_indicator
    
    def _clear_screen(self) -> None:
        """Clear the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _display_header(self) -> None:
        """Display the application header."""
        header = "=" * 60
        title = "ヘルスモニター - ステータスダッシュボード"
        
        print(f"{Fore.CYAN}{Style.BRIGHT}{header}")
        print(f"{title:^60}")
        print(f"{header}{Style.RESET_ALL}")
        print()
    
    def _display_target_status(self, target_name: str, status: HealthStatus) -> None:
        """Display status for a single target."""
        # Determine status color and symbol
        if status.is_healthy:
            color = Fore.GREEN
            symbol = "✓"
            status_text = "正常"
        else:
            color = Fore.RED
            symbol = "✗"
            status_text = "異常"
        
        # Check if this target has recent changes for highlighting
        has_recent_change = self._change_tracker.has_recent_change(target_name, 30)
        if has_recent_change:
            # Add blinking effect for recent changes
            color = f"{color}{Style.BRIGHT}"
            symbol = f"⚡{symbol}"
        
        # Format response time
        response_time_str = f"{status.response_time:.2f}s" if status.response_time > 0 else "N/A"
        
        # Format timestamp
        timestamp_str = status.timestamp.strftime("%H:%M:%S")
        
        # Check for status change indicator
        change_indicator = ""
        if target_name in self._status_changes:
            change = self._status_changes[target_name]
            change_time = self._change_tracker.get_change_timestamp(target_name)
            change_time_str = change_time.strftime("%H:%M:%S") if change_time else ""
            
            if change == "異常→正常":
                change_indicator = f" {Fore.GREEN}{Back.BLACK}{Style.BRIGHT}[{change} {change_time_str}]{Style.RESET_ALL}"
            else:  # 正常→異常
                change_indicator = f" {Fore.RED}{Back.BLACK}{Style.BRIGHT}[{change} {change_time_str}]{Style.RESET_ALL}"
        
        # Display target status line
        target_line = f"{color}{symbol} {target_name:<25} {status_text:<10}{Style.RESET_ALL}"
        time_line = f" | 応答時間: {response_time_str:<8} | 最終確認: {timestamp_str}"
        
        print(f"{target_line}{time_line}{change_indicator}")
        
        # Display error message if unhealthy
        if not status.is_healthy and status.error_message:
            error_indent = " " * 4
            print(f"{error_indent}{Fore.YELLOW}エラー: {status.error_message}{Style.RESET_ALL}")
        
        print()  # Add spacing between targets
    
    def _display_footer(self) -> None:
        """Display the footer with current timestamp."""
        footer = "=" * 60
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer_text = f"最終更新: {current_time}"
        
        print(f"{Fore.CYAN}{footer}")
        print(f"{footer_text:^60}")
        print(f"{footer}{Style.RESET_ALL}")
        print()
        print(f"{Fore.YELLOW}監視を停止するにはCtrl+Cを押してください{Style.RESET_ALL}")


class StatusChangeTracker:
    """Helper class to track status changes for visual indicators."""
    
    def __init__(self):
        """Initialize the status change tracker."""
        self._previous_statuses: Dict[str, HealthStatus] = {}
        self._change_timestamps: Dict[str, datetime] = {}
        self._change_indicators: Dict[str, str] = {}
    
    def track_status_change(self, target_name: str, current_status: HealthStatus) -> Optional[str]:
        """
        Track status change for a target and return change indicator.
        
        Args:
            target_name: Name of the target
            current_status: Current health status object
            
        Returns:
            Status change indicator string or None if no change
        """
        change_indicator = None
        
        if target_name in self._previous_statuses:
            previous_status = self._previous_statuses[target_name]
            
            # Check if health status changed
            if previous_status.is_healthy != current_status.is_healthy:
                if current_status.is_healthy:
                    change_indicator = "異常→正常"
                else:
                    change_indicator = "正常→異常"
                
                # Record the change timestamp and indicator
                self._change_timestamps[target_name] = current_status.timestamp
                self._change_indicators[target_name] = change_indicator
        
        # Update previous status
        self._previous_statuses[target_name] = current_status
        
        return change_indicator
    
    def get_previous_status(self, target_name: str) -> Optional[HealthStatus]:
        """Get the previous health status for a target."""
        return self._previous_statuses.get(target_name)
    
    def get_change_indicator(self, target_name: str) -> Optional[str]:
        """Get the current change indicator for a target."""
        return self._change_indicators.get(target_name)
    
    def get_change_timestamp(self, target_name: str) -> Optional[datetime]:
        """Get the timestamp of the last status change for a target."""
        return self._change_timestamps.get(target_name)
    
    def clear_change_indicator(self, target_name: str) -> None:
        """Clear the change indicator for a target (after displaying)."""
        if target_name in self._change_indicators:
            del self._change_indicators[target_name]
        if target_name in self._change_timestamps:
            del self._change_timestamps[target_name]
    
    def clear_history(self) -> None:
        """Clear all status change history."""
        self._previous_statuses.clear()
        self._change_timestamps.clear()
        self._change_indicators.clear()
    
    def has_recent_change(self, target_name: str, seconds: int = 30) -> bool:
        """
        Check if a target has had a recent status change.
        
        Args:
            target_name: Name of the target
            seconds: Number of seconds to consider as "recent"
            
        Returns:
            True if there was a recent change, False otherwise
        """
        if target_name not in self._change_timestamps:
            return False
        
        change_time = self._change_timestamps[target_name]
        current_time = datetime.now()
        time_diff = (current_time - change_time).total_seconds()
        
        return time_diff <= seconds