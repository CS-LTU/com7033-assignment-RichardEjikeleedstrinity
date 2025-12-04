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