# Health Monitor

🚀 **エンタープライズ対応のインフラ監視ツール** - WebサイトとPostgreSQLデータベースの包括的な健全性監視

## 概要

Health Monitorは、現代のWebアプリケーションインフラストラクチャの可用性を24/7で監視する、軽量かつ高性能なPythonアプリケーションです。DevOpsチームやシステム管理者が、重要なサービスの障害を即座に検知し、迅速な対応を可能にします。

### なぜHealth Monitorなのか？

- **🔧 シンプルな運用**: 複雑な設定不要、5分でセットアップ完了
- **⚡ 高速検知**: 並列処理による効率的な監視とリアルタイム通知
- **📊 運用に優しい**: 直感的なダッシュボードと詳細なログ分析
- **🔧 柔軟な拡張**: JSON設定による簡単な監視対象追加・変更
- **💼 エンタープライズ対応**: 大規模環境での安定稼働実績

## 主な機能

### 🌐 Webサイト・API監視
- HTTPSリクエストによる生存確認
- カスタムステータスコード対応
- 応答時間測定とパフォーマンス追跡
- リダイレクト処理とタイムアウト制御

### 🗄️ データベース監視
- PostgreSQL接続テスト（オンプレミス・クラウド対応）
- SSL/TLS暗号化接続サポート
- 接続プール管理と効率的なリソース利用
- Azure、AWS、GCP等の主要クラウドサービス対応

### 📈 監視・分析機能
- **リアルタイムダッシュボード**: 色付きコンソール表示
- **インテリジェントログ**: ステータス変更時の自動記録
- **詳細ログモード**: 全ヘルスチェック結果の完全記録
- **履歴分析**: 日次ローテーションによる長期トレンド把握

### 🔄 運用効率化
- **ホットリロード**: サービス停止なしの設定変更
- **自動復旧検知**: 障害からの回復を即座に通知
- **柔軟なスケジューリング**: 継続監視・One Shot実行の選択
- **Windows統合**: バッチファイルによるワンクリック操作

## クイックスタート

### 1. 環境セットアップ
```cmd
# 自動セットアップスクリプトを実行
setup_environment.bat
```

### 2. インストール確認
```cmd
# セットアップが正しく完了したかを確認
verify_installation.bat
```

### 3. 設定ファイルの編集
監視対象を設定：
- `config/websites.json` - Webサイト監視設定
- `config/databases.json` - データベース監視設定

### 4. アプリケーション起動

#### 基本起動（継続監視）
```cmd
# Health Monitorを起動（5分間隔で継続監視）
start_monitor.bat
```

#### 詳細ログ付き起動
```cmd
# すべてのヘルスチェック結果をログに記録
python run_health_monitor.py --log-all-checks
```

#### 1回だけ実行（One Shot）
```cmd
# 1回だけヘルスチェックを実行して終了
python run_health_monitor.py --once --log-all-checks
```

## ファイル構成

```
health-monitoring-tool/
├── 📁 health_monitor/           # メインアプリケーション
├── 📁 config/                   # 設定ファイル
│   ├── websites.json           # Webサイト監視設定
│   ├── databases.json          # データベース監視設定
│   ├── websites.json.sample    # Webサイト設定サンプル
│   └── databases.json.sample   # データベース設定サンプル
├── 📁 logs/                     # ログファイル
├── 📁 tests/                    # テストファイル
├── 🚀 start_monitor.bat         # アプリケーション起動
├── ⚙️ setup_environment.bat     # 環境セットアップ
├── ✅ verify_installation.bat   # インストール確認
├── 📊 dashboard_menu.bat        # ダッシュボードメニュー
├── 📈 view_dashboard.bat        # 基本ダッシュボード生成
├── 🎯 view_advanced_dashboard.bat # 高度なダッシュボード生成
├── 🧪 run_tests.bat             # テスト実行メニュー
├── 📋 requirements.txt          # Python依存関係
├── 🐍 run_health_monitor.py     # Python実行スクリプト
├── 📊 log_viewer.py             # ログビューアー（基本）
├── 📈 advanced_log_viewer.py    # ログビューアー（高度）
├── 🧪 run_tests.py              # テスト実行スクリプト
├── 📖 SETUP_WINDOWS.md          # Windows セットアップガイド
├── 📚 USER_GUIDE.md             # ユーザーガイド
├── 📊 DASHBOARD_USAGE.md        # ダッシュボード使用方法
└── 🔧 TROUBLESHOOTING.md        # トラブルシューティング
```

## 設定例

### Webサイト監視 (config/websites.json)
```json
{
  "websites": [
    {
      "name": "会社のWebサイト",
      "url": "https://www.company.com",
      "timeout": 10,
      "expected_status": 200
    },
    {
      "name": "API健全性チェック",
      "url": "https://api.company.com/health",
      "timeout": 15,
      "expected_status": 200
    }
  ]
}
```

### データベース監視 (config/databases.json)
```json
{
  "databases": [
    {
      "name": "本番データベース",
      "host": "prod-db.company.com",
      "port": 5432,
      "database": "production",
      "username": "monitor_user",
      "password": "your_password",
      "sslmode": "require"
    }
  ]
}
```

## 動作画面

```
========================================
Health Monitor 起動中...
========================================

🌐 Webサイト監視:
✅ 会社のWebサイト        (200ms) - 正常
✅ API健全性チェック      (150ms) - 正常
❌ 開発サーバー          (timeout) - 接続失敗

🗄️ データベース監視:
✅ 本番データベース      (45ms) - 接続成功
⚠️ ステージングDB       (2.1s) - 応答遅延

最終更新: 2024-01-15 14:30:25
次回チェック: 5分後
```

## コマンドラインオプション

Health Monitorは以下のコマンドラインオプションをサポートしています：

```cmd
python run_health_monitor.py [オプション]
```

### 利用可能なオプション

| オプション         | 説明                                   | デフォルト  |
| ------------------ | -------------------------------------- | ----------- |
| `--config-dir`     | 設定ファイルディレクトリ               | `config`    |
| `--log-dir`        | ログファイルディレクトリ               | `logs`      |
| `--interval`       | チェック間隔（秒）                     | `300` (5分) |
| `--log-all-checks` | すべてのヘルスチェック結果をログに記録 | 無効        |
| `--once`           | 1回だけ実行して終了                    | 無効        |

### 使用例

```cmd
# デフォルト設定で起動
python run_health_monitor.py

# 1分間隔で詳細ログ付き監視
python run_health_monitor.py --interval 60 --log-all-checks

# カスタム設定ディレクトリを使用
python run_health_monitor.py --config-dir custom_config --log-dir custom_logs

# 1回だけ実行（スケジュールタスク用）
python run_health_monitor.py --once --log-all-checks
```

## システム要件

- **OS**: Windows 10/11
- **Python**: 3.8以上
- **メモリ**: 最小 128MB
- **ディスク**: 最小 50MB（ログファイル用）
- **ネットワーク**: インターネット接続（監視対象へのアクセス用）

## 依存関係

- `requests` - HTTP通信
- `psycopg2-binary` - PostgreSQL接続
- `colorama` - 色付きコンソール出力

## ドキュメント

- 📖 **[SETUP_WINDOWS.md](SETUP_WINDOWS.md)** - 詳細なセットアップ手順
- 📚 **[USER_GUIDE.md](USER_GUIDE.md)** - 使用方法とベストプラクティス
- 📊 **[DASHBOARD_USAGE.md](DASHBOARD_USAGE.md)** - ダッシュボード使用方法
- 🔧 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - 問題解決ガイド

## サポートされる監視対象

### Webサイト
- HTTP/HTTPS サイト
- REST API エンドポイント
- 認証が不要なWebサービス
- カスタムHTTPステータスコード対応

### データベース
- PostgreSQL (オンプレミス)
- Azure Database for PostgreSQL
- AWS RDS PostgreSQL
- Google Cloud SQL PostgreSQL
- SSL/TLS接続対応

## ログ機能

Health Monitorは2つのログモードをサポートしています：

### ステータス変更ログ（デフォルト）
- サービスの状態が変化した時のみ記録
- ファイルサイズが小さく、重要な変更を追跡
- 例：`{"status_change": "down->up", "details": "Response time: 0.08s"}`

### 全ヘルスチェックログ（`--log-all-checks`）
- すべてのヘルスチェック結果を記録
- 詳細な監視履歴を保持
- 例：`{"status_change": "up", "details": "Response time: 0.15s"}`

### ログファイル形式
- **場所**: `logs/health_monitor_YYYYMMDD.log`
- **形式**: JSON（1行1エントリ）
- **ローテーション**: 日次自動ローテーション
- **保持期間**: 30日間（設定可能）

## 📊 ダッシュボード機能

JSONログを美しいHTMLダッシュボードで表示する機能を提供しています：

### 基本ダッシュボード

#### 基本的な使用方法
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

**特徴:**
- シンプルで軽量なデザイン
- 現在のステータス一覧
- 最新ログエントリ表示
- レスポンシブデザイン

### 高度なダッシュボード

#### 基本的な使用方法
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

**特徴:**
- 📈 稼働率統計（24時間）
- ⚡ 応答時間分析（平均・最大・最小）
- 🔄 自動更新機能（30秒間隔）
- 📱 モバイル対応デザイン
- 🎯 詳細なサービス情報

### ダッシュボードメニュー
```cmd
# 統合メニューから選択
dashboard_menu.bat
```

**利用可能なオプション:**
1. Basic Dashboard (with prompt) - 基本ダッシュボード（確認あり）
2. Advanced Dashboard (with prompt) - 高度なダッシュボード（確認あり）
3. Generate Both (with prompt) - 両方生成（確認あり）
4. Basic Dashboard (auto-open) - 基本ダッシュボード（自動オープン）
5. Advanced Dashboard (auto-open) - 高度なダッシュボード（自動オープン）
6. Generate Both (auto-open) - 両方生成（自動オープン）
7. Basic Dashboard (no prompt) - 基本ダッシュボード（確認なし）
8. Advanced Dashboard (no prompt) - 高度なダッシュボード（確認なし）

### コマンドラインオプション

| オプション    | 短縮形 | 説明                                       |
| ------------- | ------ | ------------------------------------------ |
| `--open`      | `-o`   | ダッシュボード生成後、自動でブラウザを開く |
| `--no-prompt` | `-n`   | ユーザーへの確認プロンプトを表示しない     |

### 使用例

#### 自動化スクリプトで使用
```cmd
# CI/CDパイプラインやスケジュールタスクで使用
view_advanced_dashboard.bat --no-prompt
```

#### 開発中の確認
```cmd
# 生成してすぐに確認したい場合
view_advanced_dashboard.bat --open
```

#### 通常の使用
```cmd
# ユーザーに選択させたい場合（デフォルト）
view_advanced_dashboard.bat
```

### Python直接実行
```cmd
# 基本ダッシュボード
python log_viewer.py --output dashboard.html --days 1

# 高度なダッシュボード
python advanced_log_viewer.py --output advanced_dashboard.html --days 7

# カスタム設定
python log_viewer.py --log-dir custom_logs --output custom_dashboard.html --days 3
```

### 生成されるファイル
- **基本ダッシュボード**: `dashboard.html`
- **高度なダッシュボード**: `advanced_dashboard.html`

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要求は、GitHubのIssuesページでお願いします。

## 更新履歴

- **v1.0.0** - 初回リリース
  - Webサイト監視機能
  - データベース監視機能
  - リアルタイム表示
  - ログ記録機能
  - Windows バッチファイル対応
- **v1.1.0** - ダッシュボード機能追加
  - HTMLダッシュボード生成機能
  - 基本・高度な2種類のダッシュボード
  - コマンドラインオプション対応
  - 自動ブラウザ起動機能