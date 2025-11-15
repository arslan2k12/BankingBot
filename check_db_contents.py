#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.app.database.database import get_db
from src.app.models.database_models import User, Account, Transaction, CreditCard

def check_database_contents():
    db = next(get_db())
    
    # Check users
    users = db.query(User).all()
    print("👥 USERS:")
    for user in users:
        print(f"  - {user.user_id}: {user.first_name} {user.last_name} ({user.email})")
    
    # Check accounts for jane_smith
    jane = db.query(User).filter(User.user_id == 'jane_smith').first()
    if jane:
        print(f"\n🏦 ACCOUNTS for {jane.user_id}:")
        accounts = db.query(Account).filter(Account.user_id == jane.id).all()
        for acc in accounts:
            print(f"  - {acc.account_number} ({acc.account_type}): ${acc.balance} - Active: {acc.is_active}")
        
        print(f"\n💳 CREDIT CARDS for {jane.user_id}:")
        cards = db.query(CreditCard).filter(CreditCard.user_id == jane.id).all()
        for card in cards:
            print(f"  - {card.card_number} ({card.card_type}): ${card.current_balance}/${card.credit_limit} - Active: {card.is_active}")
    
    db.close()

if __name__ == "__main__":
    check_database_contents()
