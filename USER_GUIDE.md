# Health Monitor - ユーザーガイド

## 概要
Health MonitorはWebサイトとPostgreSQLデータベースの生存確認を継続的に行うツールです。
リアルタイムでの監視状況表示、詳細なログ記録、設定ファイルベースの柔軟な監視対象管理を提供します。

## 主な機能
- **Webサイト監視**: HTTPリクエストによる生存確認
- **データベース監視**: PostgreSQL接続テスト
- **リアルタイム表示**: 色付きコンソール出力
- **ログ記録**: ステータス変化の詳細記録
- **設定管理**: JSONファイルベースの監視対象管理
- **ホットリロード**: 設定変更の自動反映

## クイックスタート

### 1. 初回セットアップ
```cmd
# 環境セットアップスクリプトを実行
setup_environment.bat
```

### 2. 設定ファイルの編集
監視対象を設定するため、以下のファイルを編集してください：

- `config/websites.json` - Webサイト監視設定
- `config/databases.json` - データベース監視設定

### 3. アプリケーションの起動
```cmd
# Health Monitorを起動
start_monitor.bat
```

## 設定ファイル詳細

### Webサイト監視設定 (config/websites.json)

```json
{
  "websites": [
    {
      "name": "表示名",
      "url": "https://example.com",
      "timeout": 10,
      "expected_status": 200
    }
  ]
}
```

**設定項目:**
- `name`: 監視画面に表示される名前
- `url`: 監視対象のURL（HTTP/HTTPS）
- `timeout`: タイムアウト時間（秒）
- `expected_status`: 期待するHTTPステータスコード

**使用例:**
```json
{
  "websites": [
    {
      "name": "会社のWebサイト",
      "url": "https://www.company.com",
      "timeout": 15,
      "expected_status": 200
    },
    {
      "name": "API健全性チェック",
      "url": "https://api.company.com/health",
      "timeout": 10,
      "expected_status": 200
    },
    {
      "name": "管理画面",
      "url": "https://admin.company.com/login",
      "timeout": 20,
      "expected_status": 200
    }
  ]
}
```

### データベース監視設定 (config/databases.json)

```json
{
  "databases": [
    {
      "name": "表示名",
      "host": "データベースホスト",
      "port": 5432,
      "database": "データベース名",
      "username": "ユーザー名",
      "password": "パスワード",
      "sslmode": "require"
    }
  ]
}
```

**設定項目:**
- `name`: 監視画面に表示される名前
- `host`: データベースサーバーのホスト名またはIPアドレス
- `port`: ポート番号（PostgreSQLの標準は5432）
- `database`: 接続するデータベース名
- `username`: 接続ユーザー名
- `password`: パスワード
- `sslmode`: SSL接続モード

**SSL接続モード:**
- `require`: SSL接続を必須とする
- `prefer`: SSL接続を優先するが、利用できない場合は非SSL接続
- `disable`: SSL接続を無効にする

**クラウドサービス別設定例:**

**Azure PostgreSQL:**
```json
{
  "name": "Azure本番DB",
  "host": "myserver.postgres.database.azure.com",
  "port": 5432,
  "database": "production",
  "username": "admin@myserver",
  "password": "your_password",
  "sslmode": "require"
}
```

**AWS RDS:**
```json
{
  "name": "AWS本番DB",
  "host": "mydb.cluster-xyz.us-east-1.rds.amazonaws.com",
  "port": 5432,
  "database": "production",
  "username": "dbuser",
  "password": "your_password",
  "sslmode": "require"
}
```

## 監視画面の見方

### ステータス表示
- **緑色**: 正常（接続成功）
- **赤色**: 異常（接続失敗）
- **黄色**: 警告（タイムアウト等）

### 表示情報
- 監視対象名
- 現在のステータス
- 応答時間
- 最終チェック時刻
- エラーメッセージ（異常時）

### ステータス変化の通知
ステータスが変化した場合、以下の情報が表示されます：
- 変化の種類（UP→DOWN、DOWN→UP）
- 変化発生時刻
- 詳細なエラー情報

## ログファイル

### ログの場所
- `logs/` ディレクトリに日付別でログファイルが作成されます
- ファイル名形式: `health_monitor_YYYY-MM-DD.log`

### ログの内容
- ステータス変化の記録
- エラー詳細情報
- アプリケーションの起動・終了
- 設定ファイルの変更検出

### ログの確認方法
```cmd
# 最新のログファイルを表示
type logs\health_monitor_2024-01-15.log

# ログディレクトリの一覧
dir logs
```

## 📊 ダッシュボード機能

JSONログを美しいHTMLダッシュボードで表示する機能を提供しています。

### 基本ダッシュボード

シンプルで軽量なダッシュボードです。

#### 使用方法
```cmd
# デフォルト（プロンプト付き）
view_dashboard.bat

# 自動でブラウザを開く
view_dashboard.bat --open

# プロンプトなし（生成のみ）
view_dashboard.bat --no-prompt

# 短縮形
view_dashboard.bat -o    # --open と同じ
view_dashboard.bat -n    # --no-prompt と同じ
```

#### 特徴
- シンプルで軽量なデザイン
- 現在のステータス一覧
- 最新ログエントリ表示
- レスポンシブデザイン

### 高度なダッシュボード

詳細な統計情報と分析機能を含むダッシュボードです。

#### 使用方法
```cmd
# デフォルト（プロンプト付き）
view_advanced_dashboard.bat

# 自動でブラウザを開く
view_advanced_dashboard.bat --open

# プロンプトなし（生成のみ）
view_advanced_dashboard.bat --no-prompt

# 短縮形
view_advanced_dashboard.bat -o    # --open と同じ
view_advanced_dashboard.bat -n    # --no-prompt と同じ
```

#### 特徴
- 📈 稼働率統計（24時間）
- ⚡ 応答時間分析（平均・最大・最小）
- 🔄 自動更新機能（30秒間隔）
- 📱 モバイル対応デザイン
- 🎯 詳細なサービス情報

### ダッシュボードメニュー

統合メニューから複数のオプションを選択できます。

```cmd
dashboard_menu.bat
```

#### 利用可能なオプション
1. **Basic Dashboard (with prompt)** - 基本ダッシュボード（確認あり）
2. **Advanced Dashboard (with prompt)** - 高度なダッシュボード（確認あり）
3. **Generate Both (with prompt)** - 両方生成（確認あり）
4. **Basic Dashboard (auto-open)** - 基本ダッシュボード（自動オープン）
5. **Advanced Dashboard (auto-open)** - 高度なダッシュボード（自動オープン）
6. **Generate Both (auto-open)** - 両方生成（自動オープン）
7. **Basic Dashboard (no prompt)** - 基本ダッシュボード（確認なし）
8. **Advanced Dashboard (no prompt)** - 高度なダッシュボード（確認なし）

### コマンドラインオプション

| オプション | 短縮形 | 説明 |
|-----------|--------|------|
| `--open` | `-o` | ダッシュボード生成後、自動でブラウザを開く |
| `--no-prompt` | `-n` | ユーザーへの確認プロンプトを表示しない |

### 使用シナリオ

#### 1. 日常の監視確認
```cmd
# 毎朝の状況確認
view_advanced_dashboard.bat --open
```

#### 2. 自動化スクリプトでの使用
```cmd
# CI/CDパイプラインやスケジュールタスクで使用
view_advanced_dashboard.bat --no-prompt
```

#### 3. 障害対応時の詳細確認
```cmd
# 問題発生時の詳細分析
view_advanced_dashboard.bat
```

### Python直接実行

より詳細な制御が必要な場合は、Pythonスクリプトを直接実行できます。

```cmd
# 基本ダッシュボード
python log_viewer.py --output dashboard.html --days 1

# 高度なダッシュボード（7日間のデータ）
python advanced_log_viewer.py --output advanced_dashboard.html --days 7

# カスタム設定
python log_viewer.py --log-dir custom_logs --output custom_dashboard.html --days 3
```

#### Pythonスクリプトのオプション

**log_viewer.py / advanced_log_viewer.py:**
- `--log-dir`: ログディレクトリのパス（デフォルト: logs）
- `--output`: 出力HTMLファイル名
- `--days`: 表示する日数（デフォルト: 1）

### 生成されるファイル

- **基本ダッシュボード**: `dashboard.html`
- **高度なダッシュボード**: `advanced_dashboard.html`

両方のファイルはプロジェクトルートに生成され、ブラウザで直接開くことができます。

### ダッシュボードの活用方法

#### 1. 定期レポート作成
```cmd
# 週次レポート用（7日間のデータ）
python advanced_log_viewer.py --output weekly_report.html --days 7
```

#### 2. 障害分析
- 高度なダッシュボードの稼働率統計で問題のあるサービスを特定
- 応答時間分析でパフォーマンス問題を発見
- 詳細ログで障害の原因を調査

#### 3. 運用会議での報告
- 美しいHTMLダッシュボードをプレゼンテーション資料として使用
- 自動更新機能でリアルタイムの状況を共有

### トラブルシューティング

#### ダッシュボードが生成されない
1. Pythonが正しくインストールされているか確認
2. ログファイルが存在するか確認
3. 権限問題がないか確認

#### ブラウザが自動で開かない
1. `start` コマンドが利用可能か確認
2. デフォルトブラウザが設定されているか確認
3. 手動でHTMLファイルを開く

## 運用のベストプラクティス

### 1. 監視間隔の調整
デフォルトの監視間隔は300秒（5分）です。必要に応じて調整してください：
- 重要なサービス: 60-180秒
- 一般的なサービス: 300-600秒
- 負荷の高いサービス: 600秒以上

### 2. タイムアウト設定
- 通常のWebサイト: 10-15秒
- 重い処理を含むAPI: 20-30秒
- データベース: 5-10秒

### 3. セキュリティ考慮事項
- パスワードを設定ファイルに平文で保存しない
- 専用の監視用ユーザーを作成する
- 最小限の権限のみを付与する

### 4. 定期メンテナンス
- ログファイルの定期的な削除
- 設定ファイルのバックアップ
- 監視対象の定期的な見直し

## 高度な使用方法

### 環境変数での設定
パスワードなどの機密情報は環境変数で管理できます：

```json
{
  "name": "本番DB",
  "host": "prod-db.example.com",
  "port": 5432,
  "database": "production",
  "username": "monitor_user",
  "password": "${DB_PASSWORD}",
  "sslmode": "require"
}
```

### 複数環境での運用
環境別に設定ファイルを分けて管理：
- `config/websites_prod.json`
- `config/websites_staging.json`
- `config/databases_prod.json`
- `config/databases_staging.json`

### 自動起動設定
Windowsタスクスケジューラーを使用してシステム起動時に自動実行：

1. タスクスケジューラーを開く
2. 「基本タスクの作成」を選択
3. トリガー: 「コンピューターの起動時」
4. 操作: `start_monitor.bat` のフルパスを指定

## パフォーマンス最適化

### 1. 並列処理の調整
多数の監視対象がある場合、並列実行数を調整してください。

### 2. メモリ使用量の監視
長時間実行時のメモリリークを監視してください。

### 3. ネットワーク負荷の考慮
監視間隔とタイムアウト設定でネットワーク負荷を調整してください。

## 次のステップ

### 機能拡張
- アラート通知機能の追加
- Web UIダッシュボードの作成
- メトリクス収集機能の追加

### 統合
- 監視システム（Nagios、Zabbix等）との連携
- ログ管理システムとの統合
- チャットツール（Slack、Teams等）への通知

詳細なトラブルシューティング情報については `TROUBLESHOOTING.md` を参照してください。