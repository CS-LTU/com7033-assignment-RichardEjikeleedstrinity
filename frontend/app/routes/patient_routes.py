# app/routes/patient_routes.py
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.services.api_client import api_client, login_required
from bson import ObjectId
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, validators
from werkzeug.security import check_password_hash, generate_password_hash

patient_bp = Blueprint('patient', __name__)

class PatientForm(FlaskForm):
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'), 
        ('Female', 'Female'),
        ('Other', 'Other')
    ], validators=[validators.DataRequired()])
    
    age = IntegerField('Age', [
        validators.DataRequired(),
        validators.NumberRange(min=0, max=120)
    ])
    
    hypertension = SelectField('Hypertension', choices=[
        (0, 'No'), 
        (1, 'Yes')
    ], coerce=int)
    
    heart_disease = SelectField('Heart Disease', choices=[
        (0, 'No'), 
        (1, 'Yes')
    ], coerce=int)
    
    avg_glucose_level = FloatField('Average Glucose Level', [
        validators.DataRequired(),
        validators.NumberRange(min=50, max=500)
    ])
    
    bmi = FloatField('BMI', [
        validators.DataRequired(),
        validators.NumberRange(min=10, max=80)
    ])
    
    smoking_status = SelectField('Smoking Status', choices=[
        ('never smoked', 'Never Smoked'),
        ('formerly smoked', 'Formerly Smoked'),
        ('smokes', 'Smokes'),
        ('Unknown', 'Unknown')
    ])



@patient_bp.route('/patients')
@login_required
def patient_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search_query = request.args.get('search', '')
    
    # Get patients from backend API
    response = api_client.get_patients(page, per_page, search_query)
    
    if 'error' in response:
        flash(f'Error loading patients: {response["error"]}', 'error')
        patients = []
        total_patients = 0
        total_pages = 0
    else:
        patients = response.get('patients', [])
        total_patients = response.get('total', 0)
        total_pages = response.get('total_pages', 0)
    
    # Calculate statistics
    high_risk_count = sum(1 for p in patients if p.get('risk_level') == 'High')
    stroke_cases_count = sum(1 for p in patients if p.get('stroke') == 1)
    
    # Calculate display indices
    skip = (page - 1) * per_page
    start_index = skip + 1
    end_index = min(skip + per_page, total_patients)
    
    return render_template('patient_list.html',
                         patients=patients,
                         current_page=page,
                         total_pages=total_pages,
                         total_patients=total_patients,
                         per_page=per_page,
                         search_query=search_query,
                         high_risk_count=high_risk_count,
                         stroke_cases_count=stroke_cases_count,
                         start_index=start_index,
                         end_index=end_index)

@patient_bp.route('/patient/new', methods=['GET', 'POST'])
@patient_bp.route('/patient/edit/<string:patient_id>', methods=['GET', 'POST'])
@login_required
def patient_form(patient_id=None):
    form = PatientForm()
    patient = None

    if patient_id:
        # Get patient from backend API
        response = api_client.get_patient(patient_id)
        if 'error' not in response:
            patient = response

    if request.method == 'POST':
        # Collect form data
        patient_data = {
            'gender': request.form.get('gender'),
            'age': request.form.get('age', type=int),
            'hypertension': request.form.get('hypertension', type=int),
            'heart_disease': request.form.get('heart_disease', type=int),
            'ever_married': request.form.get('ever_married'),
            'work_type': request.form.get('work_type'),
            'Residence_type': request.form.get('residence_type'),
            'avg_glucose_level': request.form.get('avg_glucose_level', type=float),
            'bmi': request.form.get('bmi', type=float),
            'smoking_status': request.form.get('smoking_status'),
            'name': request.form.get('name', ''),
            'notes': request.form.get('notes', '')
        }

        # Sanitize input
        for key in ['ever_married', 'work_type', 'Residence_type', 'smoking_status', 'name', 'notes']:
            if key in patient_data and patient_data[key]:
                patient_data[key] = sanitize_input(patient_data[key])

        if patient:
            # Update existing patient
            response = api_client.update_patient(patient_id, patient_data)
            if 'error' not in response:
                flash(f'Patient {patient.get("patient_id", "Unknown")} updated successfully!', 'success')
                return redirect(url_for('patient.patient_list'))
            else:
                flash(f'Error updating patient: {response["error"]}', 'error')
        else:
            # Create new patient
            response = api_client.create_patient(patient_data)
            if 'error' not in response:
                # Show the created patient's data
                created_patient = response.get("patient_data", {})
                flash(f'Patient created successfully! ID: {created_patient.get("patient_id", "Unknown")}', 'success')
                flash(f'Patient created successfully! ID: {created_patient}', 'success')
                return render_template('patient_view.html', patient=created_patient, user=session['user'])
        
            else:
                flash(f'Error creating patient: {response["error"]}', 'error')

    # Get recent patients for sidebar
    recent_response = api_client.get_patients(1, 5)
    existing_patients = recent_response.get('patients', []) if 'error' not in recent_response else []

    risk_score = patient.get('risk_score', 0) if patient else 0

    return render_template('patient_form.html',
                           patient=patient,
                           existing_patients=existing_patients,
                           risk_score=risk_score,
                           form=form,
                           user=session['user'])

@patient_bp.route('/patient/delete/<string:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    # Delete patient via backend API
    response = api_client.delete_patient(patient_id)
    
    if 'error' not in response:
        
        flash('Patient deleted successfully!', 'success')
    else:
        flash(f'Error deleting patient: {response["error"]}', 'error')
    
    return redirect(url_for('patient.patient_list'))

@patient_bp.route('/patient/view/<string:patient_id>')
@login_required
def view_patient(patient_id):
    # Get patient from backend API
    response = api_client.get_patient(patient_id)
    
    if 'error' in response:
        flash(f'Error loading patient: {response["error"]}', 'error')
        return redirect(url_for('patient.patient_list'))
    
    return render_template('patient_view.html',
                         patient=response,
                         user=session['user'])