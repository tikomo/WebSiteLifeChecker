@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul 2>&1
cls
echo ========================================
echo Health Monitor - Dashboard Menu
echo ========================================
echo.
echo Available dashboards:
echo.
echo 1. Basic Dashboard (with prompt)
echo 2. Advanced Dashboard (with prompt)
echo 3. Generate Both (with prompt)
echo.
echo 4. Basic Dashboard (auto-open)
echo 5. Advanced Dashboard (auto-open)
echo 6. Generate Both (auto-open)
echo.
echo 7. Basic Dashboard (no prompt)
echo 8. Advanced Dashboard (no prompt)
echo.
echo 0. Exit
echo.

:menu
set /p choice="Please select (0-8): "

if "%choice%"=="1" (
    echo.
    echo Generating basic dashboard (with prompt)...
    call view_dashboard.bat
    goto end
) else if "%choice%"=="2" (
    echo.
    echo Generating advanced dashboard (with prompt)...
    call view_advanced_dashboard.bat
    goto end
) else if "%choice%"=="3" (
    echo.
    echo Generating both dashboards...
    echo.
    echo [1/2] Generating basic dashboard...
    python log_viewer.py --output dashboard.html --days 1
    set basic_result=!ERRORLEVEL!
    echo.
    echo [2/2] Generating advanced dashboard...
    python advanced_log_viewer.py --output advanced_dashboard.html --days 1
    set advanced_result=!ERRORLEVEL!
    echo.
    if !basic_result! EQU 0 if !advanced_result! EQU 0 (
        echo SUCCESS: Both dashboards generated successfully!
        echo FILES: dashboard.html, advanced_dashboard.html
        echo.
        echo Which dashboard to open?
        echo 1. Basic Dashboard
        echo 2. Advanced Dashboard
        echo 3. Both
        set /p open_choice="Your choice (1-3): "
        
        if "!open_choice!"=="1" (
            start dashboard.html
        ) else if "!open_choice!"=="2" (
            start advanced_dashboard.html
        ) else if "!open_choice!"=="3" (
            start dashboard.html
            start advanced_dashboard.html
        )
    ) else (
        echo ERROR: Failed to generate dashboards.
        if !basic_result! NEQ 0 echo - Basic dashboard generation failed
        if !advanced_result! NEQ 0 echo - Advanced dashboard generation failed
    )
    goto end
) else if "%choice%"=="4" (
    echo.
    echo Generating basic dashboard (auto-open)...
    call view_dashboard.bat --open --no-prompt
    goto end
) else if "%choice%"=="5" (
    echo.
    echo Generating advanced dashboard (auto-open)...
    call view_advanced_dashboard.bat --open --no-prompt
    goto end
) else if "%choice%"=="6" (
    echo.
    echo Generating both dashboards (auto-open)...
    call view_dashboard.bat --open --no-prompt
    call view_advanced_dashboard.bat --open --no-prompt
    goto end
) else if "%choice%"=="7" (
    echo.
    echo Generating basic dashboard (no prompt)...
    call view_dashboard.bat --no-prompt
    goto end
) else if "%choice%"=="8" (
    echo.
    echo Generating advanced dashboard (no prompt)...
    call view_advanced_dashboard.bat --no-prompt
    goto end
) else if "%choice%"=="0" (
    echo Exiting...
    goto end
) else (
    echo Invalid selection. Please enter 0-8.
    goto menu
)

:end
echo.
pause