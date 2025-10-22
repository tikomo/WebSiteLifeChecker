@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul 2>&1
cls
echo ========================================
echo Health Monitor - Test Runner
echo ========================================
echo.

echo Available test options:
echo.
echo 1. Quick Tests (basic functionality)
echo 2. All Tests (complete test suite)
echo 3. Single Test (specify test module)
echo 0. Exit
echo.

:menu
set /p choice="Please select (0-3): "

if "%choice%"=="1" (
    echo.
    echo Running quick tests...
    python run_tests.py quick
    goto end
) else if "%choice%"=="2" (
    echo.
    echo Running all tests...
    python run_tests.py
    goto end
) else if "%choice%"=="3" (
    echo.
    echo Available test modules:
    echo - test_website_checker
    echo - test_database_checker
    echo - test_health_check_engine
    echo - test_log_manager
    echo - test_retry_handler
    echo - test_self_monitor
    echo - test_status_display
    echo - test_main_integration
    echo.
    set /p test_name="Enter test module name: "
    echo.
    echo Running single test: !test_name!
    python run_tests.py single !test_name!
    goto end
) else if "%choice%"=="0" (
    echo Exiting...
    goto end
) else (
    echo Invalid selection. Please enter 0-3.
    goto menu
)

:end
echo.
pause