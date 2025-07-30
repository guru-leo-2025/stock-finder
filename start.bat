@echo off
setlocal enabledelayedexpansion

REM ========================================
REM Kiwoom Trading System Launcher (Fixed)
REM ========================================

echo ========================================
echo Kiwoom Trading System Launcher (Fixed)
echo ========================================

REM 1. Check if running as Administrator
echo [1] Checking administrator privileges...
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Administrator privileges required
    echo.
    echo This script needs to run as Administrator to:
    echo - Access conda environments
    echo - Register OCX files if needed
    echo - Install packages system-wide
    echo.
    echo Please right-click this file and select "Run as administrator"
    pause
    exit /b 1
)
echo SUCCESS: Running with administrator privileges

REM 2. Check if Anaconda/Miniconda is installed
echo.
echo [2] Checking Anaconda/Miniconda installation...
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Conda not found in PATH
    echo.
    echo Please install Anaconda or Miniconda first:
    echo https://www.anaconda.com/download
    echo.
    echo After installation, restart this script
    pause
    exit /b 1
)
echo SUCCESS: Conda found

REM 3. Create and move to kiwoom directory
echo.
echo [3] Setting up kiwoom directory...
if not exist "C:\kiwoom" (
    mkdir "C:\kiwoom"
    echo SUCCESS: Created C:\kiwoom directory
) else (
    echo INFO: C:\kiwoom directory already exists
)

REM Copy current files to kiwoom directory if not already there
if not "%CD%"=="C:\kiwoom" (
    echo Copying files to C:\kiwoom...
    xcopy "%~dp0*.py" "C:\kiwoom\" /Y /Q >nul 2>&1
    xcopy "%~dp0*.bat" "C:\kiwoom\" /Y /Q >nul 2>&1
    xcopy "%~dp0*.txt" "C:\kiwoom\" /Y /Q >nul 2>&1
    xcopy "%~dp0*.md" "C:\kiwoom\" /Y /Q >nul 2>&1
    xcopy "%~dp0.env" "C:\kiwoom\" /Y /Q >nul 2>&1
    echo SUCCESS: Files copied to C:\kiwoom
)

REM Change to kiwoom directory
cd /d "C:\kiwoom"
echo SUCCESS: Changed to C:\kiwoom directory

REM 4. Check if kiwoom_32bit environment exists
echo.
echo [4] Checking conda environment...
call conda env list | findstr "kiwoom_32bit" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Creating kiwoom_32bit environment...
    echo This may take a few minutes...
    
    call conda create -n kiwoom_32bit python=3.10 -y
    if !ERRORLEVEL! neq 0 (
        echo ERROR: Failed to create conda environment
        pause
        exit /b 1
    )
    
    echo SUCCESS: kiwoom_32bit environment created
) else (
    echo INFO: kiwoom_32bit environment already exists
)

REM 5. Activate conda environment
echo.
echo [5] Activating kiwoom_32bit environment...
call conda activate kiwoom_32bit
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate kiwoom_32bit environment
    pause
    exit /b 1
)
echo SUCCESS: kiwoom_32bit environment activated

REM 6. Verify Python architecture
echo.
echo [6] Verifying Python installation...
python -c "import platform; print('Python Version:', platform.python_version()); print('Architecture:', platform.architecture()[0])" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not working properly
    pause
    exit /b 1
)
echo SUCCESS: Python installation verified

REM 7. Check and install packages only if needed
echo.
echo [7] Checking package dependencies...

REM Check if packages are already installed
python -c "import PyQt5; import pandas; import requests; import slack_sdk; import openai; print('All packages already installed')" 2>nul
if %ERRORLEVEL%==0 (
    echo SUCCESS: All required packages are already installed
    goto :skip_package_install
)

echo Some packages missing, installing...

REM Install core packages with conda to avoid compilation issues
echo Installing core packages with conda...
call conda install -c conda-forge pandas numpy matplotlib -y --quiet
if !ERRORLEVEL! neq 0 (
    echo WARNING: Some conda packages failed, continuing with pip...
)

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install packages one by one to identify issues
echo Installing PyQt5...
pip install PyQt5==5.15.10 --quiet
if !ERRORLEVEL! neq 0 (
    echo ERROR: Failed to install PyQt5
    pause
    exit /b 1
)

echo Installing pywin32...
pip install pywin32 --quiet
if !ERRORLEVEL! neq 0 (
    echo ERROR: Failed to install pywin32
    pause
    exit /b 1
)

echo Installing web and async packages...
pip install requests aiohttp --quiet

echo Installing environment packages...
pip install python-dotenv psutil --quiet

echo Installing AI and communication packages...
pip install openai slack-sdk --quiet

echo Installing utility packages...
pip install colorlog schedule pydantic --quiet

echo Installing optional packages...
pip install openpyxl yfinance --quiet

echo SUCCESS: Package installation completed

:skip_package_install

REM 8. Create necessary directories
echo.
echo [8] Creating system directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
echo SUCCESS: System directories created

REM 9. Check .env file
echo.
echo [9] Checking configuration...
if not exist ".env" (
    echo WARNING: .env file not found
    echo Creating template .env file...
    echo.
    
    echo # Kiwoom API Configuration > .env
    echo KIWOOM_USER_ID=your_kiwoom_user_id >> .env
    echo KIWOOM_PASSWORD=your_kiwoom_password >> .env
    echo KIWOOM_CERT_PASSWORD=your_cert_password >> .env
    echo. >> .env
    echo # OpenAI Configuration >> .env
    echo OPENAI_API_KEY=sk-your_openai_api_key >> .env
    echo. >> .env
    echo # Slack Configuration >> .env
    echo SLACK_BOT_TOKEN=xoxb-your_slack_bot_token >> .env
    echo SLACK_CHANNEL=#trading-alerts >> .env
    echo. >> .env
    REM KRX API configuration removed
    echo # DART Financial Data Configuration >> .env
    echo DART_API_KEY=your_dart_api_key >> .env
    echo. >> .env
    echo # Trading Configuration >> .env
    echo SCREENING_CONDITION_NAME=10stars >> .env
    echo MAX_STOCKS_TO_ANALYZE=10 >> .env
    echo TRADING_MODE=TEST >> .env
    echo. >> .env
    echo # Logging Configuration >> .env
    echo LOG_LEVEL=INFO >> .env
    echo LOG_FILE=logs/kiwoom_trading.log >> .env
    
    echo Template .env file created
    echo Please edit .env file with your actual credentials before next run
) else (
    echo SUCCESS: .env file found
)

REM 10. Validate configuration
echo.
echo [10] Validating configuration...
python config.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: Configuration validation failed
    echo Please check your .env file
    pause
    exit /b 1
)
echo SUCCESS: Configuration validated

REM 11. Check OpenAPI
echo.
echo [11] Checking Kiwoom OpenAPI...
if exist "C:\OpenAPI\KHOpenAPI.ocx" (
    echo SUCCESS: Kiwoom OpenAPI found at C:\OpenAPI\
    set KIWOOM_API_FOUND=true
) else (
    echo WARNING: Kiwoom OpenAPI not found
    echo System will run in TEST mode
    set KIWOOM_API_FOUND=false
)

REM 12. Check HTS
echo.
echo [12] Checking Kiwoom HTS...
tasklist | findstr nkrunlite >nul 2>&1
if %ERRORLEVEL%==0 (
    echo SUCCESS: Kiwoom HTS is running
    set KIWOOM_HTS_RUNNING=true
) else (
    echo INFO: Kiwoom HTS not running (OK for TEST mode)
    set KIWOOM_HTS_RUNNING=false
)

REM 13. Test system components
echo.
echo [13] Testing system components...

echo Testing configuration module...
python -c "from config import config; print('✅ Config module: OK')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Config module test failed
    pause
    exit /b 1
)

echo Testing Kiwoom API module...
python -c "from kiwoom_api import KiwoomAPI; print('✅ Kiwoom API module: OK')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Kiwoom API module test failed
    pause
    exit /b 1
)

REM KRX API module removed - no longer required
echo ✅ KRX API module: REMOVED (no longer required)

echo Testing Technical Analyzer module...
python -c "from technical_analyzer import TechnicalAnalyzer; print('✅ Technical Analyzer module: OK')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Technical Analyzer module test failed
    pause
    exit /b 1
)

echo Testing Slack Notifier module...
python -c "from slack_notifier import SlackNotifier; print('✅ Slack Notifier module: OK')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Slack Notifier module test failed
    pause
    exit /b 1
)

echo SUCCESS: All modules loaded successfully

REM 14. Display system status
echo.
echo ========================================
echo System Status Summary
echo ========================================
python -c "from config import config; print(f'Trading Mode: {config.trading.trading_mode}'); print(f'Screening Condition: {config.kiwoom.screening_condition}'); print(f'Max Stocks: {config.trading.max_stocks}')" 2>nul
echo Kiwoom API Available: %KIWOOM_API_FOUND%
echo Kiwoom HTS Running: %KIWOOM_HTS_RUNNING%
echo Working Directory: %CD%
echo ========================================

REM 15. Start the main system
echo.
echo [14] Starting Kiwoom Trading System...
echo.
echo Press Ctrl+C to stop the system gracefully
echo Logs will be saved to: logs/kiwoom_trading.log
echo.

if exist "main.py" (
    python main.py
    if !ERRORLEVEL! neq 0 (
        echo.
        echo ERROR: System encountered an error
        echo Check logs/kiwoom_trading.log for details
        pause
        exit /b 1
    )
) else (
    echo ERROR: main.py not found
    echo Please ensure all system files are present
    pause
    exit /b 1
)

REM 16. System shutdown
echo.
echo ========================================
echo System Shutdown Complete
echo ========================================
echo.
echo System has stopped gracefully
echo Check logs/kiwoom_trading.log for session details
echo.
pause