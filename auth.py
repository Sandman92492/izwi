from datetime import datetime, timedelta
from flask import session, request, redirect, url_for, flash
from flask_login import UserMixin, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from utils import sanitize_plain_text, validate_email

class User(UserMixin):
    def __init__(self, id, email, name, avatar_url, community_id, role, business_id=None, subscription_tier='Free'):
        self.id = id
        self.email = email
        self.name = name
        self.avatar_url = avatar_url
        self.community_id = community_id
        self.role = role
        self.business_id = business_id
        self.subscription_tier = subscription_tier
    
    def is_business_user(self):
        """Check if user is a business-level user"""
        return self.role == 'Business' or self.business_id is not None
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'Admin'
    
    def has_premium_access(self):
        """Check if user has premium access"""
        return self.subscription_tier == 'Premium' or self.role == 'Business'

def load_user(user_id):
    """Load user by ID for Flask-Login"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        # Handle both old and new database schemas gracefully
        business_id = user_data[7] if len(user_data) > 7 else None
        subscription_tier = user_data[8] if len(user_data) > 8 else 'Free'
        return User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6], business_id, subscription_tier)
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
        # Handle both old and new database schemas gracefully
        business_id = user_data[7] if len(user_data) > 7 else None
        subscription_tier = user_data[8] if len(user_data) > 8 else 'Free'
        user = User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6], business_id, subscription_tier)
        return user, None
    else:
        return None, 'Invalid email or password'

def create_user(email, password, community_id=None, business_id=None, role=None):
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
    
    # Determine user role and subscription tier
    if not role:
        if business_id:
            role = 'Business'
        elif community_id:
            role = 'Member'
        else:
            role = 'Admin'
    
    subscription_tier = 'Premium' if role == 'Business' else 'Free'
    
    # Create new user
    password_hash = generate_password_hash(password)
    
    cursor.execute('''
        INSERT INTO users (email, password_hash, name, avatar_url, community_id, role, business_id, subscription_tier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (email, password_hash, '', '', community_id, role, business_id, subscription_tier))
    
    user_id = cursor.lastrowid
    db.commit()
    
    # Create user object
    user = User(user_id, email, '', '', community_id, role, business_id, subscription_tier)
    return user, None