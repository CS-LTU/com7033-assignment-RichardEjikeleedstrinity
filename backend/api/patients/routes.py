from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from api.help_utils.mongodb import mongo
from flask_pymongo import PyMongo
from api.models import Patient
import re
from datetime import datetime

def sanitize_input(data):
    """Sanitize user input"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        data = re.sub(r'[<>&\"\']', '', data)
        # Limit length
        data = data[:500]
    return data

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_patient_data(data):
    """Validate patient data"""
    try:
        # Age validation
        age = data.get('age', 0)
        if not isinstance(age, (int, float)) or not (0 <= age <= 120):
            return False
        
        # BMI validation
        bmi = data.get('bmi', 0)
        if not isinstance(bmi, (int, float)) or not (10 <= bmi <= 80):
            return False
        
        # Glucose level validation
        glucose = data.get('avg_glucose_level', 0)
        if not isinstance(glucose, (int, float)) or not (50 <= glucose <= 500):
            return False
        
        # Smoking status validation
        smoking_status = data.get('smoking_status', '')
        valid_smoking_status = ['never smoked', 'formerly smoked', 'smokes', 'Unknown']
        if smoking_status not in valid_smoking_status:
            return False
        
        return True
    except (KeyError, TypeError):
        return False

def format_date(date_obj):
    """Format date object to string"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    return date_obj

patients_bp = Blueprint('patients', __name__)

# Helper function for risk calculation
def calculate_risk_score(patient_data):
    """Calculate stroke risk score"""
    risk_score = 0
    
    # Age factor
    age = patient_data.get('age', 0)
    if age >= 70:
        risk_score += 30
    elif age >= 60:
        risk_score += 20
    elif age >= 50:
        risk_score += 10
    
    # Hypertension
    if patient_data.get('hypertension') == 1:
        risk_score += 15
    
    # Heart disease
    if patient_data.get('heart_disease') == 1:
        risk_score += 15
    
    # Glucose level
    glucose = patient_data.get('avg_glucose_level', 0)
    if glucose > 200:
        risk_score += 20
    elif glucose > 140:
        risk_score += 10
    
    # BMI
    bmi = patient_data.get('bmi', 0)
    if bmi >= 30:
        risk_score += 15
    elif bmi >= 25:
        risk_score += 5
    
    # Smoking status
    smoking = patient_data.get('smoking_status', '')
    if smoking == 'smokes':
        risk_score += 20
    elif smoking == 'formerly smoked':
        risk_score += 10
    
    # Gender
    if patient_data.get('gender') == 'Male':
        risk_score += 5
    
    return min(risk_score, 100)

@patients_bp.route('/', methods=['GET'])
@jwt_required()
def get_patients():
    """Get all patients with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        search = request.args.get('search', '')
        
        patients, total = Patient.get_all(page, per_page, search)
        
        # Convert ObjectId to string
        for patient in patients:
            patient['_id'] = str(patient['_id'])
        
        return jsonify({
            'patients': patients,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patients_bp.route('/<patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id):
    """Get single patient by ID"""
    try:
        patient = Patient.find_by_id(patient_id)
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        patient['_id'] = str(patient['_id'])
        return jsonify(patient), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@patients_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_patients():
    """Get all patients without pagination"""
    try:
        # Fetch all patients from the database
        patients = list(mongo.db.patients.find({}, {'_id': 0}))  # Exclude MongoDB's ObjectId
        
        return jsonify({
            'patients': patients,
            'total': len(patients)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patients_bp.route('/create', methods=['POST'])
@jwt_required()
def create_patient():
    """Create new patient"""
    try:
        data = request.get_json()
        print("Request data:", data)  # Debugging: Log the incoming data
        
        # Validate required fields
        required_fields = ['gender', 'age', 'avg_glucose_level', 'bmi', 'smoking_status']
        for field in required_fields:
            if field not in data:
                print(f"Missing field: {field}")  # Debugging: Log missing fields
                return jsonify({'error': f'{field} is required'}), 400
        
        # Sanitize inputs
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = sanitize_input(value)
            else:
                sanitized_data[key] = value
        
        
        # Validate data
        if not validate_patient_data(sanitized_data):
            print("Validation failed")  # Debugging: Log validation failure
            return jsonify({'error': 'Invalid patient data'}), 400
        
        # Calculate risk score
        risk_score = calculate_risk_score(sanitized_data)
        sanitized_data['risk_score'] = risk_score
        
        # Determine risk level
        if risk_score >= 50:
            sanitized_data['risk_level'] = 'High'
        elif risk_score >= 30:
            sanitized_data['risk_level'] = 'Medium'
        else:
            sanitized_data['risk_level'] = 'Low'
        
        # Set default values
        sanitized_data['stroke'] = 0
        sanitized_data['created_at'] = datetime.utcnow()
        sanitized_data['updated_at'] = datetime.utcnow()
        
        # Generate patient ID
        total_patients = mongo.db.patients.count_documents({})
        sanitized_data['patient_id'] = f"PT{total_patients + 1:05d}"
        print("Generated patient ID:", sanitized_data['patient_id'])  # Debugging: Log patient ID
        
        # Insert patient
        result = Patient.create(sanitized_data)
        print("Insert result:", result)  # Debugging: Log insert result
        print(sanitized_data['risk_score'])
        print(sanitized_data['risk_level'])
        print(sanitized_data['patient_id'])
        print("Sanitized data:", sanitized_data)  # Debugging: Log sanitized data
        if result.inserted_id:
            return jsonify({
                'message': 'Patient created successfully',
                'patient_id': str(result.inserted_id),
                'patient_data': sanitized_data
            }), 201
        
        return jsonify({'error': 'Failed to create patient'}), 500
    except Exception as e:
        print("Exception occurred:", str(e))  # Debugging: Log the exception
        return jsonify({'error': str(e)}), 500
    
@patients_bp.route('/<patient_id>', methods=['PUT'])
@jwt_required()
def update_patient(patient_id):
    """Update existing patient"""
    try:
        data = request.get_json()
        
        # Check if patient exists
        patient = Patient.find_by_id(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Sanitize inputs
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = sanitize_input(value)
            else:
                sanitized_data[key] = value
        
        # Validate data
        if not validate_patient_data(sanitized_data):
            return jsonify({'error': 'Invalid patient data'}), 400
        
        # Calculate risk score if relevant fields changed
        if any(key in sanitized_data for key in ['age', 'hypertension', 'heart_disease', 
                                                  'avg_glucose_level', 'bmi', 'smoking_status', 'gender']):
            # Combine existing data with updates
            update_data = {**patient, **sanitized_data}
            risk_score = calculate_risk_score(update_data)
            sanitized_data['risk_score'] = risk_score
            
            # Update risk level
            if risk_score >= 50:
                sanitized_data['risk_level'] = 'High'
            elif risk_score >= 30:
                sanitized_data['risk_level'] = 'Medium'
            else:
                sanitized_data['risk_level'] = 'Low'
        
        # Update patient
        result = Patient.update(patient_id, sanitized_data)
        
        if result.modified_count > 0:
            return jsonify({
                'message': 'Patient updated successfully',
                'modified_count': result.modified_count
            }), 200
        
        return jsonify({'message': 'No changes made'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patients_bp.route('/<patient_id>', methods=['DELETE'])
@jwt_required()
def delete_patient(patient_id):
    """Delete patient"""
    try:
        result = Patient.delete(patient_id)
        
        if result.deleted_count > 0:
            return jsonify({'message': 'Patient deleted successfully'}), 200
        
        return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patients_bp.route('/bulk', methods=['POST'])
@jwt_required()
def bulk_create_patients():
    """Bulk create patients from CSV/JSON"""
    try:
        data = request.get_json()
        
        if not isinstance(data, list):
            return jsonify({'error': 'Expected array of patients'}), 400
        
        created_count = 0
        errors = []
        
        for index, patient_data in enumerate(data):
            try:
                # Validate required fields
                required_fields = ['gender', 'age', 'avg_glucose_level', 'bmi']
                missing_fields = [field for field in required_fields if field not in patient_data]
                
                if missing_fields:
                    errors.append(f"Patient {index}: Missing fields {missing_fields}")
                    continue
                
                # Calculate risk score
                risk_score = calculate_risk_score(patient_data)
                patient_data['risk_score'] = risk_score
                
                # Determine risk level
                if risk_score >= 60:
                    patient_data['risk_level'] = 'High'
                elif risk_score >= 40:
                    patient_data['risk_level'] = 'Medium'
                else:
                    patient_data['risk_level'] = 'Low'
                
                # Set defaults
                patient_data.setdefault('stroke', 0)
                patient_data['created_at'] = datetime.utcnow()
                patient_data['updated_at'] = datetime.utcnow()
                
                # Generate patient ID
                total_patients = mongo.db.patients.count_documents({}) + created_count
                patient_data['patient_id'] = f"PT{total_patients + 1:05d}"
                
                # Insert patient
                mongo.db.patients.insert_one(patient_data)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Patient {index}: {str(e)}")
        
        return jsonify({
            'message': f'Successfully created {created_count} patients',
            'created_count': created_count,
            'errors': errors if errors else None
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500