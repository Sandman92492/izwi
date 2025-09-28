from datetime import datetime, timedelta
from flask import session, request, redirect, url_for, flash
from flask_login import UserMixin, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User
from utils import sanitize_plain_text, validate_email

# User model methods moved to models.py

def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

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
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password_hash, password):
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
    if User.query.filter_by(email=email).first():
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
    
    user = User(
        email=email,
        password_hash=password_hash,
        name='',
        avatar_url='',
        community_id=community_id,
        role=role,
        business_id=business_id,
        subscription_tier=subscription_tier
    )
    
    db.session.add(user)
    db.session.commit()
    
    return user, None