import os
import sqlite3
import secrets
import string
import re
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import bleach
from markupsafe import Markup
from database import init_db, get_db

app = Flask(__name__)
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

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Initialize CSRF protection
csrf = CSRFProtect(app)

@app.before_request
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

class User(UserMixin):
    def __init__(self, id, email, name, avatar_url, community_id, role):
        self.id = id
        self.email = email
        self.name = name
        self.avatar_url = avatar_url
        self.community_id = community_id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6])
    return None

def sanitize_text_input(text):
    """Sanitize user text input to prevent XSS attacks"""
    if not text:
        return text
    # Allow basic formatting but strip dangerous tags and attributes
    allowed_tags = ['p', 'br', 'strong', 'em', 'u']
    allowed_attributes = {}
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)

def sanitize_plain_text(text):
    """Sanitize plain text input, removing all HTML tags"""
    if not text:
        return text
    return bleach.clean(text, tags=[], attributes={}, strip=True)

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_json_data(data):
    """Validate and sanitize JSON data"""
    if not data:
        return ""
    try:
        import json
        # Try to parse as JSON to validate format
        parsed = json.loads(data)
        # Re-serialize to ensure clean format
        return json.dumps(parsed)
    except (json.JSONDecodeError, ValueError):
        # If not valid JSON, treat as plain text and sanitize
        return sanitize_plain_text(data)

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

def generate_invite_slug():
    """Generate a unique invite slug for communities"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

def get_category_color(category):
    """Get color for alert category"""
    colors = {
        'Emergency': '#DC2626',  # Red
        'Fire': '#EA580C',       # Orange-red
        'Traffic': '#2563EB',    # Blue
        'Weather': '#7C3AED',    # Purple
        'Community': '#059669',  # Green
        'Other': '#6B7280'       # Gray
    }
    return colors.get(category, '#6B7280')

def get_category_icon(category):
    """Get emoji icon for alert category"""
    icons = {
        'Emergency': '🚨',
        'Fire': '🔥',
        'Traffic': '🚗',
        'Weather': '⛈️',
        'Community': '🏘️',
        'Other': '❗'
    }
    return icons.get(category, '❗')

def format_time_ago(timestamp_str):
    """Format timestamp to relative time"""
    try:
        from datetime import datetime
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    except:
        return timestamp_str

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/signup')
def signup_page():
    # Check for invite link
    invite_slug = request.args.get('invite')
    invite = None
    
    if invite_slug:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM communities WHERE invite_link_slug = ?', (invite_slug,))
        community = cursor.fetchone()
        
        if community:
            session['invite_community_id'] = community[0]
            invite = {
                'community_name': community[1],
                'slug': invite_slug
            }
    
    return render_template('landing.html', invite=invite)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = sanitize_plain_text(request.form.get('email', '').strip())
        password = request.form.get('password', '')
        
        # Validate input
        if not email or not password:
            flash('Email and password are required')
            return render_template('login.html')
        
        if not validate_email(email):
            flash('Please enter a valid email address')
            return render_template('login.html')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        
        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6])
            
            # Handle "Remember me" functionality
            remember = request.form.get('remember') == 'on'
            login_user(user, remember=remember, duration=remember_duration if remember else None)
            
            # Make session permanent if remember me is checked
            if remember:
                session.permanent = True
            
            # Add success message for login
            flash('Welcome back! You have been successfully logged in.', 'success')
            
            # Redirect based on whether user has a community
            if user.community_id:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('define_community'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup_submit():
        email = sanitize_plain_text(request.form.get('email', '').strip())
        password = request.form.get('password', '')
        consent = request.form.get('consent')
        
        # Validate input
        if not email or not password:
            flash('Email and password are required')
            return redirect(url_for('signup_page'))
        
        if not consent:
            flash('You must agree to the Terms of Service and Privacy Policy to sign up')
            return redirect(url_for('signup_page'))
        
        if not validate_email(email):
            flash('Please enter a valid email address')
            return redirect(url_for('signup_page'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long')
            return redirect(url_for('signup_page'))
        
        # Check if user already exists
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            flash('Email already registered')
            return redirect(url_for('signup_page'))
        
        # Create new user
        password_hash = generate_password_hash(password)
        community_id = session.get('invite_community_id')  # From invite link
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, name, avatar_url, community_id, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, password_hash, '', '', community_id, 'Member' if community_id else 'Admin'))
        
        user_id = cursor.lastrowid
        db.commit()
        
        # Log in the new user
        user = User(user_id, email, '', '', community_id, 'Member' if community_id else 'Admin')
        login_user(user)
        
        # Clear invite session
        session.pop('invite_community_id', None)
        
        # Add success message and redirect based on whether they joined via invite
        if community_id:
            # Store user info for welcome screen
            session['new_user_welcome'] = True
            session['user_name'] = email.split('@')[0].title()  # Use email username as name placeholder
            return redirect(url_for('welcome'))
        else:
            flash('Welcome! Your account has been created. Let\'s set up your community.', 'success')
            return redirect(url_for('define_community'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/define-community', methods=['GET', 'POST'])
@login_required
def define_community():
    if request.method == 'POST':
        community_name = sanitize_plain_text(request.form.get('community_name', '').strip())
        boundary_data = validate_json_data(request.form.get('boundary_data', ''))
        
        # Validate input
        if not community_name:
            flash('Community name is required')
            return render_template('define_community.html')
        
        if len(community_name) > 100:
            flash('Community name must be less than 100 characters')
            return render_template('define_community.html')
        
        # Create new community
        db = get_db()
        cursor = db.cursor()
        
        # Check if community name already exists
        cursor.execute('SELECT id FROM communities WHERE name = ?', (community_name,))
        existing_community = cursor.fetchone()
        if existing_community:
            flash('A community with this name already exists. Please choose a different name.')
            return render_template('define_community.html')
        
        invite_slug = generate_invite_slug()
        
        cursor.execute('''
            INSERT INTO communities (name, admin_user_id, invite_link_slug, subscription_plan, boundary_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (community_name, current_user.id, invite_slug, 'Free', boundary_data))
        
        community_id = cursor.lastrowid
        
        # Update user with community_id and admin role
        cursor.execute('''
            UPDATE users SET community_id = ?, role = ?
            WHERE id = ?
        ''', (community_id, 'Admin', current_user.id))
        
        db.commit()
        
        # Update current user object and refresh the session
        current_user.community_id = community_id
        current_user.role = 'Admin'
        
        # Refresh the user session to ensure updated data persists
        session['_user_id'] = str(current_user.id)
        session.permanent = True
        
        # Boundary data is now stored in the database
        flash(f'Congratulations! Your community "{community_name}" has been created successfully.', 'success')
        
        return redirect(url_for('dashboard'))
    
    return render_template('define_community.html')

@app.route('/welcome')
@login_required
def welcome():
    # Check if this is a new user welcome
    if not session.get('new_user_welcome'):
        return redirect(url_for('dashboard'))
    
    user_name = session.get('user_name', 'there')
    
    # Clear the welcome session flag
    session.pop('new_user_welcome', None)
    session.pop('user_name', None)
    
    return render_template('welcome.html', user_name=user_name)

@app.route('/dashboard')
@login_required
def dashboard():
    # Refresh user data from database to ensure we have the latest community_id
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT community_id, role FROM users WHERE id = ?', (current_user.id,))
    user_data = cursor.fetchone()
    
    if user_data and user_data[0]:
        # Update current user object with fresh data from database
        current_user.community_id = user_data[0]
        current_user.role = user_data[1]
    
    if not current_user.community_id:
        return redirect(url_for('define_community'))
    
    # Get community alerts
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT a.*, u.name as author_name
        FROM alerts a
        JOIN users u ON a.user_id = u.id
        WHERE a.community_id = ? AND a.is_resolved = 0
        ORDER BY a.timestamp DESC
    ''', (current_user.community_id,))
    
    alerts = cursor.fetchall()
    
    # Get community boundary data
    cursor.execute('''
        SELECT boundary_data FROM communities WHERE id = ?
    ''', (current_user.community_id,))
    
    community_result = cursor.fetchone()
    boundary_data = community_result[0] if community_result and community_result[0] else None
    
    return render_template('dashboard.html', alerts=alerts, 
                         boundary_data=boundary_data,
                         get_category_color=get_category_color, 
                         get_category_icon=get_category_icon,
                         format_time_ago=format_time_ago)

@app.route('/post-alert', methods=['GET', 'POST'])
@login_required
def post_alert():
    if not current_user.community_id:
        return redirect(url_for('define_community'))
    
    if request.method == 'POST':
        category = sanitize_plain_text(request.form.get('category', ''))
        description = sanitize_text_input(request.form.get('description', ''))
        
        # Validate input
        if not category or not description:
            flash('Category and description are required')
            return render_template('post_alert.html')
        
        if len(description) > 500:
            flash('Description must be less than 500 characters')
            return render_template('post_alert.html')
        
        # Validate and parse coordinates
        try:
            latitude = float(request.form.get('latitude', 0)) if request.form.get('latitude') else 0
            longitude = float(request.form.get('longitude', 0)) if request.form.get('longitude') else 0
        except (ValueError, TypeError):
            latitude = 0
            longitude = 0
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO alerts (community_id, user_id, category, description, latitude, longitude, timestamp, is_resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user.community_id, current_user.id, category, description, latitude, longitude, datetime.now(), 0))
        
        db.commit()
        
        flash('Alert posted successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('post_alert.html')

@app.route('/settings')
@login_required
def settings():
    if not current_user.community_id:
        return redirect(url_for('define_community'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get community info
    cursor.execute('SELECT * FROM communities WHERE id = ?', (current_user.community_id,))
    community = cursor.fetchone()
    
    # Get all members
    cursor.execute('SELECT * FROM users WHERE community_id = ?', (current_user.community_id,))
    members = cursor.fetchall()
    
    return render_template('settings.html', community=community, members=members)

@app.route('/remove-member/<int:member_id>')
@login_required
def remove_member(member_id):
    if current_user.role != 'Admin':
        flash('You do not have permission to remove members')
        return redirect(url_for('settings'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE users SET community_id = NULL WHERE id = ?', (member_id,))
    db.commit()
    
    flash('Member removed successfully')
    return redirect(url_for('settings'))

@app.route('/join/<slug>')
def join_community(slug):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM communities WHERE invite_link_slug = ?', (slug,))
    community = cursor.fetchone()
    
    if community:
        session['invite_community_id'] = community[0]
        return render_template('landing.html', invite=True)
    else:
        flash('Invalid invite link')
        return redirect(url_for('index'))

@app.route('/report-alert', methods=['POST'])
@login_required
def report_alert():
    """Handle alert reporting"""
    try:
        data = request.get_json()
        alert_id = data.get('alert_id')
        
        if not alert_id:
            return jsonify({'success': False, 'message': 'Alert ID is required'}), 400
        
        # Log the report action
        app.logger.info(f'Alert {alert_id} reported by user {current_user.id} ({current_user.email}) at {datetime.utcnow()}')
        
        # In a production system, you would save this to a reports table
        # For now, we're just logging as requested
        
        return jsonify({'success': True, 'message': 'Report submitted successfully'})
    
    except Exception as e:
        app.logger.error(f'Error processing alert report: {e}')
        return jsonify({'success': False, 'message': 'An error occurred while submitting the report'}), 500

@app.route('/update-community-name', methods=['POST'])
@login_required
def update_community_name():
    """Update community name (admin only)"""
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        new_name = sanitize_plain_text(data.get('name', '').strip())
        
        if not new_name:
            return jsonify({'success': False, 'message': 'Community name is required'}), 400
        
        if len(new_name) > 100:
            return jsonify({'success': False, 'message': 'Community name must be less than 100 characters'}), 400
        
        # Check if name already exists (excluding current community)
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM communities WHERE name = ? AND id != ?', (new_name, current_user.community_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'A community with this name already exists'}), 400
        
        # Update community name
        cursor.execute('UPDATE communities SET name = ? WHERE id = ?', (new_name, current_user.community_id))
        db.commit()
        
        app.logger.info(f'Community {current_user.community_id} name updated to "{new_name}" by admin {current_user.id}')
        return jsonify({'success': True, 'message': 'Community name updated successfully!'})
    
    except Exception as e:
        app.logger.error(f'Error updating community name: {e}')
        return jsonify({'success': False, 'message': 'An error occurred while updating the community name'}), 500

@app.route('/update-community-boundary', methods=['POST'])
@login_required
def update_community_boundary():
    """Update community boundary (admin only)"""
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        boundary_data = data.get('boundary_data', '')
        
        # Validate JSON if provided
        if boundary_data:
            try:
                json.loads(boundary_data)  # Validate JSON format
            except json.JSONDecodeError:
                return jsonify({'success': False, 'message': 'Invalid boundary data format'}), 400
        
        # Update community boundary
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE communities SET boundary_data = ? WHERE id = ?', (boundary_data, current_user.community_id))
        db.commit()
        
        app.logger.info(f'Community {current_user.community_id} boundary updated by admin {current_user.id}')
        return jsonify({'success': True, 'message': 'Community boundary updated successfully!'})
    
    except Exception as e:
        app.logger.error(f'Error updating community boundary: {e}')
        return jsonify({'success': False, 'message': 'An error occurred while updating the community boundary'}), 500

# Custom error handlers to hide technical details from users
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 Forbidden errors"""
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    # Log the error for debugging but don't show it to the user
    app.logger.error(f'Server Error: {error}')
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def too_many_requests_error(error):
    """Handle 429 Too Many Requests errors"""
    return render_template('errors/429.html'), 429

@app.errorhandler(400)
def bad_request_error(error):
    """Handle 400 Bad Request errors"""
    return render_template('errors/400.html'), 400

# Global exception handler for any unhandled exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle any unhandled exceptions"""
    # Log the error for debugging
    app.logger.error(f'Unhandled Exception: {e}', exc_info=True)
    # Return generic error page without technical details
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)