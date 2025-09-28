from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(255))
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'))
    role = db.Column(db.String(20), default='Member')
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'))
    subscription_tier = db.Column(db.String(20), default='Free')
    
    def is_business_user(self):
        """Check if user is a business-level user"""
        return self.role == 'Business' or self.business_id is not None
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'Admin'
    
    def has_premium_access(self):
        """Check if user has premium access"""
        return self.subscription_tier == 'Premium' or self.role == 'Business'


class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invite_link_slug = db.Column(db.String(100), unique=True, nullable=False)
    subscription_plan = db.Column(db.String(20), default='Free')
    boundary_data = db.Column(db.Text)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'))
    max_alerts = db.Column(db.Integer, default=100)
    max_members = db.Column(db.Integer, default=50)


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, default=0)
    longitude = db.Column(db.Float, default=0)
    timestamp = db.Column(db.DateTime, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    is_premium_feature = db.Column(db.Boolean, default=False)


class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255))
    primary_color = db.Column(db.String(7), default='#1F2937')
    contact_email = db.Column(db.String(120))
    subscription_tier = db.Column(db.String(20), default='Free')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)