# app/services/api_client.py
import requests
import json
from flask import flash, redirect, session, url_for
from functools import wraps

class BackendAPIClient:
    """Python client to communicate with your backend API"""
    
    def __init__(self, base_url='http://localhost:3000/api'):
        self.base_url = base_url
    
    def _get_headers(self, additional_headers=None):
        """Get headers with authentication token"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add token from session if available
        token = session.get('token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make HTTP request to backend API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(kwargs.get('headers', {})),
                json=kwargs.get('json'),
                data=kwargs.get('data'),
                params=kwargs.get('params'),
                timeout=30
            )
            print(f"Making {method} request to {url} with kwargs: {kwargs}")
            # Log response for debugging
            print(f"API {method} {endpoint}: {response.status_code}")
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    return {'error': error_data.get('error', f'HTTP {response.status_code}')}
                except:
                    return {'error': f'HTTP {response.status_code}'}
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {'error': f'Connection failed: {str(e)}'}
        except Exception as e:
            print(f"API request error: {e}")
            return {'error': str(e)}
    
    # Auth methods
    def login(self, email, password):
        """Login to backend"""
        return self._make_request('POST', '/auth/login', 
                                 json={'email': email, 'password': password})
    
    def get_current_user(self):
        """Get current user info"""
        return self._make_request('GET', '/auth/me')
    
    # Patient methods
    def get_patients(self, page=1, per_page=25, search=''):
        """Get patients with pagination"""
        params = {
            'page': page,
            'per_page': per_page
        }
        if search:
            params['search'] = search
        
        return self._make_request('GET', '/patients', params=params)
    
    def get_patient(self, patient_id):
        """Get single patient"""
        return self._make_request('GET', f'/patients/{patient_id}')
    
    def get_patient_all(self,):
        """Get single patient"""
        return self._make_request('GET', f'/patients/all')
    
    def create_patient(self, patient_data):
        """Create new patient"""
        return self._make_request('POST', '/patients/create', json=patient_data)
    
    def update_patient(self, patient_id, patient_data):
        """Update patient"""
        return self._make_request('PUT', f'/patients/{patient_id}', json=patient_data)
    
    def delete_patient(self, patient_id):
        """Delete patient"""
        return self._make_request('DELETE', f'/patients/{patient_id}')
    
    # Dashboard methods
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        return self._make_request('GET', '/dashboard/stats')

# Create a global instance
api_client = BackendAPIClient()

# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in first')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function