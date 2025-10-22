# Health Monitor - Windows セットアップガイド

## 概要
Health MonitorはWebサイトとPostgreSQLデータベースの生存確認を行うPythonアプリケーションです。
このガイドではWindows環境での初期セットアップ手順を説明します。

## 前提条件

### Python 3.8以上のインストール
1. [Python公式サイト](https://www.python.org/downloads/)からPython 3.8以上をダウンロード
2. インストール時に「Add Python to PATH」にチェックを入れる
3. コマンドプロンプトで確認:
   ```cmd
   python --version
   pip --version
   ```

### PostgreSQL接続用ライブラリ（オプション）
データベース監視を使用する場合、PostgreSQLクライアントライブラリが必要です：

**方法1: Microsoft C++ Build Toolsをインストール**
1. [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)をダウンロード
2. 「C++ build tools」をインストール

**方法2: 事前コンパイル済みバイナリを使用**
requirements.txtでは`psycopg2-binary`を指定しているため、通常は追加インストール不要です。

## インストール手順

### 1. プロジェクトのダウンロード
```cmd
# GitHubからクローン（または手動でダウンロード）
git clone <repository-url>
cd health-monitoring-tool
```

### 2. 仮想環境の作成（推奨）
```cmd
# 仮想環境を作成
python -m venv health_monitor_env

# 仮想環境を有効化
health_monitor_env\Scripts\activate

# 有効化の確認（プロンプトに(health_monitor_env)が表示される）
```

### 3. 依存関係のインストール
```cmd
# 必要なパッケージをインストール
pip install -r requirements.txt

# インストール確認
pip list
```

### 4. 設定ファイルの準備

#### Webサイト監視設定
`config/websites.json`を編集して監視対象のWebサイトを設定：

```json
{
  "websites": [
    {
      "name": "会社のWebサイト",
      "url": "https://www.example.com",
      "timeout": 10,
      "expected_status": 200
    },
    {
      "name": "APIエンドポイント",
      "url": "https://api.example.com/health",
      "timeout": 15,
      "expected_status": 200
    }
  ]
}
```

**設定項目説明:**
- `name`: 表示用の名前
- `url`: 監視対象のURL
- `timeout`: タイムアウト時間（秒）
- `expected_status`: 期待するHTTPステータスコード

#### データベース監視設定
`config/databases.json`を編集して監視対象のデータベースを設定：

```json
{
  "databases": [
    {
      "name": "本番データベース",
      "host": "db.example.com",
      "port": 5432,
      "database": "production",
      "username": "monitor_user",
      "password": "your_password",
      "sslmode": "require"
    }
  ]
}
```

**設定項目説明:**
- `name`: 表示用の名前
- `host`: データベースホスト名
- `port`: ポート番号（通常5432）
- `database`: データベース名
- `username`: 接続ユーザー名
- `password`: パスワード
- `sslmode`: SSL接続モード（require/prefer/disable）

**Azure PostgreSQL接続例:**
```json
{
  "name": "Azure PostgreSQL",
  "host": "myserver.postgres.database.azure.com",
  "port": 5432,
  "database": "mydb",
  "username": "admin@myserver",
  "password": "your_password",
  "sslmode": "require"
}
```

## 実行方法

### 基本実行
```cmd
# メインアプリケーションを実行
python run_health_monitor.py

# または直接モジュールを実行
python -m health_monitor.main
```

### バックグラウンド実行
```cmd
# バックグラウンドで実行（ログファイルに出力）
python run_health_monitor.py > logs\monitor.log 2>&1

# Windowsサービスとして実行する場合は別途サービス化ツールが必要
```

## ディレクトリ構造

```
health-monitoring-tool/
├── health_monitor/          # メインアプリケーション
│   ├── main.py             # エントリーポイント
│   ├── config/             # 設定管理
│   ├── models/             # データモデル
│   └── services/           # ヘルスチェックサービス
├── config/                 # 設定ファイル
│   ├── websites.json       # Webサイト設定
│   └── databases.json      # データベース設定
├── logs/                   # ログファイル
├── tests/                  # テストファイル
├── requirements.txt        # Python依存関係
├── run_health_monitor.py   # 実行スクリプト
└── SETUP_WINDOWS.md        # このファイル
```

## 動作確認

### 1. 設定ファイルの検証
```cmd
# 設定ファイルの構文チェック
python -c "import json; print('websites.json:', json.load(open('config/websites.json'))); print('databases.json:', json.load(open('config/databases.json')))"
```

### 2. 接続テスト
```cmd
# 単発でのヘルスチェック実行
python -c "from health_monitor.main import main; main()"
```

### 3. ログファイルの確認
```cmd
# ログディレクトリの確認
dir logs

# 最新のログファイルを表示
type logs\health_monitor_YYYY-MM-DD.log
```

## セキュリティ考慮事項

### 1. パスワード管理
- 設定ファイルに平文でパスワードを保存しないことを推奨
- 環境変数やWindows資格情報マネージャーの使用を検討

### 2. ファイル権限
```cmd
# 設定ファイルのアクセス権限を制限
icacls config\databases.json /grant:r "%USERNAME%":F /inheritance:r
```

### 3. ネットワークセキュリティ
- ファイアウォール設定の確認
- VPN接続が必要な場合の設定

## 次のステップ

1. **自動起動設定**: Windowsタスクスケジューラーでの自動起動設定
2. **監視強化**: アラート通知機能の追加
3. **ダッシュボード**: Web UIの追加

詳細な設定やトラブルシューティングについては、`TROUBLESHOOTING.md`を参照してください。