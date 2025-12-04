from flask_pymongo import PyMongo
from bson import ObjectId
from datetime import datetime

mongo = PyMongo()

class MongoDB:
    @staticmethod
    def get_collection(collection_name):
        return mongo.db[collection_name]
    
    @staticmethod
    def object_id(id_str):
        return ObjectId(id_str)
    
    @staticmethod
    def is_valid_id(id_str):
        try:
            ObjectId(id_str)
            return True
        except:
            return False

# Collections
patients_collection = lambda: MongoDB.get_collection('patients')
users_collection = lambda: MongoDB.get_collection('users')
predictions_collection = lambda: MongoDB.get_collection('predictions')