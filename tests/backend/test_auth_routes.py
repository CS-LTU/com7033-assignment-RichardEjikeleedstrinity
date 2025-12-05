"""
Integration tests for authentication routes
"""
import pytest
import json
from unittest.mock import patch
import bcrypt

class TestAuthRoutes:
    """Test authentication endpoints"""
    
    def test_login_success(self, client, mock_mongo):
        """Test successful login"""
        # Mock user data
        hashed_password = bcrypt.hashpw('TestPassword123!'.encode('utf-8'), bcrypt.gensalt())
        mock_user = {
            '_id': '507f1f77bcf86cd799439011',
            'email': 'doctor@hospital.com',
            'password': hashed_password,
            'full_name': 'Dr. Test',
            'role': 'doctor',
            'is_active': True
        }
        
        # Setup mocks
        mock_mongo.db.users.find_one.return_value = mock_user
        
        # Make request
        response = client.post('/api/auth/login', 
            json={'email': 'doctor@hospital.com', 'password': 'TestPassword123!'})
        
        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == 'doctor@hospital.com'
        assert data['user']['role'] == 'doctor'
    
    def test_login_invalid_credentials(self, client, mock_mongo):
        """Test login with invalid credentials"""
        mock_mongo.db.users.find_one.return_value = None
        
        response = client.post('/api/auth/login',
            json={'email': 'wrong@example.com', 'password': 'wrongpass'})
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing required fields"""
        test_cases = [
            {},
            {'email': 'test@example.com'},
            {'password': 'password123'},
            {'email': '', 'password': 'password123'}
        ]
        
        for data in test_cases:
            response = client.post('/api/auth/login', json=data)
            assert response.status_code == 400
    
    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format"""
        response = client.post('/api/auth/login',
            json={'email': 'invalid-email', 'password': 'password123'})
        
        assert response.status_code == 400
    
    def test_register_success(self, client, mock_mongo):
        """Test successful user registration"""
        # Setup mocks
        mock_mongo.db.users.find_one.return_value = None  # User doesn't exist
        mock_insert_result = Mock()
        mock_insert_result.inserted_id = '507f1f77bcf86cd799439012'
        mock_mongo.db.users.insert_one.return_value = mock_insert_result
        
        # Make request
        user_data = {
            'email': 'newdoctor@hospital.com',
            'password': 'SecurePass123!',
            'name': 'New Doctor',
            'role': 'doctor'
        }
        
        response = client.post('/api/auth/register', json=user_data)
        
        # Assertions
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'User created successfully'
        assert 'user_id' in data
    
    def test_register_existing_user(self, client, mock_mongo):
        """Test registration with existing email"""
        mock_mongo.db.users.find_one.return_value = {'email': 'existing@example.com'}
        
        user_data = {
            'email': 'existing@example.com',
            'password': 'password123',
            'name': 'Existing User'
        }
        
        response = client.post('/api/auth/register', json=user_data)
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data
    
    def test_get_current_user_authenticated(self, client, auth_headers):
        """Test getting current user info with valid token"""
        with patch('api.auth.routes.get_jwt_identity') as mock_identity:
            mock_identity.return_value = '507f1f77bcf86cd799439011'
            
            # Mock database response
            with patch('api.auth.routes.mongo') as mock_mongo_auth:
                mock_user = {
                    '_id': '507f1f77bcf86cd799439011',
                    'email': 'test@example.com',
                    'full_name': 'Test User',
                    'role': 'doctor'
                }
                mock_mongo_auth.db.users.find_one.return_value = mock_user
                
                headers = auth_headers()
                response = client.get('/api/auth/me', headers=headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['email'] == 'test@example.com'
                assert data['name'] == 'Test User'
    
    def test_get_current_user_not_found(self, client, auth_headers):
        """Test getting non-existent user"""
        with patch('api.auth.routes.get_jwt_identity') as mock_identity:
            mock_identity.return_value = 'nonexistent_id'
            
            with patch('api.auth.routes.mongo') as mock_mongo_auth:
                mock_mongo_auth.db.users.find_one.return_value = None
                
                headers = auth_headers()
                response = client.get('/api/auth/me', headers=headers)
                
                assert response.status_code == 404
    
    def test_logout(self, client, auth_headers):
        """Test logout endpoint"""
        headers = auth_headers()
        response = client.post('/api/auth/logout', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Logged out successfully'