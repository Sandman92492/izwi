import json
from flask import session
from flask_login import current_user
from app import db
from models import Community, User
from utils import sanitize_plain_text, validate_json_data, generate_invite_slug

def create_community(community_name, boundary_data='', business_id=None):
    """Create a new community"""
    # Validate input
    if not community_name:
        return None, 'Community name is required'
    
    if len(community_name) > 100:
        return None, 'Community name must be less than 100 characters'
    
    # Sanitize input
    community_name = sanitize_plain_text(community_name.strip())
    boundary_data = validate_json_data(boundary_data)
    
    # Check if community name already exists
    existing_community = Community.query.filter_by(name=community_name).first()
    if existing_community:
        return None, 'A community with this name already exists. Please choose a different name.'
    
    # Generate unique invite slug
    invite_slug = generate_invite_slug()
    
    # Determine subscription plan based on business association
    subscription_plan = 'Premium' if business_id else 'Free'
    
    # Create community
    community = Community(
        name=community_name,
        admin_user_id=current_user.id,
        invite_link_slug=invite_slug,
        subscription_plan=subscription_plan,
        boundary_data=boundary_data,
        business_id=business_id
    )
    
    db.session.add(community)
    db.session.flush()  # Get the ID
    
    # Update user with community_id and admin role
    user = User.query.get(current_user.id)
    if user:
        user.community_id = community.id
        user.role = 'Admin'
    
    db.session.commit()
    
    return community.id, None

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
    if not (admin_user.role in ['Admin', 'Business'] or admin_user.is_business_user()):
        return False, 'You do not have permission to remove members'
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE users SET community_id = NULL WHERE id = ?', (member_id,))
    db.commit()
    
    return True, 'Member removed successfully'

def update_community_name(new_name, community_id, admin_user):
    """Update community name (admin or business user only)"""
    if not (admin_user.role in ['Admin', 'Business'] or admin_user.is_business_user()):
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
    """Update community boundary (admin or business user only)"""
    if not (admin_user.role in ['Admin', 'Business'] or admin_user.is_business_user()):
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

def get_business_info(business_id):
    """Get business information for white-labeling"""
    if not business_id:
        return None
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM businesses WHERE id = ? AND is_active = 1', (business_id,))
    business = cursor.fetchone()
    return business

def get_community_business_info(community_id):
    """Get business information associated with a community"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT b.* FROM businesses b
        JOIN communities c ON b.id = c.business_id
        WHERE c.id = ? AND b.is_active = 1
    ''', (community_id,))
    business = cursor.fetchone()
    return business

def get_business_communities(business_id):
    """Get all communities associated with a business"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM communities WHERE business_id = ?', (business_id,))
    communities = cursor.fetchall()
    return communities

def create_business(name, logo_url=None, primary_color='#1F2937', contact_email=None, subscription_tier='Free'):
    """Create a new business for white-labeling"""
    db = get_db()
    cursor = db.cursor()
    
    # Sanitize inputs
    name = sanitize_plain_text(name.strip())
    if logo_url:
        logo_url = sanitize_plain_text(logo_url.strip())
    if contact_email:
        contact_email = sanitize_plain_text(contact_email.strip())
    if primary_color:
        primary_color = sanitize_plain_text(primary_color.strip())
    
    cursor.execute('''
        INSERT INTO businesses (name, logo_url, primary_color, contact_email, subscription_tier)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, logo_url, primary_color, contact_email, subscription_tier))
    
    business_id = cursor.lastrowid
    db.commit()
    
    return business_id