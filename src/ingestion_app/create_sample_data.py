import sqlite3
import hashlib
from datetime import datetime, timedelta
import random
import json
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Add the BankingBot root directory to Python path for consistent imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env file in project root
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

def create_sample_data():
    """Create sample banking data for testing"""
    
    # Database path using project root
    db_path = PROJECT_ROOT / "data" / "banking_bot.db"
    data_dir = db_path.parent
    data_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting Banking Bot setup...")
    print("✅ Created directories")
    
    # Clear existing database to prevent duplicates
    if db_path.exists():
        print("🗑️  Removing existing database to prevent duplicates...")
        db_path.unlink()
        print("✅ Cleared existing database")
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables (simplified for direct SQL)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        email VARCHAR(100) UNIQUE,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        account_number VARCHAR(20) UNIQUE NOT NULL,
        account_type VARCHAR(20) NOT NULL,
        balance REAL DEFAULT 0.0,
        currency VARCHAR(3) DEFAULT 'USD',
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        transaction_id VARCHAR(50) UNIQUE NOT NULL,
        transaction_type VARCHAR(20) NOT NULL,
        amount REAL NOT NULL,
        description VARCHAR(255),
        category VARCHAR(50),
        merchant VARCHAR(100),
        transaction_date TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES accounts (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS credit_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        card_number VARCHAR(20) UNIQUE NOT NULL,
        card_type VARCHAR(30) NOT NULL,
        credit_limit REAL NOT NULL,
        current_balance REAL DEFAULT 0.0,
        available_credit REAL,
        minimum_payment REAL DEFAULT 0.0,
        due_date TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Hash password function using SHA256
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    # Realistic Scotiabank customer profiles
    users_data = [
        {
            'user_id': 'sarah_chen',
            'password': 'password123',
            'email': 'sarah.chen@gmail.com',
            'first_name': 'Sarah',
            'last_name': 'Chen'
        },
        {
            'user_id': 'david_martinez',
            'password': 'password123',
            'email': 'david.martinez@outlook.com',
            'first_name': 'David',
            'last_name': 'Martinez'
        },
        {
            'user_id': 'emma_thompson',
            'password': 'password123',
            'email': 'emma.thompson@yahoo.ca',
            'first_name': 'Emma',
            'last_name': 'Thompson'
        },
        {
            'user_id': 'ryan_patel',
            'password': 'password123',
            'email': 'ryan.patel@gmail.com',
            'first_name': 'Ryan',
            'last_name': 'Patel'
        },
        {
            'user_id': 'lisa_wong',
            'password': 'password123',
            'email': 'lisa.wong@rogers.com',
            'first_name': 'Lisa',
            'last_name': 'Wong'
        }
    ]
    
    # Insert users
    for user in users_data:
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, password_hash, email, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
        ''', (user['user_id'], hash_password(user['password']), user['email'], 
              user['first_name'], user['last_name']))
    
    # Realistic Scotiabank accounts with proper Canadian banking patterns
    accounts_data = [
        # Sarah Chen - Young Professional (Tech Worker)
        {'user_id': 1, 'account_number': '11234567890', 'account_type': 'checking', 'balance': 3247.85},
        {'user_id': 1, 'account_number': '11234567891', 'account_type': 'savings', 'balance': 18500.00},
        
        # David Martinez - Family Man (Manager)
        {'user_id': 2, 'account_number': '11234567892', 'account_type': 'checking', 'balance': 2156.43},
        {'user_id': 2, 'account_number': '11234567893', 'account_type': 'savings', 'balance': 42750.25},
        
        # Emma Thompson - Retiree (Fixed Income)
        {'user_id': 3, 'account_number': '11234567894', 'account_type': 'checking', 'balance': 1834.67},
        {'user_id': 3, 'account_number': '11234567895', 'account_type': 'savings', 'balance': 67890.15},
        
        # Ryan Patel - University Student
        {'user_id': 4, 'account_number': '11234567896', 'account_type': 'checking', 'balance': 487.92},
        {'user_id': 4, 'account_number': '11234567897', 'account_type': 'savings', 'balance': 1250.00},
        
        # Lisa Wong - Small Business Owner
        {'user_id': 5, 'account_number': '11234567898', 'account_type': 'checking', 'balance': 8934.21},
        {'user_id': 5, 'account_number': '11234567899', 'account_type': 'savings', 'balance': 28450.75}
    ]
    
    # Insert accounts
    for account in accounts_data:
        cursor.execute('''
        INSERT OR IGNORE INTO accounts (user_id, account_number, account_type, balance)
        VALUES (?, ?, ?, ?)
        ''', (account['user_id'], account['account_number'], 
              account['account_type'], account['balance']))
    
    # Realistic Scotiabank credit cards matching typical Canadian products
    credit_cards_data = [
        # Sarah Chen - Scotia Momentum Visa Infinite
        {
            'user_id': 1, 'card_number': '4538266895432109', 'card_type': 'Scotia Momentum Visa Infinite',
            'credit_limit': 12000.00, 'current_balance': 1847.92, 'minimum_payment': 55.44,
            'due_date': (datetime.now() + timedelta(days=18)).isoformat()
        },
        
        # David Martinez - Scotia Gold American Express
        {
            'user_id': 2, 'card_number': '3782822463100059', 'card_type': 'Scotia Gold American Express',
            'credit_limit': 20000.00, 'current_balance': 3241.67, 'minimum_payment': 97.25,
            'due_date': (datetime.now() + timedelta(days=22)).isoformat()
        },
        
        # Emma Thompson - Scotia Rewards Visa
        {
            'user_id': 3, 'card_number': '4538266895432187', 'card_type': 'Scotia Rewards Visa',
            'credit_limit': 8000.00, 'current_balance': 567.43, 'minimum_payment': 17.02,
            'due_date': (datetime.now() + timedelta(days=12)).isoformat()
        },
        
        # Ryan Patel - Scotia Scene Visa
        {
            'user_id': 4, 'card_number': '4538266895432234', 'card_type': 'Scotia Scene Visa',
            'credit_limit': 2500.00, 'current_balance': 892.15, 'minimum_payment': 26.76,
            'due_date': (datetime.now() + timedelta(days=8)).isoformat()
        },
        
        # Lisa Wong - Scotia Passport Visa Infinite
        {
            'user_id': 5, 'card_number': '4538266895432276', 'card_type': 'Scotia Passport Visa Infinite',
            'credit_limit': 15000.00, 'current_balance': 2156.88, 'minimum_payment': 64.71,
            'due_date': (datetime.now() + timedelta(days=25)).isoformat()
        }
    ]
    
    # Insert credit cards
    for card in credit_cards_data:
        cursor.execute('''
        INSERT OR IGNORE INTO credit_cards 
        (user_id, card_number, card_type, credit_limit, current_balance, minimum_payment, due_date, available_credit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (card['user_id'], card['card_number'], card['card_type'], 
              card['credit_limit'], card['current_balance'], card['minimum_payment'], 
              card['due_date'], card['credit_limit'] - card['current_balance']))
    
    # Realistic Canadian merchant-category mappings for proper alignment
    merchant_category_mappings = {
        # Groceries & Food
        'Loblaws': ('Groceries', [45.67, 78.92, 123.45, 89.34, 156.78]),
        'Metro': ('Groceries', [34.56, 89.23, 67.89, 145.67, 98.45]),
        'Sobeys': ('Groceries', [67.23, 134.56, 89.12, 178.90, 76.54]),
        'No Frills': ('Groceries', [23.45, 56.78, 89.23, 45.67, 134.56]),
        'FreshCo': ('Groceries', [34.67, 67.89, 123.45, 89.34, 156.78]),
        'Food Basics': ('Groceries', [28.90, 78.45, 56.78, 123.45, 89.23]),
        
        # Restaurants & Dining
        'Tim Hortons': ('Restaurants', [4.67, 8.92, 12.45, 6.34, 15.78]),
        'McDonald\'s': ('Restaurants', [9.56, 14.23, 18.89, 12.67, 21.45]),
        'Subway': ('Restaurants', [8.23, 13.56, 17.12, 11.90, 19.54]),
        'A&W': ('Restaurants', [11.45, 16.78, 19.23, 14.67, 22.56]),
        'Boston Pizza': ('Restaurants', [34.67, 45.89, 56.45, 67.34, 78.78]),
        'Swiss Chalet': ('Restaurants', [28.90, 39.45, 48.78, 34.45, 67.23]),
        'The Keg': ('Restaurants', [89.45, 134.67, 178.90, 156.78, 198.45]),
        
        # Gas Stations
        'Petro-Canada': ('Gas', [45.67, 56.78, 67.89, 78.90, 89.45]),
        'Shell': ('Gas', [43.56, 54.23, 65.89, 76.67, 87.45]),
        'Esso': ('Gas', [47.23, 58.56, 69.12, 80.90, 91.54]),
        'Canadian Tire Gas+': ('Gas', [42.45, 53.78, 64.23, 75.67, 86.56]),
        'Costco Gas': ('Gas', [51.67, 62.89, 73.45, 84.34, 95.78]),
        
        # Utilities & Services
        'Hydro One': ('Utilities', [89.34, 123.45, 156.78, 178.90, 201.23]),
        'Toronto Hydro': ('Utilities', [78.45, 112.67, 145.89, 167.23, 189.56]),
        'Enbridge Gas': ('Utilities', [67.89, 98.45, 123.67, 145.23, 167.89]),
        'Rogers Communications': ('Utilities', [89.99, 119.99, 149.99, 179.99, 199.99]),
        'Bell Canada': ('Utilities', [85.00, 115.00, 145.00, 175.00, 195.00]),
        'Telus': ('Utilities', [75.00, 105.00, 135.00, 165.00, 185.00]),
        
        # Shopping & Retail  
        'Amazon.ca': ('Shopping', [23.45, 67.89, 134.56, 89.23, 178.90]),
        'Canadian Tire': ('Shopping', [45.67, 89.34, 156.78, 234.56, 345.67]),
        'The Bay': ('Shopping', [67.89, 123.45, 189.67, 234.89, 345.78]),
        'Winners': ('Shopping', [34.56, 67.89, 98.76, 145.23, 189.45]),
        'Costco': ('Shopping', [123.45, 189.67, 234.89, 345.67, 456.78]),
        'Home Depot': ('Home Improvement', [45.67, 89.34, 167.89, 234.56, 345.67]),
        'IKEA': ('Home Improvement', [78.90, 156.78, 234.56, 345.67, 456.78]),
        
        # Entertainment & Subscriptions
        'Netflix': ('Entertainment', [16.49, 20.99, 24.99]),
        'Spotify': ('Entertainment', [11.99, 16.99]),
        'Disney+': ('Entertainment', [11.99, 17.99]),
        'Amazon Prime': ('Entertainment', [9.99, 12.99]),
        'Cineplex': ('Entertainment', [14.99, 18.99, 22.99, 26.99]),
        
        # Healthcare & Pharmacy
        'Shoppers Drug Mart': ('Healthcare', [12.45, 34.67, 56.89, 78.90, 123.45]),
        'Rexall': ('Healthcare', [15.67, 34.89, 67.23, 89.45, 134.67]),
        'Medical Centre': ('Healthcare', [150.00, 200.00, 250.00, 300.00]),
        
        # Transportation
        'TTC': ('Transportation', [3.35, 12.00, 156.00]),  # Single ride, day pass, monthly
        'GO Transit': ('Transportation', [5.70, 12.35, 24.70, 389.00]),
        'Uber': ('Transportation', [12.45, 18.67, 23.89, 34.56, 45.78]),
        'Lyft': ('Transportation', [11.23, 17.89, 22.45, 33.67, 44.89]),
        
        # Banking & Financial
        'Scotiabank ATM': ('Banking', [2.50, 3.50]),  # ATM fees
        'Interac e-Transfer': ('Banking', [1.50]),
        
        # Government & Insurance
        'CRA': ('Government', [1250.00, 2500.00, 3750.00]),  # Tax payments
        'Service Ontario': ('Government', [120.00, 180.00, 240.00]),
        'TD Insurance': ('Insurance', [89.50, 156.75, 234.50, 312.25]),
        'State Farm': ('Insurance', [95.25, 167.50, 239.75, 312.00]),
        
        # Education (for student)
        'University of Toronto': ('Education', [2500.00, 5000.00, 7500.00]),
        'Indigo Books': ('Education', [23.45, 67.89, 134.56, 189.23]),
        
        # Business (for business owner)
        'Staples Business': ('Business', [45.67, 89.34, 167.89, 234.56]),
        'Office Depot': ('Business', [34.56, 78.90, 156.78, 234.67]),
        
        # Salary & Income (Credits)
        'Payroll Deposit': ('Income', [3250.00, 4500.00, 5750.00, 6500.00]),
        'Direct Deposit': ('Income', [2800.00, 3500.00, 4200.00]),
        'Pension Deposit': ('Income', [1850.00, 2300.00, 2750.00]),
        'OSAP': ('Income', [1200.00, 1800.00, 2400.00]),  # Student loans
    }
    
    # User profiles for realistic transaction patterns
    user_profiles = {
        1: {  # Sarah Chen - Tech Professional
            'salary_range': [4500.00, 5750.00],
            'spending_habits': {
                'Groceries': 0.20, 'Restaurants': 0.15, 'Shopping': 0.25, 
                'Entertainment': 0.10, 'Gas': 0.08, 'Utilities': 0.12, 
                'Healthcare': 0.05, 'Transportation': 0.05
            },
            'preferred_merchants': ['Loblaws', 'Tim Hortons', 'Amazon.ca', 'Uber', 'Netflix', 'Petro-Canada'],
            'monthly_transactions': 45
        },
        2: {  # David Martinez - Family Manager
            'salary_range': [5500.00, 6500.00],
            'spending_habits': {
                'Groceries': 0.30, 'Restaurants': 0.12, 'Shopping': 0.20, 
                'Gas': 0.12, 'Utilities': 0.15, 'Insurance': 0.06, 
                'Healthcare': 0.03, 'Home Improvement': 0.02
            },
            'preferred_merchants': ['Costco', 'Metro', 'Canadian Tire', 'Shell', 'Boston Pizza', 'Home Depot'],
            'monthly_transactions': 55
        },
        3: {  # Emma Thompson - Retiree
            'salary_range': [2300.00, 2750.00],  # Pension
            'spending_habits': {
                'Groceries': 0.25, 'Healthcare': 0.20, 'Utilities': 0.18, 
                'Restaurants': 0.08, 'Shopping': 0.12, 'Transportation': 0.10, 
                'Insurance': 0.05, 'Entertainment': 0.02
            },
            'preferred_merchants': ['Sobeys', 'Shoppers Drug Mart', 'TTC', 'Swiss Chalet', 'The Bay'],
            'monthly_transactions': 35
        },
        4: {  # Ryan Patel - University Student
            'salary_range': [1200.00, 1800.00],  # OSAP + part-time
            'spending_habits': {
                'Groceries': 0.15, 'Restaurants': 0.25, 'Education': 0.35, 
                'Transportation': 0.10, 'Entertainment': 0.08, 'Shopping': 0.05, 
                'Healthcare': 0.02
            },
            'preferred_merchants': ['No Frills', 'Tim Hortons', 'McDonald\'s', 'TTC', 'Indigo Books'],
            'monthly_transactions': 28
        },
        5: {  # Lisa Wong - Small Business Owner
            'salary_range': [3500.00, 4200.00],
            'spending_habits': {
                'Business': 0.25, 'Groceries': 0.18, 'Restaurants': 0.15, 
                'Gas': 0.12, 'Shopping': 0.12, 'Utilities': 0.10, 
                'Transportation': 0.05, 'Healthcare': 0.03
            },
            'preferred_merchants': ['FreshCo', 'Staples Business', 'Esso', 'The Keg', 'Costco'],
            'monthly_transactions': 40
        }
    }
    
    # Generate realistic transactions for all 10 accounts (2 per user)
    account_ids = list(range(1, 11))  # Account IDs 1-10
    transaction_id_counter = 1
    
    for account_id in account_ids:
        user_id = ((account_id - 1) // 2) + 1  # Map account to user (2 accounts per user)
        profile = user_profiles[user_id]
        
        # Generate 12 months of transactions
        for month_offset in range(12):
            base_date = datetime.now() - timedelta(days=30 * month_offset)
            monthly_transactions = profile['monthly_transactions']
            
            # Add some randomness to monthly transaction count
            actual_transactions = random.randint(
                int(monthly_transactions * 0.8), 
                int(monthly_transactions * 1.2)
            )
            
            # Generate monthly salary/income (only for checking accounts - odd IDs)
            if account_id % 2 == 1:  # Checking accounts
                income_amount = random.choice(profile['salary_range'])
                # Generate salary date safely (avoid February 29/30 issues)
                try:
                    salary_date = base_date.replace(day=random.randint(1, 28))
                except ValueError:
                    salary_date = base_date.replace(day=15)  # Fallback to mid-month
                
                income_merchant = 'Payroll Deposit'
                if user_id == 3:  # Retiree gets pension
                    income_merchant = 'Pension Deposit'
                elif user_id == 4:  # Student gets OSAP
                    income_merchant = 'OSAP'
                
                cursor.execute('''
                INSERT OR IGNORE INTO transactions 
                (account_id, transaction_id, transaction_type, amount, description, category, merchant, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (account_id, f'TXN{transaction_id_counter:06d}', 'credit', 
                      income_amount, f'Monthly income - {income_merchant}', 'Income', 
                      income_merchant, salary_date.isoformat()))
                transaction_id_counter += 1
            
            # Generate spending transactions based on user profile
            for _ in range(actual_transactions):
                # Select category based on spending habits
                category_weights = list(profile['spending_habits'].values())
                category = random.choices(list(profile['spending_habits'].keys()), weights=category_weights)[0]
                
                # Find merchants that match this category
                matching_merchants = [merchant for merchant, (cat, amounts) in merchant_category_mappings.items() 
                                    if cat == category]
                
                if not matching_merchants:
                    continue
                    
                # Prefer merchants from user's preferred list if available
                preferred_matches = [m for m in matching_merchants if m in profile['preferred_merchants']]
                if preferred_matches and random.random() < 0.6:  # 60% chance to use preferred
                    merchant = random.choice(preferred_matches)
                else:
                    merchant = random.choice(matching_merchants)
                
                # Get realistic amount for this merchant
                _, amounts = merchant_category_mappings[merchant]
                amount = random.choice(amounts)
                
                # Add some realistic variation (±20%)
                variation = random.uniform(0.8, 1.2)
                amount = round(amount * variation, 2)
                
                # Generate transaction date within the month
                days_in_month = random.randint(1, 28)
                transaction_date = base_date - timedelta(days=days_in_month)
                
                # Determine transaction type (mostly debits, some credits for returns)
                transaction_type = 'debit'
                description = f'Purchase - {merchant}'
                
                # Small chance of returns/refunds
                if random.random() < 0.02:  # 2% chance
                    transaction_type = 'credit'
                    description = f'Refund - {merchant}'
                    amount = amount * 0.5  # Partial refunds are common
                
                cursor.execute('''
                INSERT OR IGNORE INTO transactions 
                (account_id, transaction_id, transaction_type, amount, description, category, merchant, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (account_id, f'TXN{transaction_id_counter:06d}', transaction_type, 
                      amount, description, category, merchant, transaction_date.isoformat()))
                
                transaction_id_counter += 1
    
    # Get actual transaction count before closing connection
    cursor.execute("SELECT COUNT(*) FROM transactions")
    actual_transaction_count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    print("✅ Initialized database with realistic Canadian banking data")
    print(f"✅ Created {len(users_data)} diverse customer profiles")
    print(f"✅ Created {len(accounts_data)} Scotiabank accounts")
    print(f"✅ Generated {actual_transaction_count} realistic transactions over 12 months")
    print(f"✅ Created {len(credit_cards_data)} authentic Scotiabank credit cards")
    
    # Create ChromaDB and ingest documents using ingestion_app
    ingest_sample_documents(data_dir)
    
    print("✅ Banking Bot setup completed successfully!")
    print(f"\n📂 Database location: {db_path}")
    print(f"📊 Total merchants: {len(merchant_category_mappings)}")
    print(f"💳 Card types: Scotia Momentum, Scotia Gold Amex, Scotia Rewards, Scotia Scene, Scotia Passport")
    print("\n👥 Sample users for workshop testing:")
    user_descriptions = [
        "Young Tech Professional", "Family Manager", "Retiree", 
        "University Student", "Small Business Owner"
    ]
    for i, user in enumerate(users_data):
        print(f"- {user['user_id']} (password: {user['password']}) - {user_descriptions[i]}")

async def clear_chromadb_collection(ingestion_service):
    """Clear existing ChromaDB collection to prevent data duplication"""
    try:
        # For complete cleanup, remove the entire ChromaDB directory
        # This prevents UUID folder accumulation
        from src.app.config.service_config import settings
        import shutil
        
        chromadb_path = Path(settings.chromadb_path)
        if chromadb_path.exists():
            print(f"🗑️  Removing entire ChromaDB directory to prevent UUID accumulation...")
            shutil.rmtree(chromadb_path)
            print("✅ Completely cleared ChromaDB directory")
            
            # Reset the service's client and collection references
            ingestion_service._client = None
            ingestion_service._collection = None
        else:
            print("ℹ️  ChromaDB directory doesn't exist, no need to clear")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not clear ChromaDB directory: {str(e)}")
        print("   Trying collection-level clearing instead...")
        
        # Fallback to collection-level clearing
        try:
            result = ingestion_service.clear_collection()
            
            if result["status"] == "success":
                print(f"🗑️  Cleared existing ChromaDB collection '{result['collection_name']}' ({result['cleared_chunks']} chunks)")
            elif result["status"] == "empty":
                print("ℹ️  ChromaDB collection is empty, no need to clear")
            elif result["status"] == "not_found":
                print("ℹ️  No existing ChromaDB collection found")
            else:
                print(f"⚠️  Warning: {result.get('error', 'Unknown error clearing collection')}")
                
        except Exception as e2:
            print(f"⚠️  Warning: Could not clear ChromaDB collection: {str(e2)}")
            print("   Continuing with ingestion...")

def ingest_sample_documents(data_dir):
    """Use the ingestion_app to create ChromaDB and ingest sample documents"""
    try:
        # Check if OpenAI API key is available
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            print("⚠️  Warning: OPENAI_API_KEY not found. ChromaDB creation skipped.")
            print("   Set your OpenAI API key in .env file to enable document search.")
            return
            
        # Import the ingestion service using consistent path from project root
        from src.ingestion_app.services.document_ingestion import DocumentIngestionService
        import asyncio
        
        async def run_ingestion():
            ingestion_service = DocumentIngestionService()
            
            # Clear existing ChromaDB collection before ingesting new data
            await clear_chromadb_collection(ingestion_service)
            
            # Process sample documents
            sample_docs_dir = data_dir / "sample_documents"
            documents_processed = 0
            total_chunks_stored = 0
            
            print("📄 Processing sample documents...")
            
            # Check if sample documents directory exists
            if not sample_docs_dir.exists():
                print(f"⚠️  Sample documents directory not found: {sample_docs_dir}")
                return 0
            
            # Get all supported files in the directory
            supported_extensions = ['.pdf', '.txt', '.docx']
            all_files = []
            
            for extension in supported_extensions:
                files = list(sample_docs_dir.glob(f"*{extension}"))
                all_files.extend(files)
            
            if not all_files:
                print(f"⚠️  No supported documents found in {sample_docs_dir}")
                print(f"   Supported formats: {', '.join(supported_extensions)}")
                return 0
            
            print(f"📁 Found {len(all_files)} documents to process")
            
            # Process each file
            for file_path in sorted(all_files):  # Sort for consistent processing order
                file_name = file_path.name
                file_ext = file_path.suffix.lower()
                
                # Determine document type based on filename patterns
                document_type = "document"  # Default type
                
                if "policy" in file_name.lower() or "policies" in file_name.lower():
                    document_type = "policy"
                elif "benefit" in file_name.lower() or "benefits" in file_name.lower():
                    document_type = "benefits"
                elif "credit" in file_name.lower() and ("card" in file_name.lower() or "visa" in file_name.lower()):
                    document_type = "credit_card"
                elif "passport" in file_name.lower():
                    document_type = "passport_card"
                elif "scotia" in file_name.lower():
                    document_type = "scotiabank_document"
                elif file_ext == ".pdf":
                    document_type = "banking_document"
                
                print(f"📄 Processing {file_name} (type: {document_type})...")
                
                try:
                    result = await ingestion_service.ingest_document(
                        str(file_path),
                        document_type=document_type
                    )
                    
                    if result.get("status") == "success":
                        documents_processed += 1
                        chunks_stored = result.get("chunks_stored", 0)
                        total_chunks_stored += chunks_stored
                        
                        # Show different messages for PDFs vs other files
                        if file_ext == ".pdf":
                            print(f"✅ Processed {file_name} ({chunks_stored} page-based chunks)")
                        else:
                            print(f"✅ Processed {file_name} ({chunks_stored} text chunks)")
                    else:
                        print(f"⚠️  Warning processing {file_name}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ Error processing {file_name}: {str(e)}")
            
            if documents_processed > 0:
                print(f"✅ Created ChromaDB with {documents_processed} documents ({total_chunks_stored} total chunks)")
                print(f"📝 Chunks include: PDF pages (page-based) + text file chunks in structured markdown format")
                print(f"🔍 Document types processed: PDF, TXT, DOCX files with automatic type detection")
            else:
                print("⚠️  No documents were successfully processed")
            
            return documents_processed
        
        # Run the async ingestion
        documents_count = asyncio.run(run_ingestion())
        
    except ImportError as e:
        print(f"⚠️  Warning: Could not import ingestion service: {str(e)}")
        print("   Document search functionality will be limited.")
    except Exception as e:
        print(f"⚠️  Warning: Document ingestion failed: {str(e)}")
        print("   This won't affect basic banking functionality, but document search will be limited.")

if __name__ == "__main__":
    create_sample_data()
