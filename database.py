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
            FOREIGN KEY (community_id) REFERENCES communities (id)
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
            FOREIGN KEY (admin_user_id) REFERENCES users (id)
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
            FOREIGN KEY (community_id) REFERENCES communities (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    db.commit()
    db.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")