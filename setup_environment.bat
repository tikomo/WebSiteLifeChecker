@echo off
chcp 65001 >nul
REM Health Monitor - 環境セットアップスクリプト
REM このスクリプトは初回セットアップ時に実行してください

echo ========================================
echo Health Monitor 環境セットアップ
echo ========================================

REM 現在のディレクトリを保存
set ORIGINAL_DIR=%CD%

REM スクリプトのディレクトリに移動
cd /d "%~dp0"

REM Pythonのバージョンチェック
echo Pythonのバージョンを確認中...
python --version
if errorlevel 1 (
    echo エラー: Pythonが見つかりません。
    echo Python 3.8以上をインストールしてください。
    echo https://www.python.org/downloads/
    pause
    goto :end
)

REM 仮想環境の作成
echo.
echo 仮想環境を作成中...
if exist "health_monitor_env" (
    echo 仮想環境は既に存在します。
) else (
    python -m venv health_monitor_env
    if errorlevel 1 (
        echo エラー: 仮想環境の作成に失敗しました。
        pause
        goto :end
    )
    echo 仮想環境が作成されました。
)

REM 仮想環境の有効化
echo 仮想環境を有効化中...
call health_monitor_env\Scripts\activate.bat

REM pipのアップグレード
echo pipをアップグレード中...
python -m pip install --upgrade pip

REM 依存関係のインストール
echo.
echo 依存関係をインストール中...
pip install -r requirements.txt
if errorlevel 1 (
    echo エラー: 依存関係のインストールに失敗しました。
    echo.
    echo PostgreSQL関連のエラーが発生した場合:
    echo 1. Microsoft C++ Build Tools をインストール
    echo 2. または psycopg2-binary を使用（requirements.txtで指定済み）
    pause
    goto :end
)

REM 設定ファイルのセットアップ
echo.
echo 設定ファイルをセットアップ中...

if not exist "config" mkdir config
if not exist "logs" mkdir logs

if not exist "config\websites.json" (
    if exist "config\websites.json.sample" (
        copy "config\websites.json.sample" "config\websites.json"
        echo websites.json をサンプルからコピーしました。
    ) else (
        echo 警告: websites.json.sample が見つかりません。
    )
) else (
    echo websites.json は既に存在します。
)

if not exist "config\databases.json" (
    if exist "config\databases.json.sample" (
        copy "config\databases.json.sample" "config\databases.json"
        echo databases.json をサンプルからコピーしました。
    ) else (
        echo 警告: databases.json.sample が見つかりません。
    )
) else (
    echo databases.json は既に存在します。
)

REM インストール確認
echo.
echo インストールを確認中...
python -c "import requests, psycopg2, colorama; print('すべての依存関係が正常にインストールされました。')"
if errorlevel 1 (
    echo 警告: 一部の依存関係でエラーが発生しました。
    pause
    goto :end
)

echo.
echo ========================================
echo セットアップが完了しました！
echo ========================================
echo.
echo 次のステップ:
echo 1. config\websites.json を編集して監視対象のWebサイトを設定
echo 2. config\databases.json を編集して監視対象のデータベースを設定
echo 3. start_monitor.bat を実行してHealth Monitorを起動
echo.
echo 設定ファイルの編集方法については SETUP_WINDOWS.md を参照してください。
echo.

:end
REM 元のディレクトリに戻る
cd /d "%ORIGINAL_DIR%"
pause