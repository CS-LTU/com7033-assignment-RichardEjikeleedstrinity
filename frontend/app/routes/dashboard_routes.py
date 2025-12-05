# app/routes/dashboard_routes.py
from flask import Blueprint, flash, render_template, session, redirect, url_for
from app.services.api_client import api_client, login_required
from datetime import datetime

# Blueprint for dashboard-related routes
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Fetch dashboard stats from the backend API
    stats_response = api_client.get_dashboard_stats()
    
    if 'error' in stats_response:
        # Handle error in fetching stats
        flash(f'Error loading dashboard: {stats_response["error"]}', 'error')
        stats = {
            'total_patients': 0,
            'high_risk_patients': 0,
            'todays_predictions': 0,
            'risk_distribution': {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0},
        }
        recent_patients = []
    else:
        # Extract stats and recent patients from the response
        stats = stats_response.get('stats', {
            'total_patients': 0,
            'high_risk_patients': 0,
            'todays_predictions': 0,
            'risk_distribution': {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0},
        })
        recent_patients = stats_response.get('recent_patients', [])
    
    # Debugging: Print the stats object for verification
    print("Stats object being passed to the template:", stats)
    
    # Process recent patients to include additional details
    processed_patients = []
    for patient in recent_patients:
        risk_score = patient.get('risk_score', 0)
        # Determine risk level based on risk score
        if risk_score >= 60:
            risk_level = "High"
        elif risk_score >= 40:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Ensure the patient name is valid, fallback to "Patient <ID>" if missing
        name = patient.get('name', f"Patient {patient.get('patient_id', 'Unknown')}")
        if not name or name == "None Patient":
            name = f"Patient {patient.get('patient_id', 'Unknown')}"
        
        # Append processed patient data
        processed_patients.append({
            'id': patient.get('patient_id', 'Unknown'),
            'name': name,
            'age': patient.get('age', 'N/A'),
            'gender': patient.get('gender', 'Unknown'),
            'risk_level': risk_level,
            'prediction_date': patient.get('created_at', datetime.utcnow().strftime('%Y-%m-%d'))
        })
    
    # Render the dashboard template with stats and processed patient data
    return render_template('dashboard.html', 
                           stats=stats,
                           recent_patients=processed_patients,
                           user=session['user'])
