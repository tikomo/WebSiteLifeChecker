@echo off
chcp 65001 >nul
REM Health Monitor - インストール検証スクリプト
REM このスクリプトはHealth Monitorが正しくセットアップされているかを確認します

echo ========================================
echo Health Monitor インストール検証
echo ========================================

set ERROR_COUNT=0

REM 現在のディレクトリを保存
set ORIGINAL_DIR=%CD%

REM スクリプトのディレクトリに移動
cd /d "%~dp0"

echo.
echo [1/8] Pythonのバージョン確認...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ エラー: Pythonが見つかりません
    set /a ERROR_COUNT+=1
) else (
    python --version
    echo ✅ Python OK
)

echo.
echo [2/8] 仮想環境の確認...
if exist "health_monitor_env\Scripts\activate.bat" (
    echo ✅ 仮想環境が見つかりました
    call health_monitor_env\Scripts\activate.bat
) else (
    echo ⚠️  警告: 仮想環境が見つかりません（システムPythonを使用）
)

echo.
echo [3/8] 必要なパッケージの確認...
python -c "import requests; print('✅ requests:', requests.__version__)" 2>nul
if errorlevel 1 (
    echo ❌ エラー: requests パッケージが見つかりません
    set /a ERROR_COUNT+=1
)

python -c "import psycopg2; print('✅ psycopg2:', psycopg2.__version__)" 2>nul
if errorlevel 1 (
    echo ❌ エラー: psycopg2 パッケージが見つかりません
    set /a ERROR_COUNT+=1
)

python -c "import colorama; print('✅ colorama:', colorama.__version__)" 2>nul
if errorlevel 1 (
    echo ❌ エラー: colorama パッケージが見つかりません
    set /a ERROR_COUNT+=1
)

echo.
echo [4/8] プロジェクト構造の確認...
if exist "health_monitor\main.py" (
    echo ✅ メインアプリケーション: health_monitor\main.py
) else (
    echo ❌ エラー: health_monitor\main.py が見つかりません
    set /a ERROR_COUNT+=1
)

if exist "run_health_monitor.py" (
    echo ✅ 実行スクリプト: run_health_monitor.py
) else (
    echo ❌ エラー: run_health_monitor.py が見つかりません
    set /a ERROR_COUNT+=1
)

echo.
echo [5/8] 設定ファイルの確認...
if exist "config\websites.json" (
    echo ✅ Webサイト設定: config\websites.json
    python -c "import json; json.load(open('config/websites.json')); print('  📄 JSON構文 OK')" 2>nul
    if errorlevel 1 (
        echo ❌ エラー: websites.json の構文エラー
        set /a ERROR_COUNT+=1
    )
) else (
    echo ⚠️  警告: config\websites.json が見つかりません
    if exist "config\websites.json.sample" (
        echo   💡 config\websites.json.sample からコピーしてください
    )
)

if exist "config\databases.json" (
    echo ✅ データベース設定: config\databases.json
    python -c "import json; json.load(open('config/databases.json')); print('  📄 JSON構文 OK')" 2>nul
    if errorlevel 1 (
        echo ❌ エラー: databases.json の構文エラー
        set /a ERROR_COUNT+=1
    )
) else (
    echo ⚠️  警告: config\databases.json が見つかりません
    if exist "config\databases.json.sample" (
        echo   💡 config\databases.json.sample からコピーしてください
    )
)

echo.
echo [6/8] ログディレクトリの確認...
if exist "logs" (
    echo ✅ ログディレクトリ: logs\
) else (
    echo ⚠️  警告: logs ディレクトリが見つかりません
    mkdir logs
    echo   📁 logs ディレクトリを作成しました
)

echo.
echo [7/8] 実行スクリプトの確認...
if exist "start_monitor.bat" (
    echo ✅ 起動スクリプト: start_monitor.bat
) else (
    echo ❌ エラー: start_monitor.bat が見つかりません
    set /a ERROR_COUNT+=1
)

if exist "setup_environment.bat" (
    echo ✅ セットアップスクリプト: setup_environment.bat
) else (
    echo ❌ エラー: setup_environment.bat が見つかりません
    set /a ERROR_COUNT+=1
)

echo.
echo [8/8] アプリケーションの動作テスト...
python -c "
try:
    from health_monitor.main import main
    print('✅ アプリケーションのインポート OK')
except ImportError as e:
    print('❌ エラー: アプリケーションのインポートに失敗')
    print('   詳細:', str(e))
    exit(1)
except Exception as e:
    print('⚠️  警告: インポート時に問題が発生')
    print('   詳細:', str(e))
" 2>nul
if errorlevel 1 (
    set /a ERROR_COUNT+=1
)

echo.
echo ========================================
echo 検証結果
echo ========================================

if %ERROR_COUNT% EQU 0 (
    echo ✅ すべての検証に合格しました！
    echo.
    echo Health Monitorを起動するには:
    echo   start_monitor.bat
    echo.
    echo 設定を変更するには:
    echo   config\websites.json   - Webサイト監視設定
    echo   config\databases.json  - データベース監視設定
) else (
    echo ❌ %ERROR_COUNT% 個のエラーが見つかりました
    echo.
    echo 解決方法:
    echo 1. setup_environment.bat を実行してセットアップを完了
    echo 2. TROUBLESHOOTING.md を参照してエラーを解決
    echo 3. 必要に応じて pip install -r requirements.txt を実行
)

echo.
echo 詳細なセットアップ手順: SETUP_WINDOWS.md
echo トラブルシューティング: TROUBLESHOOTING.md
echo ユーザーガイド: USER_GUIDE.md

:end
REM 元のディレクトリに戻る
cd /d "%ORIGINAL_DIR%"
pause