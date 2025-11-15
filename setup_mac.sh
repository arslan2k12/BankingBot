#!/bin/bash

# 🏦 Banking Bot Workshop Setup Script for Mac
# This script automates the entire backend setup process

set -e  # Exit on any error

echo "🎯 Banking Bot Workshop Setup Starting..."
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $PYTHON_VERSION found"

# Check if we're in the BankingBot directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the BankingBot directory"
    print_error "Current directory: $(pwd)"
    exit 1
fi

print_success "Running from correct directory: $(pwd)"

# Step 1: Create and activate virtual environment
print_status "Step 1/7: Setting up Python virtual environment..."

if [ -d "venv_bankbot" ]; then
    print_warning "Virtual environment already exists. Removing old one..."
    rm -rf venv_bankbot
fi

python3 -m venv venv_bankbot
if [ ! -d "venv_bankbot" ]; then
    print_error "Failed to create virtual environment"
    exit 1
fi

print_success "Virtual environment created"

# Activate virtual environment
source venv_bankbot/bin/activate
print_success "Virtual environment activated"

# Step 2: Upgrade pip and install dependencies
print_status "Step 2/7: Installing Python dependencies..."
print_warning "This may take 2-5 minutes depending on your internet connection..."

pip install --upgrade pip > /dev/null 2>&1
print_success "Pip upgraded"

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi
print_success "All Python dependencies installed"

# Step 3: Set up environment variables
print_status "Step 3/7: Setting up environment configuration..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env file from template"
    else
        print_error ".env.example file not found"
        exit 1
    fi
else
    print_warning ".env file already exists, skipping..."
fi

# Step 4: Create necessary directories
print_status "Step 4/7: Creating required directories..."

mkdir -p data/chromadb
mkdir -p data/checkpoints
mkdir -p data/sample_documents
mkdir -p logs

print_success "Directories created"

# Step 5: Create sample data
print_status "Step 5/7: Creating sample banking data..."

python src/ingestion_app/create_sample_data.py
if [ $? -ne 0 ]; then
    print_error "Failed to create sample data"
    exit 1
fi

print_success "Sample banking data created"

# Step 6: Create sample documents if they don't exist
print_status "Step 6/7: Setting up sample documents..."

if [ ! -f "data/sample_documents/bank_policies.txt" ]; then
    cat > data/sample_documents/bank_policies.txt << 'EOF'
BANK POLICIES AND PROCEDURES

INTERNATIONAL TRANSFER FEES:
- Wire transfers: $25 for amounts under $1,000, $15 for amounts over $1,000
- Online transfers: $5 flat fee
- Same-day transfers: Additional $10 fee

ACCOUNT MINIMUMS:
- Checking Account: $100 minimum balance
- Savings Account: $500 minimum balance
- Premium Account: $2,500 minimum balance

OVERDRAFT POLICIES:
- Overdraft fee: $35 per transaction
- Daily limit: 4 overdraft fees maximum
- Grace period: 24 hours to deposit funds

CUSTOMER SERVICE:
- Phone: 1-800-BANK-HELP (24/7)
- Online chat: Available 8 AM - 10 PM EST
- Branch hours: Monday-Friday 9 AM - 5 PM, Saturday 9 AM - 1 PM
EOF
fi

if [ ! -f "data/sample_documents/credit_card_benefits.txt" ]; then
    cat > data/sample_documents/credit_card_benefits.txt << 'EOF'
CREDIT CARD BENEFITS GUIDE

CASHBACK REWARDS:
- Groceries: 3% cashback
- Gas: 2% cashback
- All other purchases: 1% cashback
- Bonus: 5% on rotating quarterly categories

TRAVEL BENEFITS:
- No foreign transaction fees
- Travel insurance up to $100,000
- Lost luggage reimbursement up to $500
- Airport lounge access (Premium cards only)

PURCHASE PROTECTION:
- Extended warranty: Doubles manufacturer warranty up to 1 year
- Purchase protection: 90 days against theft/damage
- Price protection: Refund price differences within 60 days

SECURITY FEATURES:
- Zero liability for fraudulent charges
- Real-time fraud alerts
- Chip technology and contactless payments
- Virtual card numbers for online shopping

CREDIT LIMITS:
- Standard Card: $500 - $5,000
- Gold Card: $2,000 - $15,000
- Platinum Card: $5,000 - $50,000
EOF
fi

print_success "Sample documents ready"

# Step 7: Final setup
print_status "Step 7/7: Final setup and validation..."

# Create a startup script for easy server management
cat > start_banking_bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv_bankbot/bin/activate
echo "🏦 Starting Banking Bot API Server..."
echo "📍 API Documentation: http://localhost:2024/docs"
echo "🔍 Health Check: http://localhost:2024/health"
echo "Press Ctrl+C to stop the server"
echo ""
uvicorn src.app.main:app --host 0.0.0.0 --port 2024 --reload
EOF

chmod +x start_banking_bot.sh
print_success "Created start_banking_bot.sh script"

# Test database connection
print_status "Testing database connection..."
python -c "
import sqlite3
import os
if os.path.exists('data/banking_bot.db'):
    conn = sqlite3.connect('data/banking_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM accounts')
    account_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM transactions')
    transaction_count = cursor.fetchone()[0]
    conn.close()
    print(f'✅ Database ready: {user_count} users, {account_count} accounts, {transaction_count} transactions')
else:
    print('❌ Database not found')
    exit(1)
"

if [ $? -ne 0 ]; then
    print_error "Database validation failed"
    exit 1
fi

print_success "Database validation passed"

echo ""
echo "🎉 SETUP COMPLETED SUCCESSFULLY!"
echo "================================="
echo ""
print_success "✅ Virtual environment created and activated"
print_success "✅ All dependencies installed"
print_success "✅ Sample data created (3 users, 6 accounts, 50+ transactions)"
print_success "✅ Sample documents processed"
print_success "✅ Database validated"
echo ""
echo "📋 IMPORTANT: Next Steps"
echo "========================"
echo ""
print_warning "1. ADD YOUR OPENAI API KEY:"
echo "   - Edit the .env file: nano .env"
echo "   - Add your OpenAI API key: OPENAI_API_KEY=sk-your-key-here"
echo "   - Get API key from: https://platform.openai.com/api-keys"
echo ""
print_warning "2. START THE BACKEND SERVER:"
echo "   ./start_banking_bot.sh"
echo "   OR"
echo "   source venv_bankbot/bin/activate && uvicorn src.app.main:app --host 0.0.0.0 --port 2024 --reload"
echo ""
print_warning "3. SET UP THE FRONTEND:"
echo "   Run the frontend setup script in the banking-bot-ui folder"
echo ""
echo "🧪 TEST USERS CREATED:"
echo "======================"
echo "Username: john_doe     | Password: password123"
echo "Username: jane_smith   | Password: password123"
echo "Username: mike_johnson | Password: password123"
echo ""
echo "🔗 USEFUL LINKS:"
echo "================"
echo "API Docs:    http://localhost:2024/docs"
echo "Health:      http://localhost:2024/health"
echo "Frontend:    http://localhost:3000 (after frontend setup)"
echo ""
print_success "Happy coding! 🚀"
echo ""
