import os
from datetime import timedelta
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Flask app configuration
    app.secret_key = os.environ.get('SESSION_SECRET')
    if not app.secret_key:
        raise ValueError("SESSION_SECRET environment variable is required")
    
    # Enhanced security configuration
    is_production = os.environ.get('FLASK_ENV') == 'production'
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # CSRF token expires in 1 hour
    app.config['WTF_CSRF_SSL_STRICT'] = is_production
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Sessions expire after 24 hours
    
    # Configure session for remember me functionality
    remember_duration = timedelta(days=7) if is_production else timedelta(days=3)  # Shorter in production
    app.permanent_session_lifetime = timedelta(hours=24)
    app.config['REMEMBER_COOKIE_DURATION'] = remember_duration
    app.config['REMEMBER_COOKIE_SECURE'] = is_production
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_REFRESH_EACH_REQUEST'] = False
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    
    return app

def init_login_manager(app):
    """Initialize Flask-Login manager"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # type: ignore
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    return login_manager

def init_csrf(app):
    """Initialize CSRF protection"""
    csrf = CSRFProtect(app)
    return csrf