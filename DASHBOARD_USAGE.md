# Health Monitor - ダッシュボード使用方法

Health MonitorのJSONログを美しいHTMLダッシュボードで表示する機能の詳細な使用方法を説明します。

## 📊 ダッシュボードの種類

### 1. 基本ダッシュボード
- **ファイル**: `dashboard.html`
- **特徴**: シンプルで軽量、現在のステータスと最新ログを表示
- **用途**: 日常的な監視状況の確認

### 2. 高度なダッシュボード
- **ファイル**: `advanced_dashboard.html`
- **特徴**: 稼働率統計、応答時間分析、自動更新機能付き
- **用途**: 詳細な分析、レポート作成、プレゼンテーション

## 🚀 基本的な使用方法

### 1. メニューから選択
```cmd
dashboard_menu.bat
```
統合メニューから8つのオプションを選択できます。

### 2. 直接実行

#### 基本ダッシュボード
```cmd
# プロンプト付き（デフォルト）
view_dashboard.bat

# 自動でブラウザを開く
view_dashboard.bat --open

# プロンプトなし（生成のみ）
view_dashboard.bat --no-prompt

# 短縮形
view_dashboard.bat -o    # --open と同じ
view_dashboard.bat -n    # --no-prompt と同じ
```

#### 高度なダッシュボード
```cmd
# プロンプト付き（デフォルト）
view_advanced_dashboard.bat

# 自動でブラウザを開く
view_advanced_dashboard.bat --open

# プロンプトなし（生成のみ）
view_advanced_dashboard.bat --no-prompt

# 短縮形
view_advanced_dashboard.bat -o    # --open と同じ
view_advanced_dashboard.bat -n    # --no-prompt と同じ
```

## オプション説明

| オプション | 短縮形 | 説明 |
|-----------|--------|------|
| `--open` | `-o` | ダッシュボード生成後、自動でブラウザを開く |
| `--no-prompt` | `-n` | ユーザーへの確認プロンプトを表示しない |

## 使用例

### 自動化スクリプトで使用
```cmd
REM CI/CDパイプラインやスケジュールタスクで使用
view_advanced_dashboard.bat --no-prompt
```

### 開発中の確認
```cmd
REM 生成してすぐに確認したい場合
view_advanced_dashboard.bat --open
```

### 通常の使用
```cmd
REM ユーザーに選択させたい場合（デフォルト）
view_advanced_dashboard.bat
```

## メニューオプション

ダッシュボードメニュー（`dashboard_menu.bat`）では以下のオプションが利用できます：

1. **Basic Dashboard (with prompt)** - 基本ダッシュボード（確認あり）
2. **Advanced Dashboard (with prompt)** - 高度なダッシュボード（確認あり）
3. **Generate Both (with prompt)** - 両方生成（確認あり）
4. **Basic Dashboard (auto-open)** - 基本ダッシュボード（自動オープン）
5. **Advanced Dashboard (auto-open)** - 高度なダッシュボード（自動オープン）
6. **Generate Both (auto-open)** - 両方生成（自動オープン）
7. **Basic Dashboard (no prompt)** - 基本ダッシュボード（確認なし）
8. **Advanced Dashboard (no prompt)** - 高度なダッシュボード（確認なし）

## 🎯 実用的な使用例

### 開発・運用シナリオ

#### 1. 毎朝の状況確認
```cmd
# 出社時の状況確認（自動でブラウザを開く）
view_advanced_dashboard.bat --open
```

#### 2. 障害対応時の詳細分析
```cmd
# 問題発生時の詳細確認（プロンプト付きで慎重に）
view_advanced_dashboard.bat
```

#### 3. 定期レポート作成
```cmd
# 週次レポート用（7日間のデータ）
python advanced_log_viewer.py --output weekly_report.html --days 7
```

#### 4. CI/CDパイプラインでの使用
```cmd
# 自動化スクリプトで使用（プロンプトなし）
view_advanced_dashboard.bat --no-prompt
```

#### 5. 運用会議での報告
```cmd
# プレゼンテーション用（両方生成して自動オープン）
dashboard_menu.bat
# → オプション6を選択
```

### バッチ処理での活用

#### 複数期間のレポート生成
```cmd
# 日次レポート
python advanced_log_viewer.py --output daily_report.html --days 1

# 週次レポート
python advanced_log_viewer.py --output weekly_report.html --days 7

# 月次レポート
python advanced_log_viewer.py --output monthly_report.html --days 30
```

#### カスタムログディレクトリの使用
```cmd
# 別のログディレクトリを使用
python log_viewer.py --log-dir backup_logs --output backup_dashboard.html --days 3
```

## 🔧 高度な設定

### Python直接実行のオプション

#### log_viewer.py（基本ダッシュボード）
```cmd
python log_viewer.py [オプション]
```

#### advanced_log_viewer.py（高度なダッシュボード）
```cmd
python advanced_log_viewer.py [オプション]
```

#### 共通オプション
| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--log-dir` | `logs` | ログディレクトリのパス |
| `--output` | `dashboard.html` / `advanced_dashboard.html` | 出力HTMLファイル名 |
| `--days` | `1` | 表示する日数 |

### 環境変数での設定
```cmd
# 環境変数でデフォルト設定を変更
set HEALTH_MONITOR_LOG_DIR=custom_logs
set HEALTH_MONITOR_DAYS=7
view_advanced_dashboard.bat --no-prompt
```

## 📱 ダッシュボードの機能

### 基本ダッシュボードの機能
- ✅ 現在のステータス一覧
- 📊 ステータス別統計
- 📝 最新ログエントリ（10件）
- 📱 レスポンシブデザイン
- 🎨 美しいUI/UX

### 高度なダッシュボードの機能
- 📈 稼働率統計（24時間）
- ⚡ 応答時間分析（平均・最大・最小）
- 🔄 自動更新機能（30秒間隔）
- 📊 詳細なサービス情報
- 📱 モバイル対応デザイン
- 🎯 インタラクティブな要素
- 📈 トレンド分析

### 自動更新機能の使用方法
1. 高度なダッシュボードを開く
2. 右上の「🔄 自動更新: OFF」ボタンをクリック
3. 30秒間隔で自動的にページが更新される
4. 再度クリックで無効化

## 🛠️ トラブルシューティング

### よくある問題と解決方法

#### 1. ダッシュボードが生成されない
**症状**: バッチファイル実行時にエラーが発生
**解決方法**:
```cmd
# Python環境の確認
python --version

# 必要なライブラリの確認
pip list | findstr requests

# ログファイルの存在確認
dir logs
```

#### 2. ブラウザが自動で開かない
**症状**: `--open` オプション使用時にブラウザが起動しない
**解決方法**:
- デフォルトブラウザが設定されているか確認
- 手動でHTMLファイルを開く
- セキュリティソフトの設定を確認

#### 3. 古いデータが表示される
**症状**: 最新のログが反映されない
**解決方法**:
```cmd
# 強制的に最新データで再生成
view_advanced_dashboard.bat --no-prompt
```

#### 4. 文字化けが発生する
**症状**: 日本語が正しく表示されない
**解決方法**:
- ブラウザの文字エンコーディングをUTF-8に設定
- ログファイルの文字エンコーディングを確認

## 📋 チェックリスト

### 初回使用時
- [ ] Python環境が正しくインストールされている
- [ ] 必要なライブラリがインストールされている
- [ ] ログファイルが存在する
- [ ] 書き込み権限がある

### 定期的な確認
- [ ] ログファイルのサイズが適切
- [ ] 古いログファイルの削除
- [ ] ダッシュボードの動作確認
- [ ] ブラウザの互換性確認

## 生成されるファイル

- **基本ダッシュボード**: `dashboard.html`
- **高度なダッシュボード**: `advanced_dashboard.html`

両方のファイルはプロジェクトルートに生成され、ブラウザで直接開くことができます。

## 📚 関連ドキュメント

- **README.md**: プロジェクト概要とクイックスタート
- **USER_GUIDE.md**: 詳細なユーザーガイド
- **TROUBLESHOOTING.md**: トラブルシューティング情報
- **SETUP_WINDOWS.md**: Windows環境でのセットアップ手順