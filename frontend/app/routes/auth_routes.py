
# app/routes/auth_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired, Email

import requests
import json

auth_bp = Blueprint('auth', __name__)

# Your backend API base URL
API_BASE_URL = 'http://localhost:3000/api'

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html', form=form)

        try:
            # Call your backend API service
            response = requests.post(
                f'{API_BASE_URL}/auth/register',
                json={
                    'email': email,
                    'password': password,
                    'name': first_name + last_name,
                 
                },
                headers={'Content-Type': 'application/json'}
            )
            print("Registration response received")
            print(response.status_code)
            print(response.text)
            if response.status_code == 201:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                error_data = response.json()
                flash(f'Registration failed: {error_data.get("error", "Unable to register")}', 'error')
                
        except requests.exceptions.RequestException as e:
            flash(f'Connection error: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('register.html', form=form)
@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        try:
            # Call your backend API service
            response = requests.post(
                f'{API_BASE_URL}/auth/login',
                json={'email': email, 'password': password},
                headers={'Content-Type': 'application/json'}
            )
            print("Login response received")
            print(response.status_code)
            print(response.text)
            if response.status_code == 200:
                data = response.json()
                
                # Store token and user info in session
                session['token'] = data['token']
                session['user'] = data['user']
                session['logged_in'] = True
                
                flash('Login successful!', 'success')
                
                # Redirect based on role
                if data['user']['role'] == 'admin':
                    return redirect(url_for('dashboard.dashboard'))
                else:
                    return redirect(url_for('patient.patient_list'))
            else:
                error_data = response.json()
                flash(f'Login failed: {error_data.get("error", "Invalid credentials")}', 'error')
                
        except requests.exceptions.RequestException as e:
            flash(f'Connection error: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    # Clear session
    session.pop('token', None)
    session.pop('user', None)
    session.pop('logged_in', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))