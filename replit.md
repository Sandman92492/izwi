# iZwi Community Alert App

## Overview
A Flask-based community alert system that allows users to create and join communities, post alerts, and manage members. The application features user authentication, community management, and real-time alert posting with categorization.

## Recent Changes
- **2025-09-26**: Complete Flask backend implementation with SQLite database
- **2025-09-26**: User authentication system with Flask-Login
- **2025-09-26**: Dynamic Jinja2 template integration
- **2025-09-26**: All core routes implemented (login, signup, dashboard, settings, community creation)
- **2025-09-26**: Security improvements (environment-based secret key)

## Project Architecture
### Backend Structure
- `main.py`: Flask application with all routes and authentication logic
- `database.py`: SQLite database initialization and schema management
- `templates/`: Jinja2 templates converted from original HTML designs
  - `login.html`: User login page
  - `landing.html`: Landing/signup page with community invitation support
  - `dashboard.html`: Main dashboard with alert feed and map view
  - `settings.html`: Community management and member administration
  - `define_community.html`: Community creation interface
  - `post_alert.html`: Alert posting modal/interface

### Database Schema
- **users**: id, email, password_hash, name, avatar_url, community_id, role
- **communities**: id, name, admin_user_id, invite_link_slug, subscription_plan
- **alerts**: id, community_id, user_id, category, description, latitude, longitude, timestamp, is_resolved

### Key Features
- User registration and authentication with secure password hashing
- Community creation with unique invite link generation
- Role-based access control (Admin/Member)
- Alert posting with categories: Emergency, Fire, Traffic, Weather, Community, Other
- Member management with admin controls
- Community invitation system via unique URL slugs
- Responsive design with Tailwind CSS

## User Preferences
- Uses Flask as the backend framework
- SQLite for development database
- Jinja2 templating for dynamic content
- Material Symbols for icons
- Tailwind CSS for styling

## Environment Configuration
- SESSION_SECRET: Flask session secret key (uses environment variable)
- Port 5000 for development server
- Debug mode enabled for development

## Current Status
Flask server running successfully on port 5000 with all core functionality implemented.