import re
import json
import secrets
import string
from datetime import datetime
import bleach

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
        # Try to parse as JSON to validate format
        parsed = json.loads(data)
        # Re-serialize to ensure clean format
        return json.dumps(parsed)
    except (json.JSONDecodeError, ValueError):
        # If not valid JSON, treat as plain text and sanitize
        return sanitize_plain_text(data)

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

# Subscription and Premium Feature Utilities

def check_premium_feature_access(user, feature_name=None):
    """Check if user has access to premium features"""
    if not user:
        return False, "Please log in to access this feature."
    
    # Business users and premium subscribers have access
    if user.has_premium_access():
        return True, None
    
    # Free users are blocked
    feature_msg = f" '{feature_name}'" if feature_name else ""
    return False, f"This{feature_msg} is a premium feature. Please upgrade your plan."

def get_subscription_limits(subscription_tier):
    """Get limits based on subscription tier"""
    limits = {
        'Free': {
            'max_alerts_per_month': 100,
            'max_community_members': 50,
            'max_communities': 1,
            'advanced_analytics': False,
            'custom_branding': False,
            'priority_support': False
        },
        'Premium': {
            'max_alerts_per_month': 1000,
            'max_community_members': 500,
            'max_communities': 10,
            'advanced_analytics': True,
            'custom_branding': True,
            'priority_support': True
        }
    }
    return limits.get(subscription_tier, limits['Free'])

def check_community_limits(community, action_type):
    """Check if community has reached limits for certain actions"""
    from database import get_db
    
    if not community:
        return False, "Community not found"
    
    # Get subscription limits - properly handle sqlite3.Row object
    try:
        subscription_plan = community['subscription_plan'] if 'subscription_plan' in community.keys() else 'Free'
    except (TypeError, AttributeError):
        # Fallback for older community data structures
        subscription_plan = community[4] if len(community) > 4 else 'Free'
    
    limits = get_subscription_limits(subscription_plan)
    
    db = get_db()
    cursor = db.cursor()
    
    if action_type == 'add_member':
        # Check member count
        cursor.execute('SELECT COUNT(*) FROM users WHERE community_id = ?', (community[0],))
        member_count = cursor.fetchone()[0]
        
        if member_count >= limits['max_community_members']:
            return False, f"You've reached the maximum number of members ({limits['max_community_members']}) for your plan. Please upgrade to add more members."
    
    elif action_type == 'post_alert':
        # Check alerts this month
        cursor.execute('''
            SELECT COUNT(*) FROM alerts 
            WHERE community_id = ? AND timestamp >= date('now', 'start of month')
        ''', (community[0],))
        alert_count = cursor.fetchone()[0]
        
        if alert_count >= limits['max_alerts_per_month']:
            return False, f"You've reached the maximum number of alerts ({limits['max_alerts_per_month']}) for this month. Please upgrade your plan."
    
    return True, None

# Business Branding Utilities

def get_community_branding(community_id):
    """Get branding information for a community"""
    from community import get_community_business_info
    
    business_info = get_community_business_info(community_id)
    
    if business_info:
        return {
            'business_name': business_info[1],  # name
            'logo_url': business_info[2],       # logo_url
            'primary_color': business_info[3],  # primary_color
            'is_white_labeled': True
        }
    
    # Default branding for non-business communities
    return {
        'business_name': 'iZwi',
        'logo_url': None,
        'primary_color': '#1F2937',
        'is_white_labeled': False
    }

def apply_business_branding(template_data, community_id):
    """Apply business branding to template data"""
    branding = get_community_branding(community_id)
    
    # Add branding information to template context
    template_data.update({
        'branding': branding,
        'app_name': branding['business_name'],
        'primary_color': branding['primary_color'],
        'logo_url': branding['logo_url']
    })
    
    return template_data

def get_upgrade_prompt(feature_name=None):
    """Get standardized upgrade prompt message"""
    feature_text = f" '{feature_name}'" if feature_name else ""
    return {
        'title': 'Premium Feature',
        'message': f"This{feature_text} is a premium feature. Please upgrade your plan.",
        'action_text': 'Upgrade Now',
        'action_url': '/upgrade'
    }