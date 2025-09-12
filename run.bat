@echo off
REM Quick launcher for Badminton Slot Checker
REM This batch file makes it easy to run the checker on Windows

echo.
echo 🏸 Badminton Slot Checker Launcher
echo =======================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "src\main.py" (
    echo ❌ main.py not found. Please run this from the project root directory.
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist ".venv" (
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Show menu
echo.
echo Choose an option:
echo 1. Run setup (first time)
echo 2. Test configuration  
echo 3. Check slots once
echo 4. Start continuous monitoring
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo 🔧 Running setup...
    python setup.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo 🧪 Testing configuration...
    cd src
    python main.py --mode test
    cd ..
    pause
) else if "%choice%"=="3" (
    echo.
    echo 🔍 Checking slots once...
    cd src
    python main.py --mode single
    cd ..
    pause  
) else if "%choice%"=="4" (
    echo.
    echo 🔄 Starting continuous monitoring...
    echo Press Ctrl+C to stop
    cd src
    python main.py --mode continuous
    cd ..
    pause
) else if "%choice%"=="5" (
    echo.
    echo 👋 Goodbye!
    exit /b 0
) else (
    echo.
    echo ❌ Invalid choice. Please run the script again.
    pause
)

echo.
echo Press any key to exit...
pause >nul
