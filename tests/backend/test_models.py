"""
Unit tests for data models
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from bson import ObjectId

from api.models import User, Patient

class TestUserModel:
    """Test User model methods"""
    
    @patch('api.models.mongo')
    def test_find_by_email(self, mock_mongo):
        """Test finding user by email"""
        # Setup mock
        mock_user = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'email': 'test@example.com',
            'password': 'hashed_password',
            'full_name': 'Test User',
            'role': 'doctor'
        }
        mock_mongo.db.users.find_one.return_value = mock_user
        
        # Test
        user = User.find_by_email('test@example.com')
        
        # Assertions
        mock_mongo.db.users.find_one.assert_called_once_with({'email': 'test@example.com'})
        assert user == mock_user
    
    @patch('api.models.mongo')
    def test_find_by_email_not_found(self, mock_mongo):
        """Test finding non-existent user by email"""
        mock_mongo.db.users.find_one.return_value = None
        
        user = User.find_by_email('nonexistent@example.com')
        
        assert user is None
    
    @patch('api.models.mongo')
    def test_create_user(self, mock_mongo):
        """Test creating a new user"""
        # Setup mock
        mock_insert_result = Mock()
        mock_insert_result.inserted_id = ObjectId('507f1f77bcf86cd799439012')
        mock_mongo.db.users.insert_one.return_value = mock_insert_result
        
        user_data = {
            'email': 'new@example.com',
            'password': 'hashed_password',
            'full_name': 'New User',
            'role': 'doctor'
        }
        
        # Test
        result = User.create_user(user_data)
        
        # Assertions
        mock_mongo.db.users.insert_one.assert_called_once()
        assert result.inserted_id == mock_insert_result.inserted_id

class TestPatientModel:
    """Test Patient model methods"""
    
    @patch('api.models.mongo')
    def test_get_all_patients(self, mock_mongo):
        """Test getting all patients with pagination"""
        # Setup mock data
        mock_patients = [
            {'_id': ObjectId('1'), 'name': 'Patient 1'},
            {'_id': ObjectId('2'), 'name': 'Patient 2'}
        ]
        mock_mongo.db.patients.find.return_value.skip.return_value.limit.return_value = mock_patients
        mock_mongo.db.patients.count_documents.return_value = 100
        
        # Test
        patients, total = Patient.get_all(page=1, per_page=10, search='')
        
        # Assertions
        assert len(patients) == 2
        assert total == 100
    
    @patch('api.models.mongo')
    def test_find_by_id(self, mock_mongo):
        """Test finding patient by ID"""
        mock_patient = {
            '_id': ObjectId('507f1f77bcf86cd799439013'),
            'name': 'Test Patient',
            'age': 45
        }
        mock_mongo.db.patients.find_one.return_value = mock_patient
        
        patient = Patient.find_by_id('507f1f77bcf86cd799439013')
        
        mock_mongo.db.patients.find_one.assert_called_once_with({'_id': ObjectId('507f1f77bcf86cd799439013')})
        assert patient == mock_patient
    
    @patch('api.models.mongo')
    def test_create_patient(self, mock_mongo):
        """Test creating a new patient"""
        mock_insert_result = Mock()
        mock_insert_result.inserted_id = ObjectId('507f1f77bcf86cd799439014')
        mock_mongo.db.patients.insert_one.return_value = mock_insert_result
        
        patient_data = {
            'name': 'New Patient',
            'age': 30,
            'risk_score': 45
        }
        
        result = Patient.create(patient_data)
        
        mock_mongo.db.patients.insert_one.assert_called_once_with(patient_data)
        assert result == mock_insert_result
    
    @patch('api.models.mongo')
    def test_update_patient(self, mock_mongo):
        """Test updating a patient"""
        mock_update_result = Mock()
        mock_update_result.modified_count = 1
        mock_mongo.db.patients.update_one.return_value = mock_update_result
        
        patient_id = '507f1f77bcf86cd799439015'
        update_data = {'age': 46, 'bmi': 26.5}
        
        result = Patient.update(patient_id, update_data)
        
        mock_mongo.db.patients.update_one.assert_called_once_with(
            {'_id': ObjectId(patient_id)},
            {'$set': update_data}
        )
        assert result.modified_count == 1
    
    @patch('api.models.mongo')
    def test_delete_patient(self, mock_mongo):
        """Test deleting a patient"""
        mock_delete_result = Mock()
        mock_delete_result.deleted_count = 1
        mock_mongo.db.patients.delete_one.return_value = mock_delete_result
        
        patient_id = '507f1f77bcf86cd799439016'
        
        result = Patient.delete(patient_id)
        
        mock_mongo.db.patients.delete_one.assert_called_once_with({'_id': ObjectId(patient_id)})
        assert result.deleted_count == 1
    
    @patch('api.models.mongo')
    def test_get_patient_summary(self, mock_mongo):
        """Test getting patient summary"""
        mock_patient = {
            '_id': ObjectId('507f1f77bcf86cd799439017'),
            'name': 'Summary Patient',
            'age': 50,
            'gender': 'Female',
            'risk_score': 75,
            'risk_level': 'High'
        }
        mock_mongo.db.patients.find_one.return_value = mock_patient
        
        summary = Patient.get_summary('507f1f77bcf86cd799439017')
        
        assert summary == mock_patient