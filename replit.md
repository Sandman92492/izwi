# iZwi Community Alert App

## Overview
A Flask-based community alert system that allows users to create and join communities, post alerts, and manage members. The application features user authentication, community management, and real-time alert posting with categorization.

## Recent Changes
- **2025-09-26**: Complete Flask backend implementation with SQLite database
- **2025-09-26**: User authentication system with Flask-Login
- **2025-09-26**: Dynamic Jinja2 template integration
- **2025-09-26**: All core routes implemented (login, signup, dashboard, settings, community creation)
- **2025-09-26**: Security improvements (environment-based secret key)
- **2025-09-26**: Interactive maps functionality using Leaflet.js
- **2025-09-26**: Dashboard map with real-time alert markers and category icons
- **2025-09-26**: Post alert location selection with click-to-set and geolocation
- **2025-09-26**: Community boundary drawing with Leaflet Draw tools
- **2025-09-26**: Separated home screen from sign-up page for better user experience
- **2025-09-26**: Added clear sign-in option for existing users on home and sign-up pages
- **2025-09-28**: Color-coded alert system with simplified card design and emoji icons
- **2025-09-28**: Enhanced map markers with larger, more visible category-specific pins
- **2025-09-28**: Community boundary display on dashboard map with persistent storage
- **2025-09-28**: Added comprehensive legal documents for POPIA compliance
- **2025-09-28**: Created Privacy Policy emphasizing South African data storage and user rights
- **2025-09-28**: Created Terms of Service with emergency service disclaimers and user responsibilities
- **2025-09-28**: Added footer links to legal documents across all main application templates
- **2025-09-28**: **Major Backend Refactoring**: Restructured monolithic main.py into organized modules for better maintainability and extensibility

## Project Architecture
### Backend Structure (Modular Architecture)
- **Core Application**:
  - `main.py`: Flask app initialization and route definitions only
  - `config.py`: Flask application configuration and extension setup
  - `database.py`: SQLite database initialization and schema management

- **Feature Modules**:
  - `auth.py`: User authentication logic (User class, login/logout, signup, session management)
  - `community.py`: Community management (creation, invites, member management, boundaries)
  - `alerts.py`: Alert functionality (posting, displaying, reporting, categorization)
  - `utils.py`: Helper functions (sanitization, validation, formatting, category handling)

- **Templates**:
  - `templates/`: Jinja2 templates converted from original HTML designs
    - `home.html`: Main landing page with sign-in and sign-up options
    - `login.html`: User login page with link back to sign-up
    - `landing.html`: Community sign-up page with community invitation support
    - `dashboard.html`: Main dashboard with alert feed and map view
    - `settings.html`: Community management and member administration
    - `define_community.html`: Community creation interface
    - `post_alert.html`: Alert posting modal/interface

**Architecture Benefits**:
- **Separation of Concerns**: Each module handles a specific domain (auth, communities, alerts)
- **Maintainability**: Easier to locate and modify specific functionality
- **Extensibility**: New features can be added to appropriate modules without affecting others
- **Testing**: Individual modules can be tested in isolation
- **Clean Dependencies**: One-way import flow (routes → modules → database/utils)

### Database Schema
- **users**: id, email, password_hash, name, avatar_url, community_id, role
- **communities**: id, name, admin_user_id, invite_link_slug, subscription_plan, boundary_data
- **alerts**: id, community_id, user_id, category, description, latitude, longitude, timestamp, is_resolved

### Key Features
- User registration and authentication with secure password hashing
- Community creation with unique invite link generation
- Role-based access control (Admin/Member)
- Alert posting with categories: Emergency, Fire, Traffic, Weather, Community, Other
- **Interactive Maps with Leaflet.js**:
  - Dashboard map displaying community alerts as markers with category icons
  - Click-to-set location selection for posting alerts
  - Automatic geolocation support for user's current position
  - Community boundary drawing tools with polygon/circle/rectangle options
  - **Community boundary display**: Boundaries drawn during creation are stored and displayed on dashboard
  - Real-time map interactions with popups showing alert details
  - Automatic map fitting to community boundaries when no alerts are present
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
Project imported to Replit - setting up for Replit environment with proper database configuration and hosting setup.