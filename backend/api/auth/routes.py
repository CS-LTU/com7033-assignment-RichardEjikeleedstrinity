from flask import Blueprint, redirect, request, jsonify, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
from datetime import timedelta
from api.models import User
from api.help_utils.helpers import validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    print("Login attempt received")
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email'].strip().lower()
    password = data['password']
    
    # Validate email
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Find user
    print("Looking up user by email: " + email)
    user = User.find_by_email(email)
    print("User lookup complete" + str(user))
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check password
    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Create JWT token
    access_token = create_access_token(
        identity=str(user['_id']),
        expires_delta=timedelta(hours=24),
        additional_claims={
            'email': user['email'],
            'role': user['role'],
            'name': user.get('full_name', 'User')
        }
    )
    
    return jsonify({
        'token': access_token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'name': user.get('full_name', 'User'),
            'role': user['role']
        }
    }), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user (admin only)"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Email, password and name required'}), 400
    
    email = data['email'].strip().lower()
    password = data['password']
    name = data['name'].strip()
    
    # Validate email
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if user exists
    if User.find_by_email(email):
        return jsonify({'error': 'User already exists'}), 409
    
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user_data = {
        'email': email,
        'password': hashed_password,
        'full_name': name,
        'role': data.get('role', 'doctor'),
        'is_active': True
    }
    
    result = User.create_user(user_data)
    
    if result.inserted_id:
        return jsonify({
            'message': 'User created successfully',
            'user_id': str(result.inserted_id)
        }), 201
    
    return jsonify({'error': 'Failed to create user'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    current_user = get_jwt_identity()
    
    # Get user from database
    from api.help_utils.mongodb import MongoDB
    from api.help_utils.mongodb import mongo
    user = mongo.db.users.find_one({'_id': MongoDB.object_id(current_user)})
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': str(user['_id']),
        'email': user['email'],
        'name': user.get('full_name', 'User'),
        'role': user['role']
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint (client-side token removal)"""
    return jsonify({'message': 'Logged out successfully'}), 200