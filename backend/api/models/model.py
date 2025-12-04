from datetime import datetime
from api.help_utils.mongodb import mongo

class User:
    @staticmethod
    def create_default_admin():
        """Create default admin user if none exists"""
        users = mongo.db.users
        if users.count_documents({}) == 0:
            import bcrypt
            hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            
            admin_user = {
                'email': 'admin@hospital.com',
                'password': hashed_password,
                'full_name': 'System Administrator',
                'role': 'admin',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            users.insert_one(admin_user)
            print("✅ Default admin user created")
    
    @staticmethod
    def find_by_email(email):
        return mongo.db.users.find_one({'email': email, 'is_active': True})
    
    @staticmethod
    def create_user(user_data):
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        return mongo.db.users.insert_one(user_data)

class Patient:
    @staticmethod
    def create(patient_data):
        patient_data['created_at'] = datetime.utcnow()
        patient_data['updated_at'] = datetime.utcnow()
        return mongo.db.patients.insert_one(patient_data)
    
    @staticmethod
    def find_by_id(patient_id):
        from api.help_utils.mongodb import MongoDB
        if not MongoDB.is_valid_id(patient_id):
            return None
        return mongo.db.patients.find_one({'_id': MongoDB.object_id(patient_id)})
    
    @staticmethod
    def update(patient_id, update_data):
        from api.help_utils.mongodb import MongoDB
        update_data['updated_at'] = datetime.utcnow()
        return mongo.db.patients.update_one(
            {'_id': MongoDB.object_id(patient_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def delete(patient_id):
        from api.help_utils.mongodb import MongoDB
        return mongo.db.patients.delete_one({'_id': MongoDB.object_id(patient_id)})
    
    @staticmethod
    def get_all(page=1, per_page=25, search=None):
        query = {}
        if search:
            query['$or'] = [
                {'patient_id': {'$regex': search, '$options': 'i'}},
                {'name': {'$regex': search, '$options': 'i'}},
                {'gender': {'$regex': search, '$options': 'i'}}
            ]
        
        skip = (page - 1) * per_page
        patients = list(mongo.db.patients.find(query).skip(skip).limit(per_page))
        total = mongo.db.patients.count_documents(query)
        
        return patients, total