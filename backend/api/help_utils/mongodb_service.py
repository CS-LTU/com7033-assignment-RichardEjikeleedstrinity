from flask_pymongo import PyMongo
from bson import ObjectId
from datetime import datetime
import pandas as pd
from werkzeug.security import generate_password_hash
import json

mongo = PyMongo()

class MongoDBService:
    """MongoDB Service with all database operations"""
    
    @staticmethod
    def init_db(app):
        """Initialize database with default data"""
        try:
            # Create indexes
            MongoDBService.create_indexes()
            
            # Create default collections and data
            MongoDBService.create_default_admin()
            MongoDBService.create_default_patients()
            
            print("✅ MongoDB initialized successfully")
        except Exception as e:
            print(f"⚠️ MongoDB initialization error: {e}")
    
    @staticmethod
    def create_indexes():
        """Create database indexes for performance"""
        try:
            # Patients collection indexes
            mongo.db.patients.create_index([("patient_id", 1)], unique=True)
            mongo.db.patients.create_index([("created_at", -1)])
            mongo.db.patients.create_index([("risk_score", -1)])
            mongo.db.patients.create_index([("risk_level", 1)])
            mongo.db.patients.create_index([("name", "text"), ("patient_id", "text")])
            
            # Users collection indexes
            mongo.db.users.create_index([("email", 1)], unique=True)
            mongo.db.users.create_index([("role", 1)])
            
            # Predictions collection indexes
            mongo.db.predictions.create_index([("patient_id", 1)])
            mongo.db.predictions.create_index([("created_at", -1)])
            mongo.db.predictions.create_index([("user_id", 1)])
            
            print("✅ Database indexes created")
        except Exception as e:
            print(f"⚠️ Error creating indexes: {e}")
    
    @staticmethod
    def create_default_admin():
        """Create default admin user"""
        try:
            if mongo.db.users.count_documents({"email": "admin@hospital.com"}) == 0:
                admin_user = {
                    "email": "admin@hospital.com",
                    "password": generate_password_hash("admin123"),
                    "full_name": "System Administrator",
                    "role": "admin",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "settings": {
                        "email_notifications": True,
                        "sms_notifications": False,
                        "dark_mode": False
                    }
                }
                mongo.db.users.insert_one(admin_user)
                print("✅ Default admin user created")
        except Exception as e:
            print(f"⚠️ Error creating admin: {e}")
    
    @staticmethod
    def create_default_patients():
        """Create sample patients for testing"""
        try:
            if mongo.db.patients.count_documents({}) == 0:
                sample_patients = [
                    {
                        "patient_id": "PT00001",
                        "name": "John Smith",
                        "age": 65,
                        "gender": "Male",
                        "hypertension": 1,
                        "heart_disease": 0,
                        "ever_married": "Yes",
                        "work_type": "Private",
                        "Residence_type": "Urban",
                        "avg_glucose_level": 185.5,
                        "bmi": 28.3,
                        "smoking_status": "formerly smoked",
                        "stroke": 0,
                        "risk_score": 75,
                        "risk_level": "High",
                        "notes": "High glucose levels, former smoker",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    {
                        "patient_id": "PT00002",
                        "name": "Mary Johnson",
                        "age": 45,
                        "gender": "Female",
                        "hypertension": 0,
                        "heart_disease": 0,
                        "ever_married": "Yes",
                        "work_type": "Self-employed",
                        "Residence_type": "Rural",
                        "avg_glucose_level": 120.0,
                        "bmi": 24.5,
                        "smoking_status": "never smoked",
                        "stroke": 0,
                        "risk_score": 25,
                        "risk_level": "Low",
                        "notes": "Healthy lifestyle",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    {
                        "patient_id": "PT00003",
                        "name": "Robert Chen",
                        "age": 58,
                        "gender": "Male",
                        "hypertension": 1,
                        "heart_disease": 1,
                        "ever_married": "Yes",
                        "work_type": "Govt_job",
                        "Residence_type": "Urban",
                        "avg_glucose_level": 210.0,
                        "bmi": 32.1,
                        "smoking_status": "smokes",
                        "stroke": 1,
                        "risk_score": 90,
                        "risk_level": "High",
                        "notes": "Previous stroke patient, multiple risk factors",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    {
                        "patient_id": "PT00004",
                        "name": "Sarah Williams",
                        "age": 72,
                        "gender": "Female",
                        "hypertension": 0,
                        "heart_disease": 0,
                        "ever_married": "No",
                        "work_type": "Never_worked",
                        "Residence_type": "Urban",
                        "avg_glucose_level": 95.0,
                        "bmi": 22.8,
                        "smoking_status": "never smoked",
                        "stroke": 0,
                        "risk_score": 35,
                        "risk_level": "Low",
                        "notes": "Elderly but healthy",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    {
                        "patient_id": "PT00005",
                        "name": "David Brown",
                        "age": 50,
                        "gender": "Male",
                        "hypertension": 1,
                        "heart_disease": 0,
                        "ever_married": "Yes",
                        "work_type": "Private",
                        "Residence_type": "Urban",
                        "avg_glucose_level": 160.0,
                        "bmi": 31.5,
                        "smoking_status": "smokes",
                        "stroke": 0,
                        "risk_score": 65,
                        "risk_level": "Medium",
                        "notes": "Hypertension with smoking habit",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                ]
                
                mongo.db.patients.insert_many(sample_patients)
                print(f"✅ {len(sample_patients)} sample patients created")
        except Exception as e:
            print(f"⚠️ Error creating sample patients: {e}")
    
    # Patients Operations
    @staticmethod
    def get_patients(page=1, per_page=25, filters=None, sort_field="created_at", sort_order=-1):
        """Get patients with pagination and filtering"""
        try:
            query = filters or {}
            
            # Handle search
            if "search" in query and query["search"]:
                search_term = query.pop("search")
                query["$or"] = [
                    {"patient_id": {"$regex": search_term, "$options": "i"}},
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"gender": {"$regex": search_term, "$options": "i"}},
                    {"risk_level": {"$regex": search_term, "$options": "i"}}
                ]
            
            skip = (page - 1) * per_page
            sort = [(sort_field, sort_order)]
            
            cursor = mongo.db.patients.find(query).sort(sort).skip(skip).limit(per_page)
            patients = list(cursor)
            
            # Convert ObjectId to string
            for patient in patients:
                patient["_id"] = str(patient["_id"])
                if "created_at" in patient and isinstance(patient["created_at"], datetime):
                    patient["created_at"] = patient["created_at"].isoformat()
                if "updated_at" in patient and isinstance(patient["updated_at"], datetime):
                    patient["updated_at"] = patient["updated_at"].isoformat()
            
            total = mongo.db.patients.count_documents(query)
            
            return {
                "patients": patients,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        except Exception as e:
            print(f"Error getting patients: {e}")
            return {"patients": [], "total": 0, "page": page, "per_page": per_page}
    
    @staticmethod
    def get_patient_by_id(patient_id):
        """Get patient by MongoDB _id"""
        try:
            if not ObjectId.is_valid(patient_id):
                return None
            
            patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
            if patient:
                patient["_id"] = str(patient["_id"])
                if "created_at" in patient and isinstance(patient["created_at"], datetime):
                    patient["created_at"] = patient["created_at"].isoformat()
                if "updated_at" in patient and isinstance(patient["updated_at"], datetime):
                    patient["updated_at"] = patient["updated_at"].isoformat()
            return patient
        except Exception as e:
            print(f"Error getting patient: {e}")
            return None
    
    @staticmethod
    def create_patient(patient_data):
        """Create new patient"""
        try:
            # Generate patient ID if not provided
            if "patient_id" not in patient_data:
                last_patient = mongo.db.patients.find_one(
                    {}, 
                    sort=[("patient_id", -1)]
                )
                if last_patient and "patient_id" in last_patient:
                    last_num = int(last_patient["patient_id"][2:])
                    patient_data["patient_id"] = f"PT{last_num + 1:05d}"
                else:
                    patient_data["patient_id"] = "PT00001"
            
            # Set timestamps
            patient_data["created_at"] = datetime.utcnow()
            patient_data["updated_at"] = datetime.utcnow()
            
            # Insert patient
            result = mongo.db.patients.insert_one(patient_data)
            
            if result.inserted_id:
                return {
                    "success": True,
                    "patient_id": str(result.inserted_id),
                    "data": patient_data
                }
            return {"success": False, "error": "Failed to create patient"}
        except Exception as e:
            print(f"Error creating patient: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_patient(patient_id, update_data):
        """Update patient"""
        try:
            if not ObjectId.is_valid(patient_id):
                return {"success": False, "error": "Invalid patient ID"}
            
            # Update timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update patient
            result = mongo.db.patients.update_one(
                {"_id": ObjectId(patient_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return {
                    "success": True,
                    "modified_count": result.modified_count
                }
            return {"success": False, "error": "Patient not found or no changes made"}
        except Exception as e:
            print(f"Error updating patient: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_patient(patient_id):
        """Delete patient"""
        try:
            if not ObjectId.is_valid(patient_id):
                return {"success": False, "error": "Invalid patient ID"}
            
            result = mongo.db.patients.delete_one({"_id": ObjectId(patient_id)})
            
            if result.deleted_count > 0:
                return {"success": True, "deleted_count": result.deleted_count}
            return {"success": False, "error": "Patient not found"}
        except Exception as e:
            print(f"Error deleting patient: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def bulk_import_patients(patients_data):
        """Bulk import patients"""
        try:
            if not isinstance(patients_data, list):
                return {"success": False, "error": "Expected array of patients"}
            
            processed_count = 0
            errors = []
            
            for idx, patient in enumerate(patients_data):
                try:
                    # Generate patient ID
                    last_patient = mongo.db.patients.find_one(
                        {}, 
                        sort=[("patient_id", -1)]
                    )
                    if last_patient and "patient_id" in last_patient:
                        last_num = int(last_patient["patient_id"][2:])
                        patient_id_num = last_num + processed_count + 1
                    else:
                        patient_id_num = processed_count + 1
                    
                    patient["patient_id"] = f"PT{patient_id_num:05d}"
                    patient["created_at"] = datetime.utcnow()
                    patient["updated_at"] = datetime.utcnow()
                    
                    mongo.db.patients.insert_one(patient)
                    processed_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {idx + 1}: {str(e)}")
            
            return {
                "success": True,
                "imported_count": processed_count,
                "errors": errors if errors else None
            }
        except Exception as e:
            print(f"Error bulk importing patients: {e}")
            return {"success": False, "error": str(e)}
    
    # Dashboard Statistics
    @staticmethod
    def get_dashboard_stats():
        """Get dashboard statistics"""
        try:
            # Total patients
            total_patients = mongo.db.patients.count_documents({})
            
            # High risk patients
            high_risk_patients = mongo.db.patients.count_documents({"risk_score": {"$gte": 70}})
            
            # Medium risk patients
            medium_risk_patients = mongo.db.patients.count_documents({
                "risk_score": {"$gte": 40, "$lt": 70}
            })
            
            # Low risk patients
            low_risk_patients = mongo.db.patients.count_documents({"risk_score": {"$lt": 40}})
            
            # Patients added today
            today = datetime.utcnow().date()
            start_of_day = datetime(today.year, today.month, today.day)
            todays_patients = mongo.db.patients.count_documents({
                "created_at": {"$gte": start_of_day}
            })
            
            # Stroke cases
            stroke_cases = mongo.db.patients.count_documents({"stroke": 1})
            
            # Gender distribution
            gender_distribution = list(mongo.db.patients.aggregate([
                {"$group": {"_id": "$gender", "count": {"$sum": 1}}}
            ]))
            
            # Age distribution
            age_distribution = list(mongo.db.patients.aggregate([
                {"$bucket": {
                    "groupBy": "$age",
                    "boundaries": [0, 18, 30, 40, 50, 60, 70, 100],
                    "default": "Other",
                    "output": {
                        "count": {"$sum": 1},
                        "avg_risk": {"$avg": "$risk_score"}
                    }
                }}
            ]))
            
            # Recent patients (last 5)
            recent_patients = list(mongo.db.patients.find(
                {},
                {
                    "patient_id": 1,
                    "name": 1,
                    "age": 1,
                    "gender": 1,
                    "risk_score": 1,
                    "risk_level": 1,
                    "created_at": 1
                }
            ).sort("created_at", -1).limit(5))
            
            # Format recent patients
            for patient in recent_patients:
                patient["_id"] = str(patient["_id"])
                if "created_at" in patient and isinstance(patient["created_at"], datetime):
                    patient["created_at"] = patient["created_at"].strftime("%Y-%m-%d")
            
            return {
                "total_patients": total_patients,
                "high_risk_patients": high_risk_patients,
                "medium_risk_patients": medium_risk_patients,
                "low_risk_patients": low_risk_patients,
                "todays_patients": todays_patients,
                "stroke_cases": stroke_cases,
                "gender_distribution": gender_distribution,
                "age_distribution": age_distribution,
                "recent_patients": recent_patients
            }
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {}
    
    @staticmethod
    def get_risk_analysis():
        """Get detailed risk analysis"""
        try:
            # Average risk score
            avg_risk = mongo.db.patients.aggregate([
                {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
            ])
            avg_risk_result = list(avg_risk)
            average_risk = round(avg_risk_result[0]["avg_risk"], 2) if avg_risk_result else 0
            
            # Risk factors correlation
            risk_factors = {
                "hypertension": mongo.db.patients.count_documents({"hypertension": 1}),
                "heart_disease": mongo.db.patients.count_documents({"heart_disease": 1}),
                "smoking": mongo.db.patients.count_documents({"smoking_status": "smokes"}),
                "obesity": mongo.db.patients.count_documents({"bmi": {"$gte": 30}}),
                "high_glucose": mongo.db.patients.count_documents({"avg_glucose_level": {"$gte": 200}})
            }
            
            # Monthly trend (last 6 months)
            six_months_ago = datetime.utcnow().replace(day=1)  # First day of current month
            for _ in range(5):
                # Go back 5 more months
                if six_months_ago.month == 1:
                    six_months_ago = six_months_ago.replace(year=six_months_ago.year - 1, month=12)
                else:
                    six_months_ago = six_months_ago.replace(month=six_months_ago.month - 1)
            
            monthly_trend = list(mongo.db.patients.aggregate([
                {"$match": {"created_at": {"$gte": six_months_ago}}},
                {"$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"}
                    },
                    "count": {"$sum": 1},
                    "avg_risk": {"$avg": "$risk_score"}
                }},
                {"$sort": {"_id.year": 1, "_id.month": 1}}
            ]))
            
            return {
                "average_risk_score": average_risk,
                "risk_factors": risk_factors,
                "monthly_trend": monthly_trend
            }
        except Exception as e:
            print(f"Error getting risk analysis: {e}")
            return {}
    
    # User Operations
    @staticmethod
    def find_user_by_email(email):
        """Find user by email"""
        try:
            return mongo.db.users.find_one({"email": email, "is_active": True})
        except Exception as e:
            print(f"Error finding user: {e}")
            return None
    
    @staticmethod
    def create_user(user_data):
        """Create new user"""
        try:
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            user_data.setdefault("is_active", True)
            user_data.setdefault("role", "doctor")
            
            result = mongo.db.users.insert_one(user_data)
            return {"success": True, "user_id": str(result.inserted_id)}
        except Exception as e:
            print(f"Error creating user: {e}")
            return {"success": False, "error": str(e)}
    
    # Prediction Operations
    @staticmethod
    def save_prediction(prediction_data):
        """Save prediction"""
        try:
            prediction_data["created_at"] = datetime.utcnow()
            result = mongo.db.predictions.insert_one(prediction_data)
            return {"success": True, "prediction_id": str(result.inserted_id)}
        except Exception as e:
            print(f"Error saving prediction: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_patient_predictions(patient_id):
        """Get predictions for a patient"""
        try:
            predictions = list(mongo.db.predictions.find(
                {"patient_id": patient_id}
            ).sort("created_at", -1))
            
            for pred in predictions:
                pred["_id"] = str(pred["_id"])
                if "created_at" in pred and isinstance(pred["created_at"], datetime):
                    pred["created_at"] = pred["created_at"].isoformat()
            
            return predictions
        except Exception as e:
            print(f"Error getting predictions: {e}")
            return []