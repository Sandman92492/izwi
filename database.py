import sqlite3
import os

DATABASE = 'izwi.db'

def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize the database with required tables"""
    db = get_db()
    cursor = db.cursor()
    
    # Create businesses table for white-labeling
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            logo_url TEXT,
            primary_color TEXT DEFAULT '#1F2937',
            contact_email TEXT,
            subscription_tier TEXT DEFAULT 'Free',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            avatar_url TEXT,
            community_id INTEGER,
            role TEXT DEFAULT 'Member',
            business_id INTEGER,
            subscription_tier TEXT DEFAULT 'Free',
            FOREIGN KEY (community_id) REFERENCES communities (id),
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    ''')
    
    # Create communities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS communities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            admin_user_id INTEGER NOT NULL,
            invite_link_slug TEXT UNIQUE NOT NULL,
            subscription_plan TEXT DEFAULT 'Free',
            boundary_data TEXT,
            business_id INTEGER,
            max_alerts INTEGER DEFAULT 100,
            max_members INTEGER DEFAULT 50,
            FOREIGN KEY (admin_user_id) REFERENCES users (id),
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            community_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            latitude REAL DEFAULT 0,
            longitude REAL DEFAULT 0,
            timestamp DATETIME NOT NULL,
            is_resolved INTEGER DEFAULT 0,
            is_premium_feature INTEGER DEFAULT 0,
            FOREIGN KEY (community_id) REFERENCES communities (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Migration: Add new columns to existing tables if they don't exist
    migrations = [
        ('communities', 'boundary_data', 'TEXT'),
        ('communities', 'business_id', 'INTEGER'),
        ('communities', 'max_alerts', 'INTEGER DEFAULT 100'),
        ('communities', 'max_members', 'INTEGER DEFAULT 50'),
        ('users', 'business_id', 'INTEGER'),
        ('users', 'subscription_tier', 'TEXT DEFAULT "Free"'),
        ('alerts', 'is_premium_feature', 'INTEGER DEFAULT 0')
    ]
    
    for table, column, column_type in migrations:
        try:
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {column_type}')
        except sqlite3.OperationalError:
            # Column already exists
            pass
    
    db.commit()
    db.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")