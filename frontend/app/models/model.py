# app/models_all/user_models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()

class User(db.Model):
    """User model for SQLite database"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='doctor', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # One-to-many relationship with predictions
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def create_default_admin(cls):
        """Create default admin user if doesn't exist"""
        admin = cls.query.filter_by(email='admin@hospital.com').first()
        if not admin:
            admin = cls(
                email='admin@hospital.com',
                full_name='System Administrator',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin user created")
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active
        }

class Prediction(db.Model):
    """Prediction model for tracking predictions in SQLite"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.String(50), nullable=False)  # MongoDB patient ID
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)  # High, Medium, Low
    input_data = db.Column(db.Text, nullable=False)  # JSON string of input data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert prediction to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'patient_id': self.patient_id,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'input_data': self.input_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }