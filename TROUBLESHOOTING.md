# Health Monitor - トラブルシューティングガイド

## 一般的な問題と解決方法

### インストール関連の問題

#### 問題: "python は内部コマンドまたは外部コマンドとして認識されていません"
**原因**: PythonがPATHに追加されていない

**解決方法**:
1. Pythonを再インストールし、「Add Python to PATH」にチェックを入れる
2. または手動でPATHを設定:
   ```cmd
   # システム環境変数にPythonのパスを追加
   # 例: C:\Python39\;C:\Python39\Scripts\
   ```

#### 問題: psycopg2のインストールエラー
**エラーメッセージ**: "Microsoft Visual C++ 14.0 is required"

**解決方法**:
1. **推奨**: `psycopg2-binary` を使用（requirements.txtで指定済み）
   ```cmd
   pip install psycopg2-binary
   ```

2. **代替**: Microsoft C++ Build Toolsをインストール
   - [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)をダウンロード
   - 「C++ build tools」をインストール

#### 問題: 仮想環境の作成に失敗
**エラーメッセージ**: "venv module not available"

**解決方法**:
```cmd
# Python venvモジュールを明示的にインストール
python -m pip install --user virtualenv

# または別の方法で仮想環境を作成
pip install virtualenv
virtualenv health_monitor_env
```

### 設定ファイル関連の問題

#### 問題: "config/websites.json が見つかりません"
**解決方法**:
1. サンプルファイルからコピー:
   ```cmd
   copy config\websites.json.sample config\websites.json
   ```

2. 手動で作成:
   ```json
   {
     "websites": [
       {
         "name": "テストサイト",
         "url": "https://www.google.com",
         "timeout": 10,
         "expected_status": 200
       }
     ]
   }
   ```

#### 問題: JSON構文エラー
**エラーメッセージ**: "JSONDecodeError: Expecting ',' delimiter"

**解決方法**:
1. JSON構文チェッカーでファイルを検証
2. 一般的な構文エラー:
   - 最後の要素の後にカンマがある
   - 文字列がダブルクォートで囲まれていない
   - 括弧の対応が取れていない

**正しい形式**:
```json
{
  "websites": [
    {
      "name": "サイト1",
      "url": "https://example1.com",
      "timeout": 10,
      "expected_status": 200
    },
    {
      "name": "サイト2",
      "url": "https://example2.com",
      "timeout": 15,
      "expected_status": 200
    }
  ]
}
```

### 接続関連の問題

#### 問題: Webサイトへの接続が失敗する
**症状**: すべてのWebサイトが赤色（エラー）で表示される

**診断方法**:
1. 手動でURLにアクセスして確認
2. コマンドプロンプトでpingテスト:
   ```cmd
   ping www.google.com
   ```

**解決方法**:
1. **プロキシ設定**: 企業環境でプロキシが必要な場合
   ```cmd
   set HTTP_PROXY=http://proxy.company.com:8080
   set HTTPS_PROXY=http://proxy.company.com:8080
   ```

2. **ファイアウォール設定**: Windows Defenderファイアウォールの確認
   - 「Windows セキュリティ」→「ファイアウォールとネットワーク保護」
   - Pythonアプリケーションの通信を許可

3. **DNS設定**: DNS解決の問題
   ```cmd
   nslookup www.google.com
   ipconfig /flushdns
   ```

#### 問題: データベース接続が失敗する
**症状**: すべてのデータベースが赤色（エラー）で表示される

**診断方法**:
1. 接続情報の確認:
   ```cmd
   # PostgreSQLクライアントでテスト接続
   psql -h hostname -p 5432 -U username -d database
   ```

2. ネットワーク接続の確認:
   ```cmd
   telnet hostname 5432
   ```

**解決方法**:
1. **認証情報の確認**:
   - ユーザー名、パスワードが正しいか
   - データベース名が存在するか

2. **SSL設定の調整**:
   ```json
   {
     "sslmode": "disable"  // SSL接続を無効にしてテスト
   }
   ```

3. **ファイアウォール設定**:
   - データベースサーバーのファイアウォール設定
   - ポート5432の開放確認

4. **Azure PostgreSQL固有の問題**:
   - ユーザー名の形式: `username@servername`
   - SSL接続が必須: `"sslmode": "require"`

### 実行時の問題

#### 問題: アプリケーションが起動しない
**エラーメッセージ**: "ModuleNotFoundError: No module named 'requests'"

**解決方法**:
1. 依存関係の再インストール:
   ```cmd
   pip install -r requirements.txt
   ```

2. 仮想環境の確認:
   ```cmd
   # 仮想環境が有効化されているか確認
   where python
   ```

#### 問題: メモリ使用量が増加し続ける
**症状**: 長時間実行後にシステムが重くなる

**解決方法**:
1. 定期的な再起動スケジュールの設定
2. 監視間隔の調整（負荷軽減）
3. ログファイルの定期削除

#### 問題: ログファイルが作成されない
**解決方法**:
1. ログディレクトリの権限確認:
   ```cmd
   # logsディレクトリの作成
   mkdir logs
   
   # 権限の確認
   icacls logs
   ```

2. ディスク容量の確認:
   ```cmd
   dir C:\ 
   ```

### パフォーマンス関連の問題

#### 問題: 監視の応答が遅い
**症状**: ステータス更新に時間がかかる

**解決方法**:
1. **タイムアウト値の調整**:
   ```json
   {
     "timeout": 5  // デフォルトの10秒から短縮
   }
   ```

2. **監視対象の削減**: 不要な監視対象を削除

3. **並列処理の最適化**: 同時実行数の調整

#### 問題: CPU使用率が高い
**解決方法**:
1. 監視間隔の延長
2. 不要な監視対象の削除
3. ログレベルの調整

### ネットワーク関連の問題

#### 問題: 間欠的な接続エラー
**症状**: 時々接続が失敗する

**解決方法**:
1. **リトライ機能の活用**: アプリケーションに組み込み済み
2. **タイムアウト値の調整**: より長い値に設定
3. **ネットワーク品質の確認**: 
   ```cmd
   ping -t www.google.com
   ```

#### 問題: プロキシ環境での接続エラー
**解決方法**:
1. 環境変数の設定:
   ```cmd
   set HTTP_PROXY=http://username:password@proxy.company.com:8080
   set HTTPS_PROXY=http://username:password@proxy.company.com:8080
   set NO_PROXY=localhost,127.0.0.1
   ```

2. プロキシ認証が必要な場合の設定確認

### Windows固有の問題

#### 問題: 文字化けが発生する
**解決方法**:
1. コマンドプロンプトの文字コード設定:
   ```cmd
   chcp 65001  # UTF-8に設定
   ```

2. フォントの変更: コマンドプロンプトのプロパティでフォントを変更

#### 問題: バッチファイルが実行できない
**エラーメッセージ**: "実行ポリシーにより実行が制限されています"

**解決方法**:
1. PowerShell実行ポリシーの確認:
   ```powershell
   Get-ExecutionPolicy
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. バッチファイルの権限確認:
   ```cmd
   icacls start_monitor.bat
   ```

## 診断用コマンド

### システム情報の確認
```cmd
# Python環境の確認
python --version
pip --version
pip list

# ネットワーク設定の確認
ipconfig /all
netstat -an | findstr :5432

# システムリソースの確認
tasklist | findstr python
```

### ログの確認
```cmd
# 最新のログファイルを表示
for /f %i in ('dir /b /od logs\*.log') do set newest=%i
type logs\%newest%

# エラーメッセージの検索
findstr /i "error" logs\*.log
findstr /i "failed" logs\*.log
```

### 設定ファイルの検証
```cmd
# JSON構文の確認
python -c "import json; print('websites.json OK' if json.load(open('config/websites.json')) else 'Error')"
python -c "import json; print('databases.json OK' if json.load(open('config/databases.json')) else 'Error')"
```

## サポートが必要な場合

### 情報収集
問題報告時には以下の情報を含めてください：

1. **環境情報**:
   - Windows バージョン
   - Python バージョン
   - インストールされているパッケージ一覧

2. **エラー情報**:
   - 完全なエラーメッセージ
   - エラー発生時の操作手順
   - ログファイルの内容

3. **設定情報**:
   - 設定ファイルの内容（パスワードは除く）
   - ネットワーク環境の詳細

### 情報収集用スクリプト
```cmd
# 診断情報を収集
echo "=== システム情報 ===" > diagnostic.txt
python --version >> diagnostic.txt
pip list >> diagnostic.txt
echo "=== 設定ファイル ===" >> diagnostic.txt
type config\websites.json >> diagnostic.txt
echo "=== 最新ログ ===" >> diagnostic.txt
for /f %i in ('dir /b /od logs\*.log') do type logs\%i >> diagnostic.txt
```

このファイルを作成して、サポートに送信してください。