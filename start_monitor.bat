@echo off
chcp 65001 >nul
REM Health Monitor - Windows起動スクリプト
REM このスクリプトはHealth Monitorアプリケーションを起動します

echo ========================================
echo Health Monitor 起動中...
echo ========================================

REM 現在のディレクトリを保存
set ORIGINAL_DIR=%CD%

REM スクリプトのディレクトリに移動
cd /d "%~dp0"

REM 仮想環境が存在するかチェック
if exist "health_monitor_env\Scripts\activate.bat" (
    echo 仮想環境を有効化中...
    call health_monitor_env\Scripts\activate.bat
    if errorlevel 1 (
        echo 警告: 仮想環境の有効化に失敗しました。システムのPythonを使用します。
    )
) else (
    echo 警告: 仮想環境が見つかりません。システムのPythonを使用します。
)

REM Pythonが利用可能かチェック
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonが見つかりません。
    echo Python 3.8以上がインストールされていることを確認してください。
    pause
    goto :end
)

REM 必要なパッケージがインストールされているかチェック
python -c "import requests, psycopg2, colorama" >nul 2>&1
if errorlevel 1 (
    echo 警告: 必要なパッケージがインストールされていない可能性があります。
    echo pip install -r requirements.txt を実行してください。
    pause
)

REM 設定ファイルの存在チェック
if not exist "config\websites.json" (
    echo 警告: config\websites.json が見つかりません。
    if exist "config\websites.json.sample" (
        echo サンプルファイルをコピーしています...
        copy "config\websites.json.sample" "config\websites.json"
    ) else (
        echo config\websites.json.sample からコピーして設定を行ってください。
    )
)

if not exist "config\databases.json" (
    echo 警告: config\databases.json が見つかりません。
    if exist "config\databases.json.sample" (
        echo サンプルファイルをコピーしています...
        copy "config\databases.json.sample" "config\databases.json"
    ) else (
        echo config\databases.json.sample からコピーして設定を行ってください。
    )
)

REM ログディレクトリを作成
if not exist "logs" mkdir logs

echo.
echo Health Monitor を起動しています...
echo 停止するには Ctrl+C を押してください。
echo.

REM Health Monitorを実行
python run_health_monitor.py --log-all-checks

:end
REM 元のディレクトリに戻る
cd /d "%ORIGINAL_DIR%"

echo.
echo Health Monitor が終了しました。
pause