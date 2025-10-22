@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul 2>&1
cls

REM Parse command line arguments
set "auto_open="
set "skip_prompt="

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--open" set "auto_open=1"
if /i "%~1"=="--no-prompt" set "skip_prompt=1"
if /i "%~1"=="-o" set "auto_open=1"
if /i "%~1"=="-n" set "skip_prompt=1"
shift
goto parse_args
:args_done

echo ========================================
echo Health Monitor - Dashboard Generator
echo ========================================
echo.

echo Generating HTML dashboard...
python log_viewer.py --output dashboard.html --days 1

if !ERRORLEVEL! EQU 0 (
    echo.
    echo SUCCESS: Dashboard generated successfully!
    echo FILE: dashboard.html
    echo.
    
    REM Handle browser opening
    if defined auto_open (
        echo Opening dashboard in browser...
        start dashboard.html
        goto skip_pause
    )
    
    if defined skip_prompt (
        echo Dashboard generated. Use --open or -o to automatically open in browser.
        goto skip_pause
    )
    
    REM Default behavior - ask user
    echo Open dashboard in browser? ^(Y/N^)
    set /p choice="Your choice: "
    
    if /i "!choice!"=="Y" (
        echo Opening dashboard in browser...
        start dashboard.html
    ) else (
        echo Please open dashboard.html manually in your browser.
    )
    
) else (
    echo.
    echo ERROR: Failed to generate dashboard.
    echo Please check Python environment and log files.
)

:skip_pause
if not defined skip_prompt (
    echo.
    pause
)