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
    
    # Sample users
    users_data = [
        {
            'user_id': 'john_doe',
            'password': 'password123',
            'email': 'john.doe@email.com',
            'first_name': 'John',
            'last_name': 'Doe'
        },
        {
            'user_id': 'jane_smith',
            'password': 'password123',
            'email': 'jane.smith@email.com',
            'first_name': 'Jane',
            'last_name': 'Smith'
        },
        {
            'user_id': 'mike_johnson',
            'password': 'password123',
            'email': 'mike.johnson@email.com',
            'first_name': 'Mike',
            'last_name': 'Johnson'
        }
    ]
    
    # Insert users
    for user in users_data:
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, password_hash, email, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
        ''', (user['user_id'], hash_password(user['password']), user['email'], 
              user['first_name'], user['last_name']))
    
    # Sample accounts
    accounts_data = [
        # John Doe's accounts
        {'user_id': 1, 'account_number': '1001234567', 'account_type': 'checking', 'balance': 2500.75},
        {'user_id': 1, 'account_number': '1001234568', 'account_type': 'savings', 'balance': 15000.00},
        # Jane Smith's accounts
        {'user_id': 2, 'account_number': '1001234569', 'account_type': 'checking', 'balance': 1800.25},
        {'user_id': 2, 'account_number': '1001234570', 'account_type': 'savings', 'balance': 25000.50},
        # Mike Johnson's accounts
        {'user_id': 3, 'account_number': '1001234571', 'account_type': 'checking', 'balance': 750.30},
        {'user_id': 3, 'account_number': '1001234572', 'account_type': 'savings', 'balance': 5000.00}
    ]
    
    # Insert accounts
    for account in accounts_data:
        cursor.execute('''
        INSERT OR IGNORE INTO accounts (user_id, account_number, account_type, balance)
        VALUES (?, ?, ?, ?)
        ''', (account['user_id'], account['account_number'], 
              account['account_type'], account['balance']))
    
    # Sample credit cards
    credit_cards_data = [
        # John Doe's credit cards
        {
            'user_id': 1, 'card_number': '4111111111111111', 'card_type': 'Premium Rewards',
            'credit_limit': 10000.00, 'current_balance': 1250.75, 'minimum_payment': 35.00,
            'due_date': (datetime.now() + timedelta(days=15)).isoformat()
        },
        # Jane Smith's credit cards
        {
            'user_id': 2, 'card_number': '4222222222222222', 'card_type': 'Gold Cash Back',
            'credit_limit': 15000.00, 'current_balance': 890.50, 'minimum_payment': 25.00,
            'due_date': (datetime.now() + timedelta(days=20)).isoformat()
        },
        # Mike Johnson's credit cards
        {
            'user_id': 3, 'card_number': '4333333333333333', 'card_type': 'Student Card',
            'credit_limit': 2000.00, 'current_balance': 456.25, 'minimum_payment': 15.00,
            'due_date': (datetime.now() + timedelta(days=10)).isoformat()
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
    
    # Sample transactions
    merchants = [
        'Amazon', 'Walmart', 'Target', 'Starbucks', 'McDonald\'s', 'Shell Gas Station',
        'Home Depot', 'Best Buy', 'Grocery Store', 'Netflix', 'Spotify', 'Electric Company',
        'Water Department', 'Insurance Payment', 'Salary Deposit', 'ATM Withdrawal'
    ]
    
    categories = [
        'Shopping', 'Groceries', 'Entertainment', 'Gas', 'Utilities', 'Salary',
        'Restaurants', 'Subscription', 'Home Improvement', 'Healthcare', 'Insurance'
    ]
    
    # Generate transactions for each account
    account_ids = [1, 2, 3, 4, 5, 6]  # Account IDs from the accounts table
    
    transaction_id_counter = 1
    for account_id in account_ids:
        # Generate 20-30 transactions per account
        num_transactions = random.randint(20, 30)
        
        for i in range(num_transactions):
            # Random transaction details
            is_credit = random.choice([True, False])
            amount = round(random.uniform(10.00, 500.00), 2)
            
            if is_credit and random.random() < 0.1:  # 10% chance of salary deposit
                amount = round(random.uniform(2000.00, 5000.00), 2)
                merchant = 'Salary Deposit'
                category = 'Salary'
                transaction_type = 'credit'
                description = 'Monthly Salary'
            else:
                merchant = random.choice(merchants)
                category = random.choice(categories)
                transaction_type = 'credit' if is_credit else 'debit'
                description = f'{transaction_type.title()} - {merchant}'
            
            # Random date within last 90 days
            days_ago = random.randint(1, 90)
            transaction_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            cursor.execute('''
            INSERT OR IGNORE INTO transactions 
            (account_id, transaction_id, transaction_type, amount, description, category, merchant, transaction_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, f'TXN{transaction_id_counter:06d}', transaction_type, 
                  amount, description, category, merchant, transaction_date))
            
            transaction_id_counter += 1
    
    conn.commit()
    conn.close()
    
    print("✅ Initialized database")
    print(f"✅ Created {len(users_data)} sample users")
    print(f"✅ Created {len(accounts_data)} bank accounts")
    print(f"✅ Created {len(account_ids) * 25} transactions")  # Approximate
    print(f"✅ Created {len(credit_cards_data)} credit cards")
    
    # Create ChromaDB and ingest documents using ingestion_app
    ingest_sample_documents(data_dir)
    
    print("✅ Setup completed successfully!")
    print(f"\nDatabase location: {db_path}")
    print("\nSample users created:")
    for user in users_data:
        print(f"- {user['user_id']} (password: {user['password']})")

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
            
            # Process bank policies
            bank_policies_file = sample_docs_dir / "bank_policies.txt"
            if bank_policies_file.exists():
                result = await ingestion_service.ingest_document(
                    str(bank_policies_file),
                    document_type="policy"
                )
                if result.get("status") == "success":
                    documents_processed += 1
                    chunks_stored = result.get("chunks_stored", 0)
                    print(f"✅ Processed bank_policies.txt ({chunks_stored} chunks)")
                else:
                    print(f"⚠️  Warning: {result.get('error', 'Unknown error')}")
            
            # Process credit card benefits
            benefits_file = sample_docs_dir / "credit_card_benefits.txt"
            if benefits_file.exists():
                result = await ingestion_service.ingest_document(
                    str(benefits_file),
                    document_type="benefits"
                )
                if result.get("status") == "success":
                    documents_processed += 1
                    chunks_stored = result.get("chunks_stored", 0)
                    print(f"✅ Processed credit_card_benefits.txt ({chunks_stored} chunks)")
                else:
                    print(f"⚠️  Warning: {result.get('error', 'Unknown error')}")
            
            if documents_processed > 0:
                print(f"✅ Created ChromaDB with {documents_processed} policy documents")
            
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
