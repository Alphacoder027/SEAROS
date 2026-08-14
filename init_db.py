"""
SAEROS - Database Initialization Script
Creates all tables and seeds initial data.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db, bcrypt
from app.models import User, Role


def init_database():
    app = create_app('development')

    with app.app_context():
        print("=" * 50)
        print("SAEROS - Database Initialization")
        print("=" * 50)

        # Create all tables
        print("\n[1] Creating database tables...")
        db.create_all()
        print("    Tables created successfully!")

        # Seed roles
        print("\n[2] Seeding roles...")
        roles_data = [
            ('admin', 'System administrator with full access'),
            ('agent', 'Field agent who submits raw material batches'),
            ('scrap_team', 'Scrap processing team handling by-products'),
        ]

        for role_name, description in roles_data:
            existing = Role.query.filter_by(name=role_name).first()
            if not existing:
                role = Role(name=role_name, description=description)
                db.session.add(role)
                print(f"    Created role: {role_name}")
            else:
                print(f"    Role already exists: {role_name}")

        db.session.commit()

        # Seed admin user
        print("\n[3] Creating default admin user...")
        admin_role = Role.query.filter_by(name='admin').first()
        existing_admin = User.query.filter_by(username='admin').first()

        if not existing_admin:
            password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                username='admin',
                email='admin@saeros.com',
                password_hash=password_hash,
                full_name='System Administrator',
                role_id=admin_role.id,
                is_approved=True,
                is_active=True,
                is_admin=True,
                department='IT Administration'
            )
            db.session.add(admin)
            db.session.commit()
            print("    Admin user created!")
            print("    Username: admin")
            print("    Password: admin123")
        else:
            print("    Admin user already exists.")

        # Create sample users for testing
        print("\n[4] Creating sample users...")
        sample_users = [
            {
                'username': 'agent1',
                'email': 'agent1@saeros.com',
                'password': 'agent123',
                'full_name': 'John Smith',
                'role': 'agent',
                'department': 'Field Operations'
            },
            {
                'username': 'scrap1',
                'email': 'scrap1@saeros.com',
                'password': 'scrap123',
                'full_name': 'Maria Garcia',
                'role': 'scrap_team',
                'department': 'Scrap Processing'
            }
        ]

        for user_data in sample_users:
            existing = User.query.filter_by(username=user_data['username']).first()
            if not existing:
                role = Role.query.filter_by(name=user_data['role']).first()
                password_hash = bcrypt.generate_password_hash(user_data['password']).decode('utf-8')
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=password_hash,
                    full_name=user_data['full_name'],
                    role_id=role.id,
                    is_approved=True,
                    is_active=True,
                    department=user_data['department']
                )
                db.session.add(user)
                print(f"    Created user: {user_data['username']} ({user_data['role']})")
            else:
                print(f"    User already exists: {user_data['username']}")

        db.session.commit()

        print("\n" + "=" * 50)
        print("Database initialization complete!")
        print("=" * 50)
        print("\nDefault credentials:")
        print("  Admin:      admin / admin123")
        print("  Agent:      agent1 / agent123")
        print("  Scrap Team: scrap1 / scrap123")
        print("\nRun 'python run.py' to start the application.")


if __name__ == '__main__':
    init_database()
