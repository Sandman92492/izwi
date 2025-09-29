import os
from datetime import timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# Validate required environment variables
SESSION_SECRET = os.environ.get("SESSION_SECRET")
DATABASE_URL = os.environ.get("DATABASE_URL")

if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET environment variable is required")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

# create the app
app = Flask(__name__)
app.secret_key = SESSION_SECRET
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Session configuration for production compatibility
# Check if running in production (common deployment indicator)
is_production = os.environ.get('REPLIT_DEPLOYMENT') == '1' or os.environ.get('FLASK_ENV') == 'production'

app.config.update(
    SESSION_COOKIE_SECURE=is_production,  # True for HTTPS production environments
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

def init_database():
    """Initialize database tables - safe for multiple calls"""
    with app.app_context():
        # Make sure to import the models here or their tables won't be created
        import models  # noqa: F401
        
        try:
            # Create all tables if they don't exist
            db.create_all()
            app.logger.info("Database tables initialized successfully")
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")
            raise

# Initialize database during app creation
init_database()