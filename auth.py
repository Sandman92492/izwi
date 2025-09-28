from datetime import datetime, timedelta
from flask import session, request, redirect, url_for, flash
from flask_login import UserMixin, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from utils import sanitize_plain_text, validate_email

class User(UserMixin):
    def __init__(self, id, email, name, avatar_url, community_id, role):
        self.id = id
        self.email = email
        self.name = name
        self.avatar_url = avatar_url
        self.community_id = community_id
        self.role = role

def load_user(user_id):
    """Load user by ID for Flask-Login"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6])
    return None

def check_session_timeout():
    """Check if the current session has timed out"""
    try:
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.now() - last_activity > timedelta(hours=24):
                session.clear()
                return True
        session['last_activity'] = datetime.now().isoformat()
        return False
    except (ValueError, TypeError):
        # Handle malformed timestamp data
        session.clear()
        return True

def check_session_activity():
    """Check session timeout before each request to authenticated routes"""
    # Skip session timeout for certain routes that don't need authentication
    if request.endpoint in ['index', 'signup_page', 'login', 'join_community', 'static', 'privacy_policy', 'terms_of_service']:
        return
    
    # Check session timeout for authenticated users
    if current_user.is_authenticated:
        if check_session_timeout():
            logout_user()
            flash('Your session has expired. Please log in again.')
            return redirect(url_for('login'))

def authenticate_user(email, password):
    """Authenticate user with email and password"""
    # Validate input
    if not email or not password:
        return None, 'Email and password are required'
    
    if not validate_email(email):
        return None, 'Please enter a valid email address'
    
    # Sanitize email
    email = sanitize_plain_text(email.strip())
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user_data = cursor.fetchone()
    
    if user_data and check_password_hash(user_data[2], password):
        user = User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6])
        return user, None
    else:
        return None, 'Invalid email or password'

def create_user(email, password, community_id=None):
    """Create a new user account"""
    # Validate input
    if not email or not password:
        return None, 'Email and password are required'
    
    if not validate_email(email):
        return None, 'Please enter a valid email address'
    
    if len(password) < 8:
        return None, 'Password must be at least 8 characters long'
    
    # Sanitize email
    email = sanitize_plain_text(email.strip())
    
    # Check if user already exists
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        return None, 'Email already registered'
    
    # Create new user
    password_hash = generate_password_hash(password)
    role = 'Member' if community_id else 'Admin'
    
    cursor.execute('''
        INSERT INTO users (email, password_hash, name, avatar_url, community_id, role)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (email, password_hash, '', '', community_id, role))
    
    user_id = cursor.lastrowid
    db.commit()
    
    # Create user object
    user = User(user_id, email, '', '', community_id, role)
    return user, None