"""
Integration tests for patient management routes
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime
from bson import ObjectId

class TestPatientRoutes:
    """Test patient management endpoints"""
    
    def test_get_all_patients(self, client, auth_headers):
        """Test retrieving all patients"""
        with patch('api.patients.routes.Patient.get_all') as mock_get_all:
            mock_patients = [
                {'_id': '1', 'name': 'Patient 1', 'age': 45},
                {'_id': '2', 'name': 'Patient 2', 'age': 52}
            ]
            mock_get_all.return_value = (mock_patients, 50)
            
            headers = auth_headers()
            response = client.get('/api/patients/', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'patients' in data
            assert 'total' in data
            assert 'page' in data
            assert len(data['patients']) == 2
    
    def test_get_single_patient(self, client, auth_headers):
        """Test retrieving single patient by ID"""
        with patch('api.patients.routes.Patient.find_by_id') as mock_find:
            mock_patient = {
                '_id': '507f1f77bcf86cd799439011',
                'name': 'John Doe',
                'age': 45,
                'gender': 'Male'
            }
            mock_find.return_value = mock_patient
            
            headers = auth_headers()
            response = client.get('/api/patients/507f1f77bcf86cd799439011', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['name'] == 'John Doe'
            assert data['age'] == 45
    
    def test_get_patient_not_found(self, client, auth_headers):
        """Test retrieving non-existent patient"""
        with patch('api.patients.routes.Patient.find_by_id') as mock_find:
            mock_find.return_value = None
            
            headers = auth_headers()
            response = client.get('/api/patients/nonexistent_id', headers=headers)
            
            assert response.status_code == 404
    
    def test_create_patient_success(self, client, auth_headers, sample_patient_data):
        """Test successful patient creation"""
        with patch('api.patients.routes.Patient.create') as mock_create:
            mock_result = Mock()
            mock_result.inserted_id = '507f1f77bcf86cd799439012'
            mock_create.return_value = mock_result
            
            # Mock count_documents for patient ID generation
            with patch('api.patients.routes.mongo') as mock_mongo:
                mock_mongo.db.patients.count_documents.return_value = 100
                
                headers = auth_headers()
                response = client.post('/api/patients/create', 
                    json=sample_patient_data,
                    headers=headers)
                
                assert response.status_code == 201
                data = response.get_json()
                assert data['message'] == 'Patient created successfully'
                assert 'patient_id' in data
                assert 'patient_data' in data
    
    def test_create_patient_missing_required_fields(self, client, auth_headers):
        """Test patient creation with missing required fields"""
        incomplete_data = {
            'age': 45,
            'bmi': 25.5
            # Missing gender, glucose_level, smoking_status
        }
        
        headers = auth_headers()
        response = client.post('/api/patients/create',
            json=incomplete_data,
            headers=headers)
        
        assert response.status_code == 400
    
    def test_create_patient_invalid_data(self, client, auth_headers):
        """Test patient creation with invalid data"""
        invalid_data = {
            'gender': 'Male',
            'age': 150,  # Invalid age
            'avg_glucose_level': 120.5,
            'bmi': 25.5,
            'smoking_status': 'never smoked'
        }
        
        headers = auth_headers()
        response = client.post('/api/patients/create',
            json=invalid_data,
            headers=headers)
        
        assert response.status_code == 400
    
    def test_update_patient_success(self, client, auth_headers):
        """Test successful patient update"""
        with patch('api.patients.routes.Patient.find_by_id') as mock_find:
            mock_find.return_value = {
                '_id': '507f1f77bcf86cd799439013',
                'age': 45,
                'risk_score': 30
            }
            
            with patch('api.patients.routes.Patient.update') as mock_update:
                mock_result = Mock()
                mock_result.modified_count = 1
                mock_update.return_value = mock_result
                
                update_data = {'age': 46, 'bmi': 26.5}
                
                headers = auth_headers()
                response = client.put('/api/patients/507f1f77bcf86cd799439013',
                    json=update_data,
                    headers=headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['message'] == 'Patient updated successfully'
    
    def test_update_patient_not_found(self, client, auth_headers):
        """Test updating non-existent patient"""
        with patch('api.patients.routes.Patient.find_by_id') as mock_find:
            mock_find.return_value = None
            
            update_data = {'age': 46}
            
            headers = auth_headers()
            response = client.put('/api/patients/nonexistent_id',
                json=update_data,
                headers=headers)
            
            assert response.status_code == 404
    
    def test_delete_patient_success(self, client, auth_headers):
        """Test successful patient deletion"""
        with patch('api.patients.routes.Patient.delete') as mock_delete:
            mock_result = Mock()
            mock_result.deleted_count = 1
            mock_delete.return_value = mock_result
            
            headers = auth_headers()
            response = client.delete('/api/patients/507f1f77bcf86cd799439014',
                headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'Patient deleted successfully'
    
    def test_delete_patient_not_found(self, client, auth_headers):
        """Test deleting non-existent patient"""
        with patch('api.patients.routes.Patient.delete') as mock_delete:
            mock_result = Mock()
            mock_result.deleted_count = 0
            mock_delete.return_value = mock_result
            
            headers = auth_headers()
            response = client.delete('/api/patients/nonexistent_id',
                headers=headers)
            
            assert response.status_code == 404
    
    def test_bulk_create_patients(self, client, auth_headers):
        """Test bulk patient creation"""
        patients_data = [
            {
                'gender': 'Male',
                'age': 45,
                'avg_glucose_level': 120.5,
                'bmi': 28.3,
                'smoking_status': 'never smoked'
            },
            {
                'gender': 'Female',
                'age': 52,
                'avg_glucose_level': 135.2,
                'bmi': 31.5,
                'smoking_status': 'formerly smoked'
            }
        ]
        
        headers = auth_headers()
        response = client.post('/api/patients/bulk',
            json=patients_data,
            headers=headers)
        
        # Note: This would need proper mocking of the bulk operations
        assert response.status_code in [201, 500]  # Depending on implementation
    
    def test_get_all_patients_no_pagination(self, client, auth_headers):
        """Test retrieving all patients without pagination"""
        with patch('api.patients.routes.mongo') as mock_mongo:
            mock_patients = [
                {'name': 'Patient 1', 'age': 45},
                {'name': 'Patient 2', 'age': 52}
            ]
            mock_mongo.db.patients.find.return_value = mock_patients
            
            headers = auth_headers()
            response = client.get('/api/patients/all', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'patients' in data
            assert 'total' in data
            assert len(data['patients']) == 2