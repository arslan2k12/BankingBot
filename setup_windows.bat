@echo off
setlocal enabledelayedexpansion

REM 🏦 Banking Bot Workshop Setup Script for Windows
REM This script automates the entire backend setup process

echo 🎯 Banking Bot Workshop Setup Starting...
echo ========================================
echo.

REM Function to print colored output (Windows compatible)
echo [INFO] Checking prerequisites...

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo [ERROR] Please install Python 3.11 or higher from https://www.python.org/downloads/
    echo [ERROR] Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found

REM Check if we're in the BankingBot directory
if not exist "requirements.txt" (
    echo [ERROR] Please run this script from the BankingBot directory
    echo [ERROR] Current directory: %cd%
    pause
    exit /b 1
)

echo [SUCCESS] Running from correct directory: %cd%

REM Step 1: Create and activate virtual environment
echo [INFO] Step 1/7: Setting up Python virtual environment...

if exist "venv_bankbot" (
    echo [WARNING] Virtual environment already exists. Removing old one...
    rmdir /s /q venv_bankbot
)

python -m venv venv_bankbot
if not exist "venv_bankbot" (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment created

REM Activate virtual environment
call venv_bankbot\Scripts\activate.bat
echo [SUCCESS] Virtual environment activated

REM Step 2: Upgrade pip and install dependencies
echo [INFO] Step 2/7: Installing Python dependencies...
echo [WARNING] This may take 2-5 minutes depending on your internet connection...

python -m pip install --upgrade pip >nul 2>&1
echo [SUCCESS] Pip upgraded

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo [ERROR] Check your internet connection and try again
    pause
    exit /b 1
)
echo [SUCCESS] All Python dependencies installed

REM Step 3: Set up environment variables
echo [INFO] Step 3/7: Setting up environment configuration...

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [SUCCESS] Created .env file from template
    ) else (
        echo [ERROR] .env.example file not found
        pause
        exit /b 1
    )
) else (
    echo [WARNING] .env file already exists, skipping...
)

REM Step 4: Create necessary directories
echo [INFO] Step 4/7: Creating required directories...

if not exist "data" mkdir data
if not exist "data\chromadb" mkdir data\chromadb
if not exist "data\checkpoints" mkdir data\checkpoints
if not exist "data\sample_documents" mkdir data\sample_documents
if not exist "logs" mkdir logs

echo [SUCCESS] Directories created

REM Step 5: Create sample data
echo [INFO] Step 5/7: Creating sample banking data...

python src/ingestion_app/create_sample_data.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create sample data
    pause
    exit /b 1
)

echo [SUCCESS] Sample banking data created

REM Step 6: Create sample documents if they don't exist
echo [INFO] Step 6/7: Setting up sample documents...

if not exist "data\sample_documents\bank_policies.txt" (
    (
    echo BANK POLICIES AND PROCEDURES
    echo.
    echo INTERNATIONAL TRANSFER FEES:
    echo - Wire transfers: $25 for amounts under $1,000, $15 for amounts over $1,000
    echo - Online transfers: $5 flat fee
    echo - Same-day transfers: Additional $10 fee
    echo.
    echo ACCOUNT MINIMUMS:
    echo - Checking Account: $100 minimum balance
    echo - Savings Account: $500 minimum balance
    echo - Premium Account: $2,500 minimum balance
    echo.
    echo OVERDRAFT POLICIES:
    echo - Overdraft fee: $35 per transaction
    echo - Daily limit: 4 overdraft fees maximum
    echo - Grace period: 24 hours to deposit funds
    echo.
    echo CUSTOMER SERVICE:
    echo - Phone: 1-800-BANK-HELP ^(24/7^)
    echo - Online chat: Available 8 AM - 10 PM EST
    echo - Branch hours: Monday-Friday 9 AM - 5 PM, Saturday 9 AM - 1 PM
    ) > "data\sample_documents\bank_policies.txt"
)

if not exist "data\sample_documents\credit_card_benefits.txt" (
    (
    echo CREDIT CARD BENEFITS GUIDE
    echo.
    echo CASHBACK REWARDS:
    echo - Groceries: 3%% cashback
    echo - Gas: 2%% cashback
    echo - All other purchases: 1%% cashback
    echo - Bonus: 5%% on rotating quarterly categories
    echo.
    echo TRAVEL BENEFITS:
    echo - No foreign transaction fees
    echo - Travel insurance up to $100,000
    echo - Lost luggage reimbursement up to $500
    echo - Airport lounge access ^(Premium cards only^)
    echo.
    echo PURCHASE PROTECTION:
    echo - Extended warranty: Doubles manufacturer warranty up to 1 year
    echo - Purchase protection: 90 days against theft/damage
    echo - Price protection: Refund price differences within 60 days
    echo.
    echo SECURITY FEATURES:
    echo - Zero liability for fraudulent charges
    echo - Real-time fraud alerts
    echo - Chip technology and contactless payments
    echo - Virtual card numbers for online shopping
    echo.
    echo CREDIT LIMITS:
    echo - Standard Card: $500 - $5,000
    echo - Gold Card: $2,000 - $15,000
    echo - Platinum Card: $5,000 - $50,000
    ) > "data\sample_documents\credit_card_benefits.txt"
)

echo [SUCCESS] Sample documents ready

REM Step 7: Final setup
echo [INFO] Step 7/7: Final setup and validation...

REM Create a startup script for easy server management
(
echo @echo off
echo cd /d "%%~dp0"
echo call venv_bankbot\Scripts\activate.bat
echo echo 🏦 Starting Banking Bot API Server...
echo echo 📍 API Documentation: http://localhost:2024/docs
echo echo 🔍 Health Check: http://localhost:2024/health
echo echo Press Ctrl+C to stop the server
echo echo.
echo uvicorn src.app.main:app --host 0.0.0.0 --port 2024 --reload
echo pause
) > start_banking_bot.bat

echo [SUCCESS] Created start_banking_bot.bat script

REM Test database connection
echo [INFO] Testing database connection...
python -c "import sqlite3; import os; conn = sqlite3.connect('data/banking_bot.db') if os.path.exists('data/banking_bot.db') else exit(1); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM users'); user_count = cursor.fetchone()[0]; cursor.execute('SELECT COUNT(*) FROM accounts'); account_count = cursor.fetchone()[0]; cursor.execute('SELECT COUNT(*) FROM transactions'); transaction_count = cursor.fetchone()[0]; conn.close(); print(f'✅ Database ready: {user_count} users, {account_count} accounts, {transaction_count} transactions')"

if %errorlevel% neq 0 (
    echo [ERROR] Database validation failed
    pause
    exit /b 1
)

echo [SUCCESS] Database validation passed

echo.
echo 🎉 SETUP COMPLETED SUCCESSFULLY!
echo =================================
echo.
echo [SUCCESS] ✅ Virtual environment created and activated
echo [SUCCESS] ✅ All dependencies installed
echo [SUCCESS] ✅ Sample data created (3 users, 6 accounts, 50+ transactions)
echo [SUCCESS] ✅ Sample documents processed
echo [SUCCESS] ✅ Database validated
echo.
echo 📋 IMPORTANT: Next Steps
echo ========================
echo.
echo [WARNING] 1. ADD YOUR OPENAI API KEY:
echo    - Edit the .env file: notepad .env
echo    - Add your OpenAI API key: OPENAI_API_KEY=sk-your-key-here
echo    - Get API key from: https://platform.openai.com/api-keys
echo.
echo [WARNING] 2. START THE BACKEND SERVER:
echo    Double-click: start_banking_bot.bat
echo    OR run: venv_bankbot\Scripts\activate.bat ^&^& uvicorn src.app.main:app --host 0.0.0.0 --port 2024 --reload
echo.
echo [WARNING] 3. SET UP THE FRONTEND:
echo    Run the frontend setup script in the banking-bot-ui folder
echo.
echo 🧪 TEST USERS CREATED:
echo ======================
echo Username: john_doe     ^| Password: password123
echo Username: jane_smith   ^| Password: password123
echo Username: mike_johnson ^| Password: password123
echo.
echo 🔗 USEFUL LINKS:
echo ================
echo API Docs:    http://localhost:2024/docs
echo Health:      http://localhost:2024/health
echo Frontend:    http://localhost:3000 (after frontend setup)
echo.
echo [SUCCESS] Happy coding! 🚀
echo.
echo Press any key to continue...
pause >nul
