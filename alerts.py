from datetime import datetime
from flask import current_app
from flask_login import current_user
from database import get_db
from utils import sanitize_plain_text, sanitize_text_input

def get_community_alerts(community_id, include_resolved=False):
    """Get all alerts for a community"""
    db = get_db()
    cursor = db.cursor()
    
    query = '''
        SELECT a.*, u.name as author_name
        FROM alerts a
        JOIN users u ON a.user_id = u.id
        WHERE a.community_id = ?
    '''
    params = [community_id]
    
    if not include_resolved:
        query += ' AND a.is_resolved = 0'
    
    query += ' ORDER BY a.timestamp DESC'
    
    cursor.execute(query, params)
    alerts = cursor.fetchall()
    return alerts

def create_alert(community_id, user_id, category, description, latitude=0, longitude=0):
    """Create a new alert"""
    # Validate input
    if not category or not description:
        return None, 'Category and description are required'
    
    if len(description) > 500:
        return None, 'Description must be less than 500 characters'
    
    # Sanitize input
    category = sanitize_plain_text(category)
    description = sanitize_text_input(description)
    
    # Validate and parse coordinates
    try:
        latitude = float(latitude) if latitude else 0
        longitude = float(longitude) if longitude else 0
    except (ValueError, TypeError):
        latitude = 0
        longitude = 0
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO alerts (community_id, user_id, category, description, latitude, longitude, timestamp, is_resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (community_id, user_id, category, description, latitude, longitude, datetime.now(), 0))
    
    alert_id = cursor.lastrowid
    db.commit()
    
    return alert_id, None

def report_alert(alert_id, reporter_user):
    """Report an alert for inappropriate content"""
    if not alert_id:
        return False, 'Alert ID is required'
    
    # Log the report action
    current_app.logger.info(f'Alert {alert_id} reported by user {reporter_user.id} ({reporter_user.email}) at {datetime.utcnow()}')
    
    # In a production system, you would save this to a reports table
    # For now, we're just logging as requested
    
    return True, 'Report submitted successfully'

def resolve_alert(alert_id, user):
    """Mark an alert as resolved (admin only)"""
    if user.role != 'Admin':
        return False, 'Admin access required'
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE alerts SET is_resolved = 1 WHERE id = ?', (alert_id,))
    db.commit()
    
    return True, 'Alert marked as resolved'

def get_alert_by_id(alert_id):
    """Get a specific alert by ID"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT a.*, u.name as author_name
        FROM alerts a
        JOIN users u ON a.user_id = u.id
        WHERE a.id = ?
    ''', (alert_id,))
    alert = cursor.fetchone()
    return alert