# Design Document

## Overview

Health Monitoring Toolは、WebサイトとPostgreSQLデータベースの生存確認を行うPythonアプリケーションです。リアルタイムでの監視状況表示、設定ファイルベースの監視対象管理、詳細なログ記録機能を提供します。

## Architecture

### システム構成
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Config Files  │    │  Health Monitor  │    │   Log Storage   │
│                 │    │                  │    │                 │
│ - websites.json │───▶│ - Monitor Engine │───▶│ - status.log    │
│ - databases.json│    │ - Status Display │    │ - daily logs    │
└─────────────────┘    │ - Log Manager    │    └─────────────────┘
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Target Systems  │
                       │                  │
                       │ - Web Sites      │
                       │ - PostgreSQL DBs │
                       └──────────────────┘
```

### 主要コンポーネント
- **Configuration Manager**: 設定ファイルの読み込みと検証
- **Health Check Engine**: 監視対象への接続テスト実行
- **Status Display**: リアルタイムステータス表示とUI
- **Log Manager**: ステータス変化の記録と履歴管理

## Components and Interfaces

### 1. Configuration Manager
**責務**: 監視対象の設定ファイル管理

**インターフェース**:
```python
class ConfigurationManager:
    def load_website_config(self) -> List[WebsiteTarget]
    def load_database_config(self) -> List[DatabaseTarget]
    def validate_config(self, config: dict) -> bool
    def reload_config(self) -> None
```

**設定ファイル形式**:
- `websites.json`: WebサイトURL一覧
- `databases.json`: PostgreSQL接続情報一覧

### 2. Health Check Engine
**責務**: 実際のヘルスチェック実行

**インターフェース**:
```python
class HealthCheckEngine:
    def check_website(self, target: WebsiteTarget) -> HealthStatus
    def check_database(self, target: DatabaseTarget) -> HealthStatus
    def run_all_checks(self) -> Dict[str, HealthStatus]
```

**チェック方式**:
- Webサイト: HTTP GET リクエスト（タイムアウト: 10秒）
- データベース: PostgreSQL接続テスト（タイムアウト: 5秒）

### 3. Status Display
**責務**: 監視結果の視覚的表示

**インターフェース**:
```python
class StatusDisplay:
    def update_display(self, statuses: Dict[str, HealthStatus]) -> None
    def show_error(self, target: str, error: str) -> None
    def refresh_ui(self) -> None
```

**表示方式**:
- コンソール出力（colorama使用）
- 正常: 緑色表示
- 異常: 赤色表示
- リアルタイム更新

### 4. Log Manager
**責務**: ステータス変化の記録と管理

**インターフェース**:
```python
class LogManager:
    def log_status_change(self, target: str, old_status: str, new_status: str) -> None
    def get_daily_log(self, date: str) -> List[LogEntry]
    def cleanup_old_logs(self, retention_days: int) -> None
```

## Data Models

### WebsiteTarget
```python
@dataclass
class WebsiteTarget:
    name: str
    url: str
    timeout: int = 10
    expected_status: int = 200
```

### DatabaseTarget
```python
@dataclass
class DatabaseTarget:
    name: str
    host: str
    port: int
    database: str
    username: str
    password: str
    sslmode: str
```

### HealthStatus
```python
@dataclass
class HealthStatus:
    target_name: str
    is_healthy: bool
    response_time: float
    error_message: Optional[str]
    timestamp: datetime
```

### LogEntry
```python
@dataclass
class LogEntry:
    timestamp: datetime
    target_name: str
    target_type: str  # 'website' or 'database'
    status_change: str  # 'up->down' or 'down->up'
    details: str
```

## Error Handling

### 接続エラー処理
- **Webサイト**: requests.exceptions処理、HTTPステータスコード検証
- **データベース**: psycopg2.Error処理、接続タイムアウト処理
- **設定ファイル**: JSON解析エラー、必須フィールド検証

### ログエラー処理
- ファイル書き込み権限エラー
- ディスク容量不足エラー
- ログローテーション失敗

### 復旧処理
- 一時的な接続失敗時の自動リトライ
- 設定ファイル更新時の自動リロード
- アプリケーション異常終了時の状態復旧

## Testing Strategy

### 単体テスト
- Configuration Manager: 設定ファイル読み込み、検証ロジック
- Health Check Engine: モックサーバーを使用したHTTP/DB接続テスト
- Log Manager: ログ書き込み、読み込み機能

### 統合テスト
- 実際のWebサイトとデータベースを使用したエンドツーエンドテスト
- 設定ファイル変更時の動作確認
- 長時間実行時の安定性テスト

### 技術スタック
- **Python 3.8+**: メインランタイム
- **requests**: HTTP通信
- **psycopg2**: PostgreSQL接続
- **colorama**: コンソール色付け表示
- **json**: 設定ファイル処理
- **logging**: ログ管理
- **threading**: 並行処理
- **datetime**: 時刻管理