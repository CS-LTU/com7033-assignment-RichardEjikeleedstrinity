"""
Pytest configuration and fixtures for the healthcare API tests
"""
import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from api.help_utils.mongodb import mongo

@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret-key',
        'MONGO_URI': 'mongodb://localhost:27017/healthcare_test_db',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    with app.app_context():
        # Clear test database
        if mongo.db:
            collections = mongo.db.list_collection_names()
            for collection in collections:
                mongo.db[collection].delete_many({})
    
    yield app

@pytest.fixture
def client(app):
    """Test client for making requests"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers():
    """Generate authentication headers for testing"""
    def _create_headers(token=None, user_id='test_user_123'):
        if not token:
            # Create a mock JWT token
            token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6IjEyMzQ1Njc4OTAiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJyb2xlIjoiZG9jdG9yIiwibmFtZSI6IlRlc3QgVXNlciIsImlhdCI6MTYxNjIzOTAyMn0.mock_signature'
        
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    return _create_headers

@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        'gender': 'Male',
        'age': 45,
        'avg_glucose_level': 120.5,
        'bmi': 28.3,
        'smoking_status': 'formerly smoked',
        'hypertension': 0,
        'heart_disease': 0,
        'name': 'John Doe'
    }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'name': 'Test User',
        'role': 'doctor'
    }

@pytest.fixture
def mock_mongo():
    """Mock MongoDB for unit tests"""
    with patch('api.help_utils.mongodb.mongo') as mock_mongo:
        mock_db = Mock()
        mock_mongo.db = mock_db
        
        # Mock collections
        mock_db.patients = Mock()
        mock_db.users = Mock()
        mock_db.predictions = Mock()
        
        yield mock_mongo