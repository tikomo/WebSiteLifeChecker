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
echo Health Monitor - Advanced Dashboard
echo ========================================
echo.

echo Generating advanced HTML dashboard...
echo Features: Uptime stats, response analysis, auto-refresh
echo.

python advanced_log_viewer.py --output advanced_dashboard.html --days 1

if !ERRORLEVEL! EQU 0 (
    echo.
    echo SUCCESS: Advanced dashboard generated successfully!
    echo FILE: advanced_dashboard.html
    echo.
    echo Features included:
    echo   - Real-time uptime statistics
    echo   - Response time analysis
    echo   - Auto-refresh ^(30 second intervals^)
    echo   - Responsive design
    echo.
    
    REM Handle browser opening
    if defined auto_open (
        echo Opening advanced dashboard in browser...
        start advanced_dashboard.html
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
        echo Opening advanced dashboard in browser...
        start advanced_dashboard.html
    ) else (
        echo Please open advanced_dashboard.html manually in your browser.
    )
    
) else (
    echo.
    echo ERROR: Failed to generate advanced dashboard.
    echo Please check Python environment and log files.
)

:skip_pause
if not defined skip_prompt (
    echo.
    pause
)