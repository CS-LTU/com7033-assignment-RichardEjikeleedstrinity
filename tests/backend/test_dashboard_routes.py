"""
Integration tests for dashboard routes
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime
from bson import ObjectId

class TestDashboardRoutes:
    """Test dashboard endpoints"""
    
    def test_get_dashboard_stats(self, client, auth_headers):
        """Test retrieving dashboard statistics"""
        with patch('api.dashboard.routes.mongo') as mock_mongo:
            # Setup mock responses
            mock_mongo.db.patients.count_documents.side_effect = [
                150,  # Total patients
                25,   # High risk patients
                5     # Today's patients
            ]
            
            # Mock aggregation for risk distribution
            mock_risk_dist = [
                {'_id': 'High', 'count': 25},
                {'_id': 'Medium', 'count': 50},
                {'_id': 'Low', 'count': 75}
            ]
            
            mock_aggregate = Mock()
            mock_aggregate.aggregate.return_value = mock_risk_dist
            mock_mongo.db.patients.aggregate.return_value = mock_risk_dist
            
            # Mock recent patients
            mock_recent_patients = [
                {
                    '_id': ObjectId('1'),
                    'patient_id': 'PT001',
                    'name': 'Patient 1',
                    'age': 45,
                    'gender': 'Male',
                    'risk_score': 75,
                    'risk_level': 'High',
                    'created_at': datetime.utcnow()
                }
            ]
            mock_mongo.db.patients.find.return_value.sort.return_value.limit.return_value = mock_recent_patients
            
            # Mock monthly trend
            mock_monthly_trend = [
                {'_id': {'year': 2023, 'month': 12}, 'count': 10},
                {'_id': {'year': 2024, 'month': 1}, 'count': 15}
            ]
            mock_mongo.db.patients.aggregate.return_value = mock_monthly_trend
            
            # Mock gender distribution
            mock_gender_dist = [
                {'_id': 'Male', 'count': 80},
                {'_id': 'Female', 'count': 70}
            ]
            mock_mongo.db.patients.aggregate.return_value = mock_gender_dist
            
            headers = auth_headers()
            response = client.get('/api/dashboard/stats', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Check stats structure
            assert 'stats' in data
            assert 'recent_patients' in data
            assert 'monthly_trend' in data
            assert 'gender_distribution' in data
            
            # Check specific values
            assert data['stats']['total_patients'] == 150
            assert data['stats']['high_risk_patients'] == 25
            assert data['stats']['todays_patients'] == 5
            
            # Check risk distribution
            risk_dist = data['stats']['risk_distribution']
            assert risk_dist['High'] == 25
            assert risk_dist['Medium'] == 50
            assert risk