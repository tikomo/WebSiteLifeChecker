"""
Main Health Monitor application entry point.
Integrates all components and provides continuous monitoring loop.
"""
import time
import sys
import os
import signal
import threading
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from health_monitor.services.configuration_manager import ConfigurationManager, ConfigurationError
from health_monitor.services.health_check_engine import HealthCheckEngine
from health_monitor.services.status_display import StatusDisplay
from health_monitor.services.log_manager import LogManager
from health_monitor.models.data_models import WebsiteTarget, DatabaseTarget, HealthStatus


class HealthMonitorApp:
    """Main Health Monitor application class."""
    
    def __init__(self, config_dir: str = "config", log_dir: str = "logs", check_interval: int = 300, log_all_checks: bool = False):
        """
        Initialize the Health Monitor application.
        
        Args:
            config_dir: Directory containing configuration files
            log_dir: Directory for log files
            check_interval: Interval between health checks in seconds
            log_all_checks: Whether to log all health check results (not just status changes)
        """
        self.config_dir = config_dir
        self.log_dir = log_dir
        self.check_interval = check_interval
        self.running = False
        
        # Initialize components
        self.config_manager = ConfigurationManager(config_dir)
        self.log_manager = LogManager(log_dir)
        self.health_engine = HealthCheckEngine(log_manager=self.log_manager, log_all_checks=log_all_checks)
        self.status_display = StatusDisplay()
        
        # Configuration cache
        self.website_targets: List[WebsiteTarget] = []
        self.database_targets: List[DatabaseTarget] = []
        self.last_config_load_time = None
        
        # Configuration file monitoring
        self.config_file_timestamps = {}
        self._update_config_timestamps()
        
        # Shutdown handling
        self.shutdown_event = threading.Event()
        self._setup_signal_handlers()
        
    def initialize(self) -> bool:
        """
        Initialize the application and load initial configuration.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            print("Health Monitor を初期化しています...")
            
            # Create directories if they don't exist
            os.makedirs(self.config_dir, exist_ok=True)
            os.makedirs(self.log_dir, exist_ok=True)
            
            # Load initial configuration
            self._load_configuration()
            
            # Validate that we have at least one target to monitor
            if not self.website_targets and not self.database_targets:
                print("警告: 監視対象が設定されていません。設定ファイルを確認してください。")
                return False
            
            print(f"初期化完了: Webサイト {len(self.website_targets)}件, データベース {len(self.database_targets)}件")
            return True
            
        except Exception as e:
            print(f"初期化エラー: {e}")
            return False
    
    def run(self) -> None:
        """
        Run the main monitoring loop.
        Performs continuous health checks at configured intervals.
        """
        if not self.initialize():
            print("初期化に失敗しました。アプリケーションを終了します。")
            return
        
        self.running = True
        print(f"監視を開始します (間隔: {self.check_interval}秒)")
        print("監視を停止するには Ctrl+C を押してください。")
        
        try:
            while self.running and not self.shutdown_event.is_set():
                # Check for configuration changes and reload if necessary
                self._check_and_reload_config()
                
                # Perform health checks
                self._perform_health_checks()
                
                # Wait for next check interval with shutdown check
                self._interruptible_sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\nキーボード割り込みを受信しました。監視を停止しています...")
            self._shutdown()
        except Exception as e:
            print(f"\n予期しないエラーが発生しました: {e}")
            self._shutdown()
    
    def run_once(self) -> None:
        """
        Run a single health check cycle and exit.
        Useful for scheduled tasks or testing.
        """
        print("Health Monitor を初期化しています...")
        
        if not self.initialize():
            return
        
        print("1回限りのヘルスチェックを実行しています...")
        
        try:
            # Perform single health check
            self._perform_health_checks()
            
            # Display results
            self.status_display.display_status(
                website_statuses={name: status for name, status in self.health_engine.get_current_statuses().items() 
                                if any(target.name == name for target in self.website_targets)},
                database_statuses={name: status for name, status in self.health_engine.get_current_statuses().items() 
                                 if any(target.name == name for target in self.database_targets)}
            )
            
            print("\nヘルスチェックが完了しました。")
            
        except Exception as e:
            error_msg = f"ヘルスチェック実行中にエラーが発生しました: {e}"
            print(f"\n{error_msg}")
            self.log_manager.log_status_change(
                target="system",
                target_type="application",
                old_status="running",
                new_status="error",
                details=error_msg
            )
        finally:
            self._shutdown()
    
    def _load_configuration(self) -> None:
        """Load configuration from files."""
        try:
            # Load website targets
            try:
                self.website_targets = self.config_manager.load_website_config()
            except ConfigurationError as e:
                print(f"Webサイト設定の読み込みエラー: {e}")
                self.website_targets = []
            
            # Load database targets
            try:
                self.database_targets = self.config_manager.load_database_config()
            except ConfigurationError as e:
                print(f"データベース設定の読み込みエラー: {e}")
                self.database_targets = []
            
            self.last_config_load_time = datetime.now()
            
        except Exception as e:
            print(f"設定読み込み中にエラーが発生しました: {e}")
            raise
    
    def _perform_health_checks(self) -> None:
        """Perform health checks on all configured targets."""
        try:
            # Run all health checks
            results = self.health_engine.run_all_checks(
                website_targets=self.website_targets,
                database_targets=self.database_targets
            )
            
            # Update status display
            self.status_display.update_display(results)
            
        except Exception as e:
            error_msg = f"ヘルスチェック実行中にエラーが発生しました: {e}"
            print(f"\n{error_msg}")
            self.log_manager.log_status_change(
                target="system",
                target_type="application",
                old_status="running",
                new_status="error",
                details=error_msg
            )
    
    def _shutdown(self) -> None:
        """Perform graceful shutdown of the application."""
        print("グレースフルシャットダウンを実行しています...")
        self.running = False
        self.shutdown_event.set()
        
        try:
            # Log shutdown initiation
            self.log_manager.log_status_change(
                target="system",
                target_type="application",
                old_status="running",
                new_status="shutting_down",
                details="Graceful shutdown initiated"
            )
            
            # Log final status for all targets
            current_statuses = self.health_engine.get_current_statuses()
            if current_statuses:
                print("最終ステータスをログに記録しています...")
                for target_name, status in current_statuses.items():
                    final_status = "up" if status.is_healthy else "down"
                    target_type = self._get_target_type(target_name)
                    
                    self.log_manager.log_status_change(
                        target=target_name,
                        target_type=target_type,
                        old_status=final_status,
                        new_status="shutdown",
                        details="Application shutdown - final status recorded"
                    )
            
            # Clean up resources
            print("リソースをクリーンアップしています...")
            self.health_engine.close()
            
            # Log successful shutdown
            self.log_manager.log_status_change(
                target="system",
                target_type="application",
                old_status="shutting_down",
                new_status="shutdown_complete",
                details="Graceful shutdown completed successfully"
            )
            
            print("Health Monitor が正常に終了しました。")
            
        except Exception as e:
            error_msg = f"シャットダウン中にエラーが発生しました: {e}"
            print(error_msg)
            try:
                self.log_manager.log_status_change(
                    target="system",
                    target_type="application",
                    old_status="shutting_down",
                    new_status="shutdown_error",
                    details=error_msg
                )
            except:
                pass  # Ignore logging errors during shutdown
    
    def _get_target_type(self, target_name: str) -> str:
        """Get the type of a target by its name."""
        for target in self.website_targets:
            if target.name == target_name:
                return "website"
        for target in self.database_targets:
            if target.name == target_name:
                return "database"
        return "unknown"
    
    def _update_config_timestamps(self) -> None:
        """Update the timestamps of configuration files for change detection."""
        config_files = [
            Path(self.config_dir) / "websites.json",
            Path(self.config_dir) / "databases.json"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                self.config_file_timestamps[str(config_file)] = config_file.stat().st_mtime
            else:
                self.config_file_timestamps[str(config_file)] = 0
    
    def _check_config_file_changes(self) -> bool:
        """
        Check if any configuration files have been modified.
        
        Returns:
            True if any configuration file has changed, False otherwise
        """
        config_files = [
            Path(self.config_dir) / "websites.json",
            Path(self.config_dir) / "databases.json"
        ]
        
        for config_file in config_files:
            file_path = str(config_file)
            current_mtime = config_file.stat().st_mtime if config_file.exists() else 0
            last_mtime = self.config_file_timestamps.get(file_path, 0)
            
            if current_mtime != last_mtime:
                return True
        
        return False
    
    def _check_and_reload_config(self) -> None:
        """Check for configuration changes and reload if necessary."""
        try:
            if self._check_config_file_changes():
                print("\n設定ファイルの変更を検出しました。設定を再読み込みしています...")
                
                # Store old configuration for comparison
                old_website_count = len(self.website_targets)
                old_database_count = len(self.database_targets)
                
                # Reload configuration
                self._load_configuration()
                self._update_config_timestamps()
                
                # Log configuration reload
                new_website_count = len(self.website_targets)
                new_database_count = len(self.database_targets)
                
                reload_details = (
                    f"Webサイト: {old_website_count} -> {new_website_count}, "
                    f"データベース: {old_database_count} -> {new_database_count}"
                )
                
                self.log_manager.log_status_change(
                    target="system",
                    target_type="application",
                    old_status="running",
                    new_status="config_reloaded",
                    details=reload_details
                )
                
                print(f"設定再読み込み完了: {reload_details}")
                
        except Exception as e:
            error_msg = f"設定再読み込み中にエラーが発生しました: {e}"
            print(f"\n{error_msg}")
            self.log_manager.log_status_change(
                target="system",
                target_type="application",
                old_status="running",
                new_status="config_reload_error",
                details=error_msg
            )
    
    def get_status_summary(self) -> Dict[str, int]:
        """
        Get a summary of current target statuses.
        
        Returns:
            Dictionary with counts of healthy/unhealthy targets
        """
        current_statuses = self.health_engine.get_current_statuses()
        
        summary = {
            "total": len(current_statuses),
            "healthy": 0,
            "unhealthy": 0,
            "websites": 0,
            "databases": 0
        }
        
        for target_name, status in current_statuses.items():
            if status.is_healthy:
                summary["healthy"] += 1
            else:
                summary["unhealthy"] += 1
            
            target_type = self._get_target_type(target_name)
            if target_type == "website":
                summary["websites"] += 1
            elif target_type == "database":
                summary["databases"] += 1
        
        return summary
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            print(f"\n\n{signal_name} シグナルを受信しました。グレースフルシャットダウンを開始します...")
            self.shutdown_event.set()
            self.running = False
        
        # Register signal handlers for common termination signals
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_handler)
        # Windows specific
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
    
    def _interruptible_sleep(self, duration: float) -> None:
        """
        Sleep for the specified duration but can be interrupted by shutdown event.
        
        Args:
            duration: Sleep duration in seconds
        """
        end_time = time.time() + duration
        
        while time.time() < end_time and not self.shutdown_event.is_set():
            remaining = end_time - time.time()
            sleep_time = min(1.0, remaining)  # Check shutdown event every second
            if sleep_time > 0:
                time.sleep(sleep_time)


def main():
    """Main entry point for the Health Monitor application."""
    # Parse command line arguments for configuration
    import argparse
    
    parser = argparse.ArgumentParser(description="Health Monitor - Webサイトとデータベースの監視ツール")
    parser.add_argument("--config-dir", default="config", help="設定ファイルディレクトリ (デフォルト: config)")
    parser.add_argument("--log-dir", default="logs", help="ログファイルディレクトリ (デフォルト: logs)")
    parser.add_argument("--interval", type=int, default=300, help="チェック間隔（秒） (デフォルト: 300)")
    parser.add_argument("--log-all-checks", action="store_true", help="すべてのヘルスチェック結果をログに記録")
    parser.add_argument("--once", action="store_true", help="1回だけヘルスチェックを実行して終了")
    
    args = parser.parse_args()
    
    # Create and run the application
    app = HealthMonitorApp(
        config_dir=args.config_dir,
        log_dir=args.log_dir,
        check_interval=args.interval,
        log_all_checks=args.log_all_checks
    )
    
    if args.once:
        app.run_once()
    else:
        app.run()


if __name__ == "__main__":
    main()