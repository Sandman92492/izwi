import json
from flask import session
from flask_login import current_user
from database import get_db
from utils import sanitize_plain_text, validate_json_data, generate_invite_slug

def create_community(community_name, boundary_data=''):
    """Create a new community"""
    # Validate input
    if not community_name:
        return None, 'Community name is required'
    
    if len(community_name) > 100:
        return None, 'Community name must be less than 100 characters'
    
    # Sanitize input
    community_name = sanitize_plain_text(community_name.strip())
    boundary_data = validate_json_data(boundary_data)
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if community name already exists
    cursor.execute('SELECT id FROM communities WHERE name = ?', (community_name,))
    existing_community = cursor.fetchone()
    if existing_community:
        return None, 'A community with this name already exists. Please choose a different name.'
    
    # Generate unique invite slug
    invite_slug = generate_invite_slug()
    
    # Create community
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
    
    return community_id, None

def get_community_by_invite_slug(invite_slug):
    """Get community by invite slug"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM communities WHERE invite_link_slug = ?', (invite_slug,))
    community = cursor.fetchone()
    return community

def get_community_info(community_id):
    """Get community information"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM communities WHERE id = ?', (community_id,))
    community = cursor.fetchone()
    return community

def get_community_members(community_id):
    """Get all members of a community"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE community_id = ?', (community_id,))
    members = cursor.fetchall()
    return members

def get_community_boundary_data(community_id):
    """Get community boundary data"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT boundary_data FROM communities WHERE id = ?', (community_id,))
    result = cursor.fetchone()
    return result[0] if result and result[0] else None

def remove_member(member_id, admin_user):
    """Remove a member from the community (admin only)"""
    if admin_user.role != 'Admin':
        return False, 'You do not have permission to remove members'
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE users SET community_id = NULL WHERE id = ?', (member_id,))
    db.commit()
    
    return True, 'Member removed successfully'

def update_community_name(new_name, community_id, admin_user):
    """Update community name (admin only)"""
    if admin_user.role != 'Admin':
        return False, 'Admin access required'
    
    # Sanitize and validate input
    new_name = sanitize_plain_text(new_name.strip())
    
    if not new_name:
        return False, 'Community name is required'
    
    if len(new_name) > 100:
        return False, 'Community name must be less than 100 characters'
    
    # Check if name already exists (excluding current community)
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM communities WHERE name = ? AND id != ?', (new_name, community_id))
    if cursor.fetchone():
        return False, 'A community with this name already exists'
    
    # Update community name
    cursor.execute('UPDATE communities SET name = ? WHERE id = ?', (new_name, community_id))
    db.commit()
    
    return True, 'Community name updated successfully!'

def update_community_boundary(boundary_data, community_id, admin_user):
    """Update community boundary (admin only)"""
    if admin_user.role != 'Admin':
        return False, 'Admin access required'
    
    # Validate JSON if provided
    if boundary_data:
        try:
            json.loads(boundary_data)  # Validate JSON format
        except json.JSONDecodeError:
            return False, 'Invalid boundary data format'
    
    # Update community boundary
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE communities SET boundary_data = ? WHERE id = ?', (boundary_data, community_id))
    db.commit()
    
    return True, 'Community boundary updated successfully!'