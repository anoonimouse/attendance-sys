#!/usr/bin/env python3
"""
Quick script to check and update user roles
"""

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("  USER ROLE CHECKER")
    print("="*60 + "\n")
    
    users = User.query.all()
    
    if not users:
        print("❌ No users found in database.\n")
        exit()
    
    print(f"{'ID':<5} {'Email':<35} {'Role':<10} {'Banned'}")
    print("-" * 60)
    
    for u in users:
        banned = "Yes" if u.is_banned else "No"
        print(f"{u.id:<5} {u.email:<35} {u.role:<10} {banned}")
    
    print("\n" + "="*60)
    print("\nWould you like to update a user's role?")
    
    update = input("Enter user ID (or press Enter to skip): ").strip()
    
    if update and update.isdigit():
        user_id = int(update)
        user = User.query.get(user_id)
        
        if not user:
            print(f"❌ User ID {user_id} not found.")
            exit()
        
        print(f"\nCurrent role: {user.role}")
        print("\nAvailable roles:")
        print("1. student")
        print("2. teacher")
        print("3. admin")
        
        choice = input("\nEnter new role (1-3): ").strip()
        
        role_map = {
            "1": "student",
            "2": "teacher",
            "3": "admin"
        }
        
        if choice in role_map:
            old_role = user.role
            user.role = role_map[choice]
            db.session.commit()
            print(f"\n✅ Updated {user.email}")
            print(f"   {old_role} → {user.role}")
            print("\n🔄 Please log out and log back in for changes to take effect.\n")
        else:
            print("❌ Invalid choice.")
    else:
        print("\nNo changes made.\n")