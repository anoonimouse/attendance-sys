#!/usr/bin/env python3
"""
Database Utility Script
Run this to reset database, create admin, or check configuration
"""

import sys
import os
from getpass import getpass

def reset_database():
    """Reset the database (delete and recreate)"""
    print("🗑️  Resetting database...")
    
    if os.path.exists('app.db'):
        confirm = input("This will delete all data. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
        os.remove('app.db')
        print("✓ Old database deleted")
    
    from app import create_app, db
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print("✓ New database created")
    
    print("✅ Database reset complete!\n")


def create_admin():
    """Create or promote a user to admin"""
    print("👤 Create Admin User")
    email = input("Enter email address: ").strip().lower()
    
    if not email:
        print("❌ Email required")
        return
    
    from app import create_app, db
    from app.models import User
    
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            name = input("Enter name: ").strip()
            if not name:
                name = email.split('@')[0]
            
            user = User(
                email=email,
                name=name,
                role='admin'
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created new admin: {email}")
        else:
            user.role = 'admin'
            user.is_banned = False
            db.session.commit()
            print(f"✅ Promoted to admin: {email}")


def create_teacher():
    """Create or promote a user to teacher"""
    print("👨‍🏫 Create Teacher User")
    email = input("Enter email address: ").strip().lower()
    
    if not email:
        print("❌ Email required")
        return
    
    from app import create_app, db
    from app.models import User
    
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            name = input("Enter name: ").strip()
            if not name:
                name = email.split('@')[0]
            
            user = User(
                email=email,
                name=name,
                role='teacher'
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created new teacher: {email}")
        else:
            user.role = 'teacher'
            user.is_banned = False
            db.session.commit()
            print(f"✅ Promoted to teacher: {email}")


def list_users():
    """List all users"""
    print("📋 User List\n")
    
    from app import create_app
    from app.models import User
    
    app = create_app()
    
    with app.app_context():
        users = User.query.order_by(User.created_at.desc()).all()
        
        if not users:
            print("No users found.")
            return
        
        print(f"{'Email':<40} {'Role':<10} {'Banned':<7} {'Created'}")
        print("-" * 80)
        
        for u in users:
            banned = "Yes" if u.is_banned else "No"
            created = u.created_at.strftime('%Y-%m-%d') if u.created_at else "N/A"
            print(f"{u.email:<40} {u.role:<10} {banned:<7} {created}")


def check_config():
    """Check configuration"""
    print("🔍 Configuration Check\n")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    checks = {
        'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY'),
        'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID'),
        'GOOGLE_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET'),
        'ALLOWED_DOMAIN': os.getenv('ALLOWED_DOMAIN'),
        'ADMINS': os.getenv('ADMINS')
    }
    
    all_ok = True
    
    for key, value in checks.items():
        if value:
            # Mask secrets
            if 'SECRET' in key:
                display = value[:10] + '...' if len(value) > 10 else '***'
            else:
                display = value
            print(f"✓ {key}: {display}")
        else:
            print(f"✗ {key}: NOT SET")
            all_ok = False
    
    print()
    
    if all_ok:
        print("✅ All required configuration is set!")
    else:
        print("❌ Some configuration is missing. Check your .env file.")


def main():
    """Main menu"""
    print("=" * 50)
    print("  Attendance System - Database Utility")
    print("=" * 50)
    print()
    print("1. Reset Database (⚠️  Deletes all data)")
    print("2. Create/Promote Admin User")
    print("3. Create/Promote Teacher User")
    print("4. List All Users")
    print("5. Check Configuration")
    print("0. Exit")
    print()
    
    choice = input("Enter choice: ").strip()
    print()
    
    if choice == '1':
        reset_database()
    elif choice == '2':
        create_admin()
    elif choice == '3':
        create_teacher()
    elif choice == '4':
        list_users()
    elif choice == '5':
        check_config()
    elif choice == '0':
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice")
    
    print()
    input("Press Enter to continue...")
    main()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)