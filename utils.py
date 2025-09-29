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

def format_time_ago(timestamp_input):
    """Format timestamp to relative time"""
    try:
        # Handle both datetime objects and timestamp strings
        if isinstance(timestamp_input, datetime):
            timestamp = timestamp_input
        else:
            # If it's a string, parse it
            timestamp_str = str(timestamp_input)
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        diff = now - timestamp
        
        if diff.days > 7:
            # For older dates, show month and day
            return timestamp.strftime("%b %d")
        elif diff.days > 0:
            return f"{diff.days} {'day' if diff.days == 1 else 'days'} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
        else:
            return "Just now"
    except Exception as e:
        # Fallback: return the original input as string
        return str(timestamp_input)

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
    from app import db
    from models import User, Alert
    from datetime import datetime
    from sqlalchemy import func, extract
    
    if not community:
        return False, "Community not found"
    
    # Get subscription limits - handle Community model object
    try:
        subscription_plan = getattr(community, 'subscription_plan', 'Free')
    except (TypeError, AttributeError):
        subscription_plan = 'Free'
    
    limits = get_subscription_limits(subscription_plan)
    
    if action_type == 'add_member':
        # Check member count using SQLAlchemy
        member_count = db.session.query(User).filter_by(community_id=community.id).count()
        
        if member_count >= limits['max_community_members']:
            return False, f"You've reached the maximum number of members ({limits['max_community_members']}) for your plan. Please upgrade to add more members."
    
    elif action_type == 'post_alert':
        # Check alerts this month using SQLAlchemy
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        alert_count = db.session.query(Alert).filter(
            Alert.community_id == community.id,
            extract('year', Alert.timestamp) == current_year,
            extract('month', Alert.timestamp) == current_month
        ).count()
        
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
            'business_name': business_info.name,
            'logo_url': business_info.logo_url,
            'primary_color': business_info.primary_color,
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