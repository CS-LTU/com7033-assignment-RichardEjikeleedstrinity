# api/database.py
import sqlite3
from flask import g
import os
from werkzeug.security import generate_password_hash

DATABASE = 'users.db'

def get_db():
    """Get SQLite database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize SQLite database with users table"""
    print("Initializing SQLite database...")
    
    try:
        # Connect to database (creates it if doesn't exist)
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        
        # Create users table
        db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'doctor',
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create index on email
        db.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        # Check if admin exists
        cursor = db.execute('SELECT id FROM users WHERE email = ?', ('admin@hospital.com',))
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            # Create default admin user
            password_hash = generate_password_hash('admin123')
            db.execute(
                'INSERT INTO users (email, password_hash, full_name, role) VALUES (?, ?, ?, ?)',
                ('admin@hospital.com', password_hash, 'System Administrator', 'admin')
            )
            print("✅ Created default admin user")
        
        db.commit()
        db.close()
        print("✅ SQLite database initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing SQLite database: {e}")
        raise

def init_app(app):
    """Register database functions with Flask app"""
    # Register teardown function
    app.teardown_appcontext(close_db)
    
    # Initialize database within app context
    with app.app_context():
        init_db()