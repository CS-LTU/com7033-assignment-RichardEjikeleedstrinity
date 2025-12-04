from pymongo import MongoClient
from flask import current_app
from bson import ObjectId
import pandas as pd
from datetime import datetime

from config import Config
from utils.predictions import calculate_risk_score


import ssl
from pymongo import MongoClient

class MongoDBService:
    def __init__(self, app=None):
        self.client = None
        self.db = None
        self.patients_collection = None
        if app is not None:
            self.init_app()
    
    def init_app(self):
        try:
            print('start')
            print(Config.MONGODB_URI)
            
            # CORRECTED: Use tls instead of ssl with proper parameter names
            self.client = MongoClient(
                Config.MONGODB_URI,
                tls=True,  # Use tls instead of ssl
                tlsAllowInvalidCertificates=True,  # Correct parameter name
                serverSelectionTimeoutMS=50000,
                connectTimeoutMS=100000,
                socketTimeoutMS=100000
            )
            
            self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB!")
            
            self.db = self.client[Config.MONGODB_DB_NAME]
            self.patients_collection = self.db[Config.MONGODB_PATIENTS_COLLECTION]
            
            # Create indexes for better performance
            self.patients_collection.create_index([('patient_id', 1)], unique=True)
            self.patients_collection.create_index([('created_at', -1)])
            self.patients_collection.create_index([('risk_score', -1)])
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise
    def update_all_patients_risk_scores(self, batch_size=100):
        """
        Update risk scores for all patients in the database using the ML model
        
        Args:
            batch_size (int): Number of patients to process in each batch
            
        Returns:
            dict: Statistics about the update process
        """
        try:
            print("🔄 Starting to update risk scores for all patients...")
            
            # Get total count of patients
            total_patients = self.patients_collection.count_documents({})
            print(f"📊 Total patients to process: {total_patients}")
            
            updated_count = 0
            error_count = 0
            skipped_count = 0
            
            # Process patients in batches to avoid memory issues
            skip = 0
            while True:
                # Get batch of patients
                patients_batch = list(self.patients_collection.find().skip(skip).limit(batch_size))
                
                if not patients_batch:
                    break  # No more patients to process
                
                print(f"🔄 Processing batch {skip//batch_size + 1}: {len(patients_batch)} patients")
                
                batch_updates = []
                
                for patient in patients_batch:
                    try:
                        # Extract required fields for risk calculation
                        age = patient.get('age')
                        hypertension = patient.get('hypertension', 0)
                        avg_glucose_level = patient.get('avg_glucose_level')
                        bmi = patient.get('bmi')
                        smoking_status = patient.get('smoking_status', 'Unknown')
                        heart_disease = patient.get('heart_disease', 0)
                        gender = patient.get('gender', 'Male')
                        residence_type= patient.get('residence_type'), 
                        work_type = patient.get('work_type'), 
                        ever_married = patient.get('ever_married')
                        
                        # Skip patients with missing required fields
                        if None in [age, avg_glucose_level, bmi]:
                            print(f"⚠️ Skipping patient {patient.get('patient_id', 'Unknown')}: Missing required fields")
                            skipped_count += 1
                            continue
                        
                        # Calculate risk score using your ML model
                        risk_score = calculate_risk_score(
                            age=age,
                            hypertension=hypertension,
                            avg_glucose_level=avg_glucose_level,
                            bmi=bmi,
                            smoking_status=smoking_status,
                            heart_disease=heart_disease,
                            gender=gender,
                              residence_type= residence_type, 
                        work_type = work_type, 
                        ever_married = ever_married
                        )
                        
                        # Determine risk level based on score
                        risk_level = self._determine_risk_level(risk_score)
                        
                        # Prepare update
                        update_data = {
                            'risk_score': risk_score,  # This is now an integer
                            'risk_level': risk_level,  # This is a string
                            'risk_updated_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        }
                        
                        batch_updates.append((
                            {'_id': patient['_id']},
                            {'$set': update_data}
                        ))
                        
                        updated_count += 1
                        
                    except Exception as e:
                        print(f"❌ Error processing patient {patient.get('patient_id', 'Unknown')}: {e}")
                        error_count += 1
                        continue
                
                # Perform batch update
                if batch_updates:
                    for query, update in batch_updates:
                        try:
                            self.patients_collection.update_one(query, update)
                        except Exception as e:
                            print(f"❌ Error updating patient in database: {e}")
                            error_count += 1
                
                skip += batch_size
                print(f"✅ Processed {min(skip, total_patients)}/{total_patients} patients")
            
            # Print summary
            print("\n" + "="*50)
            print("📈 RISK SCORE UPDATE SUMMARY")
            print("="*50)
            print(f"✅ Successfully updated: {updated_count} patients")
            print(f"⚠️ Skipped (missing data): {skipped_count} patients")
            print(f"❌ Errors: {error_count} patients")
            print(f"📊 Total processed: {updated_count + skipped_count + error_count}/{total_patients}")
            
            return {
                'total_patients': total_patients,
                'updated': updated_count,
                'skipped': skipped_count,
                'errors': error_count,
                'success_rate': (updated_count / total_patients * 100) if total_patients > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error in update_all_patients_risk_scores: {e}")
            return {
                'total_patients': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 1,
                'success_rate': 0
            }
    
    def update_single_patient_risk_score(self, patient_id):
        """
        Update risk score for a single patient
        
        Args:
            patient_id: MongoDB _id or custom patient_id
            
        Returns:
            dict: Updated patient data or None if error
        """
        try:
            # Try to find patient by _id first, then by patient_id
            if isinstance(patient_id, ObjectId):
                patient = self.patients_collection.find_one({'_id': patient_id})
            else:
                patient = self.patients_collection.find_one({'patient_id': patient_id})
            
            if not patient:
                print(f"❌ Patient not found: {patient_id}")
                return None
            
            # Extract required fields
            age = patient.get('age')
            hypertension = patient.get('hypertension', 0)
            avg_glucose_level = patient.get('avg_glucose_level')
            bmi = patient.get('bmi')
            smoking_status = patient.get('smoking_status', 'Unknown')
            heart_disease = patient.get('heart_disease', 0)
            gender = patient.get('gender', 'Male'),
            residence_type= patient.get('residence_type'), 
            work_type = patient.get('work_type'), 
            ever_married = patient.get('ever_married')
            
            # Check for missing required fields
            if None in [age, avg_glucose_level, bmi]:
                missing_fields = []
                if age is None: missing_fields.append('age')
                if avg_glucose_level is None: missing_fields.append('avg_glucose_level')
                if bmi is None: missing_fields.append('bmi')
                print(f"❌ Missing required fields for patient {patient_id}: {', '.join(missing_fields)}")
                return None
            
            # Calculate risk score
            risk_score = calculate_risk_score(
                age=age,
                hypertension=hypertension,
                avg_glucose_level=avg_glucose_level,
                bmi=bmi,
                smoking_status=smoking_status,
                heart_disease=heart_disease,
                gender=gender,
                residence_type= residence_type, 
                work_type = work_type, 
                ever_married = ever_married
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Update patient
            update_data = {
                'risk_score': risk_score,  # Integer
                'risk_level': risk_level,  # String
                'risk_updated_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = self.patients_collection.update_one(
                {'_id': patient['_id']},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                print(f"✅ Updated risk score for patient {patient_id}: {risk_score}% ({risk_level})")
                # Return updated patient data
                return self.patients_collection.find_one({'_id': patient['_id']})
            else:
                print(f"⚠️ No changes made for patient {patient_id}")
                return patient
                
        except Exception as e:
            print(f"❌ Error updating risk score for patient {patient_id}: {e}")
            return None
    
    def _determine_risk_level(self, risk_score):
        """
        Determine risk level based on risk score
        
        Args:
            risk_score (int): Risk score from 0-100
            
        Returns:
            str: Risk level category
        """
        if risk_score >= 50:
            return 'High'
        elif risk_score >= 25:
            return 'Medium'
        else:
            return 'Low'
    
    def get_risk_statistics(self):
        """
        Get statistics about current risk scores in the database
        
        Returns:
            dict: Risk statistics
        """
        try:
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'total_patients': {'$sum': 1},
                        'avg_risk_score': {'$avg': '$risk_score'},
                        'max_risk_score': {'$max': '$risk_score'},
                        'min_risk_score': {'$min': '$risk_score'},
                        'high_risk_count': {
                            '$sum': {
                                '$cond': [{'$gte': ['$risk_score', 70]}, 1, 0]
                            }
                        },
                        'medium_risk_count': {
                            '$sum': {
                                '$cond': [
                                    {'$and': [
                                        {'$gte': ['$risk_score', 30]},
                                        {'$lt': ['$risk_score', 70]}
                                    ]}, 1, 0
                                ]
                            }
                        },
                        'low_risk_count': {
                            '$sum': {
                                '$cond': [{'$lt': ['$risk_score', 30]}, 1, 0]
                            }
                        }
                    }
                }
            ]
            
            result = list(self.patients_collection.aggregate(pipeline))
            
            if result:
                stats = result[0]
                stats.pop('_id', None)  # Remove MongoDB group id
                return stats
            else:
                return {
                    'total_patients': 0,
                    'avg_risk_score': 0,
                    'max_risk_score': 0,
                    'min_risk_score': 0,
                    'high_risk_count': 0,
                    'medium_risk_count': 0,
                    'low_risk_count': 0
                }
                
        except Exception as e:
            print(f"❌ Error getting risk statistics: {e}")
            return {}
    
    def insert_patient(self, patient_data):
        """Insert a single patient into MongoDB"""
        try:
            # Calculate risk score for new patient
            risk_score = calculate_risk_score(
                age=patient_data.get('age'),
                hypertension=patient_data.get('hypertension', 0),
                avg_glucose_level=patient_data.get('avg_glucose_level'),
                bmi=patient_data.get('bmi'),
                smoking_status=patient_data.get('smoking_status', 'Unknown'),
                heart_disease=patient_data.get('heart_disease', 0),
                gender=patient_data.get('gender', 'Male')
            )
            
            patient_data['risk_score'] = risk_score
            patient_data['risk_level'] = self._determine_risk_level(risk_score)
            patient_data['created_at'] = datetime.utcnow()
            patient_data['updated_at'] = datetime.utcnow()
            patient_data['risk_updated_at'] = datetime.utcnow()
            
            result = self.patients_collection.insert_one(patient_data)
            print(f"✅ Inserted patient with risk score: {risk_score}%")
            return result.inserted_id
        except Exception as e:
            print(f"❌ Error inserting patient: {e}")
            return None

    def bulk_insert_patients(self, patients_data):
        """Insert multiple patients into MongoDB"""
        try:
            for patient in patients_data:
                patient['created_at'] = datetime.utcnow()
                patient['updated_at'] = datetime.utcnow()
            
            result = self.patients_collection.insert_many(patients_data)
            print(f"✅ Successfully inserted {len(result.inserted_ids)} patients into MongoDB")
            return result.inserted_ids
        except Exception as e:
            print(f"Error bulk inserting patients: {e}")
            return []
    
    def get_all_patients(self, limit=0, skip=0):
        """Get all patients with pagination"""
        try:
            cursor = self.patients_collection.find().sort('created_at', -1).skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"Error getting patients: {e}")
            return []
    
    def get_patient_by_id(self, patient_id):
        """Get patient by MongoDB _id"""
        try:
            return self.patients_collection.find_one({'_id': ObjectId(patient_id)})
        except Exception as e:
            print(f"Error getting patient by ID: {e}")
            return None
    
    def get_patient_by_patient_id(self, patient_id):
        """Get patient by custom patient_id"""
        try:
            return self.patients_collection.find_one({'patient_id': patient_id})
        except Exception as e:
            print(f"Error getting patient by patient_id: {e}")
            return None
    
    def update_patient(self, patient_id, update_data):
        """Update patient data"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            return self.patients_collection.update_one(
                {'_id': ObjectId(patient_id)}, 
                {'$set': update_data}
            )
        except Exception as e:
            print(f"Error updating patient: {e}")
            return None
    
    def delete_patient(self, patient_id):
        """Delete a patient"""
        try:
            return self.patients_collection.delete_one({'_id': ObjectId(patient_id)})
        except Exception as e:
            print(f"Error deleting patient: {e}")
            return None
    
    def count_patients(self):
        """Count total patients"""
        try:
            return self.patients_collection.count_documents({})
        except Exception as e:
            print(f"Error counting patients: {e}")
            return 0
    
    def count_high_risk_patients(self):
        """Count patients with high risk (risk_score >= 70)"""
        try:
            return self.patients_collection.count_documents({'risk_score': {'$gte': 60}})
        except Exception as e:
            print(f"Error counting high risk patients: {e}")
            return 0
    
    def get_risk_distribution(self):
        """Get count of patients by risk level"""
        try:
            pipeline = [
                {
                    '$group': {
                        '_id': '$risk_level',
                        'count': {'$sum': 1}
                    }
                }
            ]
            result = self.patients_collection.aggregate(pipeline)
            distribution = {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0}
            for item in result:
                distribution[item['_id']] = item['count']
            return distribution
        except Exception as e:
            print(f"Error getting risk distribution: {e}")
            return {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0}
    
    def get_recent_patients(self, limit=5):
        """Get most recently added patients"""
        try:
            return list(self.patients_collection.find().sort('created_at', -1).limit(limit))
        except Exception as e:
            print(f"Error getting recent patients: {e}")
            return []

# Create global instance
mongo_service = MongoDBService()

# Usage example
if __name__ == "__main__":
    # Initialize with your Flask app if needed
    mongo_service.init_app()
    
    # Update all patients
    results = mongo_service.update_all_patients_risk_scores(batch_size=50)
    print(f"Update completed: {results}")
    
    # Get statistics
    stats = mongo_service.get_risk_statistics()
    print(f"Current risk statistics: {stats}")
    
    # Update single patient
    # patient = mongo_service.update_single_patient_risk_score("some_patient_id")