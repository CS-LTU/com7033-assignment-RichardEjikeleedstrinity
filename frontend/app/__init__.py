from datetime import timedelta
import os
import secrets
from flask import Flask
from app.models_all.user_models import db
from app.mongodb_service import mongo_service
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
limiter = Limiter(
    
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
def create_app():
    app = Flask(__name__)


    csrf.init_app(app)
    
    # CSRF configuration
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('CSRF_SECRET_KEY', secrets.token_hex(32))
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    # Secure configuration - use environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///stroke_database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    csp = {
        'default-src': ["'self'"],
        'style-src': [
            "'self'", 
            "'unsafe-inline'", 
            "https://fonts.googleapis.com",
            "https://cdn.tailwindcss.com"
        ],
        'script-src': [
            "'self'", 
            "'unsafe-inline'",
            "https://cdn.tailwindcss.com"
        ],
        'font-src': [
            "'self'",
            "https://fonts.gstatic.com",
            "https://fonts.googleapis.com"
        ],
        'connect-src': ["'self'", "http://localhost:5000", "http://127.0.0.1:5000"],
        'img-src': ["'self'", "data:", "https:"],
        'frame-src': ["'self'"]
    }
    
    Talisman(
        app, 
        content_security_policy=csp,
        content_security_policy_nonce_in='self',
        force_https=False,  # Keep False for development
        session_cookie_secure=False
    )
    
    # Rate limiting

    
    

    
    # Import and register blueprints AFTER db initialization
    with app.app_context():
        from app.routes.auth_routes import auth_bp
        from app.routes.dashboard_routes import dashboard_bp
        from app.routes.patient_routes import patient_bp

        
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(patient_bp)


        limiter.limit("10 per minute")(auth_bp)
        limiter.limit("100 per hour")(patient_bp)
    
    return app