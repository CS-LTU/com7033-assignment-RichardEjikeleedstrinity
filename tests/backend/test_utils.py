"""
Unit tests for utility functions
"""
import pytest
from datetime import datetime
import re

from api.help_utils.helpers import (
    sanitize_input, 
    validate_email, 
    validate_patient_data,
    format_date,
    calculate_risk_score
)

class TestSanitizeInput:
    """Test sanitize_input function"""
    
    def test_sanitize_input_removes_dangerous_chars(self):
        """Test that dangerous HTML characters are removed"""
        dangerous_input = '<script>alert("xss")</script>'
        sanitized = sanitize_input(dangerous_input)
        assert '<' not in sanitized
        assert '>' not in sanitized
        assert '"' not in sanitized
        assert "'" not in sanitized
        assert '&' not in sanitized
    
    def test_sanitize_input_limits_length(self):
        """Test that input length is limited to 500 characters"""
        long_input = 'a' * 600
        sanitized = sanitize_input(long_input)
        assert len(sanitized) == 500
    
    def test_sanitize_input_non_string(self):
        """Test that non-string inputs are returned unchanged"""
        test_cases = [123, 45.67, True, None, ['list'], {'dict': 'value'}]
        for case in test_cases:
            assert sanitize_input(case) == case
    
    def test_sanitize_input_empty_string(self):
        """Test empty string handling"""
        assert sanitize_input('') == ''

class TestValidateEmail:
    """Test validate_email function"""
    
    def test_valid_emails(self):
        """Test various valid email formats"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user@sub.domain.com'
        ]
        for email in valid_emails:
            assert validate_email(email) is True
    
    def test_invalid_emails(self):
        """Test various invalid email formats"""
        invalid_emails = [
            'invalid-email',
            'user@.com',
            '@example.com',
            'user@domain.',
            'user name@domain.com'
        ]
        for email in invalid_emails:
            assert validate_email(email) is False
    
    def test_email_case_insensitive(self):
        """Test email validation is case-insensitive"""
        assert validate_email('Test@Example.COM') is True

class TestValidatePatientData:
    """Test validate_patient_data function"""
    
    def test_valid_patient_data(self):
        """Test valid patient data"""
        valid_data = {
            'age': 45,
            'bmi': 25.5,
            'avg_glucose_level': 120.5,
            'smoking_status': 'never smoked',
            'hypertension': 0,
            'heart_disease': 0,
            'gender': 'Female'
        }
        assert validate_patient_data(valid_data) is True
    
    def test_invalid_age(self):
        """Test invalid age values"""
        invalid_ages = [
            {'age': -5},
            {'age': 150},
            {'age': 'forty-five'},
            {'age': None}
        ]
        for data in invalid_ages:
            full_data = {**data, 'bmi': 25, 'avg_glucose_level': 100, 'smoking_status': 'never smoked'}
            assert validate_patient_data(full_data) is False
    
    def test_invalid_bmi(self):
        """Test invalid BMI values"""
        invalid_bmis = [
            {'bmi': 5},     # Too low
            {'bmi': 85},    # Too high
            {'bmi': 'high'},
            {'bmi': None}
        ]
        for data in invalid_bmis:
            full_data = {**data, 'age': 45, 'avg_glucose_level': 100, 'smoking_status': 'never smoked'}
            assert validate_patient_data(full_data) is False
    
    def test_invalid_glucose_level(self):
        """Test invalid glucose levels"""
        invalid_glucose = [
            {'avg_glucose_level': 30},   # Too low
            {'avg_glucose_level': 600},  # Too high
            {'avg_glucose_level': 'high'},
            {'avg_glucose_level': None}
        ]
        for data in invalid_glucose:
            full_data = {**data, 'age': 45, 'bmi': 25, 'smoking_status': 'never smoked'}
            assert validate_patient_data(full_data) is False
    
    def test_invalid_smoking_status(self):
        """Test invalid smoking status"""
        invalid_status = [
            {'smoking_status': 'sometimes'},
            {'smoking_status': 1},
            {'smoking_status': None},
            {'smoking_status': ''}
        ]
        for data in invalid_status:
            full_data = {**data, 'age': 45, 'bmi': 25, 'avg_glucose_level': 100}
            assert validate_patient_data(full_data) is False

class TestFormatDate:
    """Test format_date function"""
    
    def test_format_datetime(self):
        """Test formatting datetime objects"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        formatted = format_date(dt)
        assert formatted == '2023-12-25 14:30:45'
    
    def test_format_string_date(self):
        """Test formatting string dates"""
        date_string = '2023-12-25'
        formatted = format_date(date_string)
        assert formatted == '2023-12-25'
    
    def test_format_none(self):
        """Test formatting None"""
        assert format_date(None) is None
    
    def test_format_integer(self):
        """Test formatting non-date types"""
        assert format_date(123) == 123

class TestCalculateRiskScore:
    """Test calculate_risk_score function"""
    
    def test_risk_score_elderly_patient(self):
        """Test risk calculation for elderly patient"""
        patient_data = {
            'age': 75,
            'hypertension': 1,
            'heart_disease': 1,
            'avg_glucose_level': 210,
            'bmi': 32,
            'smoking_status': 'smokes',
            'gender': 'Male'
        }
        score = calculate_risk_score(patient_data)
        # Expected: 30(age) + 15(hypertension) + 15(heart) + 20(glucose) + 15(bmi) + 20(smoking) + 5(gender) = 120 -> capped at 100
        assert score == 100
    
    def test_risk_score_young_healthy_patient(self):
        """Test risk calculation for young healthy patient"""
        patient_data = {
            'age': 25,
            'hypertension': 0,
            'heart_disease': 0,
            'avg_glucose_level': 90,
            'bmi': 22,
            'smoking_status': 'never smoked',
            'gender': 'Female'
        }
        score = calculate_risk_score(patient_data)
        # Expected: 0(age) + 0(hypertension) + 0(heart) + 0(glucose) + 0(bmi) + 0(smoking) + 0(gender) = 0
        assert score == 0
    
    def test_risk_score_middle_aged_moderate(self):
        """Test risk calculation for middle-aged patient with moderate risk"""
        patient_data = {
            'age': 55,
            'hypertension': 1,
            'heart_disease': 0,
            'avg_glucose_level': 150,
            'bmi': 28,
            'smoking_status': 'formerly smoked',
            'gender': 'Male'
        }
        score = calculate_risk_score(patient_data)
        # Expected: 10(age) + 15(hypertension) + 0(heart) + 10(glucose) + 5(bmi) + 10(smoking) + 5(gender) = 55
        assert score == 55
    
    def test_risk_score_missing_fields(self):
        """Test risk calculation with missing fields"""
        patient_data = {
            'age': 45,
            'bmi': 25,
            'smoking_status': 'never smoked'
        }
        score = calculate_risk_score(patient_data)
        # Missing fields should be treated as 0/low risk
        assert score >= 0
        assert score <= 100
    
    def test_risk_score_capped_at_100(self):
        """Test that risk score is capped at 100"""
        patient_data = {
            'age': 80,
            'hypertension': 1,
            'heart_disease': 1,
            'avg_glucose_level': 300,
            'bmi': 40,
            'smoking_status': 'smokes',
            'gender': 'Male'
        }
        score = calculate_risk_score(patient_data)
        assert score == 100