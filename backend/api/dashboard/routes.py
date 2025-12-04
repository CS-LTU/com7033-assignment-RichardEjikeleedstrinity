from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta

from flask_pymongo import PyMongo
from api.help_utils.mongodb import mongo

dashboard_bp = Blueprint('dashboard', __name__)
@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        print("Starting /stats route execution...")
        print(mongo.db)
        # Total patients
        total_patients = mongo.db.patients.count_documents({})
        print(f"Total patients: {total_patients}")

        # High risk patients (risk_score >= 70)
        high_risk_patients = mongo.db.patients.count_documents({'risk_score': {'$gte': 70}})
        print(f"High risk patients: {high_risk_patients}")

        # Today's date
        today = datetime.utcnow().date()
        start_of_day = datetime(today.year, today.month, today.day)
        print(f"Today's date: {today}, Start of day: {start_of_day}")

        # Patients added today
        todays_patients = mongo.db.patients.count_documents({
            'created_at': {'$gte': start_of_day}
        })
        print(f"Patients added today: {todays_patients}")

        # Risk distribution
        pipeline = [
            {
                '$group': {
                    '_id': '$risk_level',
                    'count': {'$sum': 1}
                }
            }
        ]
        print("Executing risk distribution pipeline...")
        risk_distribution_result = list(mongo.db.patients.aggregate(pipeline))
        print(f"Risk distribution result: {risk_distribution_result}")

        risk_distribution = {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0}
        for item in risk_distribution_result:
            risk_level = item['_id'] if item['_id'] else 'Unknown'
            risk_distribution[risk_level] = item['count']
        print(f"Formatted risk distribution: {risk_distribution}")

        # Recent patients (last 5)
        print("Fetching recent patients...")
        recent_patients = list(mongo.db.patients.find(
            {},
            {'patient_id': 1, 'name': 1, 'age': 1, 'gender': 1, 'risk_score': 1, 'risk_level': 1, 'created_at': 1}
        ).sort('created_at', -1).limit(5))
        print(f"Recent patients: {recent_patients}")

        # Convert ObjectId to string and format dates
        for patient in recent_patients:
            patient['_id'] = str(patient['_id'])
            if 'created_at' in patient and isinstance(patient['created_at'], datetime):
                patient['created_at'] = patient['created_at'].isoformat()
        print(f"Formatted recent patients: {recent_patients}")

        # Monthly trend (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        print(f"Six months ago: {six_months_ago}")

        monthly_pipeline = [
            {
                '$match': {
                    'created_at': {'$gte': six_months_ago}
                }
            },
            {
                '$group': {
                    '_id': {
                        'year': {'$year': '$created_at'},
                        'month': {'$month': '$created_at'}
                    },
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id.year': 1, '_id.month': 1}
            }
        ]
        print("Executing monthly trend pipeline...")
        monthly_trend = list(mongo.db.patients.aggregate(monthly_pipeline))
        print(f"Monthly trend result: {monthly_trend}")

        # Format monthly trend
        formatted_trend = []
        for item in monthly_trend:
            formatted_trend.append({
                'month': f"{item['_id']['year']}-{item['_id']['month']:02d}",
                'count': item['count']
            })
        print(f"Formatted monthly trend: {formatted_trend}")

        # Gender distribution
        gender_pipeline = [
            {
                '$group': {
                    '_id': '$gender',
                    'count': {'$sum': 1}
                }
            }
        ]

        
        gender_distribution = list(mongo.db.patients.aggregate(gender_pipeline))


        # Return the response
        response = {
            'stats': {
                'total_patients': total_patients,
                'high_risk_patients': high_risk_patients,
                'todays_patients': todays_patients,
                'risk_distribution': risk_distribution
            },
            'recent_patients': recent_patients,
            'monthly_trend': formatted_trend,
            'gender_distribution': gender_distribution
        }
        print(f"Response: {response}")
        return jsonify(response), 200

    except Exception as e:
        print(f"Error in /stats: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

@dashboard_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Get advanced analytics"""
    try:
        # Average risk score
        avg_risk_score = mongo.db.patients.aggregate([
            {
                '$group': {
                    '_id': None,
                    'avg_risk': {'$avg': '$risk_score'}
                }
            }
        ])
        
        avg_risk_result = list(avg_risk_score)
        avg_risk = avg_risk_result[0]['avg_risk'] if avg_risk_result else 0
        
        # Age distribution
        age_pipeline = [
            {
                '$bucket': {
                    'groupBy': '$age',
                    'boundaries': [0, 18, 30, 40, 50, 60, 70, 100],
                    'default': 'Other',
                    'output': {
                        'count': {'$sum': 1},
                        'avg_risk': {'$avg': '$risk_score'}
                    }
                }
            }
        ]
        
        age_distribution = list(mongo.db.patients.aggregate(age_pipeline))
        
        # BMI categories
        bmi_pipeline = [
            {
                '$bucket': {
                    'groupBy': '$bmi',
                    'boundaries': [0, 18.5, 25, 30, 100],
                    'default': 'Other',
                    'output': {
                        'count': {'$sum': 1}
                    }
                }
            }
        ]
        
        bmi_categories = list(mongo.db.patients.aggregate(bmi_pipeline))
        
        # Risk factors correlation
        risk_factors = {
            'hypertension': mongo.db.patients.count_documents({'hypertension': 1}),
            'heart_disease': mongo.db.patients.count_documents({'heart_disease': 1}),
            'smoking': mongo.db.patients.count_documents({'smoking_status': 'smokes'})
        }
        
        return jsonify({
            'analytics': {
                'average_risk_score': round(avg_risk, 2),
                'age_distribution': age_distribution,
                'bmi_categories': bmi_categories,
                'risk_factors': risk_factors
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500