import os
import sqlite3
import secrets
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET')
if not app.secret_key:
    raise ValueError("SESSION_SECRET environment variable is required")

# Configure session for remember me functionality
app.permanent_session_lifetime = timedelta(days=30)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_REFRESH_EACH_REQUEST'] = False

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.remember_cookie_duration = timedelta(days=30)  # Remember for 30 days
login_manager.session_protection = None  # Disable for remember me to work properly

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
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        
        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6])
            
            # Handle "Remember me" functionality
            remember = request.form.get('remember') == 'on'
            login_user(user, remember=remember, duration=timedelta(days=30) if remember else None)
            
            # Make session permanent if remember me is checked
            if remember:
                session.permanent = True
            
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
        email = request.form['email']
        password = request.form['password']
        
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
        
        # Redirect based on whether they joined via invite
        if community_id:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('define_community'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/define-community', methods=['GET', 'POST'])
@login_required
def define_community():
    if request.method == 'POST':
        community_name = request.form['community_name']
        boundary_data = request.form.get('boundary_data', '')
        
        # Create new community
        db = get_db()
        cursor = db.cursor()
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
        if boundary_data:
            print(f"Community boundary data saved for {community_name}")
        
        return redirect(url_for('dashboard'))
    
    return render_template('define_community.html')

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
        category = request.form['category']
        description = request.form['description']
        latitude = float(request.form.get('latitude', 0)) if request.form.get('latitude') else 0
        longitude = float(request.form.get('longitude', 0)) if request.form.get('longitude') else 0
        
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

if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)